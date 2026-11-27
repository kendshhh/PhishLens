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


if __name__ == "__main__":
    unittest.main()
