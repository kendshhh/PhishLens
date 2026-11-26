"""The trusted staging preflight is exact-head, read-only, and fail-closed."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.hosted_staging_finalize import finalize

SHA = "a" * 40
EXTENSION_ID = "ceneonaedddlkdocdapimkfggbjcchlb"
ORIGIN = "https://phishlens-staging.onrender.com"
REPOSITORY = "kendshhh/PhishLens"


class BridgeResponse:
    def __init__(self, url, *, status=200, content_type=None, csp=None, body=b""):
        self.status = status
        self._url = url
        self.headers = {"Content-Type": content_type or self._content_type(url)}
        if csp is not None:
            self.headers["Content-Security-Policy"] = csp
        self._body = body

    @staticmethod
    def _content_type(url):
        return "text/html; charset=utf-8" if url.endswith("/auth/bridge") else "application/javascript"

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self._url

    def read(self, _limit=-1):
        return self._body


class BridgeOpener:
    def __init__(self, *, bad_csp=False, fail_path=None):
        self.requests = []
        self.bad_csp = bad_csp
        self.fail_path = fail_path

    def open(self, request, timeout=20):
        url = request.full_url
        self.requests.append((url, timeout))
        path = url.removeprefix(ORIGIN)
        if path == self.fail_path:
            return BridgeResponse(url, status=302)
        csp = "frame-ancestors https://example.invalid" if self.bad_csp else (
            f"frame-ancestors chrome-extension://{EXTENSION_ID}"
        )
        body = f'<div data-extension-origin="chrome-extension://{EXTENSION_ID}"></div>'.encode()
        return BridgeResponse(url, csp=csp if path == "/auth/bridge" else None, body=body)


class HostedStagingFinalizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package_evidence = self.root / "package-evidence.json"
        self.output = self.root / "preflight-evidence.json"
        self.package_evidence.write_text(json.dumps({
            "source_commit": SHA,
            "chrome_extension_id": EXTENSION_ID,
        }), encoding="utf-8")
        self.api = Mock()
        self.api.request.return_value = {"state": "open"}
        self.opener = BridgeOpener()
        self.environment = {
            "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_TOKEN": "test-token",
            "STAGING_PR": "296",
            "STAGING_PR_HEAD_SHA": SHA,
            "STAGING_COMMIT": SHA,
            "STAGING_BASE_URL": ORIGIN,
            "RELEASE_EXTENSION_EVIDENCE": str(self.package_evidence),
            "STAGING_PREFLIGHT_EVIDENCE": str(self.output),
        }

    def run_finalize(self, current=(True, True), *, opener=None, package=None):
        if package is not None:
            self.package_evidence.write_text(json.dumps(package), encoding="utf-8")
        with (
            patch.dict(os.environ, self.environment, clear=True),
            patch("scripts.hosted_staging_finalize.requested_pr_identity", return_value=(296, SHA)),
            patch("scripts.hosted_staging_finalize.ReadOnlyGitHub", return_value=self.api),
            patch("scripts.hosted_staging_finalize.live_pr_matches", side_effect=current),
            patch("scripts.hosted_staging_finalize.smoke", return_value={"health": "passed"}) as smoke,
            patch("scripts.hosted_staging_finalize.urllib.request.build_opener",
                  return_value=opener or self.opener),
        ):
            result = finalize()
        return result, smoke

    def test_writes_redacted_evidence_for_exact_sha_and_package(self):
        result, smoke = self.run_finalize()

        self.assertEqual(result["sha"], SHA)
        self.assertEqual(result["deployed_commit"], SHA)
        self.assertEqual(result["auth_bridge"]["/auth/bridge"], 200)
        self.assertEqual(len(self.opener.requests), 3)
        self.assertTrue(self.output.exists())
        self.assertEqual(json.loads(self.output.read_text(encoding="utf-8"))["sha"], SHA)
        smoke.assert_called_once_with(ORIGIN, SHA, report_auth_mode="neon")

    def test_wrong_origin_or_deployed_sha_fails_before_external_check(self):
        for field, value, message in (
            ("STAGING_BASE_URL", "https://wrong.example", "origin differs"),
            ("STAGING_COMMIT", "b" * 40, "Deployed staging SHA"),
        ):
            with self.subTest(field=field):
                env = dict(self.environment, **{field: value})
                with (
                    patch.dict(os.environ, env, clear=True),
                    patch("scripts.hosted_staging_finalize.requested_pr_identity", return_value=(296, SHA)),
                    patch("scripts.hosted_staging_finalize.ReadOnlyGitHub", return_value=self.api),
                    self.assertRaisesRegex(RuntimeError, message),
                ):
                    finalize()
                self.assertFalse(self.output.exists())

    def test_wrong_package_identity_fails_before_api_or_smoke(self):
        package = {"source_commit": "b" * 40, "chrome_extension_id": EXTENSION_ID}
        self.package_evidence.write_text(json.dumps(package), encoding="utf-8")
        with (
            patch.dict(os.environ, self.environment, clear=True),
            patch("scripts.hosted_staging_finalize.requested_pr_identity", return_value=(296, SHA)),
            patch("scripts.hosted_staging_finalize.ReadOnlyGitHub", return_value=self.api) as client,
            patch("scripts.hosted_staging_finalize.smoke") as smoke,
            self.assertRaisesRegex(RuntimeError, "package does not match"),
        ):
            finalize()
        client.assert_not_called()
        smoke.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_missing_extension_id_fails_before_api_or_smoke(self):
        self.package_evidence.write_text(json.dumps({"source_commit": SHA}), encoding="utf-8")
        with (
            patch.dict(os.environ, self.environment, clear=True),
            patch("scripts.hosted_staging_finalize.requested_pr_identity", return_value=(296, SHA)),
            patch("scripts.hosted_staging_finalize.ReadOnlyGitHub", return_value=self.api) as client,
            patch("scripts.hosted_staging_finalize.smoke") as smoke,
            self.assertRaisesRegex(RuntimeError, "identity is missing"),
        ):
            finalize()
        client.assert_not_called()
        smoke.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_stale_head_before_or_during_bridge_checks_never_writes_evidence(self):
        with self.assertRaisesRegex(RuntimeError, "Stale PR head"):
            self.run_finalize(current=(False,))
        self.assertFalse(self.output.exists())

        opener = BridgeOpener()
        with self.assertRaisesRegex(RuntimeError, "Stale PR head"):
            self.run_finalize(current=(True, False), opener=opener)
        self.assertEqual(len(opener.requests), 3)
        self.assertFalse(self.output.exists())

    def test_auth_bridge_rejects_redirect_and_wrong_extension_csp(self):
        for opener, message in (
            (BridgeOpener(fail_path="/auth/bridge/client.js"), "Auth bridge GET failed"),
            (BridgeOpener(bad_csp=True), "Auth bridge GET failed"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(RuntimeError, message):
                    self.run_finalize(opener=opener)
                self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
