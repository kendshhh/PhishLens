"""Canonical synthetic Render staging environment for control-plane tests."""

STAGING_HOST = "staging.invalid"
PRODUCTION_HOST = "production.invalid"


def render_staging_environment_rows(**overrides):
    """Build the complete least-privilege environment returned by Render."""
    values = {
        "DATABASE_URL": f"postgresql://phishlens_staging_app:synthetic@{STAGING_HOST}/phishlens_dev",
        "STAGING_MIGRATION_DATABASE_URL": f"postgresql://neondb_owner:synthetic@{STAGING_HOST}/phishlens_dev",
        "STAGING_APP_DATABASE_ROLE": "phishlens_staging_app",
        "STAGING_DATABASE_HOST": STAGING_HOST,
        "APP_ENV": "staging",
        "AI_MODE": "mock",
    }
    values.update(overrides)
    return [{"envVar": {"key": key, "value": value}} for key, value in values.items()]


def set_render_environment_value(rows, key, value):
    """Change one Render variable in a fixture without depending on row order."""
    for row in rows:
        if row["envVar"]["key"] == key:
            row["envVar"]["value"] = value
            return
    raise KeyError(key)
