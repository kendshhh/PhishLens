"""Keep trusted workflow triggers and deployment locks narrowly scoped."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


class SecretaryWorkflowTests(unittest.TestCase):
    def test_actionlint_runs_on_all_workflows_with_narrow_queue_schema_ignore(self):
        workflow = (WORKFLOWS / "actionlint.yml").read_text(encoding="utf-8")

        self.assertIn("raven-actions/actionlint@3d39aea434753780c3b3d4a1a31c854b4dbf49d7", workflow)
        self.assertIn("version: 1.7.9", workflow)
        self.assertIn(
            r"unexpected\x20key\x20\x22queue\x22\x20for\x20\x22concurrency\x22\x20section",
            workflow,
        )

    def test_dependency_security_checks_block_configured_findings(self):
        workflow = (WORKFLOWS / "dependency-review.yml").read_text(encoding="utf-8")
        permissions = workflow.split("jobs:", 1)[0]
        dependency_review = workflow.split("  dependency-review:", 1)[1]
        review_permissions = dependency_review.split("steps:", 1)[0]

        self.assertIn("pull_request:", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("name: Dependency security", workflow)
        self.assertIn("npm audit --audit-level=high --package-lock-only", workflow)
        self.assertIn("pip-audit==2.10.1", workflow)
        self.assertIn("python -m pip_audit --no-deps -r backend/requirements-dev.txt", workflow)
        self.assertIn("name: Dependency graph review (GitHub Advanced Security)", workflow)
        self.assertIn("fail-on-severity: high", workflow)
        self.assertNotIn("DEPENDENCY_REVIEW_ENABLED", workflow)
        self.assertNotIn("warn-only:", workflow)
        self.assertIn("contents: read", permissions)
        self.assertIn("pull-requests: read", review_permissions)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("pull-requests: write", workflow)

    def test_secretary_report_has_issue_write_permission_for_pr_comments(self):
        workflow = (WORKFLOWS / "secretary-report.yml").read_text(encoding="utf-8")
        permissions = workflow.split("concurrency:", 1)[0]

        self.assertIn("issues: write", permissions)
        self.assertIn("pull-requests: write", permissions)
        self.assertIn("except APIError as error", (ROOT / "scripts/secretary/report.py").read_text(encoding="utf-8"))

    def test_dependabot_tracks_python_npm_and_pinned_github_actions(self):
        config = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")

        self.assertIn("package-ecosystem: github-actions", config)
        self.assertIn("package-ecosystem: npm", config)
        self.assertIn("package-ecosystem: pip", config)
        self.assertIn("directory: /backend", config)
        self.assertEqual(config.count("interval: weekly"), 3)
        self.assertNotIn("auto-merge", config)

    def test_secretary_preview_is_a_read_only_status_mirror(self):
        workflow = (WORKFLOWS / "secretary-preview.yml").read_text(encoding="utf-8")
        controller = (ROOT / "scripts/secretary/hosted_status.py").read_text(encoding="utf-8")

        self.assertIn("types: [completed]", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("statuses: write", workflow)
        self.assertNotIn("deployments:", workflow)
        self.assertNotIn("RENDER_", workflow)
        self.assertNotIn("NEON_", workflow)
        self.assertNotIn('"Hosted staging"', controller)
        self.assertIn('"Secretary staging"', (ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
        self.assertIn('return "pending", "Waiting for the trusted controller', controller)
        self.assertIn('if state == "pending":', controller)
        self.assertIn("no competing status was published", controller)
        self.assertNotIn("render_request", controller)

    def test_secretary_required_context_uses_commit_status_from_trusted_controller(self):
        workflow = (WORKFLOWS / "secretary-preview.yml").read_text(encoding="utf-8")
        permissions = workflow.split("jobs:", 1)[0]
        controller = (ROOT / "scripts/secretary/hosted_status.py").read_text(encoding="utf-8")

        self.assertIn("statuses: write", permissions)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn('api.request("statuses/" + sha, {', controller)
        self.assertIn('"context": context', controller)
        self.assertIn('publish_status(api, run["head_sha"], config["preview_check"]', controller)

    def test_report_runs_once_after_workflow_completion(self):
        workflow = (WORKFLOWS / "secretary-report.yml").read_text(encoding="utf-8")
        workflow_run = workflow.split("  schedule:", 1)[0]

        self.assertIn("types: [completed]", workflow_run)
        self.assertNotIn("requested", workflow_run)
        self.assertNotIn("in_progress", workflow_run)

    def test_production_observer_cannot_create_a_predeploy_ci_check(self):
        workflow = (WORKFLOWS / "secretary-production.yml").read_text(encoding="utf-8")
        triggers = workflow.split("permissions:", 1)[0]

        self.assertIn("workflow_dispatch:", triggers)
        self.assertNotIn("workflow_run:", triggers)
        self.assertNotIn("schedule:", triggers)

    def test_auto_labeler_checks_out_only_trusted_default_branch(self):
        workflow = (WORKFLOWS / "auto-labels.yml").read_text(encoding="utf-8")
        permissions = workflow.split("concurrency:", 1)[0]

        self.assertIn("pull_request_target:", workflow)
        self.assertIn("issues: write", permissions)
        self.assertIn("pull-requests: write", permissions)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("github.event.pull_request.head.sha", workflow)

    def test_trusted_neon_preflight_covers_intentionally_stacked_pr_bases(self):
        workflow = (WORKFLOWS / "staging-neon-preflight.yml").read_text(encoding="utf-8")
        triggers = workflow.split("permissions:", 1)[0]

        self.assertIn("pull_request_target:", triggers)
        self.assertNotIn("branches:", triggers)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", workflow)
        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertIn("environment: staging-neon-preflight", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("needs-hosted-staging", workflow)


    def test_pr_ci_has_no_hosted_deployment_credentials_or_auth_secrets(self):
        workflow = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertNotIn("RENDER_STAGING_API_KEY", workflow)
        self.assertNotIn("NEON_API_KEY", workflow)
        self.assertNotIn("STAGING_AUTH_USER_A_PASSWORD", workflow)
        self.assertNotIn("STAGING_AUTH_USER_B_PASSWORD", workflow)
        self.assertNotIn("environment: staging", workflow)
        self.assertNotIn("environment: release-staging", workflow)

    def test_trusted_controller_isolates_deploy_credential_from_candidate_code(self):
        workflow = (WORKFLOWS / "trusted-hosted-staging.yml").read_text(encoding="utf-8")
        ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        deploy = workflow.split("  deploy-staging:\n", 1)[1].split("  accept-staging:\n", 1)[0]
        accept = workflow.split("  accept-staging:\n", 1)[1].split("  report:\n", 1)[0]

        self.assertIn("workflow_run:", workflow)
        self.assertIn("workflows: [CI]", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("environment: release-staging", deploy)
        self.assertIn("RENDER_STAGING_API_KEY: ${{ secrets.RENDER_STAGING_API_KEY }}", deploy)
        self.assertNotIn("actions/checkout", deploy.split("Deploy only the verified PR head", 1)[1])
        self.assertNotIn("STAGING_AUTH_USER_A_PASSWORD", deploy)
        self.assertNotIn("STAGING_AUTH_USER_B_PASSWORD", deploy)
        self.assertIn("environment: staging", accept)
        self.assertIn("ref: ${{ needs.inspect.outputs.source_sha }}", accept)
        self.assertIn("STAGING_AUTH_USER_A_PASSWORD", accept)
        self.assertIn("STAGING_AUTH_USER_B_PASSWORD", accept)
        self.assertNotIn("RENDER_STAGING_API_KEY", accept)
        self.assertNotIn("RENDER_STAGING_API_KEY", ci)
        acceptance_step = accept.split(
            "- name: Run authenticated exact-package CRUD and extension acceptance", 1
        )[1].split("- name: Require authenticated CRUD/UX evidence", 1)[0]
        self.assertNotIn("working-directory: pr-source", acceptance_step)
        self.assertIn("node scripts/staging_extension_acceptance.mjs", acceptance_step)
        browser_dependencies = workflow.split(
            "- name: Install trusted browser dependencies without acceptance credentials", 1
        )[1].split("- name: Confirm live staging identity", 1)[0]
        self.assertNotIn("working-directory: pr-source", browser_dependencies)
        self.assertIn("npm ci", browser_dependencies)

    def test_required_secretary_status_stays_pending_until_trusted_acceptance(self):
        controller = (ROOT / "scripts/secretary/hosted_status.py").read_text(encoding="utf-8")
        workflow = (WORKFLOWS / "trusted-hosted-staging.yml").read_text(encoding="utf-8")

        self.assertIn('return "pending", "Waiting for the trusted controller', controller)
        self.assertIn('"context": config["preview_check"]',
                      (ROOT / "scripts/secretary/trusted_staging.py").read_text(encoding="utf-8"))
        self.assertIn("INSPECT_RESULT: ${{ needs.inspect.result }}", workflow)
        self.assertIn("DEPLOY_RESULT: ${{ needs.deploy-staging.result }}", workflow)
        self.assertIn("ACCEPTANCE_RESULT: ${{ needs.accept-staging.result }}", workflow)
        self.assertIn('state = "success" if passed else "failure"',
                      (ROOT / "scripts/secretary/trusted_staging.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

