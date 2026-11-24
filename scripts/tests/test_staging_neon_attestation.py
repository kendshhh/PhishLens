from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

from scripts.staging_neon_attestation import (
    STATUS_CONTEXT, WORKFLOW_PATH, describe_target, has_attestation,
)


class AttestationTests(TestCase):
    def test_enforces_exact_target_and_trusted_workflow_run(self):
        sha = "a" * 40
        target = {"branch_id": "br-staging"}
        api = Mock(repo="kendshhh/PhishLens")
        status = {
            "context": STATUS_CONTEXT, "state": "success",
            "description": describe_target(target),
            "creator": {"login": "github-actions[bot]"},
            "target_url": "https://github.com/kendshhh/PhishLens/actions/runs/17",
        }
        run = {
            "path": WORKFLOW_PATH, "event": "pull_request_target",
            "display_title": f"Staging Neon PR 251 @ {sha}", "conclusion": "success",
        }
        api.pages.return_value = [status]
        api.request.return_value = run
        self.assertTrue(has_attestation(api, 251, sha, target))
        self.assertFalse(has_attestation(api, 251, sha, {"branch_id": "br-other"}))
        self.assertFalse(has_attestation(api, 251, "b" * 40, target))
        for changes in (
            {"path": ".github/workflows/ci.yml"},
            {"event": "pull_request"},
            {"conclusion": None},
        ):
            with self.subTest(changes=changes):
                api.request.return_value = {**run, **changes}
                self.assertFalse(has_attestation(api, 251, sha, target))

    def test_key_workflow_uses_only_base_code(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / WORKFLOW_PATH).read_text()
        self.assertIn("pull_request_target:", workflow)
        self.assertIn("environment: staging-neon-preflight", workflow)
        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertNotIn("ref: ${{ github.event.pull_request.head", workflow)
        self.assertIn("run: python -m scripts.staging_neon_attestation publish", workflow)
