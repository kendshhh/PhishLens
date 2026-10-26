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


    def test_staging_preflight_runs_before_environment_approval(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        preflight_start = workflow.index("  hosted-staging-preflight:\n")
        hosted_start = workflow.index("  hosted-staging:\n", preflight_start)
        preflight = workflow[preflight_start:hosted_start]
        hosted = workflow[hosted_start:]

        self.assertIn("Check PR head before requesting staging approval", preflight)
        self.assertNotIn("environment: staging", preflight)
        hosted_header = hosted.split("    steps:\n", 1)[0]
        self.assertIn("needs: [staging, hosted-staging-preflight]", hosted_header)
        self.assertIn("needs.staging.result == 'success'", hosted_header)
        self.assertIn("needs.hosted-staging-preflight.result == 'success'", hosted_header)
        self.assertIn("needs.hosted-staging-preflight.outputs.current == 'true'", hosted_header)
        self.assertIn("Recheck PR head after staging approval", hosted)
        self.assertIn("steps.staging-final-preflight.outputs.current == 'true'", hosted)

    def test_new_pr_ci_run_cancels_stale_approval_run(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("phishlens-ci-${{ github.event.pull_request.number || github.ref }}", workflow)
        self.assertIn("cancel-in-progress: true", workflow)

if __name__ == "__main__":
    unittest.main()
