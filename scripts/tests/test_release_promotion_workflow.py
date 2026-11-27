"""Protect release-promotion preflight wiring and module-based migration execution."""

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/release-promotion.yml"


class ReleasePromotionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = WORKFLOW.read_text(encoding="utf-8")
        jobs = text.split("jobs:\n", 1)[1]
        matches = list(re.finditer(r"^  ([a-z][a-z0-9-]*):\n", jobs, re.MULTILINE))
        cls.jobs = {
            match.group(1): jobs[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(jobs)]
            for index, match in enumerate(matches)
        }

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

    def test_migration_lineage_is_verified_through_its_supported_cli(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "verify_migration_lineage.py"),
                "--repo-root",
                str(ROOT),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Migration preflight passed:", result.stdout)
        self.assertRegex(result.stdout, r"Alembic head is [A-Za-z0-9_]+\.")

    def test_release_credentials_are_scoped_to_their_protected_environment_jobs(self):
        neon = self.jobs["staging-neon"]
        deploy = self.jobs["deploy-staging"]
        acceptance = self.jobs["staging-acceptance"]

        self.assertIn("environment: staging-neon-preflight", neon)
        self.assertIn("${{ secrets.NEON_API_KEY }}", neon)
        self.assertIn("${{ secrets.STAGING_MIGRATION_DATABASE_URL }}", neon)
        self.assertNotIn("RENDER_STAGING_API_KEY", neon)
        self.assertNotIn("STAGING_AUTH_USER_A_PASSWORD", neon)

        self.assertIn("environment: release-staging", deploy)
        self.assertIn("${{ secrets.RENDER_STAGING_API_KEY }}", deploy)
        self.assertIn("STAGING_RENDER_DATABASE_CONFIG_ATTESTATION", deploy)
        self.assertNotIn("NEON_API_KEY", deploy)
        self.assertNotIn("STAGING_MIGRATION_DATABASE_URL", deploy)
        self.assertNotIn("STAGING_AUTH_USER_A_PASSWORD", deploy)

        self.assertIn("environment: staging", acceptance)
        self.assertIn("${{ secrets.STAGING_AUTH_USER_A_PASSWORD }}", acceptance)
        self.assertIn("${{ secrets.STAGING_AUTH_USER_B_PASSWORD }}", acceptance)
        self.assertIn("${{ secrets.STAGING_AI_APPROVAL_JSON }}", acceptance)
        self.assertNotIn("RENDER_STAGING_API_KEY", acceptance)
        self.assertNotIn("NEON_API_KEY", acceptance)
        self.assertNotIn("STAGING_MIGRATION_DATABASE_URL", acceptance)

    def test_production_requires_all_exact_candidate_staging_gates(self):
        production = self.jobs["production"]
        outcome = self.jobs["release-outcome"]
        for job in ("staging-neon", "deploy-staging", "staging-acceptance"):
            self.assertIn(job, production.split("steps:", 1)[0])
            self.assertIn(job, outcome.split("steps:", 1)[0])
        self.assertIn("STAGING_ACCEPTANCE_RESULT", outcome)
        self.assertIn("STAGING_DEPLOY_RESULT", outcome)
        self.assertIn("authenticated acceptance did not pass", outcome)


if __name__ == "__main__":
    unittest.main()
