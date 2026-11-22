"""Tests for protected staging Neon branch identity checks."""

import json
import os
import unittest
from unittest.mock import Mock, patch

from scripts.verify_neon_release_branch import NeonReleaseError, verify_branch


class NeonReleaseBranchTests(unittest.TestCase):
    def response(self, payload):
        response = Mock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return response

    @patch.dict(os.environ, {"NEON_API_KEY": "test-token"})
    @patch("scripts.verify_neon_release_branch.urlopen")
    def test_independent_root_is_accepted_when_production_rows_are_absent(self, urlopen):
        branch_id = "br-staging-12345678"
        host = "ep-staging.c-4.ap-southeast-1.aws.neon.tech"
        urlopen.side_effect = [
            self.response({
                "branch": {
                    "id": branch_id,
                    "name": "main",
                    "parent_id": None,
                    "current_state": "ready",
                }
            }),
            self.response({
                "endpoints": [{"host": host, "branch_id": branch_id}]
            }),
        ]

        result = verify_branch(
            project_id="staging-project-123",
            branch_id=branch_id,
            production_project_id="production-project-123",
            production_branch_id="br-production-12345678",
            schema_only_attestation="false",
            production_rows_present="false",
            expected_host=host,
        )

        self.assertEqual(result["branch_kind"], "independent-root")
        self.assertFalse(result["schema_only_attested"])
        self.assertEqual(result["endpoint_host"], host)
        self.assertEqual(urlopen.call_count, 2)

    def test_production_rows_must_be_explicitly_absent(self):
        with self.assertRaisesRegex(NeonReleaseError, "production rows are absent"):
            verify_branch(
                project_id="staging-project-123",
                branch_id="br-staging-12345678",
                production_project_id="production-project-123",
                production_branch_id="br-production-12345678",
                schema_only_attestation="false",
                production_rows_present="true",
            )


if __name__ == "__main__":
    unittest.main()
