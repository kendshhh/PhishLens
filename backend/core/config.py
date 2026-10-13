"""Load local settings explicitly, including when invoked by Alembic or scripts."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def get_database_url() -> str:
    load_dotenv(ENV_FILE, override=False)
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(f"DATABASE_URL is missing; set it in {ENV_FILE} or the environment")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql+psycopg://"):
        return url
    raise RuntimeError("DATABASE_URL must be a PostgreSQL URL")
