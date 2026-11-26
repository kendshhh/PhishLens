"""Only the trusted controller publishes runtime acceptance status."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.secretary.hosted_status import decision, main

SHA = "a" * 40
REPOSITORY = "kendshhh/PhishLens"
CONFIG = {
    "preview_check": "Secretary staging",
    "preview_opt_in_label": "needs-hosted-staging",
}


def pull_request():
    return {
        "state": "open",
        "draft": False,
        "head": {"sha": SHA, "repo": {"full_name": REPOSITORY}},
        "labels": [{"name": "needs-hosted-staging"}],
    }


def passed_jobs():
    return {
        name: {"status": "completed", "conclusion": "success"}
        for name in ("Backend checks", "Extension checks", "Staging integration")
    }


class HostedStatusTests(unittest.TestCase):
    def test_runtime_status_is_pending_until_protected_acceptance_completes(self):
        state, message = decision(
            pull_request(), [{"filename": "extension/js/history.js"}],
            {"head_sha": SHA, "conclusion": "success"}, passed_jobs(), REPOSITORY, CONFIG,
        )
        self.assertEqual(state, "pending")
        self.assertIn("trusted controller", message)

    def test_runtime_status_requires_label_and_current_required_ci_jobs(self):
        pr = pull_request()
        pr["labels"] = []
        state, message = decision(
            pr, [{"filename": "backend/app/main.py"}],
            {"head_sha": SHA, "conclusion": "success"}, passed_jobs(), REPOSITORY, CONFIG,
        )
        self.assertEqual(state, "failure")
        self.assertIn("needs-hosted-staging", message)

        jobs = passed_jobs()
        jobs["Backend checks"]["conclusion"] = "failure"
        state, _ = decision(
            pull_request(), [{"filename": "extension/js/history.js"}],
            {"head_sha": SHA, "conclusion": "success"}, jobs, REPOSITORY, CONFIG,
        )
        self.assertEqual(state, "failure")

    def test_only_non_runtime_changes_can_pass_without_staging(self):
        state, message = decision(
            pull_request(), [{"filename": "docs/README.md"}],
            {"head_sha": SHA, "conclusion": "success"}, passed_jobs(), REPOSITORY, CONFIG,
        )
        self.assertEqual(state, "success")
        self.assertIn("no application/runtime changes", message)

    def test_stale_and_fork_prs_cannot_pass(self):
        pr = pull_request()
        pr["head"]["sha"] = "b" * 40
        state, _ = decision(pr, [{"filename": "extension/a.js"}],
                            {"head_sha": SHA, "conclusion": "success"}, passed_jobs(), REPOSITORY, CONFIG)
        self.assertEqual(state, "stale")

        pr = pull_request()
        pr["head"]["repo"]["full_name"] = "fork/PhishLens"
        state, _ = decision(pr, [{"filename": "extension/a.js"}],
                            {"head_sha": SHA, "conclusion": "success"}, passed_jobs(), REPOSITORY, CONFIG)
        self.assertEqual(state, "failure")

    def test_mirror_does_not_overwrite_trusted_runtime_status(self):
        run = {
            "id": 77, "run_attempt": 2, "event": "pull_request", "head_sha": SHA,
            "conclusion": "success", "html_url": "https://github.com/kendshhh/PhishLens/actions/runs/77",
            "pull_requests": [{"number": 266}],
        }
        api = Mock(repo=REPOSITORY)
        api.request.return_value = pull_request()
        api.pull_request_files.return_value = [{"filename": "extension/js/history.js"}]
        jobs = passed_jobs()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/secretary.json").write_text(json.dumps(CONFIG), encoding="utf-8")
            event_path = root / "event.json"
            event_path.write_text(json.dumps({"workflow_run": run}), encoding="utf-8")
            with patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event_path)}, clear=True), \
                    patch("scripts.secretary.hosted_status.ROOT", root), \
                    patch("scripts.secretary.hosted_status.GitHub", return_value=api), \
                    patch("scripts.secretary.hosted_status.latest_jobs",
                          return_value=(jobs, {"id": 77, "run_attempt": 2})), \
                    patch("scripts.secretary.hosted_status.publish_status") as publish:
                main()

                publish.assert_not_called()

    def test_old_run_attempt_does_not_overwrite_latest_status(self):
        run = {
            "id": 77, "run_attempt": 1, "event": "pull_request", "head_sha": SHA,
            "conclusion": "failure", "pull_requests": [{"number": 266}],
        }
        api = Mock(repo=REPOSITORY)
        api.request.return_value = pull_request()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/secretary.json").write_text(json.dumps(CONFIG), encoding="utf-8")
            event_path = root / "event.json"
            event_path.write_text(json.dumps({"workflow_run": run}), encoding="utf-8")
            with patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event_path)}, clear=True), \
                    patch("scripts.secretary.hosted_status.ROOT", root), \
                    patch("scripts.secretary.hosted_status.GitHub", return_value=api), \
                    patch("scripts.secretary.hosted_status.latest_jobs",
                          return_value=(passed_jobs(), {"id": 77, "run_attempt": 2})), \
                    patch("scripts.secretary.hosted_status.publish_status") as publish:
                main()
        publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
