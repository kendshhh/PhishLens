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


def get_ai_config() -> tuple[str, str | None, str | None]:
    load_dotenv(ENV_FILE, override=False)
    mode = os.getenv("AI_MODE", "mock").strip().lower()

    if mode in {"mock", "local", "tfidf"}:
        return mode, None, None
    if mode != "gemini":
        raise RuntimeError("AI_MODE must be 'mock', 'gemini', 'local', or 'tfidf'")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required when AI_MODE=gemini")
    if not model:
        raise RuntimeError("GEMINI_MODEL is required when AI_MODE=gemini")

    return mode, api_key, model
