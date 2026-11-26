"""Hosted acceptance must identify the requested staging commit and data."""
import copy
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.secretary.preview import smoke, verify_saved_report

SHA = "a" * 40


class HostedIdentityTests(unittest.TestCase):
    def responses(self):
        return [
            {"status": "ok", "service": "phishlens-api"},
            {"status": "ready", "database": "connected"},
            {"commit": SHA, "environment": "staging"},
            {"items": [{"subject": "Synthetic account notice"}]},
        ]

    def verify(self, payloads, *, report_auth_mode="demo"):
        responses = [value if isinstance(value, HTTPError) else io.BytesIO(json.dumps(value).encode())
                     for value in payloads]
        with patch("urllib.request.urlopen", side_effect=responses), patch(
            "scripts.secretary.preview.time.monotonic", side_effect=[0, 181]
        ):
            return smoke("https://staging.invalid", SHA, report_auth_mode=report_auth_mode)

    def test_exact_staging_commit_and_seed_pass(self):
        evidence = self.verify(self.responses())
        self.assertEqual(evidence["version"], SHA)
        self.assertEqual(evidence["history"], "passed")

    def test_neon_smoke_records_the_anonymous_auth_challenge(self):
        values = self.responses()[:3]
        values.append(HTTPError("https://staging.invalid/api/analyses", 401, "Unauthorized",
                                {"WWW-Authenticate": "Bearer"}, io.BytesIO()))
        evidence = self.verify(values, report_auth_mode="neon")
        self.assertEqual(evidence["version"], SHA)
        self.assertEqual(evidence["history"], "authentication_required")
        self.assertEqual(evidence["seeded_history"], "not_checked")
        self.assertEqual(
            evidence["anonymous_saved_report"],
            {"path": "/api/analyses", "status_code": 401, "challenge": "Bearer", "redirected": False},
        )

    def test_neon_smoke_fails_if_anonymous_history_is_accessible(self):
        with self.assertRaisesRegex(RuntimeError, "did not reject an anonymous saved-report request"):
            self.verify(self.responses(), report_auth_mode="neon")

    def test_neon_smoke_rejects_an_unrelated_unauthorized_response(self):
        values = self.responses()[:3]
        values.append(HTTPError("https://other.invalid/api/analyses", 401, "Unauthorized",
                                {"WWW-Authenticate": "Bearer"}, io.BytesIO()))
        with self.assertRaisesRegex(RuntimeError, "expected saved-report authentication challenge"):
            self.verify(values, report_auth_mode="neon")

    def test_saved_report_runner_accepts_only_complete_machine_evidence(self):
        result = {
            "result": "passed", "cleanedUp": True,
            "analysisMode": "real",
            "analysisProvenance": {"providerMode": "gemini"},
        }
        with patch("scripts.secretary.preview.subprocess.run", return_value=type(
            "Completed", (), {"returncode": 0, "stdout": json.dumps(result)}
        )()) as run:
            self.assertEqual(verify_saved_report("https://staging.invalid", SHA), result)
        command = run.call_args.args[0]
        self.assertIn("--environment", command)
        self.assertIn("staging", command)
        self.assertIn("--allow-writes", command)
        self.assertIn(SHA, command)

    def test_saved_report_runner_rejects_failed_or_unclean_result(self):
        result = {"result": "passed", "cleanedUp": False, "analysisMode": "real",
                  "analysisProvenance": {"providerMode": "gemini"}}
        with patch("scripts.secretary.preview.subprocess.run", return_value=type(
            "Completed", (), {"returncode": 0, "stdout": json.dumps(result)}
        )()), self.assertRaisesRegex(RuntimeError, "did not confirm cleanup"):
            verify_saved_report("https://staging.invalid", SHA)

    def test_saved_report_runner_preserves_mock_mode_for_checklist(self):
        result = {
            "result": "passed", "cleanedUp": True, "analysisMode": "mock",
            "analysisProvenance": {"providerMode": "mock"},
        }
        with patch("scripts.secretary.preview.subprocess.run", return_value=type(
            "Completed", (), {"returncode": 0, "stdout": json.dumps(result)}
        )()):
            self.assertEqual(verify_saved_report("https://staging.invalid", SHA), result)

    def test_saved_report_runner_rejects_inconsistent_mode_and_provider(self):
        result = {
            "result": "passed", "cleanedUp": True, "analysisMode": "real",
            "analysisProvenance": {"providerMode": "mock"},
        }
        with patch("scripts.secretary.preview.subprocess.run", return_value=type(
            "Completed", (), {"returncode": 0, "stdout": json.dumps(result)}
        )()), self.assertRaisesRegex(RuntimeError, "inconsistent AI provenance"):
            verify_saved_report("https://staging.invalid", SHA)

    def test_wrong_commit_fails(self):
        values = self.responses()
        values[2]["commit"] = "b" * 40
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_production_environment_fails(self):
        values = self.responses()
        values[2]["environment"] = "production"
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_missing_synthetic_history_fails(self):
        values = self.responses()
        values[3]["items"] = []
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_unhealthy_or_unready_service_fails(self):
        for index in (0, 1):
            with self.subTest(index=index):
                values = copy.deepcopy(self.responses())
                values[index]["status"] = "unavailable"
                with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
                    self.verify(values)

if __name__ == "__main__":
    unittest.main()

