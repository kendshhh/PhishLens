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

    def test_hosted_job_keeps_a_required_status_and_fails_closed_on_bad_prerequisites(self):
        condition = job_condition(self.hosted_job)
        self.assertIn("always()", condition)
        prerequisite_guard = named_step(
            self.hosted_job,
            "Fail instead of skipping when an eligible staging prerequisite failed",
        )
        for dependency in ("staging", "hosted-staging-preflight", "backend"):
            self.assertIn(f"needs.{dependency}.result", prerequisite_guard)
        self.assertIn("PREFLIGHT_CURRENT", prerequisite_guard)
        self.assertIn("if failures:", prerequisite_guard)
        self.assertIn("Hosted staging prerequisites failed:", prerequisite_guard)

    def test_render_deploy_step_repeats_all_dependency_success_gates(self):
        step = named_step(
            self.hosted_job,
            "Deploy exact PR head using the trusted controller",
        )
        match = re.search(r"(?ms)^        if:\s*(.*?)(?=^        env:)", step)
        self.assertIsNotNone(match, "deployment step must have its own if condition")
        condition = match.group(1)
        self.assertIn("success()", condition)
        for dependency in ("staging", "hosted-staging-preflight", "backend"):
            self.assertIn(f"needs.{dependency}.result == 'success'", condition)
        self.assertIn("needs.staging.result == 'success'", condition)
        self.assertIn("needs.hosted-staging-preflight.result == 'success'", condition)
        self.assertIn("needs.backend.result == 'success'", condition)
        self.assertIn("steps.staging-deploy-preflight.outputs.current == 'true'", condition)

    def test_local_staging_monitors_process_and_uploads_log_even_after_failure(self):
        staging_job = named_job(self.workflow_text, "staging")
        self.assertIn('kill -0 "$api_pid"', staging_job)
        self.assertIn("startup deadline expired", staging_job)
        self.assertIn("--connect-timeout 1 --max-time 2", staging_job)
        self.assertIn("name: Preserve local staging server log", staging_job)
        self.assertIn("if: always()", staging_job)
        self.assertIn("path: output/staging/staging-server.log", staging_job)


if __name__ == "__main__":
    unittest.main()
