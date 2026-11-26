"""Trusted staging controller must bind deployment to reviewed exact PR evidence."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.secretary import trusted_staging

SHA = "a" * 40
REPO = "kendshhh/PhishLens"
PR = {
    "number": 296,
    "state": "open",
    "draft": False,
    "head": {"sha": SHA, "repo": {"full_name": REPO}},
    "base": {"ref": "main"},
    "labels": [{"name": "needs-hosted-staging"}],
}
RUN = {
    "id": 123,
    "run_attempt": 1,
    "event": "pull_request",
    "head_sha": SHA,
    "conclusion": "success",
    "pull_requests": [{"number": 296}],
}
CONFIG = {
    "base_branch": "main",
    "preview_check": "Secretary staging",
    "preview_opt_in_label": "needs-hosted-staging",
    "staging_predeployment_checks": [
        {"context": "Backend checks", "app_id": 15368},
        {"context": "CodeQL", "app_id": 57789},
    ],
}


def passing_check(name, app_id):
    return {"name": name, "app": {"id": app_id}, "head_sha": SHA,
            "id": app_id, "status": "completed", "conclusion": "success"}


class TrustedStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".github").mkdir()
        (self.root / ".github/secretary.json").write_text(json.dumps(CONFIG), encoding="utf-8")
        self.event_path = self.root / "event.json"
        self.output_path = self.root / "output.txt"
        self.event_path.write_text(json.dumps({"repository": {"full_name": REPO},
                                               "workflow_run": RUN}), encoding="utf-8")
        self.environment = {
            "GITHUB_EVENT_PATH": str(self.event_path),
            "GITHUB_OUTPUT": str(self.output_path),
            "GITHUB_REPOSITORY": REPO,
            "GITHUB_TOKEN": "test-token",
            "GITHUB_RUN_ID": "456",
            "GITHUB_SERVER_URL": "https://github.com",
            "STAGING_PR": "296",
            "STAGING_PR_HEAD_SHA": SHA,
        }

    def tearDown(self):
        self.temp.cleanup()

    def api(self, *, checks=None):
        api = Mock(repo=REPO)
        api.request.return_value = PR
        api.pages.side_effect = lambda path, **kwargs: checks or []
        api.pull_request_files.return_value = [{"filename": "backend/app/main.py"}]
        return api

    def run_inspect(self, api, *, pr=None, run=None, checks=None, files=None):
        event = {"repository": {"full_name": REPO}, "workflow_run": run or RUN}
        self.event_path.write_text(json.dumps(event), encoding="utf-8")
        api.request.return_value = pr or PR
        api.pages.side_effect = lambda path, **kwargs: checks or []
        if files is not None:
            api.pull_request_files.return_value = files
        with patch.dict(os.environ, self.environment, clear=True), \
                patch.object(trusted_staging, "ROOT", self.root), \
                patch("scripts.secretary.trusted_staging.latest_jobs",
                      return_value=(self.job_map(), RUN)):
            trusted_staging.inspect_candidate(timeout=0, api=api)

    @staticmethod
    def job_map():
        return {name: {"status": "completed", "conclusion": "success"}
                for name in ("Backend checks", "Extension checks", "Staging integration")}

    def test_exact_current_runtime_candidate_is_eligible_only_after_required_checks(self):
        checks = [passing_check("Backend checks", 15368), passing_check("CodeQL", 57789)]
        api = self.api(checks=checks)
        self.run_inspect(api, checks=checks)
        self.assertIn("disposition=eligible", self.output_path.read_text(encoding="utf-8"))

    def test_missing_or_failed_required_check_blocks_deployment(self):
        api = self.api(checks=[passing_check("Backend checks", 15368)])
        with self.assertRaisesRegex(SystemExit, "did not finish"):
            self.run_inspect(api, checks=[passing_check("Backend checks", 15368)])

        failed = passing_check("CodeQL", 57789)
        failed["conclusion"] = "failure"
        checks = [passing_check("Backend checks", 15368), failed]
        api = self.api(checks=checks)
        with self.assertRaisesRegex(SystemExit, "Required pre-deployment checks failed"):
            self.run_inspect(api, checks=checks)

    def test_stale_fork_draft_or_unlabelled_pr_is_rejected(self):
        variants = []
        stale = dict(PR, head={"sha": "b" * 40, "repo": {"full_name": REPO}})
        variants.append(stale)
        fork = dict(PR, head={"sha": SHA, "repo": {"full_name": "fork/PhishLens"}})
        variants.append(fork)
        draft = dict(PR, draft=True)
        variants.append(draft)
        unlabelled = dict(PR, labels=[])
        variants.append(unlabelled)
        for candidate in variants:
            with self.subTest(candidate=candidate):
                api = self.api()
                with self.assertRaises(SystemExit):
                    self.run_inspect(api, pr=candidate,
                                     checks=[passing_check("Backend checks", 15368),
                                             passing_check("CodeQL", 57789)])

    def test_docs_only_candidate_is_explicitly_not_applicable(self):
        api = self.api()
        self.run_inspect(api, files=[{"filename": "docs/README.md"}])
        self.assertIn("disposition=not-applicable", self.output_path.read_text(encoding="utf-8"))

    def test_final_status_fails_for_any_skipped_stage_and_passes_only_all_success(self):
        api = self.api()
        with patch.dict(os.environ, self.environment, clear=True), \
                patch.object(trusted_staging, "ROOT", self.root), \
                patch.object(trusted_staging, "latest_jobs", return_value=({}, RUN)):
            trusted_staging.report_outcome(
                inspect_result="success", deploy_result="success", acceptance_result="success", api=api
            )
        payload = api.request.call_args.args[1]
        self.assertEqual(payload["state"], "success")
        self.assertEqual(payload["context"], "Secretary staging")

        api.reset_mock()
        api.request.return_value = PR
        with patch.dict(os.environ, self.environment, clear=True), \
                patch.object(trusted_staging, "ROOT", self.root), \
                patch.object(trusted_staging, "latest_jobs", return_value=({}, RUN)):
            trusted_staging.report_outcome(
                inspect_result="success", deploy_result="success", acceptance_result="skipped", api=api
            )
        self.assertEqual(api.request.call_args.args[1]["state"], "failure")

    def test_removed_staging_label_replaces_an_old_green_with_failure(self):
        api = self.api()
        api.request.return_value = dict(PR, labels=[])
        with patch.dict(os.environ, self.environment, clear=True), \
                patch.object(trusted_staging, "ROOT", self.root), \
                patch.object(trusted_staging, "latest_jobs", return_value=({}, RUN)):
            trusted_staging.report_outcome(
                inspect_result="success", deploy_result="success", acceptance_result="success", api=api
            )
        self.assertEqual(api.request.call_args.args[1]["state"], "failure")

    def test_old_workflow_attempt_does_not_overwrite_latest_attempt(self):
        api = self.api()
        newer = {**RUN, "id": 124, "run_attempt": 1}
        with patch.dict(os.environ, self.environment, clear=True), \
                patch.object(trusted_staging, "ROOT", self.root), \
                patch.object(trusted_staging, "latest_jobs", return_value=({}, newer)):
            trusted_staging.report_outcome(
                inspect_result="success", deploy_result="success", acceptance_result="success", api=api
            )
        self.assertFalse(any(call.args and call.args[0].startswith("statuses/")
                             for call in api.request.call_args_list))

    def test_required_check_wait_reads_workflow_run_payload(self):
        checks = [passing_check("Backend checks", 15368), passing_check("CodeQL", 57789)]
        api = self.api(checks=checks)
        with patch.dict(os.environ, self.environment, clear=True), \
                patch.object(trusted_staging, "ROOT", self.root):
            trusted_staging.wait_for_required_checks(timeout=0, api=api)

    def test_live_pr_api_error_blocks_staging_with_diagnostic(self):
        checks = [passing_check("Backend checks", 15368), passing_check("CodeQL", 57789)]
        api = self.api(checks=checks)
        api.request.side_effect = [PR, trusted_staging.APIError("GitHub HTTP 502")]

        with self.assertRaisesRegex(
            SystemExit, "GitHub could not confirm the live PR; staging is blocked"
        ):
            self.run_inspect(api, checks=checks)

        self.assertEqual(api.request.call_count, 2)

    def test_workflow_run_identity_is_required_for_deployment_context(self):
        from scripts.deploy_staging import requested_pr_identity

        with patch.dict(os.environ, self.environment, clear=True):
            self.assertEqual(requested_pr_identity(), (296, SHA))
            self.event_path.write_text(json.dumps({
                "repository": {"full_name": REPO},
                "workflow_run": {**RUN, "head_sha": "b" * 40},
            }), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "does not match"):
                requested_pr_identity()


if __name__ == "__main__":
    unittest.main()
