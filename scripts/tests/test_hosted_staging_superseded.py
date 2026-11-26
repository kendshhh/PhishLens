"""Hosted staging stays non-green when its candidate is stale or incomplete."""

import re
import textwrap
import unittest
from pathlib import Path

from scripts.secretary.hosted_status import decision

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40
REPO = "kendshhh/PhishLens"
CONFIG = {"preview_opt_in_label": "needs-hosted-staging"}


def pr():
    return {"state": "open", "draft": False,
            "head": {"sha": SHA, "repo": {"full_name": REPO}},
            "labels": [{"name": "needs-hosted-staging"}]}


def jobs(hosted_status="completed", hosted_conclusion="success"):
    result = {name: {"status": "completed", "conclusion": "success"}
              for name in ("Backend checks", "Extension checks", "Staging integration")}
    result["Hosted staging"] = {"status": hosted_status, "conclusion": hosted_conclusion}
    return result


class HostedStagingSupersededTests(unittest.TestCase):
    def test_stale_head_and_every_incomplete_hosted_result_stay_non_green(self):
        current = pr()
        current["head"]["sha"] = "b" * 40
        state, _ = decision(current, [{"filename": "extension/history.js"}],
                            {"head_sha": SHA, "conclusion": "success"}, jobs(), REPO, CONFIG)
        self.assertEqual(state, "stale")

        for status, conclusion in (("in_progress", None), ("completed", "failure"),
                                  ("completed", "skipped")):
            state, _ = decision(pr(), [{"filename": "extension/history.js"}],
                                {"head_sha": SHA, "conclusion": "success"},
                                jobs(status, conclusion), REPO, CONFIG)
            self.assertEqual(state, "failure")

    def test_workflow_does_not_skip_eligible_runtime_gate_when_prerequisite_fails(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        start = workflow.index("  hosted-staging:\n")
        body_start = start + len("  hosted-staging:\n")
        next_job = re.search(r"(?m)^  [a-z][a-z0-9_-]*:\s*$", workflow[body_start:])
        end = body_start + next_job.start() if next_job else len(workflow)
        hosted = workflow[start:end]
        header = hosted.split("    needs:", 1)[0]

        self.assertIn("if: always()", header)
        self.assertNotIn("needs.staging.result == 'success'", header)
        self.assertIn("Fail instead of skipping when an eligible staging prerequisite failed", hosted)
        self.assertIn("STAGING_INTEGRATION_RESULT", hosted)
        self.assertIn("PREFLIGHT_CURRENT", hosted)


    def test_stale_live_head_withholds_evidence_and_auth_acceptance(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        hosted_start = workflow.index("  hosted-staging:\n")
        hosted = workflow[hosted_start:]
        start = hosted.index("      - name: Verify PR-head identity and package staging assets")
        end = hosted.index("      - name: Run authenticated extension and persistent CRUD acceptance", start)
        finalizer = hosted[start:end]
        acceptance_preflight_start = hosted.index("      - name: Recheck live PR head before authenticated acceptance", start)
        acceptance_preflight = hosted[acceptance_preflight_start:end]
        acceptance = hosted[end:]
        artifact = hosted[hosted.index("      - name: Preserve hosted staging acceptance evidence and extension", end):]

        self.assertIn("id: staging-finalize", finalizer)
        self.assertIn("requested_pr_identity()", finalizer)
        self.assertIn("live_pr_matches(current, number, pr_head_sha, repository)", finalizer)
        self.assertIn("ReadOnlyGitHub", finalizer)
        self.assertEqual(finalizer.count("if superseded():"), 3)
        self.assertIn("result.write('current=false\\n')", finalizer)
        self.assertIn("result.write('current=true\\n')", finalizer)
        self.assertIn("id: staging-acceptance-preflight", acceptance_preflight)
        self.assertIn("requested_pr_identity()", acceptance_preflight)
        self.assertIn("live_pr_matches(", acceptance_preflight)
        self.assertIn("if: steps.staging-acceptance-preflight.outputs.current == 'true'", acceptance)
        self.assertIn("if: always() && steps.staging-acceptance-preflight.outputs.current == 'true'", artifact)

        marker = "          python - <<'PY'\n"
        script_start = finalizer.index(marker) + len(marker)
        script_end = finalizer.index("\n          PY", script_start)
        compile(textwrap.dedent(finalizer[script_start:script_end]),
                ".github/workflows/ci.yml hosted-staging-finalize", "exec")


if __name__ == "__main__":
    unittest.main()
