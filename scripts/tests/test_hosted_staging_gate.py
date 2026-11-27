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
        cls.readonly_job = named_job(cls.workflow_text, "issue-90-readonly-hosted")

    def test_hosted_package_job_is_scoped_to_the_named_same_repository_pr(self):
        condition = re.search(r"(?m)^    if:\s*(.*)$", self.readonly_job)
        self.assertIsNotNone(condition, "read-only staging package job must be explicitly scoped")
        for required in (
            "github.event_name == 'pull_request'",
            "github.event.pull_request.head.repo.full_name == github.repository",
            "github.event.pull_request.head.ref == 'codex/issue-90-readonly-artifact-v2-20261106'",
        ):
            self.assertIn(required, condition.group(1))

    def test_hosted_package_job_is_read_only_and_never_deploys(self):
        self.assertRegex(self.readonly_job, r"(?m)^    permissions:\n      contents: read$")
        self.assertNotIn("environment:", self.readonly_job)
        self.assertNotIn("secrets.", self.readonly_job)
        self.assertNotRegex(self.readonly_job, r"(?mi)^\s*- name: .*deploy")
        self.assertIn("saved_analysis_crud_performed': False", self.readonly_job)
        self.assertIn("production_writes_performed': False", self.readonly_job)

        read_identity = named_step(
            self.readonly_job,
            "Read current staging identity, readiness, and model",
        )
        package = named_step(
            self.readonly_job,
            "Build and verify a staging-only extension package",
        )
        recheck = named_step(
            self.readonly_job,
            "Recheck staging identity before upload",
        )
        self.assertIn("urlopen(request, timeout=30)", read_identity)
        self.assertIn("package_staging_extension.py", package)
        self.assertIn("verify_staging_extension_package.py", package)
        self.assertIn("urlopen(request, timeout=30)", recheck)

    def test_local_staging_cleans_up_process_and_prints_log_on_smoke_failure(self):
        staging_job = named_job(self.workflow_text, "staging")
        self.assertIn("trap 'kill \"$api_pid\" 2>/dev/null || true' EXIT", staging_job)
        self.assertIn("if ! node scripts/staging_smoke.mjs; then", staging_job)
        self.assertIn("cat /tmp/phishlens-staging.log", staging_job)
        self.assertIn("exit 1", staging_job)


if __name__ == "__main__":
    unittest.main()
