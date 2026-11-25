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
        self.assertIn('"Hosted staging"', controller)
        self.assertIn('"Secretary staging"', (ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
        self.assertIn("hosted.get(\"status\") != \"completed\"", controller)
        self.assertIn("hosted.get(\"conclusion\") != \"success\"", controller)
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

    def test_ci_required_hosted_staging_runs_exact_authenticated_extension_acceptance(self):
        workflow = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        start = workflow.index("  hosted-staging:\n")
        hosted = workflow[start:]

        self.assertIn("name: Hosted staging", hosted)
        self.assertIn("Run authenticated extension and persistent CRUD acceptance", hosted)
        self.assertIn("node scripts/staging_extension_acceptance.mjs", hosted)
        self.assertIn("--expected-sha \"$EXPECTED_SHA\"", hosted)
        self.assertIn("verify-pr-staging", hosted)
        self.assertIn("STAGING_AUTH_USER_A_EMAIL", hosted)
        self.assertIn("STAGING_AUTH_USER_B_EMAIL", hosted)
        self.assertIn("STAGING_NEON_BRANCH_KIND: schema-only", hosted)
        self.assertIn("Authenticated Hosted staging did not pass", (ROOT / "scripts/secretary/hosted_status.py").read_text(encoding="utf-8"))
        self.assertNotIn("staging_smoke.mjs", hosted)
        self.assertNotIn("verify_crud.mjs", hosted)
        self.assertIn("set -euo pipefail", hosted)
        self.assertIn("if: always() && steps.staging-acceptance-preflight.outputs.current == 'true'", hosted)


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


    def test_ci_runs_packaged_browser_and_read_only_auth_staging_checks(self):
        workflow = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        hosted_start = workflow.index("  hosted-staging:\n")
        hosted = workflow[hosted_start:]
        finalizer_start = hosted.index("      - name: Verify PR-head identity and package staging assets")
        finalizer_end = hosted.index("      - name: Run authenticated extension and persistent CRUD acceptance", finalizer_start)
        finalizer = hosted[finalizer_start:finalizer_end]

        self.assertIn("npm run test:browser", workflow)
        self.assertIn("Extension-Browser-Acceptance", workflow)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha }}", hosted)
        self.assertIn("smoke(config['staging_origin'], deploy_sha, report_auth_mode='neon')", finalizer)
        self.assertIn("('/auth/bridge', 'text/html')", finalizer)
        self.assertIn("('/auth/bridge/client.js', 'javascript')", finalizer)
        self.assertIn("('/auth/bridge/sdk.mjs', 'javascript')", finalizer)
        self.assertIn("'application_crud_writes_performed': False", finalizer)
        self.assertIn("'saved_report_crud': {'result': 'not_run'}", finalizer)
        self.assertIn("endpoint preflight uses GET requests only", finalizer)
        self.assertNotIn("scripts/verify_crud.mjs", hosted)
        self.assertNotIn("--allow-writes", finalizer)


if __name__ == "__main__":
    unittest.main()

