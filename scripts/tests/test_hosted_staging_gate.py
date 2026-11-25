from pathlib import Path
import re
import unittest


WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def named_job(workflow_text, name):
    match = re.search(
        rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:|\Z)",
        workflow_text,
    )
    if not match:
        raise AssertionError(f"workflow job {name!r} was not found")
    return match.group(1)


def job_condition(job_text):
    match = re.search(r"(?ms)^    if:\s*(.*?)(?=^    (?:needs|runs-on):)", job_text)
    if not match:
        raise AssertionError("job-level if condition was not found")
    return match.group(1)


def named_step(job_text, name):
    match = re.search(
        rf"(?ms)^      - name: {re.escape(name)}\n(.*?)(?=^      - (?:name:|uses:)|\Z)",
        job_text,
    )
    if not match:
        raise AssertionError(f"workflow step {name!r} was not found")
    return match.group(1)


class HostedStagingGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow_text = WORKFLOW.read_text(encoding="utf-8")
        cls.hosted_job = named_job(cls.workflow_text, "hosted-staging")

    def test_hosted_job_runs_prerequisite_failure_check_only_for_eligible_prs(self):
        condition = job_condition(self.hosted_job)
        self.assertIn("always()", condition)
        self.assertIn("github.event_name == 'pull_request'", condition)
        self.assertIn("contains(github.event.pull_request.labels.*.name, 'needs-hosted-staging')", condition)
        self.assertIn("vars.SECRETARY_PREVIEW_ENABLED == 'true'", condition)
        self.assertIn("vars.SECRETARY_REPLACES_LEGACY_STAGING != 'true'", condition)
        self.assertIn("!github.event.pull_request.draft", condition)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", condition)
        self.assertIn("github.event.pull_request.head.ref != 'codex/issue-90-readonly-artifact-v2-20261106'", condition)

        failure_check = named_step(
            self.hosted_job,
            "Fail instead of skipping when an eligible staging prerequisite failed",
        )
        for dependency in ("STAGING_INTEGRATION_RESULT", "PREFLIGHT_RESULT", "BACKEND_RESULT"):
            self.assertIn(dependency, failure_check)
        self.assertIn("PREFLIGHT_CURRENT", failure_check)
        self.assertIn("MIGRATION_REVISION", failure_check)
        self.assertIn("if value != ('true' if name == 'current PR head' else 'success')", failure_check)
        self.assertIn("if failures:", failure_check)
        self.assertIn("raise SystemExit", failure_check)

    def test_render_deploy_requires_fresh_pr_head_preflight(self):
        step = named_step(
            self.hosted_job,
            "Deploy exact PR head using the trusted controller",
        )
        match = re.search(r"(?ms)^        if:\s*(.*?)(?=^        env:)", step)
        self.assertIsNotNone(match, "deployment step must have its own if condition")
        condition = match.group(1)
        self.assertIn("steps.staging-deploy-preflight.outputs.current == 'true'", condition)
        preflight = named_step(
            self.hosted_job,
            "Recheck PR head immediately before staging deploy",
        )
        preflight_match = re.search(r"(?ms)^        if:\s*(.*?)(?=^        env:)", preflight)
        self.assertIsNotNone(preflight_match, "deployment preflight must have its own if condition")
        self.assertIn("steps.staging-final-preflight.outputs.current == 'true'", preflight_match.group(1))
        self.assertIn("live_pr_matches", preflight)

    def test_local_staging_cleans_up_process_and_prints_log_on_smoke_failure(self):
        staging_job = named_job(self.workflow_text, "staging")
        self.assertIn('trap \'kill "$api_pid" 2>/dev/null || true\' EXIT', staging_job)
        self.assertIn("if ! node scripts/staging_smoke.mjs; then", staging_job)
        self.assertIn("cat /tmp/phishlens-staging.log", staging_job)
        self.assertIn("exit 1", staging_job)


if __name__ == "__main__":
    unittest.main()

