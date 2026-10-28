"""Keep exact-source migration validation tied to the current PR head."""

import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.secretary.github_api import APIError, GitHub

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SHA = "a" * 40


class MigrationPreflightTests(unittest.TestCase):
    def workflow(self):
        return (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    def workflow_python_script(self):
        workflow = self.workflow()
        marker = "      - name: Check whether migration source is still the current PR head"
        start = workflow.index(marker)
        run_start = workflow.index("        run: |\n", start)
        body_start = run_start + len("        run: |\n")
        block_end = workflow.index("\n          PY", body_start)
        block = workflow[body_start : block_end + len("\n          PY")].splitlines()
        self.assertEqual(block[0].strip(), "python - <<'PY'")
        self.assertEqual(block[-1].strip(), "PY")
        return "\n".join(line.removeprefix("          ") for line in block[1:-1])

    def run_preflight(self, response):
        script = self.workflow_python_script()
        with tempfile.TemporaryDirectory(prefix="phishlens-pr-head-") as directory:
            root = Path(directory)
            script_path = root / "preflight.py"
            output_path = root / "output.txt"
            summary_path = root / "summary.md"
            script_path.write_text(script, encoding="utf-8")
            environment = {
                "GITHUB_TOKEN": "test-token",
                "GITHUB_REPOSITORY": "kendshhh/PhishLens",
                "GITHUB_OUTPUT": str(output_path),
                "GITHUB_STEP_SUMMARY": str(summary_path),
                "MIGRATION_PR_HEAD_SHA": EXPECTED_SHA,
                "MIGRATION_PR": "82",
            }
            exit_code = None
            with patch.dict(os.environ, environment), patch.object(
                GitHub, "request", side_effect=response
            ):
                try:
                    runpy.run_path(str(script_path), run_name="__main__")
                except SystemExit as error:
                    exit_code = error.code
            return {
                "exit_code": exit_code,
                "output": output_path.read_text(encoding="utf-8") if output_path.exists() else "",
                "summary": summary_path.read_text(encoding="utf-8") if summary_path.exists() else "",
            }

    def test_current_head_runs_exact_source_migration_check(self):
        result = self.run_preflight(
            [{"state": "open", "head": {"sha": EXPECTED_SHA}, "draft": False}]
        )
        self.assertIsNone(result["exit_code"])
        self.assertIn("current=true", result["output"])

    def test_old_closed_and_draft_heads_skip_exact_source_migration_check(self):
        cases = (
            ("superseded", {"state": "open", "head": {"sha": "b" * 40}, "draft": False}),
            ("closed", {"state": "closed", "head": {"sha": EXPECTED_SHA}, "draft": False}),
            ("draft", {"state": "open", "head": {"sha": EXPECTED_SHA}, "draft": True}),
        )
        for label, current in cases:
            with self.subTest(label=label):
                result = self.run_preflight([current])
                self.assertIsNone(result["exit_code"])
                self.assertIn("current=false", result["output"])
                self.assertIn("Exact-source migration validation skipped", result["summary"])

    def test_github_api_error_fails_closed(self):
        result = self.run_preflight(APIError("GitHub HTTP 403 for pulls/82"))
        self.assertEqual(result["exit_code"], 1)
        self.assertIn("current=false", result["output"])
        self.assertIn("migration validation is blocked", result["summary"])

    def test_api_token_is_used_only_after_trusted_default_branch_checkout(self):
        workflow = self.workflow()
        preflight_start = workflow.index("  migration-source-preflight:\n")
        backend_start = workflow.index("  backend:\n", preflight_start)
        staging_start = workflow.index("  staging:\n", backend_start)
        preflight = workflow[preflight_start:backend_start]
        backend = workflow[backend_start:staging_start]

        self.assertIn("ref: ${{ github.event.repository.default_branch }}", preflight)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", preflight)
        self.assertIn("needs: migration-source-preflight", backend)
        self.assertIn("if: always()", backend)
        self.assertIn(
            "if: always() && needs.migration-source-preflight.result == 'failure'",
            backend,
        )
        backend_header = backend.split("    steps:\n", 1)[0]
        self.assertNotIn("pull-requests: read", backend_header)
        self.assertNotIn("GITHUB_TOKEN", backend)

    def test_only_current_pr_heads_reach_exact_source_checkout_and_validation(self):
        workflow = self.workflow()
        checkout_start = workflow.index("      - name: Check out exact hosted staging source")
        checkout_end = workflow.index("\n      - name:", checkout_start + 1)
        migration_start = workflow.index("      - name: Verify exact hosted staging migration history")
        migration_end = workflow.index("\n      - name:", migration_start + 1)
        output = "needs.migration-source-preflight.outputs.current == 'true'"
        self.assertIn(output, workflow[checkout_start:checkout_end])
        self.assertIn(output, workflow[migration_start:migration_end])


if __name__ == "__main__":
    unittest.main()

