import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class HostedStagingTrustBoundaryTests(unittest.TestCase):
    def test_pr_ci_has_no_render_or_synthetic_auth_credentials(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        for secret_name in (
            "RENDER_STAGING_API_KEY",
            "STAGING_AUTH_USER_A_EMAIL",
            "STAGING_AUTH_USER_A_PASSWORD",
            "STAGING_AUTH_USER_B_EMAIL",
            "STAGING_AUTH_USER_B_PASSWORD",
        ):
            with self.subTest(secret_name=secret_name):
                self.assertNotIn(secret_name, workflow)
        self.assertNotIn("environment: staging", workflow)
        self.assertNotIn("node pr-source/", workflow)

    def test_staging_deployment_uses_only_the_trusted_default_branch_controller(self):
        workflow = (ROOT / ".github/workflows/secretary-preview.yml").read_text(encoding="utf-8")

        self.assertIn("workflow_run:", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("environment: staging", workflow)
        self.assertIn("RENDER_STAGING_API_KEY: ${{ secrets.RENDER_STAGING_API_KEY }}", workflow)
        self.assertNotIn("github.event.workflow_run.head_sha }}\n          path:", workflow)


if __name__ == "__main__":
    unittest.main()
