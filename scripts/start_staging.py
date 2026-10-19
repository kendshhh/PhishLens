"""Start only against the separately configured staging database."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.engine import make_url

from backend.core.config import get_database_url


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
    subprocess.run([sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"], check=True)
    subprocess.run([sys.executable, "scripts/seed_demo.py"], check=True)
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
