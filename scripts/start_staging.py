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


def main():
    import os

    database = make_url(get_database_url())
    if database.database != "phishlens_dev":
        raise SystemExit("Staging requires a separate development database named phishlens_dev.")
    # Local disposable PostgreSQL needs no cloud host declaration. Hosted staging does.
    if os.getenv("RENDER"):
        expected_host = os.getenv("STAGING_DATABASE_HOST", "")
        if not expected_host or database.host != expected_host or os.getenv("APP_ENV") != "staging":
            raise SystemExit("Hosted staging requires APP_ENV=staging and an exact STAGING_DATABASE_HOST match before migrations.")
        database = pin_ipv4_addresses(database)
        # Pass the same verified direct endpoint and IPv4 address list to Alembic
        # and the API. Keep credentials inside the process environment only.
        os.environ["DATABASE_URL"] = database.render_as_string(hide_password=False)
    subprocess.run([sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"], check=True)
    subprocess.run([sys.executable, "scripts/seed_demo.py"], check=True)
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
