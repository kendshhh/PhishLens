"""Tests for staging-only extension packaging evidence."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.package_staging_extension import auth_settings, build as build_package, checkout_revision
from scripts.verify_staging_extension_package import (
    PRODUCTION_HOST,
    STAGING_HOSTS,
    STAGING_ORIGIN,
    verify,
)
from scripts.verify_extension_package import ASSETS


class StagingPackageVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.archive = root / "PhishLens-Staging-Extension.zip"
        self.sidecar = root / "package-evidence.json"
        self.staging_evidence = root / "staging-readonly-evidence.json"
        self.expected = "a" * 40
        self.build()

    def build(self, *, hosts=None, config_origin=STAGING_ORIGIN, extra=None, auth_enabled=False):
        files = {name: f"asset:{name}".encode() for name in ASSETS}
        auth_url = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth"
        auth_origin = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech"
        auth_database = "neondb"
        expected_hosts = STAGING_HOSTS + ([auth_origin + "/*"] if auth_enabled else [])
        files["manifest.json"] = json.dumps({
            "manifest_version": 3,
            "name": "PhishLens Staging Auth" if auth_enabled else "PhishLens Staging",
            "version": "1.2.3",
            "host_permissions": hosts or expected_hosts,
        }).encode()
        files["js/config.js"] = (
            f'export const API_BASE_URL = "{config_origin}";\n'.encode()
        )
        files["js/auth-config.js"] = (
            ("export const AUTH_CONFIG = " + json.dumps({
                "enabled": True, "authUrl": auth_url, "database": auth_database,
                "apiOrigin": STAGING_ORIGIN,
            }, separators=(",", ":")) + ";\n").encode()
            if auth_enabled else b"export const AUTH_CONFIG = null;\n"
        )
        if extra:
            files.update(extra)
        with ZipFile(self.archive, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        self.files = files
        self.evidence = {
            "environment": "staging",
            "api_origin": STAGING_ORIGIN,
            "host_permissions": expected_hosts,
            "auth_enabled": auth_enabled,
            "auth_url": auth_url if auth_enabled else None,
            "auth_database": auth_database if auth_enabled else None,
            "auth_origin": auth_origin if auth_enabled else None,
            "chrome_extension_id": None,
            "trusted_chrome_origin": None,
            "observed_staging_commit": self.expected,
            "package_checkout_commit": self.expected,
            "packager_checkout_commit": "b" * 40,
            "workflow_event_sha": "c" * 40,
            "packager_sha256": hashlib.sha256(
                Path(__file__).resolve().parents[1].joinpath("package_staging_extension.py").read_bytes()
            ).hexdigest(),
            "extension_version": "1.2.3",
            "runtime_inputs_clean": True,
            "archive": self.archive.name,
            "archive_sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
            "files_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
        }
        self.save()

    def save(self):
        self.sidecar.write_text(json.dumps(self.evidence), encoding="utf-8")

    def test_matching_staging_package_passes(self):
        result = verify(self.archive, self.sidecar, self.expected)
        self.assertEqual(result["package_checkout_commit"], self.expected)
        self.assertEqual(result["files_verified"], len(ASSETS))

    def test_event_sha_is_separate_from_staging_checkout_sha(self):
        self.assertEqual(verify(self.archive, self.sidecar, self.expected)["workflow_event_sha"], "c" * 40)

    def test_checkout_must_match_observed_staging_revision(self):
        self.evidence["package_checkout_commit"] = "d" * 40
        self.save()
        with self.assertRaisesRegex(ValueError, "checkout"):
            verify(self.archive, self.sidecar, self.expected)

    def test_expected_revision_must_match_observed_revision(self):
        with self.assertRaisesRegex(ValueError, "checkout"):
            verify(self.archive, self.sidecar, "e" * 40)

    def test_production_manifest_permission_is_rejected(self):
        self.build(hosts=[f"https://{PRODUCTION_HOST}/*"])
        with self.assertRaisesRegex(ValueError, "host permissions"):
            verify(self.archive, self.sidecar, self.expected)

    def test_production_hostname_in_runtime_asset_is_rejected(self):
        self.build(extra={"js/api.js": f"https://{PRODUCTION_HOST}".encode()})
        with self.assertRaisesRegex(ValueError, "Production API hostname"):
            verify(self.archive, self.sidecar, self.expected)

    def test_non_staging_api_origin_is_rejected(self):
        self.build(config_origin=f"https://{PRODUCTION_HOST}")
        with self.assertRaisesRegex(ValueError, "API configuration"):
            verify(self.archive, self.sidecar, self.expected)

    def test_extra_file_is_rejected(self):
        self.build(extra={"unexpected.js": b"untracked"})
        with self.assertRaisesRegex(ValueError, "inventory"):
            verify(self.archive, self.sidecar, self.expected)

    def test_auth_enabled_package_has_exact_staging_and_auth_hosts(self):
        self.build(auth_enabled=True)
        result = verify(self.archive, self.sidecar, self.expected)
        self.assertEqual(result["files_verified"], len(ASSETS))

    def test_auth_enabled_package_rejects_extra_host_permission(self):
        auth_origin = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech"
        self.build(auth_enabled=True, hosts=STAGING_HOSTS + [auth_origin + "/*", "https://*.neon.tech/*"])
        with self.assertRaisesRegex(ValueError, "host permissions"):
            verify(self.archive, self.sidecar, self.expected)

    def test_auth_enabled_package_rejects_mismatched_config(self):
        self.build(auth_enabled=True, extra={"js/auth-config.js": b"export const AUTH_CONFIG = null;\n"})
        with self.assertRaisesRegex(ValueError, "Auth configuration"):
            verify(self.archive, self.sidecar, self.expected)

    def test_auth_url_requires_exact_neon_database_path(self):
        base = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech"
        with self.assertRaisesRegex(ValueError, "canonical Neon Auth"):
            auth_settings(base + "/other/auth", "neondb")

    def test_auth_url_rejects_credentials_and_query(self):
        host = "ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech"
        with self.assertRaisesRegex(ValueError, "canonical Neon Auth"):
            auth_settings(f"https://user:password@{host}/neondb/auth", "neondb")
        with self.assertRaisesRegex(ValueError, "canonical Neon Auth"):
            auth_settings(f"https://{host}/neondb/auth?token=secret", "neondb")

    def test_disabled_package_does_not_claim_trusted_origin(self):
        self.evidence["trusted_chrome_origin"] = "chrome-extension://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        self.save()
        with self.assertRaisesRegex(ValueError, "Disabled Auth package"):
            verify(self.archive, self.sidecar, self.expected)

    def test_trusted_origin_must_match_the_recorded_chrome_id(self):
        self.build(auth_enabled=True)
        self.evidence["chrome_extension_id"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        self.evidence["trusted_chrome_origin"] = "chrome-extension://bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        self.save()
        with self.assertRaisesRegex(ValueError, "match the observed extension ID"):
            verify(self.archive, self.sidecar, self.expected)

    def test_verified_chrome_origin_pair_is_reported(self):
        self.build(auth_enabled=True)
        extension_id = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        origin = f"chrome-extension://{extension_id}"
        self.evidence["chrome_extension_id"] = extension_id
        self.evidence["trusted_chrome_origin"] = origin
        self.save()
        self.assertEqual(verify(self.archive, self.sidecar, self.expected)["trusted_chrome_origin"], origin)

    def test_auth_overlay_builds_separate_package_without_source_edits(self):
        source_config = (Path(__file__).resolve().parents[2] / "extension/js/auth-config.js").read_bytes()
        source_manifest = json.loads((Path(__file__).resolve().parents[2] / "extension/manifest.json").read_text())
        auth_url = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth"
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "PhishLens-Staging-Auth.zip"
            evidence = Path(directory) / "auth-evidence.json"
            sha = checkout_revision(Path(__file__).resolve().parents[2])
            built = build_package(
                Path(__file__).resolve().parents[2], archive, evidence, sha,
                auth_url=auth_url, auth_database="neondb",
            )
            verified = verify(archive, evidence, sha)
            with ZipFile(archive) as package:
                config = package.read("js/auth-config.js")
                manifest = json.loads(package.read("manifest.json"))
            self.assertTrue(built["auth_enabled"])
            self.assertTrue(verified["auth_enabled"])
            self.assertEqual(config, (
                "export const AUTH_CONFIG = " + json.dumps({
                    "enabled": True, "authUrl": auth_url, "database": "neondb",
                    "apiOrigin": STAGING_ORIGIN,
                }, separators=(",", ":")) + ";\n"
            ).encode())
            self.assertEqual(manifest["host_permissions"], [
                STAGING_ORIGIN + "/*",
                "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/*",
            ])
        self.assertEqual(
            (Path(__file__).resolve().parents[2] / "extension/js/auth-config.js").read_bytes(),
            source_config,
        )
        self.assertEqual(
            json.loads((Path(__file__).resolve().parents[2] / "extension/manifest.json").read_text()),
            source_manifest,
        )

    def test_builder_rejects_outputs_inside_source_checkout(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            archive = root / "must-not-be-created.zip"
            evidence = Path(directory) / "evidence.json"
            with self.assertRaisesRegex(ValueError, "separate from the source checkout"):
                build_package(root, archive, evidence, checkout_revision(root))
            self.assertFalse(archive.exists())

    def test_readonly_staging_evidence_is_bound_to_package(self):
        observed = {
            "environment": "staging",
            "backend_source_commit": self.expected,
            "version": {"commit": self.expected, "environment": "staging"},
            "ready": {"status": "ready", "database": "connected"},
            "model_info": {
                "provider_mode": "tfidf",
                "model_sha256": "f" * 64,
                "accepts_tfidf_reports": True,
                "accepts_local_reviews": True,
            },
            "saved_analysis_crud_performed": False,
            "production_writes_performed": False,
        }
        self.staging_evidence.write_text(json.dumps(observed), encoding="utf-8")
        self.assertEqual(
            verify(self.archive, self.sidecar, self.expected, self.staging_evidence)["observed_staging_commit"],
            self.expected,
        )
        observed["backend_source_commit"] = "9" * 40
        self.staging_evidence.write_text(json.dumps(observed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Read-only staging evidence"):
            verify(self.archive, self.sidecar, self.expected, self.staging_evidence)


if __name__ == "__main__":
    unittest.main()

