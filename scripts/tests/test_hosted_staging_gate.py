"""Protect the current trusted hosted-staging deployment and acceptance gates."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "trusted-hosted-staging.yml"


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


CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class HostedStagingGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow_text = WORKFLOW.read_text(encoding="utf-8")
        cls.deploy_job = named_job(cls.workflow_text, "deploy-staging")
        cls.accept_job = named_job(cls.workflow_text, "accept-staging")

    def test_deployment_requires_eligible_candidate_and_successful_preflight(self):
        self.assertIn("needs: [inspect, neon-preflight]", self.deploy_job)
        self.assertIn(
            "if: needs.inspect.outputs.disposition == 'eligible' && needs.neon-preflight.result == 'success'",
            self.deploy_job,
        )
        recheck = named_step(
            self.deploy_job,
            "Recheck the required status contract immediately before deployment",
        )
        self.assertIn("TRUSTED_STAGING_OPERATION: wait-for-checks", recheck)
        self.assertIn("python -m scripts.secretary.trusted_staging", recheck)
        deploy = named_step(
            self.deploy_job,
            "Deploy only the verified PR head with the protected Render credential",
        )
        self.assertIn("STAGING_COMMIT: ${{ needs.inspect.outputs.source_sha }}", deploy)
        self.assertIn("STAGING_PR_HEAD_SHA: ${{ needs.inspect.outputs.source_sha }}", deploy)
        self.assertIn("run: python scripts/deploy_staging.py", deploy)

    def test_authenticated_acceptance_waits_for_deployment_and_checks_exact_source(self):
        self.assertIn("needs: [inspect, neon-preflight, deploy-staging]", self.accept_job)
        self.assertIn(
            "if: needs.inspect.outputs.disposition == 'eligible' && needs.deploy-staging.result == 'success'",
            self.accept_job,
        )
        source = named_step(self.accept_job, "Check out the exact PR source for acceptance only")
        self.assertIn("ref: ${{ needs.inspect.outputs.source_sha }}", source)
        self.assertIn("path: pr-source", source)
        acceptance = named_step(
            self.accept_job,
            "Run authenticated exact-package CRUD and extension acceptance",
        )
        self.assertIn("STAGING_ACCEPTANCE_MODE: pr-source", acceptance)
        self.assertIn("node scripts/staging_extension_acceptance.mjs", acceptance)
        evidence = named_step(
            self.accept_job,
            "Require authenticated CRUD/UX evidence for the exact candidate",
        )
        self.assertIn("python -m scripts.release_readiness verify-pr-staging", evidence)
        self.assertIn("EXPECTED_SHA: ${{ needs.inspect.outputs.source_sha }}", evidence)


class Issue90HostedPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
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
        self.assertNotRegex(self.readonly_job, r"(?m)^    environment:")
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
