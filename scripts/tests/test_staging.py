"""Check deployment identity and staging guards without calling cloud services."""
import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, call, patch

from scripts.tests.staging_fixtures import render_staging_environment_rows

SCRIPT = Path(__file__).resolve().parents[1] / "deploy_staging.py"
ROOT = SCRIPT.parents[1]
CONFIG = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("deploy_staging", SCRIPT)
deploy_staging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy_staging)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.event_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.event_dir.cleanup)
        self.event_path = Path(self.event_dir.name) / "event.json"
        self.write_event()
        self.environment = patch.dict(os.environ, {
            "RENDER_STAGING_API_KEY": "test-only-key",
            "RENDER_STAGING_SERVICE_ID": CONFIG["staging_service"],
            "STAGING_COMMIT": "a" * 40,
            # Pull-request workflows expose a synthetic merge SHA here.
            "GITHUB_SHA": "b" * 40,
            "STAGING_PR": "123",
            "STAGING_PR_HEAD_SHA": "a" * 40,
            "GITHUB_EVENT_PATH": str(self.event_path),
            "GITHUB_TOKEN": "test-only-read-token",
            "GITHUB_REPOSITORY": "kendshhh/PhishLens",
            "STAGING_BASE_URL": CONFIG["staging_origin"],
            "STAGING_MIGRATION_REVISION": "0003_saved_analysis_idempotency",
            "SECRETARY_STAGING_DB_HOST": "staging.invalid",
            "SECRETARY_PRODUCTION_DB_HOST": "production.invalid",
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.live_pr = {
            "number": 123,
            "state": "open",
            "draft": False,
            "head": {
                "sha": "a" * 40,
                "repo": {"full_name": "kendshhh/PhishLens"},
            },
            "labels": [{"name": "needs-hosted-staging"}],
        }
        self.github = Mock()
        self.github.request.return_value = self.live_pr
        self.github_client = patch.object(
            deploy_staging, "ReadOnlyGitHub", return_value=self.github
        )
        self.github_client.start()
        self.addCleanup(self.github_client.stop)

    def write_event(self, *, number=123, head_sha="a" * 40):
        event = {
            "number": number,
            "repository": {"full_name": "kendshhh/PhishLens"},
            "pull_request": {
                "number": number,
                "head": {
                    "sha": head_sha,
                    "repo": {"full_name": "kendshhh/PhishLens"},
                },
            },
        }
        self.event_path.write_text(json.dumps(event), encoding="utf-8")

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
        env_vars = render_staging_environment_rows()
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
        self.assertEqual(self.github.request.call_args_list, [call("pulls/123"), call("pulls/123")])

    def test_rejects_missing_malformed_or_mismatched_pr_identity_before_render(self):
        cases = (
            ("STAGING_PR", "", "valid pull-request number"),
            ("STAGING_PR", "abc", "valid pull-request number"),
            ("STAGING_PR_HEAD_SHA", "", "full pull-request head SHA"),
            ("STAGING_PR_HEAD_SHA", "A" * 40, "full pull-request head SHA"),
        )
        for name, value, message in cases:
            with self.subTest(name=name, value=value):
                original = os.environ[name]
                os.environ[name] = value
                try:
                    with patch.object(deploy_staging, "render_request") as request, \
                            self.assertRaisesRegex(SystemExit, message):
                        deploy_staging.main()
                    request.assert_not_called()
                finally:
                    os.environ[name] = original

        os.environ["STAGING_COMMIT"] = "c" * 40
        with patch.object(deploy_staging, "render_request") as request, \
                self.assertRaisesRegex(SystemExit, "differs from the verified PR head"):
            deploy_staging.main()
        request.assert_not_called()
        self.github.request.assert_not_called()

    def test_rejects_event_identity_mismatch_before_render(self):
        self.write_event(head_sha="c" * 40)
        with patch.object(deploy_staging, "render_request") as request, \
                self.assertRaisesRegex(SystemExit, "does not match the trusted event"):
            deploy_staging.main()
        request.assert_not_called()
        self.github.request.assert_not_called()

    def test_live_head_change_is_rejected_before_render(self):
        self.github.request.return_value = {
            **self.live_pr,
            "head": {
                "sha": "c" * 40,
                "repo": {"full_name": "kendshhh/PhishLens"},
            },
        }
        with patch.object(deploy_staging, "render_request") as request, \
                self.assertRaisesRegex(SystemExit, "state, head, or staging eligibility changed"):
            deploy_staging.main()
        request.assert_not_called()

    def test_closed_draft_or_ineligible_pr_is_rejected_before_render(self):
        for changes in (
            {"number": 124},
            {"state": "closed"},
            {"draft": True},
            {"labels": []},
            {
                "head": {
                    "sha": "a" * 40,
                    "repo": {"full_name": "someone/fork"},
                },
            },
        ):
            with self.subTest(changes=changes):
                self.github.request.return_value = {**self.live_pr, **changes}
                with patch.object(deploy_staging, "render_request") as request, \
                        self.assertRaisesRegex(SystemExit, "state, head, or staging eligibility changed"):
                    deploy_staging.main()
                request.assert_not_called()

    def test_head_advanced_during_render_preflight_blocks_deploy_request(self):
        self.github.request.side_effect = [
            self.live_pr,
            {
                **self.live_pr,
                "head": {
                    "sha": "c" * 40,
                    "repo": {"full_name": "kendshhh/PhishLens"},
                },
            },
        ]
        with patch.object(deploy_staging, "render_request", side_effect=self.preflight_responses()) as request, \
                self.assertRaisesRegex(SystemExit, "state, head, or staging eligibility changed"):
            deploy_staging.main()
        self.assertEqual(request.call_count, 2)
        self.assertTrue(all(len(render_call.args) == 1 for render_call in request.call_args_list))
        self.assertEqual(self.github.request.call_count, 2)

    def test_hosted_workflow_targets_pr_head_with_scoped_read_token(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        hosted = workflow.split("  hosted-staging:\n", 1)[1]

        self.assertIn("STAGING_COMMIT: ${{ github.event.pull_request.head.sha }}", hosted)
        self.assertTrue(
            "STAGING_EXPECTED_SHA: ${{ github.event.pull_request.head.sha }}" in hosted
            or "STAGING_EXPECTED_BACKEND_SHA: ${{ github.event.pull_request.head.sha }}" in hosted,
            "Hosted staging must bind its expected backend SHA to the current PR head.",
        )
        self.assertNotIn("STAGING_COMMIT: ${{ github.sha }}", hosted)
        self.assertNotIn("STAGING_EXPECTED_SHA: ${{ github.sha }}", hosted)
        self.assertNotIn("STAGING_EXPECTED_BACKEND_SHA: ${{ github.sha }}", hosted)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", hosted)
        self.assertIn("from scripts.secretary.github_api import APIError, ReadOnlyGitHub", hosted)
        self.assertIn("hosted-migration-lineage.outputs.head", workflow)

    def test_github_denial_fails_closed_before_render(self):
        self.github.request.side_effect = deploy_staging.APIError("GitHub HTTP 403 for pulls/123")
        with patch.object(deploy_staging, "render_request") as request, \
                self.assertRaisesRegex(SystemExit, "could not be verified"):
            deploy_staging.main()
        request.assert_not_called()

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
