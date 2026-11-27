"""Offline adversarial/control-plane scenarios; no GitHub, Render or paid AI calls."""
import base64
import copy
import hashlib
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, call, patch
from zipfile import ZipFile

from scripts.secretary.core import (
    MARKER,
    application_change,
    fingerprint,
    inspect,
    recommendation,
    render,
    safe,
)
from scripts.secretary.github_api import APIError, GitHub, ReadOnlyGitHub
from scripts.secretary.preview import (
    completed_event,
    confirm_live_deployment,
    eligibility,
    package,
    preview_gate_enabled,
    publish_preview_status,
    verify_environment,
    verify_service,
)
from scripts.secretary.production import (
    deployment_metrics,
    log_categories,
    pipeline_metrics,
)
from scripts.secretary.report import (
    bot_comment,
    explain,
    latest_jobs,
    preview_state,
    report,
    validate_ai,
)
from scripts.tests.staging_fixtures import (
    PRODUCTION_HOST,
    STAGING_HOST,
    render_staging_environment_rows,
    set_render_environment_value,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / ".github/secretary.json").read_text())
SHA = "a" * 40


def fixture():
    return {"pr": {"number": 123, "title": "Synthetic history change", "body": "Related to #23. Acceptance: render history.",
        "user": {"login": "teammate"}, "state": "open", "draft": False,
        "labels": [{"name": CONFIG["preview_opt_in_label"]}],
        "head": {"sha": SHA, "ref": "feat/demo", "repo": {"full_name": "kendshhh/PhishLens"}},
        "base": {"sha": "b" * 40, "ref": "main", "repo": {"full_name": "kendshhh/PhishLens"}}},
        "files": [{"filename": "extension/js/history.js", "status": "modified", "patch": "@@ -1 +1 @@\n-old\n+new"}],
        "jobs": {n: {"conclusion": "success", "html_url": "https://github.com/kendshhh/PhishLens/actions/runs/1"} for n in CONFIG["required_ci_jobs"]},
        "preview": {"sha": SHA, "current": True, "state": "success",
                    "saved_report_crud": "passed", "analysis_mode": "real",
                    "provider_mode": "gemini", "record_cleanup": "confirmed"},
        "config": CONFIG, "gaps": [], "issues": {}, "protection": "not available"}


class PolicyTests(unittest.TestCase):
    def decision(self, s):
        findings, gaps, _ = inspect(s["pr"], s["files"], s["config"])
        preview_requested = any(
            label.get("name") == CONFIG["preview_opt_in_label"]
            for label in s["pr"].get("labels", [])
        )
        return recommendation(
            s["pr"], s["jobs"], s["preview"], findings, gaps,
            CONFIG["required_ci_jobs"], application_change(s["files"]),
            preview_requested,
        )[0]

    def test_test_only_changes_do_not_request_hosted_staging(self):
        self.assertFalse(application_change([
            {"filename": "backend/tests/test_health.py"},
            {"filename": "extension/tests/api.test.mjs"},
            {"filename": "scripts/tests/test_secretary.py"},
        ]))

    def test_runtime_changes_still_request_hosted_staging_with_test_changes(self):
        self.assertTrue(application_change([
            {"filename": "backend/tests/test_health.py"},
            {"filename": "backend/app/main.py"},
        ]))

    def test_nested_test_directories_are_not_runtime_changes(self):
        self.assertFalse(application_change([
            {"filename": "backend/app/tests/test_router.py"},
        ]))

    def test_passing_is_review_never_approval(self):
        self.assertEqual(self.decision(fixture()), "READY FOR KENDRA’S REVIEW")

    def test_report_checks_only_automated_items_with_current_passing_evidence(self):
        snapshot = fixture()
        body = render(snapshot, {"status": "disabled"}, "test")
        self.assertIn("- [x] Packaged extension browser checklist passed", body)
        self.assertIn("- [x] Exact-head staging saved-report CRUD passed", body)
        self.assertIn("- [x] Non-mock AI acceptance passed", body)
        self.assertIn("- [ ] Formal teammate review is a separate required approval", body)

        snapshot["jobs"]["Extension checks"]["conclusion"] = "failure"
        snapshot["preview"]["current"] = False
        body = render(snapshot, {"status": "disabled"}, "test")
        self.assertIn("- [ ] Packaged extension browser checklist has not passed", body)
        self.assertIn("- [ ] Exact-head staging saved-report CRUD and cleanup have not passed", body)
        self.assertIn("- [ ] Real AI acceptance is not checked", body)

    def test_unrequested_staging_keeps_formal_review_unchecked(self):
        snapshot = fixture()
        snapshot["preview_requested"] = False
        body = render(snapshot, {"status": "disabled"}, "test")
        checklist = body.split("### Automated and human follow-up checklist", 1)[1].split("### Recommended next action", 1)[0]
        self.assertIn("- [ ] Hosted staging was not requested", checklist)
        self.assertIn("- [ ] Formal teammate review is a separate required approval", checklist)
        self.assertNotIn("- [x] Exact-head staging", checklist)

    def test_mock_staging_checks_crud_but_never_ai_acceptance(self):
        snapshot = fixture()
        snapshot["preview"].update({"analysis_mode": "mock", "provider_mode": "mock"})
        body = render(snapshot, {"status": "disabled"}, "test")
        self.assertIn("- [x] Exact-head staging saved-report CRUD passed", body)
        self.assertIn("- [ ] Real AI acceptance is not checked: staging used `mock`", body)
        self.assertIn("Mock output is not AI acceptance", body)

    def test_failed_cancelled_skipped_checks(self):
        for conclusion in ("failure", "cancelled", "skipped", "timed_out"):
            s = fixture()
            s["jobs"]["Backend checks"]["conclusion"] = conclusion
            self.assertEqual(self.decision(s), "CHANGES RECOMMENDED")

    def test_pending_and_missing(self):
        for job in ({"status": "in_progress"}, {}):
            s = fixture()
            s["jobs"]["Backend checks"] = job
            self.assertEqual(self.decision(s), "WAITING FOR CHECKS")

    def test_draft(self):
        s = fixture()
        s["pr"]["draft"] = True
        self.assertEqual(self.decision(s), "BLOCKED")

    def test_new_sha_invalidates_old_preview(self):
        s = fixture()
        s["pr"]["head"]["sha"] = "c" * 40
        self.assertEqual(self.decision(s), "WAITING FOR CHECKS")

    def test_preview_failure_and_shared_conflict(self):
        s = fixture()
        s["preview"]["state"] = "failure"
        self.assertEqual(self.decision(s), "BLOCKED")
        s["preview"] = {"state": "success", "sha": SHA, "current": False}
        self.assertEqual(self.decision(s), "WAITING FOR CHECKS")

    def test_fork(self):
        s = fixture()
        s["pr"]["head"]["repo"]["full_name"] = "outside/fork"
        self.assertEqual(self.decision(s), "BLOCKED")

    def test_oversized_and_missing_patch(self):
        s = fixture()
        s["files"][0]["patch"] = "x" * 60001
        self.assertEqual(self.decision(s), "BLOCKED")
        s["files"][0]["patch"] = None
        self.assertEqual(self.decision(s), "BLOCKED")

    def test_docs_needs_no_deployment(self):
        s = fixture()
        s["files"][0]["filename"] = "docs/example.md"
        s["preview"] = {}
        self.assertEqual(self.decision(s), "READY FOR KENDRA’S REVIEW")

    def test_secret_detection_without_value_disclosure(self):
        s = fixture()
        s["files"][0] = {"filename": ".env", "patch": "+-----BEGIN PRIVATE KEY-----"}
        self.assertEqual(self.decision(s), "CHANGES RECOMMENDED")
        self.assertNotIn("BEGIN PRIVATE KEY", render(s, {}, "test"))

    def test_untrusted_content_escaped(self):
        escaped = safe("@all <script> [click](https://evil.invalid) ghp_" + "a" * 30)
        self.assertNotIn("@all", escaped)
        self.assertNotIn("<script>", escaped)
        self.assertNotIn("ghp_", escaped)


class ReportTests(unittest.TestCase):
    def test_comment_ownership(self):
        rows = [{"body": MARKER, "user": {"login": "attacker"}}, {"body": MARKER, "user": {"login": "github-actions[bot]"}, "id": 2}]
        self.assertEqual(bot_comment(rows)["id"], 2)

    def test_duplicate_events_make_no_ai_or_comment_calls(self):
        s = fixture()
        api = Mock()
        api.pages.return_value = [{"id": 2, "body": MARKER + "\n<!-- evidence:" + fingerprint(s) + " -->", "user": {"login": "github-actions[bot]"}}]
        with patch("scripts.secretary.report.snapshot", return_value=s), patch("scripts.secretary.report.explain") as ai:
            self.assertIn("unchanged", report(api, 123, CONFIG))
            ai.assert_not_called()
            api.request.assert_not_called()

    def test_stale_report_not_published(self):
        s = fixture()
        api = Mock()
        api.pages.return_value = []
        newer = copy.deepcopy(s["pr"])
        newer["head"]["sha"] = "c" * 40
        api.request.return_value = newer
        with patch("scripts.secretary.report.snapshot", return_value=s), patch("scripts.secretary.report.explain", return_value={}):
            self.assertIn("superseded", report(api, 123, CONFIG))
        self.assertEqual(api.request.call_count, 1)

    def test_rerun_uses_latest_attempt(self):
        api = Mock()
        api.pages.side_effect = [[{"id": 7, "event": "pull_request", "head_sha": SHA, "run_attempt": 2}],
                                 [{"name": "Backend checks", "conclusion": "failure"}]]
        jobs, run = latest_jobs(api, SHA)
        self.assertEqual(run["run_attempt"], 2)
        self.assertEqual(jobs["Backend checks"]["conclusion"], "failure")
        self.assertIn("attempts/2/jobs", api.pages.call_args.args[0])

    def test_disabled_ai_makes_no_call(self):
        with patch("urllib.request.urlopen") as network:
            self.assertEqual(explain(fixture())["status"], "disabled")
            network.assert_not_called()

    def test_provider_failure_and_invalid_ai_output(self):
        s = fixture()
        s["config"] = {**CONFIG, "ai_enabled": True}
        with patch.dict(os.environ, {"SECRETARY_AI_ENABLED": "true", "SECRETARY_GEMINI_KEY": "synthetic", "SECRETARY_GEMINI_MODEL": "test-model"}), patch("urllib.request.urlopen", side_effect=TimeoutError):
            self.assertEqual(explain(s)["status"], "unavailable")
        for value in ({"approve": True}, {"summary": 1}, {"summary": "x" * 1801}, []):
            with self.assertRaises(ValueError):
                validate_ai(value)

    def test_invalid_provider_payload_falls_back(self):
        s = fixture()
        s["config"] = {**CONFIG, "ai_enabled": True}
        with patch.dict(os.environ, {"SECRETARY_AI_ENABLED": "true", "SECRETARY_GEMINI_KEY": "synthetic", "SECRETARY_GEMINI_MODEL": "test-model"}), patch("urllib.request.urlopen", return_value=io.BytesIO(b'{"candidates":[]}')):
            self.assertEqual(explain(s)["status"], "unavailable")

    def test_agent_failure_publishes_explicit_unavailable(self):
        from scripts.secretary.report import main

        api = Mock()
        api.pages.side_effect = [[{"number": 123}], []]
        api.request.return_value = fixture()["pr"]
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            event.write_text("{}")
            with patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event)}), patch("scripts.secretary.report.GitHub", return_value=api), patch("scripts.secretary.report.snapshot", side_effect=RuntimeError("synthetic failure")):
                main()
        self.assertIn("Analysis unavailable", api.request.call_args.args[1]["body"])
        self.assertIn("BLOCKED", api.request.call_args.args[1]["body"])

    def test_ai_does_not_receive_diff_or_pr_prose(self):
        s = fixture()
        s["config"] = {**CONFIG, "ai_enabled": True}
        s["pr"]["body"] = "PRIVATE EMAIL DO NOT TRANSMIT"
        s["files"][0]["patch"] = "+PRIVATE SOURCE DO NOT TRANSMIT"
        response = {"candidates": [{"content": {"parts": [{"text": '{"summary":"Check the synthetic history manually."}'}]}}]}
        with patch.dict(os.environ, {"SECRETARY_AI_ENABLED": "true", "SECRETARY_GEMINI_KEY": "synthetic", "SECRETARY_GEMINI_MODEL": "test-model"}), patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(response).encode())) as network:
            self.assertTrue(explain(s)["status"].startswith("available"))
            self.assertNotIn(b"PRIVATE", network.call_args.args[0].data)

    def test_shared_deployment_newest_even_if_other_sha(self):
        api = Mock()
        api.request.side_effect = [[{"id": 2, "sha": "c" * 40, "creator": {"login": "github-actions[bot]"}, "payload": {"secretary": 1}}], [{"state": "success"}]]
        self.assertFalse(preview_state(api, CONFIG, SHA)["current"])

    def test_preview_state_preserves_mock_provider_evidence(self):
        api = Mock()
        api.request.side_effect = [
            [{"id": 2, "sha": SHA, "creator": {"login": "github-actions[bot]"},
              "payload": {"secretary": 1}}],
            [{"state": "success", "description":
              "secretary-crud=passed;analysis=mock;provider=mock;cleanup=confirmed"}],
        ]
        preview = preview_state(api, CONFIG, SHA)
        self.assertTrue(preview["current"])
        self.assertEqual(preview["saved_report_crud"], "passed")
        self.assertEqual(preview["analysis_mode"], "mock")
        self.assertEqual(preview["provider_mode"], "mock")
        self.assertEqual(preview["record_cleanup"], "confirmed")


class GitHubPaginationTests(unittest.TestCase):
    def test_pull_request_files_use_compact_pages(self):
        api = GitHub(repo="kendshhh/PhishLens", token="synthetic")
        first_page = [{"filename": f"extension/file-{index}.js"} for index in range(10)]
        second_page = [{"filename": "extension/last.js"}]
        with patch.object(api, "request", side_effect=[first_page, second_page]) as request:
            rows = api.pull_request_files(123)

        self.assertEqual(len(rows), 11)
        self.assertEqual(
            [call.args[0] for call in request.call_args_list],
            ["pulls/123/files?per_page=10&page=1", "pulls/123/files?per_page=10&page=2"],
        )

    def test_pages_reject_invalid_page_size(self):
        api = GitHub(repo="kendshhh/PhishLens", token="synthetic")
        with self.assertRaises(ValueError):
            api.pages("pulls/123/files", per_page=101)

    def test_get_retries_transient_github_server_errors(self):
        api = GitHub(repo="kendshhh/PhishLens", token="synthetic")

        def http_error(status):
            return urllib.error.HTTPError("https://api.github.com/test", status, "temporary", {}, io.BytesIO())

        with patch("urllib.request.urlopen", side_effect=[
            http_error(500), http_error(504), io.BytesIO(b'{"ok":true}')
        ]) as network, patch("scripts.secretary.github_api.time.sleep") as sleep:
            self.assertEqual(api.request("contents/extension/popup.js"), {"ok": True})

        self.assertEqual(network.call_count, 3)
        self.assertEqual(sleep.call_args_list, [call(0.25), call(0.5)])

    def test_non_get_requests_are_not_retried(self):
        api = GitHub(repo="kendshhh/PhishLens", token="synthetic")
        error = urllib.error.HTTPError("https://api.github.com/test", 500, "temporary", {}, io.BytesIO())

        with patch("urllib.request.urlopen", side_effect=error) as network, \
                patch("scripts.secretary.github_api.time.sleep") as sleep, \
                self.assertRaisesRegex(APIError, "GitHub HTTP 500"):
            api.request("deployments", data={"environment": "staging"})

        network.assert_called_once()
        sleep.assert_not_called()

    def test_read_only_client_rejects_writes_before_network_access(self):
        api = ReadOnlyGitHub(repo="kendshhh/PhishLens", token="synthetic")
        with patch("urllib.request.urlopen") as network, self.assertRaisesRegex(APIError, "GET requests only"):
            api.request("pulls/123", {"state": "closed"})
        network.assert_not_called()

    def test_read_only_client_only_reads_pr_endpoints_and_never_drops_its_token(self):
        api = ReadOnlyGitHub(repo="kendshhh/PhishLens", token="synthetic")
        with patch("urllib.request.urlopen") as network, self.assertRaisesRegex(APIError, "pull-request reads only"):
            api.request("contents/README.md")
        network.assert_not_called()
        denied = urllib.error.HTTPError("https://api.github.com/test", 403, "denied", {}, io.BytesIO())
        with patch("urllib.request.urlopen", side_effect=denied) as network, \
                self.assertRaisesRegex(APIError, "GitHub HTTP 403"):
            api.request("pulls/123")
        network.assert_called_once()

    def test_read_only_client_requires_its_dedicated_token(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(APIError, "read-only PR token"):
            ReadOnlyGitHub(repo="kendshhh/PhishLens")


class PreviewTests(unittest.TestCase):
    def test_neon_preview_runs_authenticated_saved_report_acceptance(self):
        from scripts.secretary.preview import main

        data = fixture()
        api = Mock(repo="kendshhh/PhishLens")
        api.pages.return_value = []
        api.pull_request_files.return_value = data["files"]
        responses = {"pulls/123": data["pr"], "check-runs": {"id": 1}, "deployments": {"id": 2}}
        api.request.side_effect = lambda path, *args: responses.get(path, [])
        event = {"workflow_run": {"id": 7, "event": "pull_request", "head_sha": SHA,
                                  "conclusion": "success", "pull_requests": [{"number": 123, "head": {"sha": SHA}}]}}
        service = CONFIG["staging_service"]
        render = {
            f"services/{service}": {},
            f"services/{service}/env-vars?limit=100": render_staging_environment_rows(REPORT_AUTH_MODE="neon"),
            f"services/{service}/deploys": {"id": "fixture"},
            f"services/{service}/deploys/fixture": {"status": "live", "commit": {"id": SHA}},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/secretary.json").write_text(json.dumps(CONFIG))
            event_path = root / "event.json"
            event_path.write_text(json.dumps(event))
            summary_path = root / "summary.md"
            settings = {"GITHUB_EVENT_PATH": str(event_path), "GITHUB_RUN_ID": "7",
                        "SECRETARY_PR_NUMBER": "123", "SECRETARY_PR_HEAD_SHA": SHA,
                        "SECRETARY_PR_READ_TOKEN": "synthetic-read-only",
                        "GITHUB_STEP_SUMMARY": str(summary_path),
                        "SECRETARY_PREVIEW_ENABLED": "true", "SECRETARY_STAGING_DB_HOST": STAGING_HOST,
                        "SECRETARY_PRODUCTION_DB_HOST": PRODUCTION_HOST,
                        "STAGING_AUTH_URL": "https://ep-test.neonauth.c-4.ap-southeast-1.aws.neon.tech/phishlens_dev/auth",
                        "STAGING_AUTH_DATABASE": "phishlens_dev"}
            with (patch.dict(os.environ, settings, clear=True),
                  patch("scripts.secretary.preview.ROOT", root),
                  patch("scripts.secretary.preview.GitHub", return_value=api),
                  patch("scripts.secretary.preview.ReadOnlyGitHub", return_value=api),
                  patch("scripts.secretary.preview.latest_jobs", return_value=(data["jobs"], {"id": 7})),
                  patch("scripts.secretary.preview.verify_service"),
                  patch("scripts.secretary.preview.render_request", side_effect=lambda path, *args: render[path]),
                  patch("scripts.secretary.preview.smoke", return_value={
                      "history": "authentication_required",
                      "seeded_history": "not_checked",
                      "anonymous_saved_report": {
                          "path": "/api/analyses", "status_code": 401,
                          "challenge": "Bearer", "redirected": False,
                      },
                  }) as smoke,
                  patch("scripts.secretary.preview.verify_saved_report", return_value={
                      "result": "passed", "cleanedUp": True, "analysisMode": "real",
                      "analysisProvenance": {"providerMode": "tfidf", "model": "staging-model",
                                              "modelRevision": "verified-model-sha", "promptVersion": "1"},
                  }) as crud,
                  patch("scripts.secretary.preview.package") as build):
                main()
            evidence = json.loads((root / "output/secretary/preview-evidence.json").read_text())
            step_summary = summary_path.read_text(encoding="utf-8")
        smoke.assert_called_once_with(CONFIG["staging_origin"], SHA, report_auth_mode="neon")
        crud.assert_called_once_with(CONFIG["staging_origin"], SHA)
        build.assert_called_once()
        self.assertEqual(evidence["result"], "success")
        self.assertEqual(evidence["required_status"], "success")
        self.assertEqual(evidence["report_auth_mode"], "neon")
        self.assertEqual(evidence["smoke"]["history"], "authentication_required")
        self.assertEqual(evidence["smoke"]["seeded_history"], "not_checked")
        self.assertEqual(evidence["smoke"]["anonymous_saved_report"]["status_code"], 401)
        self.assertEqual(evidence["saved_report_ai_crud"]["result"], "passed")
        status_calls = [entry.args[1]["state"] for entry in api.request.call_args_list
                        if entry.args[0] == "statuses/" + SHA]
        deployment_calls = [entry.args[1]["state"] for entry in api.request.call_args_list
                            if entry.args[0] == "deployments/2/statuses"]
        self.assertEqual(status_calls, ["pending", "success"])
        self.assertEqual(deployment_calls, ["in_progress", "success"])
        self.assertEqual(
            sum(call.args[0] == "pulls/123" for call in api.request.call_args_list),
            5,
            "PR state is checked initially, before deployment, before Render, after smoke, and after CRUD",
        )
        auth_gate = next(
            entry.args[1]
            for entry in api.request.call_args_list
            if entry.args[0] == "check-runs/1" and len(entry.args) > 2 and entry.args[2] == "PATCH"
        )
        self.assertEqual(auth_gate["conclusion"], "success")
        self.assertEqual(auth_gate["output"]["title"], "Staging: success")
        self.assertEqual(auth_gate["output"]["summary"], evidence["message"])
        self.assertIn(evidence["message"], step_summary)
        self.assertIn("two synthetic accounts passed the authenticated checks.", evidence["message"])
        self.assertIn("Synthetic saved-report provenance and CRUD lifecycle passed", evidence["message"])

    def test_duplicate_verified_deployment_republishes_required_context(self):
        from scripts.secretary.preview import main

        api = Mock()
        api.repo = "kendshhh/PhishLens"
        api.pages.return_value = []
        api.request.return_value = fixture()["pr"]
        api.pull_request_files.return_value = fixture()["files"]
        event = {
            "workflow_run": {
                "id": 7,
                "run_attempt": 1,
                "event": "pull_request",
                "head_sha": SHA,
                "conclusion": "success",
                "pull_requests": [{"number": 123, "head": {"sha": SHA}}],
            }
        }
        jobs = {name: {"conclusion": "success"} for name in CONFIG["required_ci_jobs"]}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/secretary.json").write_text(json.dumps(CONFIG))
            event_path = root / "event.json"
            event_path.write_text(json.dumps(event))
            with patch.dict(os.environ, {
                "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_RUN_ID": "7",
                "SECRETARY_PR_NUMBER": "123",
                "SECRETARY_PR_HEAD_SHA": SHA,
                "SECRETARY_PR_READ_TOKEN": "synthetic-read-only",
                "SECRETARY_PREVIEW_ENABLED": "true",
            }, clear=True), \
                    patch("scripts.secretary.preview.ROOT", root), \
                    patch("scripts.secretary.preview.GitHub", return_value=api), \
                    patch("scripts.secretary.preview.ReadOnlyGitHub", return_value=api), \
                    patch("scripts.secretary.preview.latest_jobs", return_value=(jobs, {"id": 7, "run_attempt": 1})), \
                    patch("scripts.secretary.preview.completed_event", return_value=True):
                main()

        status_calls = [call for call in api.request.call_args_list if call.args[0] == "statuses/" + SHA]
        self.assertEqual(len(status_calls), 1)
        self.assertEqual(status_calls[0].args[1]["state"], "success")
        self.assertEqual(status_calls[0].args[1]["context"], "Secretary staging")

    def test_old_failed_ci_attempt_cannot_overwrite_latest_success(self):
        from scripts.secretary.preview import main

        api = Mock()
        api.repo = "kendshhh/PhishLens"
        api.pages.return_value = []
        api.request.return_value = fixture()["pr"]
        event = {
            "workflow_run": {
                "id": 7,
                "run_attempt": 1,
                "event": "pull_request",
                "head_sha": SHA,
                "conclusion": "failure",
                "pull_requests": [{"number": 123, "head": {"sha": SHA}}],
            }
        }
        latest_jobs = {
            name: {"conclusion": "success"}
            for name in CONFIG["required_ci_jobs"]
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/secretary.json").write_text(json.dumps(CONFIG))
            event_path = root / "event.json"
            event_path.write_text(json.dumps(event))
            with patch.dict(os.environ, {
                "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_RUN_ID": "8",
                "SECRETARY_PR_NUMBER": "123",
                "SECRETARY_PR_HEAD_SHA": SHA,
                "SECRETARY_PR_READ_TOKEN": "synthetic-read-only",
                "SECRETARY_PREVIEW_ENABLED": "true",
            }, clear=True), \
                    patch("scripts.secretary.preview.ROOT", root), \
                    patch("scripts.secretary.preview.GitHub", return_value=api), \
                    patch("scripts.secretary.preview.ReadOnlyGitHub", return_value=api), \
                    patch(
                        "scripts.secretary.preview.latest_jobs",
                        return_value=(latest_jobs, {"id": 7, "run_attempt": 2}),
                    ):
                main()

        self.assertEqual(api.request.call_args_list[0].args[0], "pulls/123")
        api.pull_request_files.assert_not_called()
        self.assertFalse(any(
            call.args[0] == "statuses/" + SHA
            for call in api.request.call_args_list
        ))

    def test_failed_assessment_posts_required_status_without_check_run(self):
        from scripts.secretary.preview import main

        api = Mock()
        api.repo = "kendshhh/PhishLens"
        api.pages.return_value = []
        api.request.return_value = fixture()["pr"]
        api.pull_request_files.return_value = fixture()["files"]
        event = {
            "workflow_run": {
                "id": 7,
                "run_attempt": 1,
                "event": "pull_request",
                "head_sha": SHA,
                "conclusion": "failure",
                "pull_requests": [{"number": 123, "head": {"sha": SHA}}],
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/secretary.json").write_text(json.dumps(CONFIG))
            event_path = root / "event.json"
            event_path.write_text(json.dumps(event))
            output_path = root / "output.txt"
            with patch.dict(os.environ, {
                "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_OUTPUT": str(output_path),
                "GITHUB_RUN_ID": "8",
                "SECRETARY_PR_NUMBER": "123",
                "SECRETARY_PR_HEAD_SHA": SHA,
                "SECRETARY_PR_READ_TOKEN": "synthetic-read-only",
                "SECRETARY_PREVIEW_ENABLED": "true",
            }, clear=True), \
                    patch("scripts.secretary.preview.ROOT", root), \
                    patch("scripts.secretary.preview.GitHub", return_value=api), \
                    patch("scripts.secretary.preview.ReadOnlyGitHub", return_value=api), \
                    patch("scripts.secretary.preview.sys.argv", ["preview.py", "--assess"]), \
                    patch(
                        "scripts.secretary.preview.latest_jobs",
                        return_value=({}, {"id": 7, "run_attempt": 1}),
                    ):
                main()
            output_contents = output_path.read_text()

        status_calls = [
            call for call in api.request.call_args_list
            if call.args[0] == "statuses/" + SHA
        ]
        self.assertEqual(len(status_calls), 1)
        self.assertEqual(status_calls[0].args[1]["state"], "failure")
        self.assertEqual(status_calls[0].args[1]["context"], "Secretary staging")
        self.assertFalse(any(call.args[0] == "check-runs" for call in api.request.call_args_list))
        self.assertEqual(output_contents, "deploy=false\n")

    def test_required_secretary_context_is_published_as_commit_status(self):
        api = Mock()
        log = "https://github.com/kendshhh/PhishLens/actions/runs/123"

        publish_preview_status(api, SHA, CONFIG, "pending", "Staging verification running", log)
        publish_preview_status(api, SHA, CONFIG, "success", "Staging verification passed", log)

        self.assertEqual(api.request.call_args_list[0].args, (
            "statuses/" + SHA,
            {
                "state": "pending",
                "context": "Secretary staging",
                "description": "Staging verification running",
                "target_url": log,
            },
        ))
        self.assertEqual(api.request.call_args_list[1].args, (
            "statuses/" + SHA,
            {
                "state": "success",
                "context": "Secretary staging",
                "description": "Staging verification passed",
                "target_url": log,
            },
        ))

    def test_failure_and_controller_error_stay_non_green(self):
        api = Mock()

        publish_preview_status(api, SHA, CONFIG, "failure", "Staging verification did not pass")
        publish_preview_status(api, SHA, CONFIG, "error", "Controller error")

        self.assertEqual(api.request.call_args_list[0].args[1]["state"], "failure")
        self.assertEqual(api.request.call_args_list[1].args[1]["state"], "error")
        self.assertTrue(all(call.args[1]["context"] == "Secretary staging" for call in api.request.call_args_list))

    def test_required_status_rejects_invalid_states_and_bounds_description(self):
        api = Mock()

        with self.assertRaises(ValueError):
            publish_preview_status(api, SHA, CONFIG, "action_required", "No green status")
        api.request.assert_not_called()

        publish_preview_status(api, SHA, CONFIG, "failure", "x" * 200)
        self.assertEqual(len(api.request.call_args.args[1]["description"]), 140)

    def test_preview_gate_normalizes_case_and_whitespace(self):
        with patch.dict(os.environ, {"SECRETARY_PREVIEW_ENABLED": "  TRUE \t"}):
            self.assertTrue(preview_gate_enabled())
        with patch.dict(os.environ, {"SECRETARY_PREVIEW_ENABLED": " true "}):
            self.assertTrue(preview_gate_enabled())
        with patch.dict(os.environ, {"SECRETARY_PREVIEW_ENABLED": "yes"}):
            self.assertFalse(preview_gate_enabled())
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(preview_gate_enabled())

    def test_duplicate_ci_completion_does_not_redeploy(self):
        api = Mock()
        api.request.side_effect = [[{"id": 9, "sha": SHA, "creator": {"login": "github-actions[bot]"},
            "payload": {"run_id": 7, "run_attempt": 2}}], [{"state": "success"}]]
        self.assertTrue(completed_event(api, CONFIG, {"id": 7, "head_sha": SHA, "run_attempt": 2}))

    def test_eligibility_draft_fork_failure_docs_and_stale(self):
        s = fixture()
        run = {"head_sha": SHA, "conclusion": "success"}
        opt_in_label = CONFIG["preview_opt_in_label"]
        self.assertEqual(
            eligibility(s["pr"], s["files"], run, "kendshhh/PhishLens", opt_in_label)[0],
            "deploy",
        )
        s["pr"]["draft"] = True
        self.assertEqual(
            eligibility(s["pr"], s["files"], run, "kendshhh/PhishLens", opt_in_label)[0],
            "action_required",
        )
        s["pr"]["draft"] = False
        s["pr"]["head"]["repo"]["full_name"] = "outside/fork"
        self.assertEqual(
            eligibility(s["pr"], s["files"], run, "kendshhh/PhishLens", opt_in_label)[0],
            "action_required",
        )
        s = fixture()
        self.assertEqual(
            eligibility(
                s["pr"], s["files"], {**run, "conclusion": "failure"},
                "kendshhh/PhishLens", opt_in_label,
            )[0],
            "failure",
        )
        self.assertEqual(
            eligibility(
                s["pr"], [{"filename": "README.md"}], run,
                "kendshhh/PhishLens", opt_in_label,
            )[0],
            "success",
        )
        s = fixture()
        s["pr"]["labels"] = []
        action, message = eligibility(
            s["pr"], s["files"], run, "kendshhh/PhishLens", opt_in_label,
        )
        self.assertEqual(action, "failure")
        self.assertIn("require the `needs-hosted-staging` label", message)
        self.assertEqual(
            eligibility(
                s["pr"], s["files"], {**run, "head_sha": "c" * 40},
                "kendshhh/PhishLens", opt_in_label,
            )[0],
            "stale",
        )

    def test_preview_head_guard_rejects_only_superseded_or_closed_prs(self):
        from scripts.secretary.preview import current_pr_head_matches

        current = {"state": "open", "head": {"sha": SHA}}
        self.assertTrue(current_pr_head_matches(current, SHA))
        current["head"]["sha"] = "c" * 40
        self.assertFalse(current_pr_head_matches(current, SHA))
        current["state"] = "closed"
        self.assertFalse(current_pr_head_matches(current, SHA))

    def test_workflow_pr_identity_requires_exact_payload_number_and_head(self):
        from scripts.secretary.preview import workflow_pr_identity

        run = {
            "head_sha": SHA,
            "pull_requests": [{"number": 123, "head": {"sha": SHA}}],
        }
        self.assertEqual(workflow_pr_identity(run, "123", SHA), (123, SHA))
        with self.assertRaisesRegex(RuntimeError, "associated with this workflow run"):
            workflow_pr_identity(run, "124", SHA)
        with self.assertRaisesRegex(RuntimeError, "differs from the completed PR CI head"):
            workflow_pr_identity(run, "123", "c" * 40)
        with self.assertRaisesRegex(RuntimeError, "valid PR head SHA"):
            workflow_pr_identity(run, "123", "not-a-sha")

    def test_predeploy_live_guard_rejects_an_advanced_pr_head(self):
        from scripts.secretary.preview import require_live_pr_eligibility

        pr = copy.deepcopy(fixture()["pr"])
        pr["head"]["sha"] = "c" * 40
        api = Mock()
        api.request.return_value = pr
        with self.assertRaisesRegex(RuntimeError, "head changed; staging deployment was not started"):
            require_live_pr_eligibility(
                api, 123, SHA, fixture()["files"],
                {"head_sha": SHA, "conclusion": "success"},
                "kendshhh/PhishLens", CONFIG["preview_opt_in_label"],
            )
        api.request.assert_called_once_with("pulls/123")

    def test_database_isolation_guards(self):
        rows = render_staging_environment_rows(REPORT_AUTH_MODE="neon")
        with patch.dict(os.environ, {
            "SECRETARY_STAGING_DB_HOST": STAGING_HOST,
            "SECRETARY_PRODUCTION_DB_HOST": PRODUCTION_HOST,
            "STAGING_AUTH_URL": "https://ep-test.neonauth.c-4.ap-southeast-1.aws.neon.tech/phishlens_dev/auth",
            "STAGING_AUTH_DATABASE": "phishlens_dev",
        }):
            verify_environment(rows, require_authenticated=True)
            set_render_environment_value(
                rows, "DATABASE_URL",
                f"postgresql://phishlens_staging_app:synthetic@{PRODUCTION_HOST}/phishlens_dev",
            )
            with self.assertRaises(RuntimeError):
                verify_environment(rows, require_authenticated=True)

            set_render_environment_value(
                rows, "DATABASE_URL",
                f"postgresql://neondb_owner:synthetic@{STAGING_HOST}/phishlens_dev",
            )
            with self.assertRaisesRegex(RuntimeError, "phishlens_staging_app role"):
                verify_environment(rows, require_authenticated=True)

            set_render_environment_value(
                rows, "DATABASE_URL",
                f"postgresql://phishlens_staging_app:synthetic@{STAGING_HOST}/phishlens_dev",
            )
            set_render_environment_value(
                rows, "STAGING_MIGRATION_DATABASE_URL",
                f"postgresql://neondb_owner:synthetic@{PRODUCTION_HOST}/phishlens_dev",
            )
            with self.assertRaisesRegex(RuntimeError, "isolated branch"):
                verify_environment(rows, require_authenticated=True)

            rows = render_staging_environment_rows()
            rows = [
                row for row in rows
                if row["envVar"]["key"] != "STAGING_MIGRATION_DATABASE_URL"
            ]
            with self.assertRaisesRegex(RuntimeError, "migration credential"):
                verify_environment(rows, require_authenticated=True)

    def test_hosted_staging_rejects_implicit_or_demo_auth_mode(self):
        for rows in (
            render_staging_environment_rows(REPORT_AUTH_MODE="demo"),
            render_staging_environment_rows(),
        ):
            with patch.dict(os.environ, {
                "SECRETARY_STAGING_DB_HOST": STAGING_HOST,
                "SECRETARY_PRODUCTION_DB_HOST": PRODUCTION_HOST,
            }), self.assertRaisesRegex(RuntimeError, "requires explicit REPORT_AUTH_MODE=neon"):
                verify_environment(rows, require_authenticated=True)

    def test_production_service_rejected(self):
        with self.assertRaises(RuntimeError):
            verify_service({"id": CONFIG["production_service"]}, CONFIG)

    def test_displaced_preview_check_invalidated(self):
        api = Mock()
        api.request.return_value = [{"id": 2, "sha": "c" * 40, "creator": {"login": "github-actions[bot]"}, "payload": {"secretary": 1}}]
        api.pages.return_value = [{"id": 8, "app": {"slug": "github-actions"}, "conclusion": "success"}]
        confirmed = confirm_live_deployment(
            api, CONFIG, {"status": "live", "commit": {"id": SHA}}, SHA
        )
        self.assertTrue(confirmed)
        self.assertEqual(api.request.call_args_list[1].args[0], "statuses/" + "c" * 40)
        self.assertEqual(api.request.call_args_list[1].args[1]["state"], "failure")
        self.assertEqual(api.request.call_args_list[1].args[1]["context"], "Secretary staging")
        self.assertEqual(api.request.call_args.args[1]["conclusion"], "action_required")

    def test_wrong_live_commit_invalidates_old_preview_before_rejecting(self):
        api = Mock()
        api.request.side_effect = lambda path, *args: (
            [{"id": 2, "sha": "b" * 40, "creator": {"login": "github-actions[bot]"},
              "payload": {"secretary": 1}}]
            if path.startswith("deployments?") else {}
        )
        api.pages.side_effect = [
            [{"id": 8, "app": {"slug": "github-actions"}, "conclusion": "success"}],
            [{"id": 9, "app": {"slug": "github-actions"}, "conclusion": "success"}],
        ]
        with self.assertRaisesRegex(RuntimeError, "wrong commit"):
            confirm_live_deployment(
                api, CONFIG, {"status": "live", "commit": {"id": "c" * 40}}, SHA
            )
        status_call = next(
            call for call in api.request.call_args_list
            if call.args[0] == "statuses/" + "b" * 40
        )
        self.assertEqual(status_call.args[1]["state"], "failure")
        patch_calls = [
            call for call in api.request.call_args_list
            if len(call.args) > 2 and call.args[2] == "PATCH"
        ]
        self.assertEqual({call.args[0] for call in patch_calls}, {"check-runs/8", "check-runs/9"})
        self.assertTrue(all(call.args[1]["conclusion"] == "action_required" for call in patch_calls))

    def test_failed_render_deploy_does_not_invalidate_previous_preview(self):
        api = Mock()
        confirmed = confirm_live_deployment(
            api, CONFIG, {"status": "update_failed", "commit": {"id": "c" * 40}}, SHA
        )
        self.assertFalse(confirmed)
        api.request.assert_not_called()
        api.pages.assert_not_called()

    def test_real_extension_archive_has_staging_banner_and_origin(self):
        api = Mock()
        def read(path):
            relative = path.split("contents/extension/", 1)[1].split("?", 1)[0]
            data = (ROOT / "extension" / relative).read_bytes()
            return {"encoding": "base64", "size": len(data), "content": base64.b64encode(data).decode()}
        api.request.side_effect = read
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "test.zip"
            package(api, SHA, 123, CONFIG, output)
            with ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn(b"STAGING", archive.read("popup.html"))
                self.assertIn(SHA.encode(), archive.read("popup.html"))
                self.assertNotIn(b"127.0.0.1", archive.read("background.js"))
                self.assertEqual(json.loads(archive.read("manifest.json"))["host_permissions"], [CONFIG["staging_origin"] + "/*"])

    def test_large_model_uses_exact_repository_blob_without_external_download(self):
        api = Mock()
        model = (ROOT / "extension/ai/tfidf_v12a.json").read_bytes()
        digest = hashlib.sha1(f"blob {len(model)}\0".encode() + model).hexdigest()
        def read(path):
            if path == "git/blobs/" + digest:
                return {"encoding": "base64", "sha": digest, "size": len(model),
                        "content": base64.b64encode(model).decode()}
            relative = path.split("contents/extension/", 1)[1].split("?", 1)[0]
            data = (ROOT / "extension" / relative).read_bytes()
            if relative == "ai/tfidf_v12a.json":
                return {"encoding": "none", "sha": digest, "size": len(model)}
            return {"encoding": "base64", "size": len(data), "content": base64.b64encode(data).decode()}
        api.request.side_effect = read
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "test.zip"
            package(api, SHA, 123, CONFIG, output)
            with ZipFile(output) as archive:
                self.assertEqual(archive.read("ai/tfidf_v12a.json"), model)
                self.assertIn("js/report-client.js", archive.namelist())

    def test_large_model_with_mismatched_blob_is_rejected(self):
        api = Mock()
        def read(path):
            if path.startswith("git/blobs/"):
                return {"encoding": "base64", "sha": "b" * 40, "size": 1, "content": "eA=="}
            relative = path.split("contents/extension/", 1)[1].split("?", 1)[0]
            data = (ROOT / "extension" / relative).read_bytes()
            if relative == "ai/tfidf_v12a.json":
                return {"encoding": "none", "sha": "a" * 40, "size": len(data)}
            return {"encoding": "base64", "size": len(data), "content": base64.b64encode(data).decode()}
        api.request.side_effect = read
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(RuntimeError, "identity"):
            package(api, SHA, 123, CONFIG, Path(directory) / "test.zip")
    def test_local_scanner_archive_labels_partial_llama_package_and_staging_report_origin(self):
        api = Mock()
        files = {
            "popup.js": b"import { initializeAccountPopup } from './js/account-popup.js';\n",
            "manifest.json": json.dumps({
                "manifest_version": 3,
                "background": {"service_worker": "background.js", "type": "module"},
            }).encode(),
            "popup.html": b"<html><body><main></main></body></html>",
            "background.js": b"import { analyzeWithReview } from './ai/live-workflow.mjs';\n",
            "js/popup.js": b"import { API_BASE_URL } from './config.js';\n",
        }
        requested = []

        def read(path):
            relative = path.split("contents/extension/", 1)[1].split("?", 1)[0]
            requested.append(relative)
            data = files.get(relative, f"fixture:{relative}".encode())
            return {
                "encoding": "base64",
                "size": len(data),
                "content": base64.b64encode(data).decode(),
            }

        api.request.side_effect = read
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "local-scanner.zip"
            package(api, SHA, 123, CONFIG, output)
            with ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("STAGING_PACKAGE_NOTICE.txt", names)
                self.assertFalse(any(name.startswith("model-assets/llama/") for name in names))
                notice = archive.read("STAGING_PACKAGE_NOTICE.txt").decode()
                self.assertIn("PARTIAL STAGING PACKAGE", notice)
                self.assertIn("model-assets/llama/", notice)
                preview_info = json.loads(archive.read("preview-info.json"))
                self.assertEqual(preview_info["package_status"], "partial")
                self.assertFalse(preview_info["includes_local_llama_weights"])
                self.assertEqual(preview_info["excluded_assets"], ["model-assets/llama/"])
                for required in (
                    "ai/live-workflow.mjs",
                    "ai/local-analyzer.mjs",
                    "ai/tfidf_v12a.json",
                    "vendor/ml/ort-wasm-simd-threaded.jsep.wasm",
                    "vendor/ml/ort-wasm-simd-threaded.asyncify.wasm",
                    "js/report-workflow.js",
                    "js/account-popup.js", "js/account-session.js", "js/account-ui.js",
                ):
                    self.assertIn(required, names)
                self.assertEqual(
                    archive.read("js/config.js"),
                    ("export const API_BASE_URL = " + json.dumps(CONFIG["staging_origin"]) + ";\n").encode(),
                )
                self.assertIn(b"API_BASE_URL", archive.read("js/popup.js"))
                self.assertEqual(
                    json.loads(archive.read("manifest.json"))["host_permissions"],
                    [CONFIG["staging_origin"] + "/*"],
                )
                worker = archive.read("background.js")
                self.assertNotIn(b"127.0.0.1", worker)
                self.assertNotIn(b"localhost", worker)
                self.assertNotIn(CONFIG["production_origin"].encode(), worker)
        self.assertIn("vendor/ml/ort-wasm-simd-threaded.jsep.wasm", requested)
        self.assertIn("vendor/ml/ort-wasm-simd-threaded.asyncify.wasm", requested)
        self.assertFalse(any(asset.startswith("model-assets/llama/") for asset in requested))


class MetricsTests(unittest.TestCase):
    def test_logs_disclose_categories_never_raw_messages(self):
        result = log_categories([{"message": "ModuleNotFoundError PRIVATE_TOKEN=do-not-print"}])
        self.assertEqual(result["categories"]["missing_dependency"], 1)
        self.assertNotIn("PRIVATE_TOKEN", json.dumps(result))

    def test_production_controller_failure_emits_incident(self):
        from scripts.secretary.production import main

        api = Mock()
        api.pages.return_value = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/secretary.json").write_text(json.dumps(CONFIG))
            event = root / "event.json"
            event.write_text(json.dumps({"workflow_run": {"conclusion": "failure"}}))
            with patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event)}, clear=True), patch("scripts.secretary.production.ROOT", root), patch("scripts.secretary.production.GitHub", return_value=api), self.assertRaises(SystemExit):
                main()
            result = json.loads((root / "output/secretary-production/metrics.json").read_text())
            self.assertIn("Main CI failed", result["error"])
            self.assertTrue((root / "output/secretary-production/incident-draft.md").exists())

    def test_dedup_reruns_cancelled_separate_and_duration(self):
        base = {"id": 1, "run_attempt": 1, "event": "pull_request", "head_branch": "feat/demo", "status": "completed",
                "conclusion": "failure", "created_at": "2026-10-18T00:00:00Z"}
        runs = [base, {**base, "run_attempt": 2, "conclusion": "success"}, {**base, "id": 2, "conclusion": "cancelled"}]
        result = pipeline_metrics(runs, {1: [{"completed_at": "2026-10-18T00:02:00Z"}]})
        self.assertEqual(result["sample_workflows"], 2)
        self.assertEqual(result["success_rate_percent"], 100)
        self.assertEqual(result["cancelled"], 1)
        self.assertEqual(result["average_pr_pipeline_seconds"], 120)

    def test_production_failure_and_unknown_recovery(self):
        d = {"id": "dep1", "status": "build_failed"}
        result = deployment_metrics([d, d], {})
        self.assertEqual(result["failed_deployments"], 1)
        self.assertIsNone(result["recovery_time"])
        self.assertIsNone(result["average_merge_to_render_live_seconds"])


if __name__ == "__main__":
    unittest.main()
