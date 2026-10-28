"""Check deployment identity and staging guards without calling cloud services."""
import importlib.util
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "deploy_staging.py"
ROOT = SCRIPT.parents[1]
CONFIG = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("deploy_staging", SCRIPT)
deploy_staging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy_staging)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "RENDER_STAGING_API_KEY": "test-only-key",
            "RENDER_STAGING_SERVICE_ID": CONFIG["staging_service"],
            "STAGING_COMMIT": "a" * 40,
            "GITHUB_SHA": "a" * 40,
            "STAGING_BASE_URL": CONFIG["staging_origin"],
            "STAGING_MIGRATION_REVISION": "0003_saved_analysis_idempotency",
            "SECRETARY_STAGING_DB_HOST": "staging.invalid",
            "SECRETARY_PRODUCTION_DB_HOST": "production.invalid",
            "GITHUB_REPOSITORY": "kendshhh/PhishLens",
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def preflight_responses(self):
        service = {
            "id": CONFIG["staging_service"],
            "autoDeploy": "no",
            "branch": "main",
            "repo": "https://github.com/kendshhh/PhishLens",
            "serviceDetails": {
                "url": CONFIG["staging_origin"],
                "envSpecificDetails": {
                    "startCommand": "python scripts/start_staging.py",
                },
            },
        }
        env_vars = [
            {"envVar": {"key": "DATABASE_URL", "value": "postgresql://synthetic:synthetic@staging.invalid/phishlens_dev"}},
            {"envVar": {"key": "STAGING_DATABASE_HOST", "value": "staging.invalid"}},
            {"envVar": {"key": "APP_ENV", "value": "staging"}},
            {"envVar": {"key": "AI_MODE", "value": "mock"}},
        ]
        return [service, env_vars]

    def test_exact_commit_deployed_and_verified(self):
        with patch.object(deploy_staging, "render_request", side_effect=[
            *self.preflight_responses(),
            {"id": "dep-test"},
            {"status": "live", "commit": {"id": "a" * 40}},
        ]) as request:
            deploy_staging.main()
        body = request.call_args_list[2].args[1]
        self.assertEqual(body, {"commitId": "a" * 40})
        self.assertEqual(request.call_count, 4)

    def test_wrong_live_commit_fails(self):
        with patch.object(deploy_staging, "render_request", side_effect=[
            *self.preflight_responses(),
            {"id": "dep-test"},
            {"status": "live", "commit": {"id": "b" * 40}},
        ]), self.assertRaisesRegex(SystemExit, "does not match"):
            deploy_staging.main()

    def test_failed_deployment_fails(self):
        with patch.object(deploy_staging, "render_request", side_effect=[
            *self.preflight_responses(),
            {"id": "dep-test"},
            {"status": "build_failed"},
        ]), self.assertRaisesRegex(SystemExit, "failed"):
            deploy_staging.main()

    def test_missing_secret_fails_before_network_access(self):
        os.environ.pop("RENDER_STAGING_API_KEY")
        with patch.object(deploy_staging, "render_request") as request, self.assertRaises(SystemExit):
            deploy_staging.main()
        request.assert_not_called()

    def test_production_service_rejected_before_network_access(self):
        os.environ["RENDER_STAGING_SERVICE_ID"] = CONFIG["production_service"]
        with patch.object(deploy_staging, "render_request") as request, self.assertRaisesRegex(SystemExit, "production"):
            deploy_staging.main()
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
