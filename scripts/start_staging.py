"""Start only against the separately configured staging database."""
import queue
import socket
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core.config import get_database_url
from sqlalchemy.engine import URL, make_url

DNS_TIMEOUT_SECONDS = 15
DATABASE_CONNECT_TIMEOUT_SECONDS = 10
MIGRATION_TIMEOUT_SECONDS = 300
SEED_TIMEOUT_SECONDS = 180


def resolve_ipv4_addresses(host: str, port: int) -> list[tuple]:
    """Resolve IPv4 routes with a deadline so startup cannot hang in libc DNS."""
    result: queue.Queue[tuple[list[tuple] | None, OSError | None]] = queue.Queue(maxsize=1)

    def lookup() -> None:
        try:
            result.put((
                socket.getaddrinfo(
                    host,
                    port,
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM,
                ),
                None,
            ))
        except OSError as exc:
            result.put((None, exc))

    threading.Thread(target=lookup, daemon=True).start()
    try:
        records, error = result.get(timeout=DNS_TIMEOUT_SECONDS)
    except queue.Empty as exc:
        raise SystemExit(
            f"Hosted staging IPv4 DNS lookup timed out after {DNS_TIMEOUT_SECONDS} seconds."
        ) from exc
    if error:
        raise SystemExit(
            f"Hosted staging could not resolve an IPv4 address for DATABASE_URL: {error}"
        ) from error
    if records is None:
        raise SystemExit("Hosted staging IPv4 DNS lookup returned no result.")
    return records


def pin_ipv4_addresses(database: URL) -> URL:
    """Keep the Neon hostname for TLS while making libpq try IPv4 routes only."""
    host = database.host
    if not host or "," in host:
        raise SystemExit("Hosted staging requires one DNS hostname for DATABASE_URL.")

    records = resolve_ipv4_addresses(host, database.port or 5432)

    addresses = list(dict.fromkeys(record[4][0] for record in records))
    if not addresses:
        raise SystemExit(
            "Hosted staging DATABASE_URL must resolve to an IPv4 address; Render cannot reach the Neon IPv6 route."
        )

    query = dict(database.query)
    query["hostaddr"] = ",".join(addresses)
    query["connect_timeout"] = str(DATABASE_CONNECT_TIMEOUT_SECONDS)
    return database.set(host=",".join([host] * len(addresses)), query=query)


def validate_hosted_database_urls(runtime: URL, migration: URL, expected_host: str, app_role: str) -> None:
    """Reject production, owner-runtime, or mixed-branch staging credentials."""
    if not expected_host or app_role != "phishlens_staging_app":
        raise SystemExit("Hosted staging requires an isolated host and the phishlens_staging_app role.")
    if runtime.database != "phishlens_dev" or migration.database != "phishlens_dev":
        raise SystemExit("Staging requires both database URLs to target phishlens_dev.")
    if runtime.host != expected_host or migration.host != expected_host:
        raise SystemExit("Staging app and migration URLs must match the isolated STAGING_DATABASE_HOST.")
    if runtime.username != app_role or runtime.username in {"neondb_owner", "cloud_admin"}:
        raise SystemExit("Staging DATABASE_URL must use the configured non-owner app role.")
    if migration.username != "neondb_owner" or migration.username == runtime.username:
        raise SystemExit("Staging migrations require the isolated Neon owner credential, separate from the app role.")


def main():
    import os

    runtime_database = make_url(get_database_url())
    migration_url = os.getenv("STAGING_MIGRATION_DATABASE_URL", "").strip()
    migration_database = make_url(migration_url) if migration_url else runtime_database
    migration_environment = os.environ.copy()
    migration_environment.pop("STAGING_MIGRATION_DATABASE_URL", None)

    # Local disposable PostgreSQL needs no cloud host declaration. Hosted staging does.
    if os.getenv("RENDER"):
        expected_host = os.getenv("STAGING_DATABASE_HOST", "")
        if os.getenv("APP_ENV") != "staging":
            raise SystemExit("Hosted staging requires APP_ENV=staging before migrations.")
        if not migration_url:
            raise SystemExit("Hosted staging requires a separate STAGING_MIGRATION_DATABASE_URL.")
        app_role = os.getenv("STAGING_APP_DATABASE_ROLE", "").strip()
        validate_hosted_database_urls(runtime_database, migration_database, expected_host, app_role)
        print("[staging] resolving IPv4 routes for the runtime database", flush=True)
        runtime_database = pin_ipv4_addresses(runtime_database)
        print("[staging] resolving IPv4 routes for the migration database", flush=True)
        migration_database = pin_ipv4_addresses(migration_database)
        # Keep the owner credential in the migration subprocess only. The API and
        # seed process receive the restricted runtime URL.
        migration_environment["DATABASE_URL"] = migration_database.render_as_string(hide_password=False)
        os.environ["DATABASE_URL"] = runtime_database.render_as_string(hide_password=False)
    else:
        if runtime_database.database != "phishlens_dev" or migration_database.database != "phishlens_dev":
            raise SystemExit("Staging requires a separate development database named phishlens_dev.")
        migration_environment["DATABASE_URL"] = migration_database.render_as_string(hide_password=False)

    print("[staging] applying database migrations", flush=True)
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        check=True,
        env=migration_environment,
        timeout=MIGRATION_TIMEOUT_SECONDS,
    )
    # Do not pass the privileged migration URL into seed_demo.py, Uvicorn, or the
    # application process. In hosted staging this stays the restricted app URL.
    os.environ["DATABASE_URL"] = runtime_database.render_as_string(hide_password=False)
    os.environ.pop("STAGING_MIGRATION_DATABASE_URL", None)
    print("[staging] seeding synthetic staging records", flush=True)
    subprocess.run(
        [sys.executable, "scripts/seed_demo.py"],
        check=True,
        env=os.environ.copy(),
        timeout=SEED_TIMEOUT_SECONDS,
    )
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    print(f"[staging] starting API server on port {port}", flush=True)
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=port,
        loop="backend.core.event_loop:new_event_loop",
    )


if __name__ == "__main__":
    main()
