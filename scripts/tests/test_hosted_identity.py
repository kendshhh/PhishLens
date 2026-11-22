"""Hosted acceptance must identify the requested staging commit and data."""
import copy
import io
import json
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.secretary.github_api import APIError, ReadOnlyGitHub
from scripts.secretary.preview import smoke, verify_saved_report

SHA = "a" * 40
ROOT = Path(__file__).resolve().parents[2]


class HostedIdentityTests(unittest.TestCase):
    def workflow_python_script(self, marker):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        step_start = workflow.index(marker)
        run_start = workflow.index("        run: |\n", step_start)
        body_start = run_start + len("        run: |\n")
        block_end = workflow.find("\n          PY", body_start)
        block = workflow[body_start:block_end + len("\n          PY")].splitlines()
        self.assertEqual(block[0].strip(), "python - <<'PY'")
        self.assertEqual(block[-1].strip(), "PY")
        return "\n".join(
            line.removeprefix("          ")
            for line in block[1:-1]
        )

    def run_workflow_python(self, marker, request_effect, package_effect=None, crud_result=None):
        script = self.workflow_python_script(marker)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / ".github"
            config_dir.mkdir()
            config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
            (config_dir / "secretary.json").write_text(json.dumps(config), encoding="utf-8")
            output_dir = root / "output/hosted-staging"
            output_dir.mkdir(parents=True)
            evidence = crud_result or {
                "result": "passed", "cleanedUp": True, "analysisMode": "mock",
                "analysisProvenance": {
                    "providerMode": "mock", "model": None,
                    "modelRevision": None, "promptVersion": None,
                },
            }
            (output_dir / "saved-report-crud.json").write_text(json.dumps(evidence), encoding="utf-8")
            output_file = root / "github-output.txt"
            summary_file = root / "github-summary.md"
            script_file = root / "workflow-step.py"
            event_file = root / "event.json"
            event_file.write_text(json.dumps({
                "number": 68,
                "repository": {"full_name": "kendshhh/PhishLens"},
                "pull_request": {
                    "number": 68,
                    "head": {
                        "sha": SHA,
                        "repo": {"full_name": "kendshhh/PhishLens"},
                    },
                },
            }), encoding="utf-8")
            script_file.write_text(script, encoding="utf-8")
            environment = {
                "GITHUB_TOKEN": "test-token",
                "GITHUB_REPOSITORY": "kendshhh/PhishLens",
                "GITHUB_EVENT_PATH": str(event_file),
                "GITHUB_OUTPUT": str(output_file),
                "GITHUB_STEP_SUMMARY": str(summary_file),
                "STAGING_BASE_URL": config["staging_origin"],
                "STAGING_COMMIT": SHA,
                "STAGING_MIGRATION_REVISION": "0003_saved_analysis_idempotency",
                "STAGING_PR_HEAD_SHA": SHA,
                "STAGING_PR": "68",
            }
            extension_origin = "chrome-extension://ceneonaedddlkdocdapimkfggbjcchlb"
            bridge_requests = []

            class BridgeResponse:
                def __init__(self, url):
                    self.url = url
                    self.status = 200
                    path = url.split("?", 1)[0]
                    content_type = "text/html; charset=utf-8" if path.endswith("/auth/bridge") else "application/javascript"
                    self.headers = {"Content-Type": content_type}
                    if path.endswith("/auth/bridge"):
                        self.headers["Content-Security-Policy"] = f"frame-ancestors {extension_origin}"
                    self.body = (
                        f'<div data-extension-origin="{extension_origin}"></div>'.encode()
                        if path.endswith("/auth/bridge") else b""
                    )

                def __enter__(self):
                    return self

                def __exit__(self, *_args):
                    return False

                def geturl(self):
                    return self.url

                def read(self, _limit=-1):
                    return self.body

            class BridgeOpener:
                def open(self, request, timeout=20):
                    bridge_requests.append((request.get_method(), request.full_url, timeout))
                    return BridgeResponse(request.full_url)

            previous_dir = Path.cwd()
            exit_code = None
            step_error = None
            try:
                os.chdir(root)
                with patch.dict(os.environ, environment), patch.object(
                    ReadOnlyGitHub, "request", side_effect=request_effect
                ), patch("scripts.secretary.preview.smoke", return_value={"health": "passed"}), patch(
                    "scripts.secretary.preview.package", side_effect=package_effect
                ), patch("urllib.request.build_opener", return_value=BridgeOpener()):
                    try:
                        runpy.run_path(str(script_file), run_name="__main__")
                    except SystemExit as error:
                        exit_code = error.code
                    except RuntimeError as error:
                        exit_code = 1
                        step_error = str(error)
                    else:
                        exit_code = 0
            finally:
                os.chdir(previous_dir)

            return {
                "exit_code": exit_code,
                "step_error": step_error,
                "output": output_file.read_text(encoding="utf-8") if output_file.exists() else "",
                "summary": summary_file.read_text(encoding="utf-8") if summary_file.exists() else "",
                "evidence_exists": (output_dir / "evidence.json").exists(),
                "package_exists": (output_dir / "PhishLens-Staging-Extension.zip").exists(),
                "evidence": json.loads((output_dir / "evidence.json").read_text(encoding="utf-8"))
                    if (output_dir / "evidence.json").exists() else None,
                "bridge_requests": bridge_requests,
            }

    def responses(self):
        return [
            {"status": "ok", "service": "phishlens-api"},
            {"status": "ready", "database": "connected"},
            {"commit": SHA, "environment": "staging"},
            {"items": [{"subject": "Synthetic account notice"}]},
        ]

    def verify(self, payloads, *, report_auth_mode="demo"):
        responses = [value if isinstance(value, HTTPError) else io.BytesIO(json.dumps(value).encode())
                     for value in payloads]
        with patch("urllib.request.urlopen", side_effect=responses), patch(
            "scripts.secretary.preview.time.monotonic", side_effect=[0, 181]
        ):
            return smoke("https://staging.invalid", SHA, report_auth_mode=report_auth_mode)

    def test_exact_staging_commit_and_seed_pass(self):
        evidence = self.verify(self.responses())
        self.assertEqual(evidence["version"], SHA)
        self.assertEqual(evidence["history"], "passed")

    def test_neon_smoke_records_the_anonymous_auth_challenge(self):
        values = self.responses()[:3]
        values.append(HTTPError("https://staging.invalid/api/analyses", 401, "Unauthorized",
                                {"WWW-Authenticate": "Bearer"}, io.BytesIO()))
        evidence = self.verify(values, report_auth_mode="neon")
        self.assertEqual(evidence["version"], SHA)
        self.assertEqual(evidence["history"], "authentication_required")
        self.assertEqual(evidence["seeded_history"], "not_checked")
        self.assertEqual(
            evidence["anonymous_saved_report"],
            {"path": "/api/analyses", "status_code": 401, "challenge": "Bearer", "redirected": False},
        )

    def test_neon_smoke_fails_if_anonymous_history_is_accessible(self):
        with self.assertRaisesRegex(RuntimeError, "did not reject an anonymous saved-report request"):
            self.verify(self.responses(), report_auth_mode="neon")

    def test_neon_smoke_rejects_an_unrelated_unauthorized_response(self):
        values = self.responses()[:3]
        values.append(HTTPError("https://other.invalid/api/analyses", 401, "Unauthorized",
                                {"WWW-Authenticate": "Bearer"}, io.BytesIO()))
        with self.assertRaisesRegex(RuntimeError, "expected saved-report authentication challenge"):
            self.verify(values, report_auth_mode="neon")

    def test_saved_report_runner_accepts_only_complete_machine_evidence(self):
        result = {
            "result": "passed", "cleanedUp": True,
            "analysisMode": "real",
            "analysisProvenance": {"providerMode": "gemini"},
        }
        with patch("scripts.secretary.preview.subprocess.run", return_value=type(
            "Completed", (), {"returncode": 0, "stdout": json.dumps(result)}
        )()) as run:
            self.assertEqual(verify_saved_report("https://staging.invalid", SHA), result)
        command = run.call_args.args[0]
        self.assertIn("--environment", command)
        self.assertIn("staging", command)
        self.assertIn("--allow-writes", command)
        self.assertIn(SHA, command)

    def test_saved_report_runner_rejects_failed_or_unclean_result(self):
        result = {"result": "passed", "cleanedUp": False, "analysisMode": "real",
                  "analysisProvenance": {"providerMode": "gemini"}}
        with patch("scripts.secretary.preview.subprocess.run", return_value=type(
            "Completed", (), {"returncode": 0, "stdout": json.dumps(result)}
        )()), self.assertRaisesRegex(RuntimeError, "did not confirm cleanup"):
            verify_saved_report("https://staging.invalid", SHA)

    def test_saved_report_runner_preserves_mock_mode_for_checklist(self):
        result = {
            "result": "passed", "cleanedUp": True, "analysisMode": "mock",
            "analysisProvenance": {"providerMode": "mock"},
        }
        with patch("scripts.secretary.preview.subprocess.run", return_value=type(
            "Completed", (), {"returncode": 0, "stdout": json.dumps(result)}
        )()):
            self.assertEqual(verify_saved_report("https://staging.invalid", SHA), result)

    def test_saved_report_runner_rejects_inconsistent_mode_and_provider(self):
        result = {
            "result": "passed", "cleanedUp": True, "analysisMode": "real",
            "analysisProvenance": {"providerMode": "mock"},
        }
        with patch("scripts.secretary.preview.subprocess.run", return_value=type(
            "Completed", (), {"returncode": 0, "stdout": json.dumps(result)}
        )()), self.assertRaisesRegex(RuntimeError, "inconsistent AI provenance"):
            verify_saved_report("https://staging.invalid", SHA)

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

    def test_stale_runs_are_filtered_before_deployment(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        preflight_start = workflow.index("  hosted-staging-preflight:\n")
        hosted_start = workflow.index("  hosted-staging:\n", preflight_start)
        preflight_job = workflow[preflight_start:hosted_start]
        hosted_job = workflow[hosted_start:]

        self.assertIn("needs: [staging]", preflight_job)
        self.assertIn("pull-requests: read", preflight_job)
        self.assertIn("outputs:\n      current: ${{ steps.staging-preflight.outputs.current }}", preflight_job)
        self.assertNotIn("environment: staging", preflight_job)
        self.assertIn("live_pr_matches(", preflight_job)
        self.assertIn("ReadOnlyGitHub", preflight_job)
        self.assertIn("requested_pr_identity()", preflight_job)
        self.assertIn("github.event.pull_request.user.login != 'dependabot[bot]'", preflight_job)
        hosted_header = hosted_job.split("    steps:\n", 1)[0]
        needs_line = next(
            line.strip()
            for line in hosted_header.splitlines()
            if line.strip().startswith("needs:")
        )
        needs = {
            dependency.strip()
            for dependency in needs_line.partition(":")[2].strip().strip("[]").split(",")
        }
        self.assertEqual(needs, {"staging", "hosted-staging-preflight", "backend"})
        self.assertIn("always()", hosted_header)
        self.assertNotIn("needs.staging.result == 'success'", hosted_header)
        self.assertNotIn("needs.hosted-staging-preflight.result == 'success'", hosted_header)
        self.assertNotIn("needs.hosted-staging-preflight.outputs.current == 'true'", hosted_header)
        self.assertIn("Fail instead of skipping when an eligible staging prerequisite failed", hosted_job)
        self.assertIn("STAGING_INTEGRATION_RESULT", hosted_job)
        self.assertIn("PREFLIGHT_CURRENT", hosted_job)
        self.assertIn("github.event.pull_request.user.login != 'dependabot[bot]'", hosted_header)
        self.assertIn("environment: staging", hosted_header)

    def test_hosted_staging_rechecks_current_head_before_deployment(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        extension_start = workflow.index("  extension:\n")
        extension_end = workflow.index("  migration-source-preflight:\n", extension_start)
        extension_job = workflow[extension_start:extension_end]
        browser_test_start = extension_job.index("      - name: Test packaged extension in isolated Chromium")
        browser_upload_start = extension_job.index("      - name: Upload browser acceptance evidence", browser_test_start)
        browser_upload_end = extension_job.index("      - name: Upload extension package", browser_upload_start)
        browser_upload = extension_job[browser_upload_start:browser_upload_end]
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", extension_job)
        self.assertEqual(
            extension_job.count("SOURCE_COMMIT: ${{ github.event.pull_request.head.sha || github.sha }}"),
            3,
        )
        self.assertIn("Require browser acceptance report and evidence", extension_job)
        self.assertIn("if-no-files-found: error", browser_upload)

        hosted_start = workflow.index("  hosted-staging:\n")
        hosted_job = workflow[hosted_start:]
        first_check = "      - name: Recheck PR head immediately before deployment"
        source_checkout = "      - name: Check out exact PR head"
        second_check = "      - name: Recheck PR head immediately before staging deploy"
        auth_preflight = "      - name: Verify Render staging Auth mode and exact database mapping"
        deploy = "      - name: Deploy exact PR head using the trusted controller"
        acceptance = "      - name: Run authenticated extension and persistent CRUD acceptance"
        first_start = hosted_job.index(first_check)
        first_end = hosted_job.index(source_checkout, first_start)
        second_start = hosted_job.index(second_check, first_end)
        second_end = hosted_job.index(auth_preflight, second_start)
        deploy_start = hosted_job.index(deploy, second_end)
        deploy_end = hosted_job.index(acceptance, deploy_start)
        first = hosted_job[first_start:first_end]
        second = hosted_job[second_start:second_end]
        deployment = hosted_job[deploy_start:deploy_end]

        self.assertIn("live_pr_matches(", first)
        self.assertIn("ReadOnlyGitHub", first)
        self.assertIn("requested_pr_identity()", first)
        self.assertIn("live_pr_matches(", second)
        self.assertIn("ReadOnlyGitHub", second)
        self.assertIn("requested_pr_identity()", second)
        self.assertIn("STAGING_COMMIT: ${{ github.event.pull_request.head.sha }}", deployment)
        self.assertIn("STAGING_PR_HEAD_SHA: ${{ github.event.pull_request.head.sha }}", deployment)
        self.assertIn("STAGING_PR: ${{ github.event.pull_request.number }}", deployment)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", deployment)
        self.assertNotIn("github.sha", deployment)

        controller = (ROOT / "scripts/deploy_staging.py").read_text(encoding="utf-8")
        self.assertIn("def requested_pr_identity()", controller)
        self.assertIn("def live_pr_matches(", controller)
        self.assertIn("require_live_pr(github, number, head_sha, repository)", controller)

    def test_api_error_before_deployment_fails_closed(self):
        marker = "      - name: Check PR head before entering staging queue"
        result = self.run_workflow_python(marker, APIError("GitHub HTTP 403 for pulls/68"))

        self.assertEqual(result["exit_code"], 1)
        self.assertIn("current=false", result["output"])
        self.assertIn("no deployment was started", result["summary"])

    def test_api_error_immediately_before_deployment_fails_closed(self):
        marker = "      - name: Recheck PR head immediately before staging deploy"
        result = self.run_workflow_python(marker, APIError("GitHub HTTP 403 for pulls/68"))

        self.assertNotEqual(result["exit_code"], 0)
        self.assertIn("staging deployment blocked", str(result["exit_code"]))
        self.assertFalse(result["evidence_exists"])
        self.assertFalse(result["package_exists"])

    def test_authenticated_hosted_acceptance_uses_the_exact_pr_head(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        acceptance = (ROOT / "scripts/staging_extension_acceptance.mjs").read_text(encoding="utf-8")
        hosted = workflow[workflow.index("  hosted-staging:\n"):]
        self.assertIn("node scripts/staging_extension_acceptance.mjs", hosted)
        self.assertIn("verify-pr-staging", hosted)
        self.assertIn("--expected-sha \"$EXPECTED_SHA\"", hosted)
        self.assertIn("STAGING_AUTH_USER_A_EMAIL", hosted)
        self.assertIn("STAGING_AUTH_USER_B_EMAIL", hosted)
        self.assertIn("RELEASE_SOURCE_SHA: ${{ github.event.pull_request.head.sha }}", hosted)
        self.assertIn("STAGING_EXPECTED_BACKEND_SHA: ${{ github.event.pull_request.head.sha }}", hosted)
        self.assertIn("EXPECTED_SHA: ${{ github.event.pull_request.head.sha }}", hosted)
        self.assertNotIn("STAGING_COMMIT: ${{ github.sha }}", hosted)
        self.assertNotIn("RELEASE_SOURCE_SHA: ${{ github.sha }}", hosted)
        self.assertNotIn("STAGING_EXPECTED_BACKEND_SHA: ${{ github.sha }}", hosted)
        self.assertIn("verified_account_sessions", acceptance)
        self.assertIn("account_subject_sha256.b = subjectB", acceptance)
        self.assertLess(
            acceptance.index("const subjectB = await waitForAccountToken('b')"),
            acceptance.index("const idA = await createReport("),
        )
        self.assertNotIn("subjectHash(emailA", acceptance)

    def test_draft_pr_is_skipped_before_deployment_and_verification(self):
        current_draft = {
            "number": 68,
            "state": "open",
            "head": {"sha": SHA, "repo": {"full_name": "kendshhh/PhishLens"}},
            "draft": True,
            "labels": [{"name": "needs-hosted-staging"}],
        }
        preflight = self.run_workflow_python(
            "      - name: Check PR head before entering staging queue",
            [current_draft],
        )
        deploy_preflight = self.run_workflow_python(
            "      - name: Recheck PR head immediately before staging deploy",
            [current_draft],
        )
        hosted = self.run_workflow_python(
            "      - name: Verify PR-head identity and package staging assets",
            [current_draft],
        )

        self.assertEqual(preflight["exit_code"], 0)
        self.assertIn("current=false", preflight["output"])
        self.assertIn("a draft", preflight["summary"])
        self.assertEqual(deploy_preflight["exit_code"], 0)
        self.assertIn("current=false", deploy_preflight["output"])
        self.assertEqual(hosted["exit_code"], 0)
        self.assertIn("current=false", hosted["output"])
        self.assertIn("became a draft", hosted["summary"])
        self.assertFalse(hosted["evidence_exists"])
        self.assertFalse(hosted["package_exists"])

    def test_read_only_finalizer_runs_before_authenticated_acceptance(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        hosted = workflow[workflow.index("  hosted-staging:\n"):]
        start = hosted.index("      - name: Verify PR-head identity and package staging assets")
        end = hosted.index("      - name: Run authenticated extension and persistent CRUD acceptance", start)
        finalizer = hosted[start:end]
        acceptance_preflight_start = hosted.index("      - name: Recheck live PR head before authenticated acceptance", start)
        acceptance_preflight = hosted[acceptance_preflight_start:end]
        acceptance = hosted[end:]

        self.assertIn("requested_pr_identity()", finalizer)
        self.assertIn("live_pr_matches(current, number, pr_head_sha, repository)", finalizer)
        self.assertIn("ReadOnlyGitHub", finalizer)
        self.assertIn("STAGING_COMMIT: ${{ github.event.pull_request.head.sha }}", finalizer)
        self.assertNotIn("github.sha", finalizer)
        self.assertIn("id: staging-acceptance-preflight", acceptance_preflight)
        self.assertIn("requested_pr_identity()", acceptance_preflight)
        self.assertIn("live_pr_matches(", acceptance_preflight)
        self.assertIn("if: steps.staging-acceptance-preflight.outputs.current == 'true'", acceptance)
        self.assertIn("result.write('current=false\\n')", finalizer)
        self.assertEqual(finalizer.count("if superseded():"), 3)

    def test_api_errors_during_hosted_verification_never_publish_success(self):
        marker = "      - name: Verify PR-head identity and package staging assets"
        current_pr = {
            "number": 68,
            "state": "open",
            "head": {"sha": SHA, "repo": {"full_name": "kendshhh/PhishLens"}},
            "draft": False,
            "labels": [{"name": "needs-hosted-staging"}],
        }
        cases = (
            ("head lookup", APIError("GitHub HTTP 403 for pulls/68"), None),
            ("package lookup", [current_pr, current_pr], APIError("GitHub HTTP 403 for commits/SHA")),
        )
        for label, request_effect, package_effect in cases:
            with self.subTest(label=label):
                result = self.run_workflow_python(marker, request_effect, package_effect)

                self.assertEqual(result["exit_code"], 1)
                self.assertIn("current=false", result["output"])
                self.assertIn("No extension artifact was published", result["summary"])
                self.assertNotIn("read-only preflight passed", result["summary"])
                self.assertFalse(result["evidence_exists"])
                self.assertFalse(result["package_exists"])

    def test_hosted_finalizer_is_read_only_and_records_auth_bridge_checks(self):
        marker = "      - name: Verify PR-head identity and package staging assets"
        current_pr = {
            "number": 68,
            "state": "open",
            "head": {"sha": SHA, "repo": {"full_name": "kendshhh/PhishLens"}},
            "draft": False,
            "labels": [{"name": "needs-hosted-staging"}],
        }

        def package_effect(_api, _sha, _number, _config, output):
            Path(output).write_bytes(b"synthetic staging package")

        result = self.run_workflow_python(
            marker, [current_pr, current_pr, current_pr], package_effect
        )

        self.assertEqual(result["exit_code"], 0)
        self.assertIn("current=true", result["output"])
        self.assertIn("Hosted staging read-only preflight passed", result["summary"])
        self.assertIn("no account or saved-report writes were performed", result["summary"])
        self.assertIn("endpoint preflight uses GET requests only", result["summary"])
        self.assertTrue(result["evidence_exists"])
        self.assertTrue(result["package_exists"])

        checklist = result["evidence"]["automated_checklist"]
        read_only = checklist["read_only_preflight"]
        self.assertEqual(read_only["result"], "passed")
        self.assertEqual(read_only["auth_bridge"], "passed")
        self.assertEqual(read_only["anonymous_saved_report"], "authentication_required")
        self.assertEqual(read_only["seeded_history"], "not_checked")
        self.assertFalse(read_only["application_crud_writes_performed"])
        self.assertEqual(checklist["live_auth_acceptance"]["result"], "not_run")
        self.assertEqual(checklist["saved_report_crud"]["result"], "not_run")
        self.assertEqual([request[0] for request in result["bridge_requests"]], ["GET", "GET", "GET"])
        self.assertEqual(
            [request[1].removeprefix("https://phishlens-staging.onrender.com")
             for request in result["bridge_requests"]],
            ["/auth/bridge", "/auth/bridge/client.js", "/auth/bridge/sdk.mjs"],
        )


if __name__ == "__main__":
    unittest.main()

