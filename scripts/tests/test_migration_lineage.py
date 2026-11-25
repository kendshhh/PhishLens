"""Guard the hosted Render migration chain, including historically applied revisions."""

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.verify_migration_lineage import (
    MigrationLineageError,
    verify_migration_lineage,
)

ROOT = Path(__file__).resolve().parents[2]


class MigrationLineageTests(unittest.TestCase):
    def test_current_render_revision_chain_is_valid(self):
        self.assertEqual(
            verify_migration_lineage(ROOT),
            "0005_ai_request_quota",
        )

    def test_missing_historically_stamped_revision_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="phishlens-migration-") as temporary:
            repo_root = Path(temporary)
            shutil.copytree(ROOT / "backend", repo_root / "backend")
            missing_revision = (
                repo_root
                / "backend"
                / "migrations"
                / "versions"
                / "0005_ai_request_quota.py"
            )
            missing_revision.unlink()

            with self.assertRaisesRegex(
                MigrationLineageError,
                "0005_ai_request_quota",
            ):
                verify_migration_lineage(repo_root)

    def test_live_revision_can_be_the_head_or_an_older_revision(self):
        for applied in ("0004_neon_auth_subject", "0005_ai_request_quota"):
            with self.subTest(applied=applied):
                self.assertEqual(
                    verify_migration_lineage(ROOT, applied_revision=applied),
                    "0005_ai_request_quota",
                )

    def test_live_revision_missing_from_candidate_is_rejected(self):
        with self.assertRaisesRegex(
            MigrationLineageError,
            "applied revision '0006_newer' is missing",
        ):
            verify_migration_lineage(ROOT, applied_revision="0006_newer")


if __name__ == "__main__":
    unittest.main()
