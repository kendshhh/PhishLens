import unittest

from scripts.secretary.production_drift import inspect_production

SHA = "a" * 40
ORIGIN = "https://example.invalid"


class FakeGitHub:
    def __init__(self, sha=SHA):
        self.sha = sha

    def request(self, path):
        if path != "commits/main":
            raise AssertionError(f"unexpected API path: {path}")
        return {"sha": self.sha}


class ProductionDriftTests(unittest.TestCase):
    def test_matching_sha_health_and_readiness_pass(self):
        responses = {
            f"{ORIGIN}/version": {"commit": SHA},
            f"{ORIGIN}/health": {"status": "ok", "service": "phishlens-api"},
            f"{ORIGIN}/ready": {"status": "ready", "database": "connected"},
        }

        result = inspect_production(FakeGitHub(), ORIGIN, responses.__getitem__)

        self.assertEqual(result["expected_sha"], SHA)
        self.assertEqual(result["findings"], [])

    def test_stale_production_sha_is_reported(self):
        responses = {
            f"{ORIGIN}/version": {"commit": "b" * 40},
            f"{ORIGIN}/health": {"status": "ok", "service": "phishlens-api"},
            f"{ORIGIN}/ready": {"status": "ready", "database": "connected"},
        }

        result = inspect_production(FakeGitHub(), ORIGIN, responses.__getitem__)

        self.assertIn("Production /version does not match the current main SHA.", result["findings"])

    def test_each_endpoint_is_checked_and_failures_are_bounded(self):
        def unavailable(url):
            raise RuntimeError(f"private upstream response from {url}")

        result = inspect_production(FakeGitHub(), ORIGIN, unavailable)

        self.assertEqual(len(result["findings"]), 3)
        self.assertTrue(all("could not be read as JSON" in finding for finding in result["findings"]))
        self.assertNotIn("private", " ".join(result["findings"]))

    def test_invalid_main_sha_is_reported_without_comparing_version(self):
        responses = {
            f"{ORIGIN}/version": {"commit": SHA},
            f"{ORIGIN}/health": {"status": "ok", "service": "phishlens-api"},
            f"{ORIGIN}/ready": {"status": "ready", "database": "connected"},
        }

        result = inspect_production(FakeGitHub("not-a-sha"), ORIGIN, responses.__getitem__)

        self.assertIn("Could not read a valid current main SHA from GitHub.", result["findings"])
        self.assertNotIn("Production /version does not match the current main SHA.", result["findings"])

    def test_monitor_workflow_has_no_deployment_secrets_or_write_permissions(self):
        from pathlib import Path

        workflow_path = Path(__file__).resolve().parents[2] / ".github/workflows/production-drift.yml"
        workflow = workflow_path.read_text(encoding="utf-8")

        self.assertIn("schedule:", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("RENDER_", workflow)
        self.assertNotIn("environment:", workflow)


if __name__ == "__main__":
    unittest.main()
