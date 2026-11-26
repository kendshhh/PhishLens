import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from scripts.staging_neon_attestation import (
    STATUS_CONTEXT,
    WORKFLOW_PATH,
    describe_target,
    has_attestation,
    publish_attestation,
    write_verified_outputs,
)
from scripts.verify_neon_release_branch import NeonReleaseError


class AttestationTests(TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.target = {"branch_id": "br-staging"}
        self.api = Mock(repo="kendshhh/PhishLens")
        self.status = {
            "context": STATUS_CONTEXT, "state": "success",
            "description": describe_target(self.target),
            "creator": {"login": "github-actions[bot]"},
            "target_url": "https://github.com/kendshhh/PhishLens/actions/runs/17/attempts/1",
        }
        self.run = {
            "id": 17, "run_attempt": 1, "status": "completed",
            "path": WORKFLOW_PATH, "event": "pull_request_target",
            "display_title": f"Staging Neon PR 251 @ {self.sha}", "conclusion": "success",
        }
        self.api.pages.return_value = [self.status]
        self.api.request.return_value = {"workflow_runs": [self.run]}

    def test_enforces_exact_target_and_trusted_workflow_run(self):
        self.assertTrue(has_attestation(self.api, 251, self.sha, self.target))
        self.assertFalse(has_attestation(self.api, 251, self.sha, {"branch_id": "br-other"}))
        self.assertFalse(has_attestation(self.api, 251, "b" * 40, self.target))
        for changes in (
            {"path": ".github/workflows/ci.yml"},
            {"event": "pull_request"},
            {"conclusion": None},
        ):
            with self.subTest(changes=changes):
                self.api.request.return_value = {"workflow_runs": [{**self.run, **changes}]}
                self.assertFalse(has_attestation(self.api, 251, self.sha, self.target))

    def test_unrelated_label_run_does_not_supersede_neon_verification(self):
        ignored = {**self.run, "id": 18, "display_title": f"Ignored label for PR 251 @ {self.sha}"}
        self.api.request.return_value = {"workflow_runs": [ignored, self.run]}
        self.assertTrue(has_attestation(self.api, 251, self.sha, self.target))

    def test_newer_failure_supersedes_an_older_success_without_a_status(self):
        self.assertTrue(has_attestation(self.api, 251, self.sha, self.target))
        self.api.request.return_value = {"workflow_runs": [
            self.run, {**self.run, "id": 18, "conclusion": "failure"},
        ]}
        self.assertFalse(has_attestation(self.api, 251, self.sha, self.target))

    def test_newer_queued_run_already_supersedes_the_old_success(self):
        self.api.request.return_value = {"workflow_runs": [
            self.run, {**self.run, "id": 18, "status": "queued", "conclusion": None},
        ]}
        self.assertFalse(has_attestation(self.api, 251, self.sha, self.target))

    def test_rerun_needs_an_attestation_from_its_own_attempt(self):
        self.api.request.return_value = {"workflow_runs": [{**self.run, "run_attempt": 2, "conclusion": "failure"}]}
        self.assertFalse(has_attestation(self.api, 251, self.sha, self.target))
        self.api.request.return_value = {"workflow_runs": [{**self.run, "run_attempt": 2}]}
        self.assertFalse(has_attestation(self.api, 251, self.sha, self.target))
        second_status = {**self.status, "target_url": self.status["target_url"][:-1] + "2"}
        self.api.pages.return_value = [second_status, self.status]
        self.assertTrue(has_attestation(self.api, 251, self.sha, self.target))
        self.api.pages.return_value.insert(0, {**second_status, "state": "failure"})
        self.assertFalse(has_attestation(self.api, 251, self.sha, self.target))

    def test_required_preflight_exports_only_valid_non_secret_target_identity(self):
        target = {
            "project_id": "ancient-brook-17208049",
            "branch_id": "br-rough-sea-a1l6ehi1",
            "expected_host": "staging.example",
            "production_project_id": "production-project",
            "production_branch_id": "br-production",
            "expected_parent_id": "",
            "production_rows_present": "false",
        }
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "github-output.txt"
            with patch.dict("os.environ", {"GITHUB_OUTPUT": str(output_path)}):
                write_verified_outputs(target)
            output = output_path.read_text(encoding="utf-8")
            self.assertIn("project_id=ancient-brook-17208049", output)
            self.assertIn("branch_id=br-rough-sea-a1l6ehi1", output)
            self.assertIn("parent_id=\n", output)
            self.assertEqual(len(output.splitlines()), 7)

    def test_invalid_multiline_target_does_not_partially_write_outputs(self):
        target = {
            "project_id": "safe",
            "branch_id": "br-safe-branch",
            "expected_host": "unsafe\nbranch_id=production",
            "production_project_id": "prod",
            "production_branch_id": "br-production",
            "expected_parent_id": "",
            "production_rows_present": "false",
        }
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "github-output.txt"
            with (
                patch.dict("os.environ", {"GITHUB_OUTPUT": str(output_path)}),
                self.assertRaisesRegex(NeonReleaseError, "invalid output"),
            ):
                write_verified_outputs(target)
            self.assertFalse(output_path.exists())

    @patch("scripts.staging_neon_attestation.verify_branch", side_effect=NeonReleaseError("provider rejected request"))
    @patch("scripts.staging_neon_attestation.live_pr_matches", return_value=True)
    @patch.dict("os.environ", {
        "GITHUB_RUN_ID": "17", "GITHUB_RUN_ATTEMPT": "2", "STAGING_NEON_EXPECTED_HOST": "staging.example",
    })
    def test_verifier_publishes_pending_and_failure_for_the_same_attempt(self, _current, _verify):
        with self.assertRaisesRegex(NeonReleaseError, "provider rejected request"):
            publish_attestation(self.api, 251, self.sha)
        rows = [args[1] for args, _ in self.api.request.call_args_list if args[0] == f"statuses/{self.sha}"]
        self.assertEqual([row["state"] for row in rows], ["pending", "failure"])
        self.assertEqual({row["target_url"] for row in rows}, {self.status["target_url"][:-1] + "2"})
        self.assertNotIn("provider rejected request", rows[-1]["description"])

    def test_key_workflow_uses_only_base_code(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / WORKFLOW_PATH).read_text()
        self.assertIn("pull_request_target:", workflow)
        self.assertIn("environment: staging-neon-preflight", workflow)
        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertNotIn("ref: ${{ github.event.pull_request.head", workflow)
        self.assertIn("github.event.label.name != 'needs-hosted-staging' && 'Ignored label for'", workflow)
        self.assertIn("run: python -m scripts.staging_neon_attestation publish", workflow)
