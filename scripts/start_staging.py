"""Start only against the separately configured staging database."""
import json
import queue
import re
import socket
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit

from psycopg.conninfo import conninfo_to_dict, make_conninfo
from sqlalchemy.dialects.postgresql.psycopg import PGDialect_psycopg
from sqlalchemy.engine import URL, make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core.config import get_database_url

DNS_TIMEOUT_SECONDS = 15
DATABASE_CONNECT_TIMEOUT_SECONDS = 10
MIGRATION_TIMEOUT_SECONDS = 300
SEED_TIMEOUT_SECONDS = 180

ALLOWED_HOSTED_CONNECTION_QUERY_PARAMETERS = frozenset({"sslmode", "channel_binding"})


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


def _validate_hosted_connection_query(database: URL, name: str) -> None:
    for key, value in database.query.items():
        if not re.fullmatch(r"[a-z_]+", key) or key not in ALLOWED_HOSTED_CONNECTION_QUERY_PARAMETERS:
            raise SystemExit(
                f"Hosted staging {name} URL contains an unsupported query parameter."
            )
        if not isinstance(value, str):
            raise SystemExit(
                f"Hosted staging {name} URL must not repeat query parameters."
            )


def _validate_effective_connection_identity(database: URL, name: str) -> None:
    """Check the parameters psycopg will actually pass to libpq, without connecting."""
    try:
        _, connect_args = PGDialect_psycopg().create_connect_args(database)
        effective = conninfo_to_dict(make_conninfo(**connect_args))
    except Exception as exc:
        raise SystemExit(
            f"Hosted staging {name} URL cannot be parsed safely by the PostgreSQL driver."
        ) from exc

    expected = {
        "user": database.username,
        "dbname": database.database,
        "host": database.host,
        "port": str(database.port or 5432),
    }
    actual = {
        "user": effective.get("user"),
        "dbname": effective.get("dbname"),
        "host": effective.get("host"),
        "port": effective.get("port", "5432"),
    }
    if actual != expected:
        raise SystemExit(
            f"Hosted staging {name} URL has effective driver parameters that do not match its validated identity."
        )

    forbidden = {"hostaddr", "options", "service", "servicefile"}
    if forbidden.intersection(effective):
        raise SystemExit(
            f"Hosted staging {name} URL must not set alternate routing or libpq service parameters."
        )


def _normalized_neon_host(host: str) -> str:
    return re.sub(r"-pooler(?=\.)", "", host.rstrip(".").lower())


def validate_owner_approved_target(
    expected_host: str, project_id: str, branch_id: str, auth_url: str
) -> None:
    """Keep Render startup pinned to the target approved for this release workflow."""
    config_path = Path(__file__).resolve().parents[1] / ".github/secretary.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if (
        _normalized_neon_host(expected_host) != _normalized_neon_host(config.get("staging_database_host", ""))
        or project_id != config.get("staging_neon_project_id")
        or branch_id != config.get("staging_neon_branch_id")
    ):
        raise SystemExit("Hosted staging target differs from the owner-approved Neon project and branch.")
    auth = urlsplit((auth_url or "").strip().rstrip("/"))
    auth_database = config.get("staging_auth_database", "")
    if (
        auth.scheme != "https"
        or auth.hostname != config.get("staging_auth_host")
        or not re.fullmatch(r"[a-zA-Z0-9_-]{1,63}", auth_database)
        or auth.path != f"/{auth_database}/auth"
        or auth.username or auth.password or auth.port is not None
        or auth.query or auth.fragment
    ):
        raise SystemExit("Hosted staging Auth URL differs from the owner-approved Neon branch.")


def validate_hosted_database_urls(
    runtime: URL, migration: URL, expected_host: str, app_role: str,
    production_host: str, staging_project_id: str, production_project_id: str,
    staging_branch_id: str, production_branch_id: str,
) -> None:
    """Reject production, owner-runtime, or mixed-branch staging credentials."""
    for name, database in (("runtime", runtime), ("migration", migration)):
        _validate_hosted_connection_query(database, name)

    normalized_host = _normalized_neon_host(expected_host)
    normalized_production_host = _normalized_neon_host(production_host)
    if (not normalized_host.startswith("ep-") or not normalized_host.endswith(".aws.neon.tech")
            or not normalized_production_host.startswith("ep-")
            or not normalized_production_host.endswith(".aws.neon.tech")
            or normalized_host == normalized_production_host):
        raise SystemExit("Hosted staging must use the verified Neon staging endpoint.")
    if (not re.fullmatch(r"br-[a-z0-9-]{8,64}", staging_branch_id or "")
            or not re.fullmatch(r"br-[a-z0-9-]{8,64}", production_branch_id or "")
            or staging_branch_id == production_branch_id):
        raise SystemExit("Hosted staging must use a distinct verified Neon branch ID.")
    if (not re.fullmatch(r"[a-z0-9-]{8,64}", staging_project_id or "")
            or not re.fullmatch(r"[a-z0-9-]{8,64}", production_project_id or "")
            or staging_project_id == production_project_id):
        raise SystemExit("Hosted staging must use a separate Neon project from production.")
    if app_role != "phishlens_staging_app":
        raise SystemExit("Hosted staging requires an isolated host and the phishlens_staging_app role.")
    if runtime.database != "phishlens_dev" or migration.database != "phishlens_dev":
        raise SystemExit("Staging requires both database URLs to target phishlens_dev.")
    if runtime.host != expected_host or migration.host != expected_host:
        raise SystemExit("Staging app and migration URLs must match the isolated STAGING_DATABASE_HOST.")
    if runtime.username != app_role or runtime.username in {"neondb_owner", "cloud_admin"}:
        raise SystemExit("Staging DATABASE_URL must use the configured non-owner app role.")
    if migration.username != "neondb_owner" or migration.username == runtime.username:
        raise SystemExit("Staging migrations require the isolated Neon owner credential, separate from the app role.")
    _validate_effective_connection_identity(runtime, "runtime")
    _validate_effective_connection_identity(migration, "migration")


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
        production_host = os.getenv("PRODUCTION_NEON_EXPECTED_HOST", "")
        staging_project_id = os.getenv("STAGING_NEON_PROJECT_ID", "")
        production_project_id = os.getenv("PRODUCTION_NEON_PROJECT_ID", "")
        staging_branch_id = os.getenv("STAGING_NEON_BRANCH_ID", "")
        production_branch_id = os.getenv("PRODUCTION_NEON_BRANCH_ID", "")
        if os.getenv("APP_ENV") != "staging":
            raise SystemExit("Hosted staging requires APP_ENV=staging before migrations.")
        if os.getenv("REPORT_AUTH_MODE") != "neon":
            raise SystemExit("Hosted staging requires REPORT_AUTH_MODE=neon before migrations.")
        validate_owner_approved_target(
            expected_host,
            staging_project_id,
            staging_branch_id,
            os.getenv("NEON_AUTH_BASE_URL", ""),
        )
        if _normalized_neon_host(expected_host) != _normalized_neon_host(
                os.getenv("STAGING_NEON_EXPECTED_HOST", "")):
            raise SystemExit("STAGING_DATABASE_HOST does not match the verified staging Neon branch endpoint.")
        if not migration_url:
            raise SystemExit("Hosted staging requires a separate STAGING_MIGRATION_DATABASE_URL.")
        app_role = os.getenv("STAGING_APP_DATABASE_ROLE", "").strip()
        validate_hosted_database_urls(
            runtime_database, migration_database, expected_host, app_role,
            production_host, staging_project_id, production_project_id,
            staging_branch_id, production_branch_id,
        )
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
