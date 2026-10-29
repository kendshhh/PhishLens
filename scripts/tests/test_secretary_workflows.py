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

    def test_dependency_review_starts_advisory_with_read_only_permissions(self):
        workflow = (WORKFLOWS / "dependency-review.yml").read_text(encoding="utf-8")
        permissions = workflow.split("jobs:", 1)[0]

        self.assertIn("pull_request:", workflow)
        self.assertIn("if: vars.DEPENDENCY_REVIEW_ENABLED != 'false'", workflow)
        self.assertIn("advisory review by default", workflow)
        self.assertIn("contents: read", permissions)
        self.assertIn("pull-requests: read", permissions)
        self.assertIn("warn-only: true", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("pull-requests: write", permissions)

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

    def test_preview_concurrency_only_serializes_real_staging_deploys(self):
        workflow = (WORKFLOWS / "secretary-preview.yml").read_text(encoding="utf-8")
        jobs_start = workflow.index("jobs:\n")
        preview_start = workflow.index("  preview:\n", jobs_start)
        assess = workflow[jobs_start:preview_start]
        preview = workflow[preview_start:]

        self.assertNotIn("concurrency:", workflow[:jobs_start])
        self.assertNotIn("concurrency:", assess)
        self.assertIn("if: needs.assess.outputs.deploy == 'true'", preview)
        self.assertIn("group: phishlens-hosted-staging", preview)

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


if __name__ == "__main__":
    unittest.main()
