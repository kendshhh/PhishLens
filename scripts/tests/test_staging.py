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
spec = importlib.util.spec_from_file_location("deploy_staging", SCRIPT)
deploy_staging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy_staging)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "RENDER_STAGING_API_KEY": "test-only-key",
            "RENDER_STAGING_SERVICE_ID": "srv-test-staging",
            "STAGING_COMMIT": "a" * 40,
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def responses(self, *payloads):
        return [io.BytesIO(json.dumps(payload).encode()) for payload in payloads]

    def test_exact_commit_deployed_and_verified(self):
        with patch("urllib.request.urlopen", side_effect=self.responses(
            {"id": "dep-test"}, {"status": "live", "commit": {"id": "a" * 40}},
        )) as request:
            deploy_staging.main()
        body = json.loads(request.call_args_list[0].args[0].data)
        self.assertEqual(body, {"commitId": "a" * 40})
        self.assertEqual(request.call_count, 2)

    def test_wrong_live_commit_fails(self):
        with patch("urllib.request.urlopen", side_effect=self.responses(
            {"id": "dep-test"}, {"status": "live", "commit": {"id": "b" * 40}},
        )), self.assertRaisesRegex(SystemExit, "does not match"):
            deploy_staging.main()

    def test_failed_deployment_fails(self):
        with patch("urllib.request.urlopen", side_effect=self.responses(
            {"id": "dep-test"}, {"status": "build_failed"},
        )), self.assertRaisesRegex(SystemExit, "failed"):
            deploy_staging.main()

    def test_missing_secret_fails_before_network_access(self):
        os.environ.pop("RENDER_STAGING_API_KEY")
        with patch("urllib.request.urlopen") as request, self.assertRaises(SystemExit):
            deploy_staging.main()
        request.assert_not_called()

    def test_production_service_rejected_before_network_access(self):
        os.environ["RENDER_STAGING_SERVICE_ID"] = "srv-db7eap25b2lc73fkelpg"
        with patch("urllib.request.urlopen") as request, self.assertRaisesRegex(SystemExit, "production"):
            deploy_staging.main()
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
