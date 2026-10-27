import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class HostedStagingSupersededTests(unittest.TestCase):
    def test_changed_pr_head_skips_stale_evidence_without_failing_ci(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        start = workflow.index("      - name: Verify deployed merge identity and package staging assets")
        end = workflow.index("      - name: Preserve hosted staging evidence and extension", start)
        finalize = workflow[start:end]
        artifact = workflow[end:]

        self.assertIn("id: staging-finalize", finalize)
        self.assertIn("def superseded():", finalize)
        self.assertIn("not current.get('draft', False)", finalize)
        self.assertEqual(finalize.count("if superseded():"), 3)
        self.assertIn("raise SystemExit(0)", finalize)
        self.assertIn("result.write('current=false\\n')", finalize)
        self.assertIn("result.write('current=true\\n')", finalize)
        self.assertNotIn("PR changed during deployment; rerun CI", finalize)
        self.assertIn("if: steps.staging-finalize.outputs.current == 'true'", artifact)

        marker = "          python - <<'PY'\n"
        script_start = finalize.index(marker) + len(marker)
        script_end = finalize.index("\n          PY", script_start)
        compile(
            textwrap.dedent(finalize[script_start:script_end]),
            ".github/workflows/ci.yml hosted-staging-finalize",
            "exec",
        )


if __name__ == "__main__":
    unittest.main()
