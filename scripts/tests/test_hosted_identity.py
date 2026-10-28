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

from scripts.secretary.github_api import APIError, GitHub
from scripts.secretary.preview import smoke

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

    def run_workflow_python(self, marker, request_effect, package_effect=None):
        script = self.workflow_python_script(marker)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / ".github"
            config_dir.mkdir()
            config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
            (config_dir / "secretary.json").write_text(json.dumps(config), encoding="utf-8")
            output_dir = root / "output/hosted-staging"
            output_dir.mkdir(parents=True)
            output_file = root / "github-output.txt"
            summary_file = root / "github-summary.md"
            script_file = root / "workflow-step.py"
            script_file.write_text(script, encoding="utf-8")
            environment = {
                "GITHUB_TOKEN": "test-token",
                "GITHUB_REPOSITORY": "kendshhh/PhishLens",
                "GITHUB_OUTPUT": str(output_file),
                "GITHUB_STEP_SUMMARY": str(summary_file),
                "STAGING_BASE_URL": config["staging_origin"],
                "STAGING_COMMIT": "b" * 40,
                "STAGING_PR_HEAD_SHA": SHA,
                "STAGING_PR": "68",
            }
            previous_dir = Path.cwd()
            exit_code = None
            try:
                os.chdir(root)
                with patch.dict(os.environ, environment), patch.object(
                    GitHub, "request", side_effect=request_effect
                ), patch("scripts.secretary.preview.smoke", return_value={"health": "passed"}), patch(
                    "scripts.secretary.preview.package", side_effect=package_effect
                ):
                    try:
                        runpy.run_path(str(script_file), run_name="__main__")
                    except SystemExit as error:
                        exit_code = error.code
            finally:
                os.chdir(previous_dir)

            return {
                "exit_code": exit_code,
                "output": output_file.read_text(encoding="utf-8") if output_file.exists() else "",
                "summary": summary_file.read_text(encoding="utf-8") if summary_file.exists() else "",
                "evidence_exists": (output_dir / "evidence.json").exists(),
                "package_exists": (output_dir / "PhishLens-Staging-Extension.zip").exists(),
            }

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
        self.assertIn("not current.get('draft', False)", preflight_job)
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
        self.assertIn("needs.staging.result == 'success'", hosted_header)
        self.assertIn("needs.hosted-staging-preflight.result == 'success'", hosted_header)
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
        self.assertIn("current['state'] == 'open' and current['head']['sha'] == pr_head_sha", step)
        self.assertIn("No extension artifact was published.", step)
        self.assertNotIn("current['head']['sha'] != deploy_sha", step)
        self.assertIn("def superseded():", step)
        self.assertIn("current['state'] == 'open'", step)
        self.assertIn("current['head']['sha'] == pr_head_sha", step)
        self.assertIn("not current.get('draft', False)", step)
        self.assertEqual(step.count("if superseded():"), 3)
        self.assertIn("'deployed_commit': deploy_sha", step)
        self.assertIn("result.write('current=false\\n')", step)
        self.assertIn("raise SystemExit(0)", step)
        self.assertIn("steps.staging-finalize.outputs.current == 'true'", hosted_job[end:])

    def test_api_error_before_staging_approval_fails_closed(self):
        marker = "      - name: Check PR head before requesting staging approval"
        result = self.run_workflow_python(marker, APIError("GitHub HTTP 403 for pulls/68"))

        self.assertEqual(result["exit_code"], 1)
        self.assertIn("current=false", result["output"])
        self.assertIn("no deployment was started", result["summary"])

    def test_api_errors_during_hosted_verification_never_publish_success(self):
        marker = "      - name: Verify deployed merge identity and package staging assets"
        current_pr = {"state": "open", "head": {"sha": SHA}, "draft": False}
        cases = (
            ("head lookup", APIError("GitHub HTTP 403 for pulls/68"), None),
            (
                "package lookup",
                [current_pr, current_pr],
                APIError("GitHub HTTP 403 for commits/SHA"),
            ),
        )
        for label, request_effect, package_effect in cases:
            with self.subTest(label=label):
                result = self.run_workflow_python(marker, request_effect, package_effect)

                self.assertEqual(result["exit_code"], 1)
                self.assertIn("current=false", result["output"])
                self.assertIn("No extension artifact was published", result["summary"])
                self.assertNotIn("Hosted staging verified", result["summary"])
                self.assertFalse(result["evidence_exists"])
                self.assertFalse(result["package_exists"])

    def test_draft_pr_is_skipped_before_approval_and_verification(self):
        current_draft = {"state": "open", "head": {"sha": SHA}, "draft": True}
        preflight = self.run_workflow_python(
            "      - name: Check PR head before requesting staging approval",
            [current_draft],
        )
        hosted = self.run_workflow_python(
            "      - name: Verify deployed merge identity and package staging assets",
            [current_draft],
        )

        self.assertIn("current=false", preflight["output"])
        self.assertIn("a draft", preflight["summary"])
        self.assertEqual(hosted["exit_code"], 0)
        self.assertIn("current=false", hosted["output"])
        self.assertIn("became a draft", hosted["summary"])
        self.assertNotIn("Hosted staging verified", hosted["summary"])
        self.assertFalse(hosted["evidence_exists"])
        self.assertFalse(hosted["package_exists"])


if __name__ == "__main__":
    unittest.main()
