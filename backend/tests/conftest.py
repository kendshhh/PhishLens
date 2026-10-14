"""Provide a non-secret URL before the registered app is imported by tests."""

import os

# CI supplies its isolated PostgreSQL URL. HTTP unit tests override get_db
# and never connect to this fallback database.
os.environ.setdefault(
    "DATABASE_URL", "postgresql://test:test@localhost/phishlens_dev"
)
