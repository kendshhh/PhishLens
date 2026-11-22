"""Apply migrations only to a separately attested schema-only staging branch."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_QUERY = {"sslmode", "channel_binding"}


def verified_migration_head() -> str:
    """Load the migration checker using the repository package namespace."""
    from scripts.verify_migration_lineage import verify_migration_lineage

    return verify_migration_lineage(ROOT)


def validate_target(env: dict[str, str]) -> str:
    if env.get("STAGING_NEON_SCHEMA_ONLY_ATTESTATION") != "true":
        raise ValueError("Schema-only staging attestation is required")
    if env.get("STAGING_NEON_PARENT_ID", ""):
        raise ValueError("Staging Neon branch must be an independent root")
    branch = env.get("STAGING_NEON_BRANCH_ID", "")
    staging_project = env.get("STAGING_NEON_PROJECT_ID", "")
    production_project = env.get("PRODUCTION_NEON_PROJECT_ID", "")
    if not re.fullmatch(r"br-[a-z0-9-]{8,64}", branch):
        raise ValueError("Staging Neon branch ID is invalid")
    if (not re.fullmatch(r"[a-z0-9-]{8,64}", staging_project)
            or not re.fullmatch(r"[a-z0-9-]{8,64}", production_project)
            or staging_project == production_project):
        raise ValueError("Staging must use a Neon project separate from production")
    if branch == env.get("PRODUCTION_NEON_BRANCH_ID"):
        raise ValueError("Refusing to migrate the production Neon branch")
    staging_host = env.get("STAGING_NEON_EXPECTED_HOST", "").rstrip(".").lower()
    production_host = env.get("PRODUCTION_NEON_EXPECTED_HOST", "").rstrip(".").lower()
    if not staging_host or not production_host or staging_host == production_host:
        raise ValueError("Distinct staging and production Neon hosts must be declared")
    raw_url = env.get("STAGING_MIGRATION_DATABASE_URL", "")
    parsed = urlsplit(raw_url)
    if parsed.scheme not in {"postgres", "postgresql", "postgresql+psycopg"}:
        raise ValueError("Staging migration URL must use PostgreSQL")
    if (parsed.hostname or "").rstrip(".").lower() != staging_host:
        raise ValueError("Migration URL host does not match the attested staging branch host")
    if (parsed.hostname or "").rstrip(".").lower() == production_host:
        raise ValueError("Refusing to migrate the production Neon host")
    expected_database = env.get("STAGING_NEON_DATABASE_NAME", "")
    expected_role = env.get("STAGING_NEON_MIGRATION_ROLE", "")
    if not expected_database or parsed.path != "/" + expected_database:
        raise ValueError("Migration URL database does not match the staging allowlist")
    if unquote(parsed.username or "") != expected_role or not expected_role:
        raise ValueError("Migration URL role does not match the staging migration allowlist")
    if not parsed.password or parsed.fragment or parsed.port not in (None, 5432):
        raise ValueError("Migration URL contains an invalid credential or port")
    parameters = parse_qsl(parsed.query, keep_blank_values=True)
    if len({key for key, _ in parameters}) != len(parameters):
        raise ValueError("Migration URL repeats a connection parameter")
    for key, value in parameters:
        if key not in ALLOWED_QUERY or not value:
            raise ValueError("Migration URL contains an unsupported connection parameter")
    return raw_url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    environment = os.environ.copy()
    try:
        migration_url = validate_target(environment)
    except ValueError as exc:
        parser.exit(1, f"Staging migration rejected: {exc}\n")
    if args.check_only:
        print("Isolated schema-only staging migration target verified; no database request was made.")
        return 0
    environment["DATABASE_URL"] = migration_url
    environment["APP_ENV"] = "staging"
    environment.pop("STAGING_MIGRATION_DATABASE_URL", None)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        cwd=ROOT, env=environment, check=False, capture_output=True, text=True,
    )
    if result.returncode:
        print("Staging migration failed; the protected release run is blocked.", file=sys.stderr)
        return result.returncode
    revision = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "current", "--verbose"],
        cwd=ROOT, env=environment, check=False, capture_output=True, text=True,
    )
    if revision.returncode:
        print("Could not verify the migrated staging revision.", file=sys.stderr)
        return revision.returncode
    expected = verified_migration_head()
    match = re.search(r"^Rev:\s+([A-Za-z0-9_]+)", revision.stdout + "\n" + revision.stderr,
                      flags=re.MULTILINE)
    if not match or match.group(1) != expected:
        print("Staging database revision does not match the checked migration head.", file=sys.stderr)
        return 1
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"migration_revision={expected}\n")
    print(f"Staging schema migration completed at the verified Alembic head {expected}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
