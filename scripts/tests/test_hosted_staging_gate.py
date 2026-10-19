"""Exercise the actual required-check shell gate, including skipped deployment."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASH = shutil.which("bash")
if os.name == "nt":
    BASH = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe")


class HostedStagingGateTests(unittest.TestCase):
    def run_gate(self, changed, deployment, extension="success", staging="success"):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        gate = workflow.split("      - name: Require integration and applicable hosted deployment\n", 1)[1]
        shell = gate.split("        run: |\n", 1)[1]
        shell = "\n".join(line[10:] for line in shell.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            summary = Path(directory) / "summary.md"
            result = subprocess.run([BASH, "-c", shell], check=False, capture_output=True, text=True,
                env={**os.environ, "EXTENSION_RESULT": extension, "STAGING_RESULT": staging,
                     "APPLICATION_CHANGED": changed, "DEPLOYMENT_RESULT": deployment,
                     "GITHUB_STEP_SUMMARY": summary.as_posix()})
            return result.returncode, summary.read_text() if summary.exists() else ""

    def test_tooling_only_reports_not_applicable(self):
        code, summary = self.run_gate("false", "skipped")
        self.assertEqual(code, 0)
        self.assertIn("not applicable", summary)

    def test_runtime_requires_successful_deployment(self):
        for result in ("skipped", "failure", "cancelled"):
            with self.subTest(result=result):
                self.assertNotEqual(self.run_gate("true", result)[0], 0)
        self.assertEqual(self.run_gate("true", "success")[0], 0)

    def test_missing_scope_fails_closed(self):
        self.assertNotEqual(self.run_gate("", "skipped")[0], 0)

    def test_tooling_only_still_requires_ci(self):
        self.assertNotEqual(self.run_gate("false", "skipped", extension="failure")[0], 0)
        self.assertNotEqual(self.run_gate("false", "skipped", staging="skipped")[0], 0)


if __name__ == "__main__":
    unittest.main()
