import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from scripts.package_release_extension import (
    PRODUCTION_API,
    STAGING_API,
    build,
)
from scripts.verify_extension_package import ASSETS


SOURCE_SHA = "a" * 40
PRODUCTION_AUTH = "https://ep-production.neonauth.us-east-1.aws.neon.tech/phishlens/auth"
STAGING_AUTH = "https://ep-staging.neonauth.us-east-1.aws.neon.tech/phishlens/auth"


class ReleaseExtensionPackageTests(unittest.TestCase):
    def run_build(self, root):
        output = Path(root) / "PhishLens-Release.zip"
        evidence_path = Path(root) / "package-evidence.json"
        evidence = build(
            expected_sha=SOURCE_SHA,
            production_auth_url=PRODUCTION_AUTH,
            production_auth_database="phishlens",
            staging_auth_url=STAGING_AUTH,
            staging_auth_database="phishlens",
            output=output,
            evidence_path=evidence_path,
        )
        return output, json.loads(evidence_path.read_text()), evidence

    def test_one_zip_binds_both_auth_targets_and_defaults_to_production(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "scripts.package_release_extension._git",
            side_effect=[SOURCE_SHA, ""],
        ):
            output, evidence, result = self.run_build(directory)
            self.assertEqual(result["archive_sha256"], evidence["archive_sha256"])
            self.assertEqual(evidence["api_origins"], {
                "production": PRODUCTION_API,
                "staging": STAGING_API,
            })
            self.assertEqual(evidence["staging_selection"], "popup.html?environment=staging")
            self.assertTrue(evidence["production_default"])
            with ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), ASSETS | {"phishlens-build-evidence.json"})
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["host_permissions"], [
                    PRODUCTION_API + "/*", STAGING_API + "/*",
                ])
                auth = archive.read("js/auth-config.js").decode()
                self.assertIn(PRODUCTION_AUTH, auth)
                self.assertIn(STAGING_AUTH, auth)
                self.assertIn('"transport":"https-bridge"', auth)
                self.assertIn('"bridgeUrl":"' + STAGING_API + '/auth/bridge"', auth)
                self.assertNotIn("password", auth.lower())
                popup = archive.read("popup.js").decode()
                self.assertIn("requestedEnvironment === 'staging'", popup)
                self.assertIn("API_BASE_URLS[releaseEnvironment]", popup)
            self.assertEqual(evidence["auth_configs"]["staging"]["transport"], "https-bridge")
            self.assertEqual(evidence["auth_configs"]["staging"]["bridgeUrl"], STAGING_API + "/auth/bridge")

    def test_same_auth_endpoint_and_non_neon_endpoint_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "scripts.package_release_extension._git",
            side_effect=[SOURCE_SHA, ""],
        ):
            with self.assertRaisesRegex(ValueError, "must be different"):
                build(
                    expected_sha=SOURCE_SHA,
                    production_auth_url=PRODUCTION_AUTH,
                    production_auth_database="phishlens",
                    staging_auth_url=PRODUCTION_AUTH,
                    staging_auth_database="phishlens",
                    output=Path(directory) / "archive.zip",
                    evidence_path=Path(directory) / "evidence.json",
                )

        with tempfile.TemporaryDirectory() as directory, patch(
            "scripts.package_release_extension._git",
            side_effect=[SOURCE_SHA, ""],
        ):
            with self.assertRaisesRegex(ValueError, "canonical Neon Auth"):
                build(
                    expected_sha=SOURCE_SHA,
                    production_auth_url="https://example.test/phishlens/auth",
                    production_auth_database="phishlens",
                    staging_auth_url=STAGING_AUTH,
                    staging_auth_database="phishlens",
                    output=Path(directory) / "archive.zip",
                    evidence_path=Path(directory) / "evidence.json",
                )

    def test_dirty_source_identity_blocks_package_build(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "scripts.package_release_extension._git",
            side_effect=[SOURCE_SHA, " M extension/manifest.json"],
        ):
            with self.assertRaisesRegex(ValueError, "modified or untracked"):
                self.run_build(directory)


if __name__ == "__main__":
    unittest.main()
