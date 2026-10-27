"""Guard the historical Render migration revision against accidental removal."""

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
            "0003_saved_analysis_idempotency",
        )

    def test_missing_historically_stamped_revision_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="phishlens-migration-") as temporary:
            repo_root = Path(temporary)
            shutil.copytree(ROOT / "backend", repo_root / "backend")
            missing_revision = (
                repo_root / "backend" / "migrations" / "versions" / "0002_analysis_provenance.py"
            )
            missing_revision.unlink()

            with self.assertRaisesRegex(MigrationLineageError, "0002_analysis_provenance"):
                verify_migration_lineage(repo_root)


if __name__ == "__main__":
    unittest.main()

