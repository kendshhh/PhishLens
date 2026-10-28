"""Start only against the separately configured staging database."""
import socket
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.engine import URL, make_url

from backend.core.config import get_database_url


def pin_ipv4_addresses(database: URL) -> URL:
    """Keep the Neon hostname for TLS while making libpq try IPv4 routes only."""
    host = database.host
    if not host or "," in host:
        raise SystemExit("Hosted staging requires one DNS hostname for DATABASE_URL.")

    try:
        records = socket.getaddrinfo(
            host,
            database.port or 5432,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
    except OSError as exc:
        raise SystemExit(f"Hosted staging could not resolve an IPv4 address for DATABASE_URL: {exc}") from exc

    addresses = list(dict.fromkeys(record[4][0] for record in records))
    if not addresses:
        raise SystemExit(
            "Hosted staging DATABASE_URL must resolve to an IPv4 address; Render cannot reach the Neon IPv6 route."
        )

    query = dict(database.query)
    query["hostaddr"] = ",".join(addresses)
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
        runtime_database = pin_ipv4_addresses(runtime_database)
        migration_database = pin_ipv4_addresses(migration_database)
        # Keep the owner credential in the migration subprocess only. The API and
        # seed process receive the restricted runtime URL.
        migration_environment["DATABASE_URL"] = migration_database.render_as_string(hide_password=False)
        os.environ["DATABASE_URL"] = runtime_database.render_as_string(hide_password=False)
    else:
        if runtime_database.database != "phishlens_dev" or migration_database.database != "phishlens_dev":
            raise SystemExit("Staging requires a separate development database named phishlens_dev.")
        migration_environment["DATABASE_URL"] = migration_database.render_as_string(hide_password=False)

    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        check=True,
        env=migration_environment,
    )
    # Do not pass the privileged migration URL into seed_demo.py, Uvicorn, or the
    # application process. In hosted staging this stays the restricted app URL.
    os.environ["DATABASE_URL"] = runtime_database.render_as_string(hide_password=False)
    os.environ.pop("STAGING_MIGRATION_DATABASE_URL", None)
    subprocess.run([sys.executable, "scripts/seed_demo.py"], check=True, env=os.environ.copy())
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        loop="backend.core.event_loop:new_event_loop",
    )


if __name__ == "__main__":
    main()

