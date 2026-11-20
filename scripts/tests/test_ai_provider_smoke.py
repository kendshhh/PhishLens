"""Guarded controller tests; every HTTP response is a substitute, never staging."""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from scripts import ai_provider_smoke as smoke

SHA = "a" * 40


class AIProviderSmokeTests(unittest.TestCase):
    def setUp(self):
        config = json.loads((smoke.ROOT / ".github/secretary.json").read_bytes())
        self.origin = config["staging_origin"].rstrip("/")
        environment = {
            "EXPECTED_SOURCE_SHA": SHA, "GITHUB_SHA": "b" * 40,
            "WORKFLOW_SOURCE_SHA": "b" * 40,
            "AI_PROVIDER_SMOKE_ENABLE_REQUEST": "true", "AI_PROVIDER_SMOKE_ENABLED": "true",
            "AI_PROVIDER_SMOKE_ENV": "staging", "STAGING_BASE_URL": self.origin,
            "AI_PROVIDER_SMOKE_PROVIDER": "tfidf", "AI_PROVIDER_SMOKE_MODEL": smoke.TFIDF_MODEL,
            "AI_PROVIDER_SMOKE_MAX_REQUESTS": "1", "AI_PROVIDER_SMOKE_COST_CAP_USD": "0",
        }
        self.patch(patch.dict(os.environ, environment, clear=True))
        self.patch(patch.object(smoke, "PROVIDER_REQUEST_ATTEMPTED", False))
        self.patch(patch.object(smoke, "PROVIDER_CALLS_OBSERVED", None))
        self.preflight = {
            "/version": {"commit": SHA, "environment": "staging"},
            "/model-info": {"provider_mode": "tfidf", "model_sha256": smoke.TFIDF_REVISION},
            "/ready": {"status": "ready", "database": "connected"},
        }
        self.patch(patch.object(smoke, "_get_json", side_effect=lambda origin, path: (200, self.preflight[path])))
        self.payload = {"classification": "phishing", "risk_level": "high", "mode": "tfidf",
                        "model": smoke.TFIDF_MODEL, "model_revision": smoke.TFIDF_REVISION}
        self.response = MagicMock()
        self.response.__enter__.return_value = self.response
        self.response.status = 200
        self.response.headers = {"X-PhishLens-Revision": SHA}
        self.response.read.side_effect = lambda limit: json.dumps(self.payload).encode()
        self.opener = MagicMock()
        self.opener.open.return_value = self.response
        self.patch(patch.object(smoke, "build_opener", return_value=self.opener))

    def patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def test_tfidf_sends_one_revision_bound_nonpersisting_request(self):
        result = smoke.run()
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, self.origin + "/analyses/revision/" + SHA)
        self.assertEqual(request.get_header("X-require-provider"), "tfidf")
        self.assertEqual(json.loads(request.data), smoke.SYNTHETIC_REQUEST)
        self.opener.open.assert_called_once()
        self.assertEqual(result["provider_calls_observed"], 0)
        self.assertEqual(result["local_model_inferences"], 1)
        self.assertEqual(result["runtime_cost_cap_usd"], "0")
        self.assertEqual(result["database_writes"], 0)

    def test_disabled_or_wrong_target_is_blocked_before_post(self):
        for changes in ({"AI_PROVIDER_SMOKE_ENABLE_REQUEST": "false"},
                        {"AI_PROVIDER_SMOKE_ENABLED": "false"},
                        {"AI_PROVIDER_SMOKE_ENV": "production"},
                        {"STAGING_BASE_URL": "https://example.invalid"},
                        {"AI_PROVIDER_SMOKE_MAX_REQUESTS": "2"},
                        {"WORKFLOW_SOURCE_SHA": "c" * 40}):
            with self.subTest(changes=changes), patch.dict(os.environ, changes):
                with self.assertRaises(smoke.SmokeGateError):
                    smoke.run()
                self.opener.open.assert_not_called()

    def test_tfidf_requires_zero_cost_and_the_known_model(self):
        for changes in ({"AI_PROVIDER_SMOKE_COST_CAP_USD": "0.01"},
                        {"AI_PROVIDER_SMOKE_COST_CAP_USD": "-1"},
                        {"AI_PROVIDER_SMOKE_COST_CAP_USD": "NaN"},
                        {"AI_PROVIDER_SMOKE_MODEL": "other-model"}):
            with self.subTest(changes=changes), patch.dict(os.environ, changes):
                with self.assertRaises(smoke.SmokeGateError):
                    smoke.run()
                self.opener.open.assert_not_called()

    def test_gemini_cannot_use_the_zero_cost_tfidf_exception(self):
        with (patch.dict(os.environ, {"AI_PROVIDER_SMOKE_PROVIDER": "gemini"}),
              self.assertRaisesRegex(smoke.SmokeGateError, "owner_cost_cap_not_configured")):
            smoke.run()
        self.opener.open.assert_not_called()

    def test_stale_deployment_model_or_unready_database_blocks_post(self):
        for path, replacement in (
            ("/version", {"commit": "c" * 40, "environment": "staging"}),
            ("/version", {"commit": SHA, "environment": "production"}),
            ("/model-info", {"provider_mode": "gemini"}),
            ("/model-info", {"provider_mode": "tfidf", "model_sha256": "c" * 64}),
            ("/ready", {"status": "not_ready", "database": "unavailable"}),
        ):
            with self.subTest(path=path, replacement=replacement), patch.dict(self.preflight, {path: replacement}):
                with self.assertRaises(smoke.SmokeGateError):
                    smoke.run()
                self.opener.open.assert_not_called()

    def test_inference_revision_drift_stops_without_retry(self):
        self.response.headers = {"X-PhishLens-Revision": "c" * 40}
        with self.assertRaisesRegex(smoke.SmokeGateError, "inference_revision_mismatch_no_retry"):
            smoke.run()
        self.opener.open.assert_called_once()

    def test_response_provider_or_model_substitution_stops_without_retry(self):
        for changes in ({"mode": "gemini"}, {"model_revision": "c" * 64}):
            with self.subTest(changes=changes), patch.dict(self.payload, changes):
                self.opener.open.reset_mock()
                with self.assertRaises(smoke.SmokeGateError):
                    smoke.run()
                self.opener.open.assert_called_once()

    def test_timeout_stops_after_one_attempt(self):
        self.opener.open.side_effect = TimeoutError()
        with self.assertRaisesRegex(smoke.SmokeGateError, "provider_request_transport_error_no_retry"):
            smoke.run()
        self.opener.open.assert_called_once()

    def test_invalid_output_stops_after_one_attempt(self):
        self.response.read.side_effect = None
        self.response.read.return_value = b"not JSON"
        with self.assertRaisesRegex(smoke.SmokeGateError, "provider_response_invalid_json_no_retry"):
            smoke.run()
        self.opener.open.assert_called_once()

    def configure_gemini(self):
        os.environ.update(AI_PROVIDER_SMOKE_PROVIDER="gemini", AI_PROVIDER_SMOKE_MODEL="gemini-test",
                          AI_PROVIDER_SMOKE_COST_CAP_USD="0.01")
        self.preflight["/model-info"] = {"provider_mode": "gemini", "model": "gemini-test",
                                          "spend_guard_enabled": True, "per_request_cost_cap_usd": "0.01"}
        self.payload.update(mode="gemini", model="gemini-test", model_revision=None)

    def test_gemini_retains_positive_cap_identity_and_one_attempt(self):
        self.configure_gemini()
        result = smoke.run()
        self.assertEqual(result["provider_calls_observed"], 1)
        self.assertEqual(result["local_model_inferences"], 0)
        self.assertEqual(result["runtime_cost_cap_usd"], "0.01")
        self.opener.open.assert_called_once()

    def test_gemini_runtime_cap_mismatch_stops_before_post(self):
        self.configure_gemini()
        self.preflight["/model-info"]["per_request_cost_cap_usd"] = "0.02"
        with self.assertRaisesRegex(smoke.SmokeGateError, "staging_runtime_spend_cap_mismatch"):
            smoke.run()
        self.opener.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
