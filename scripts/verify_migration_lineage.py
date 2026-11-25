"""Verify the historical Alembic revisions required by hosted staging."""

import argparse
import os
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

REQUIRED_REVISIONS = (
    ("0001_initial_schema", None),
    ("0002_analysis_provenance", "0001_initial_schema"),
    ("0003_saved_analysis_idempotency", "0002_analysis_provenance"),
    ("0004_neon_auth_subject", "0003_saved_analysis_idempotency"),
    ("0005_ai_request_quota", "0004_neon_auth_subject"),
)


class MigrationLineageError(ValueError):
    """Raised when a required historical revision is missing or changed."""


def verify_migration_lineage(repo_root: Path, *, applied_revision: str | None = None) -> str:
    """Return the sole Alembic head after checking required and applied revisions."""
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
    if applied_revision is not None and applied_revision not in revisions:
        raise MigrationLineageError(
            f"Staging's applied revision {applied_revision!r} is missing from the candidate migration graph."
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
    parser.add_argument("--applied-revision", help="Current version_num from the staging database.")
    parser.add_argument("--expected-head", help="Alembic head verified by backend CI for this source.")
    args = parser.parse_args()

    try:
        head = verify_migration_lineage(args.repo_root, applied_revision=args.applied_revision)
        if args.expected_head is not None and head != args.expected_head:
            raise MigrationLineageError(
                f"Candidate Alembic head {head!r} differs from the verified CI head {args.expected_head!r}."
            )
    except MigrationLineageError as exc:
        print(f"Migration preflight failed: {exc}", file=sys.stderr)
        return 1

    lineage = " -> ".join(revision for revision, _ in REQUIRED_REVISIONS)
    print(f"Migration preflight passed: {lineage}; Alembic head is {head}.")
    if args.applied_revision is not None:
        print(f"Staging's applied revision {args.applied_revision} is present in the candidate.")
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as output:
            output.write(f"head={head}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
