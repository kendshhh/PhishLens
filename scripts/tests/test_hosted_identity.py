"""Hosted acceptance must identify the requested staging commit and data."""
import copy
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.secretary.preview import smoke

SHA = "a" * 40
ROOT = Path(__file__).resolve().parents[2]


class HostedIdentityTests(unittest.TestCase):
    def responses(self):
        return [
            {"status": "ok", "service": "phishlens-api"},
            {"status": "ready", "database": "connected"},
            {"commit": SHA, "environment": "staging"},
            {"items": [{"subject": "Synthetic account notice"}]},
        ]

    def verify(self, payloads):
        responses = [io.BytesIO(json.dumps(value).encode()) for value in payloads]
        with patch("urllib.request.urlopen", side_effect=responses), patch(
            "scripts.secretary.preview.time.monotonic", side_effect=[0, 181]
        ):
            return smoke("https://staging.invalid", SHA)

    def test_exact_staging_commit_and_seed_pass(self):
        evidence = self.verify(self.responses())
        self.assertEqual(evidence["version"], SHA)
        self.assertEqual(evidence["history"], "passed")

    def test_wrong_commit_fails(self):
        values = self.responses()
        values[2]["commit"] = "b" * 40
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_production_environment_fails(self):
        values = self.responses()
        values[2]["environment"] = "production"
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_missing_synthetic_history_fails(self):
        values = self.responses()
        values[3]["items"] = []
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_unhealthy_or_unready_service_fails(self):
        for index in (0, 1):
            with self.subTest(index=index):
                values = copy.deepcopy(self.responses())
                values[index]["status"] = "unavailable"
                with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
                    self.verify(values)

    def test_stale_runs_are_filtered_before_staging_approval(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        preflight_start = workflow.index("  hosted-staging-preflight:\n")
        hosted_start = workflow.index("  hosted-staging:\n", preflight_start)
        preflight_job = workflow[preflight_start:hosted_start]
        hosted_job = workflow[hosted_start:]

        self.assertIn("needs: [staging]", preflight_job)
        self.assertIn("pull-requests: read", preflight_job)
        self.assertIn("outputs:\n      current: ${{ steps.staging-preflight.outputs.current }}", preflight_job)
        self.assertNotIn("environment: staging", preflight_job)
        self.assertIn("current['head']['sha'] == expected", preflight_job)
        self.assertIn("github.event.pull_request.user.login != 'dependabot[bot]'", preflight_job)
        hosted_header = hosted_job.split("    steps:\n", 1)[0]
        self.assertIn("needs: [staging, hosted-staging-preflight]", hosted_header)
        self.assertIn("always()", hosted_header)
        self.assertIn("needs.staging.result == 'success'", hosted_header)
        self.assertIn("needs.hosted-staging-preflight.outputs.current == 'true'", hosted_header)
        self.assertIn("github.event.pull_request.user.login != 'dependabot[bot]'", hosted_header)
        self.assertIn("environment: staging", hosted_header)

    def test_hosted_staging_rechecks_current_head_after_approval(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        hosted_start = workflow.index("  hosted-staging:\n")
        hosted_job = workflow[hosted_start:]
        preflight_marker = "      - name: Recheck PR head after staging approval"
        preflight_start = hosted_job.index(preflight_marker)
        deploy_start = hosted_job.index("      - name: Deploy PR merge commit using the trusted legacy script", preflight_start)
        preflight = hosted_job[preflight_start:deploy_start]
        marker = "      - name: Verify deployed merge identity and package staging assets"
        start = hosted_job.index(marker)
        end = hosted_job.index("      - name: Preserve hosted staging evidence and extension", start)
        step = hosted_job[start:end]

        self.assertIn("current['head']['sha'] == expected", preflight)
        self.assertIn("steps.staging-final-preflight.outputs.current == 'true'", hosted_job[deploy_start:start])
        self.assertIn("STAGING_COMMIT: ${{ github.sha }}", step)
        self.assertIn("STAGING_PR_HEAD_SHA: ${{ github.event.pull_request.head.sha }}", step)
        self.assertIn("deploy_sha = os.environ['STAGING_COMMIT']", step)
        self.assertIn("pr_head_sha = os.environ['STAGING_PR_HEAD_SHA']", step)
        self.assertIn("current['head']['sha'] == pr_head_sha", step)
        self.assertNotIn("current['head']['sha'] != deploy_sha", step)
        self.assertIn("'deployed_commit': deploy_sha", step)
        self.assertIn("result.write('current=false\\n')", step)
        self.assertIn("raise SystemExit(0)", step)
        self.assertIn("steps.verify-hosted-staging.outputs.current == 'true'", hosted_job[end:])


if __name__ == "__main__":
    unittest.main()
