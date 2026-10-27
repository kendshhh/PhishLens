"""Verify the historical Alembic revisions required by hosted staging."""

import argparse
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

REQUIRED_REVISIONS = (
    ("0001_initial_schema", None),
    ("0002_analysis_provenance", "0001_initial_schema"),
    ("0003_saved_analysis_idempotency", "0002_analysis_provenance"),
)


class MigrationLineageError(ValueError):
    """Raised when a required historical revision is missing or changed."""


def verify_migration_lineage(repo_root: Path) -> str:
    """Return the sole Alembic head after validating Render's stamped history."""
    repo_root = repo_root.resolve()
    config_path = repo_root / "backend" / "alembic.ini"
    if not config_path.is_file():
        raise MigrationLineageError(f"Alembic config not found: {config_path}")

    try:
        script = ScriptDirectory.from_config(Config(str(config_path)))
        revisions = {revision.revision: revision for revision in script.walk_revisions()}
        heads = script.get_heads()
    except Exception as exc:
        raise MigrationLineageError(f"Alembic migration graph cannot be resolved: {exc}") from exc

    for revision_id, expected_parent in REQUIRED_REVISIONS:
        revision = revisions.get(revision_id)
        if revision is None:
            raise MigrationLineageError(
                f"Required historical revision {revision_id!r} is missing from the migration graph."
            )
        if revision.down_revision != expected_parent:
            raise MigrationLineageError(
                f"Revision {revision_id!r} must revise {expected_parent!r}; "
                f"found {revision.down_revision!r}."
            )

    if len(heads) != 1:
        raise MigrationLineageError(
            f"Expected one Alembic head for 'upgrade head'; found {len(heads)}: {heads!r}."
        )
    return heads[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository tree whose backend migration history should be checked.",
    )
    args = parser.parse_args()

    try:
        head = verify_migration_lineage(args.repo_root)
    except MigrationLineageError as exc:
        print(f"Migration preflight failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Migration preflight passed: "
        "0001_initial_schema -> 0002_analysis_provenance -> "
        "0003_saved_analysis_idempotency; "
        f"Alembic head is {head}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
