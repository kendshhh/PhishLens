"""Protect release-promotion preflight wiring and module-based migration execution."""

import subprocess
import sys
import unittest
from pathlib import Path

from scripts.migrate_release_staging import verified_migration_head

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/release-promotion.yml"


class ReleasePromotionWorkflowTests(unittest.TestCase):
    def test_neon_target_verifier_receives_both_required_identity_inputs(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        step = workflow.split("- name: Verify isolated schema-only Neon branch metadata", 1)[1]
        step = step.split("- name:", 1)[0]
        environment = step.split("env:", 1)[1].split("run:", 1)[0]

        self.assertIn("STAGING_NEON_EXPECTED_HOST: ${{ vars.STAGING_NEON_EXPECTED_HOST }}", environment)
        self.assertIn("STAGING_NEON_PRODUCTION_ROWS_PRESENT: ${{ vars.STAGING_NEON_PRODUCTION_ROWS_PRESENT }}", environment)

    def test_migration_script_is_invoked_as_a_package_module(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python -m scripts.migrate_release_staging", workflow)
        result = subprocess.run(
            [sys.executable, "-m", "scripts.migrate_release_staging", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("schema-only staging branch", result.stdout)

    def test_migration_lineage_checker_imports_and_matches_the_repository_head(self):
        head = verified_migration_head()
        self.assertRegex(head, r"^[A-Za-z0-9_]+$")


if __name__ == "__main__":
    unittest.main()
