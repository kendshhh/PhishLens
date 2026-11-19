"""Tests for staging-only extension packaging evidence."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.package_staging_extension import (
    IN_ARCHIVE_EVIDENCE,
    auth_settings,
    build as build_package,
    checkout_revision,
    chrome_extension_id,
    decode_manifest_public_key,
)
from scripts.verify_staging_extension_package import (
    PRODUCTION_HOST,
    STAGING_HOSTS,
    STAGING_ORIGIN,
    verify,
)
from scripts.verify_extension_package import ASSETS

VALID_TEST_PUBLIC_KEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA9uXDbuvYdLYvZipPw0YRVDCzcvU3opz2pOu44/aZ3bX2fQGF+jlf0+JQE12VwE6cD36GeJl1J9gHfD/lD2oE+tvtE6pwtLEZ9I26KZ/By/vE15pUN0xq1cJhdhebPmjSpTjNJn6P4JIGycADEWyVtkRz8SD/ahJxltSX0QQaSU0paY6zviLc+SHd4jWcwAaB/R7r8IsxNLBvCmZjz3uuLEsN5hTEEPKtfR8faPTcTr+mATwLq497r188xehai7CKGB93fGadF24BSaqXU04Mh9uKhGsGMvTOZb6ixBWTHZ7yyXdLJQU8KsGBy1ZmybhRCmbFkKugk6CadYnOZLAKmQIDAQAB"
)


class StagingPackageVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.archive = root / "PhishLens-Staging-Extension.zip"
        self.sidecar = root / "package-evidence.json"
        self.staging_evidence = root / "staging-readonly-evidence.json"
        self.expected = "a" * 40
        self.manifest_key = VALID_TEST_PUBLIC_KEY
        self.build()

    def build(self, *, hosts=None, config_origin=STAGING_ORIGIN, extra=None, auth_enabled=False):
        files = {name: f"asset:{name}".encode() for name in ASSETS}
        auth_url = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth"
        auth_origin = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech"
        auth_database = "neondb"
        expected_hosts = STAGING_HOSTS + ([auth_origin + "/*"] if auth_enabled else [])
        extension_id = chrome_extension_id(self.manifest_key) if auth_enabled else None
        key_sha256 = hashlib.sha256(decode_manifest_public_key(self.manifest_key)).hexdigest() if auth_enabled else None
        files["manifest.json"] = json.dumps({
            "manifest_version": 3,
            "name": "PhishLens Staging Auth" if auth_enabled else "PhishLens Staging",
            "version": "1.2.3",
            "host_permissions": hosts or expected_hosts,
            **({"key": self.manifest_key} if auth_enabled else {}),
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
        self.evidence = {
            "environment": "staging",
            "api_origin": STAGING_ORIGIN,
            "source_commit": self.expected,
            "in_archive_evidence": IN_ARCHIVE_EVIDENCE,
            "host_permissions": expected_hosts,
            "auth_enabled": auth_enabled,
            "auth_url": auth_url if auth_enabled else None,
            "auth_database": auth_database if auth_enabled else None,
            "auth_origin": auth_origin if auth_enabled else None,
            "manifest_key_sha256": key_sha256,
            "chrome_extension_id": extension_id,
            "expected_chrome_origin": f"chrome-extension://{extension_id}" if extension_id else None,
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
            "archive_sha256": "",
            "files_sha256": {},
        }
        embedded = {
            "format": "phishlens-staging-package-v1",
            "environment": "staging",
            "source_commit": self.expected,
            "observed_staging_commit": self.expected,
            "packager_commit": "b" * 40,
            "api_origin": STAGING_ORIGIN,
            "host_permissions": expected_hosts,
            "auth_enabled": auth_enabled,
            "auth_url": auth_url if auth_enabled else None,
            "auth_database": auth_database if auth_enabled else None,
            "auth_origin": auth_origin if auth_enabled else None,
            "manifest_key_sha256": key_sha256,
            "chrome_extension_id": extension_id,
            "expected_chrome_origin": f"chrome-extension://{extension_id}" if extension_id else None,
        }
        files[IN_ARCHIVE_EVIDENCE] = (json.dumps(embedded, indent=2, sort_keys=True) + "\n").encode()
        if extra:
            files.update(extra)
        with ZipFile(self.archive, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        self.files = files
        self.evidence["archive_sha256"] = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.evidence["files_sha256"] = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
        self.save()

    def save(self):
        self.sidecar.write_text(json.dumps(self.evidence), encoding="utf-8")

    def test_matching_staging_package_passes(self):
        result = verify(self.archive, self.sidecar, self.expected)
        self.assertEqual(result["package_checkout_commit"], self.expected)
        self.assertEqual(result["files_verified"], len(ASSETS) + 1)

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

    def test_source_commit_must_match_observed_checkout(self):
        self.evidence["source_commit"] = "d" * 40
        self.save()
        with self.assertRaisesRegex(ValueError, "checkout"):
            verify(self.archive, self.sidecar, self.expected)

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
        self.assertEqual(result["files_verified"], len(ASSETS) + 1)

    def test_auth_enabled_package_rejects_extra_host_permission(self):
        auth_origin = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech"
        self.build(auth_enabled=True, hosts=STAGING_HOSTS + [auth_origin + "/*", "https://*.neon.tech/*"])
        with self.assertRaisesRegex(ValueError, "host permissions"):
            verify(self.archive, self.sidecar, self.expected)

    def test_auth_enabled_package_rejects_mismatched_config(self):
        self.build(auth_enabled=True, extra={"js/auth-config.js": b"export const AUTH_CONFIG = null;\n"})
        with self.assertRaisesRegex(ValueError, "Auth configuration"):
            verify(self.archive, self.sidecar, self.expected)

    def test_auth_enabled_package_requires_manifest_key(self):
        self.build(auth_enabled=True)
        with ZipFile(self.archive, "r") as package:
            files = {name: package.read(name) for name in package.namelist()}
        manifest = json.loads(files["manifest.json"])
        manifest.pop("key")
        files["manifest.json"] = json.dumps(manifest).encode()
        self._rewrite_files(files)
        with self.assertRaisesRegex(ValueError, "public manifest key"):
            verify(self.archive, self.sidecar, self.expected)

    def test_auth_enabled_package_rejects_malformed_der_manifest_key(self):
        self.build(auth_enabled=True)
        with ZipFile(self.archive, "r") as package:
            files = {name: package.read(name) for name in package.namelist()}
        manifest = json.loads(files["manifest.json"])
        manifest["key"] = "c3ludGhldGljLW5vdC1hLWRlci1rZXk="
        files["manifest.json"] = json.dumps(manifest).encode()
        self._rewrite_files(files)
        with self.assertRaisesRegex(ValueError, "SubjectPublicKeyInfo"):
            verify(self.archive, self.sidecar, self.expected)

    def test_embedded_provenance_must_match_sidecar(self):
        with ZipFile(self.archive, "r") as package:
            files = {name: package.read(name) for name in package.namelist()}
        embedded = json.loads(files[IN_ARCHIVE_EVIDENCE])
        embedded["source_commit"] = "d" * 40
        files[IN_ARCHIVE_EVIDENCE] = json.dumps(embedded, indent=2, sort_keys=True).encode() + b"\n"
        self._rewrite_files(files)
        with self.assertRaisesRegex(ValueError, "Embedded provenance"):
            verify(self.archive, self.sidecar, self.expected)

    def _rewrite_files(self, files):
        with ZipFile(self.archive, "w") as package:
            for name, data in files.items():
                package.writestr(name, data)
        self.evidence["archive_sha256"] = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.evidence["files_sha256"] = {
            name: hashlib.sha256(data).hexdigest() for name, data in files.items()
        }
        self.save()

    def test_auth_url_requires_exact_neon_database_path(self):
        base = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech"
        with self.assertRaisesRegex(ValueError, "canonical Neon Auth"):
            auth_settings(base + "/other/auth", "neondb", self.manifest_key)

    def test_auth_url_rejects_credentials_and_query(self):
        host = "ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech"
        with self.assertRaisesRegex(ValueError, "canonical Neon Auth"):
            auth_settings(f"https://user:password@{host}/neondb/auth", "neondb", self.manifest_key)
        with self.assertRaisesRegex(ValueError, "canonical Neon Auth"):
            auth_settings(f"https://{host}/neondb/auth?token=secret", "neondb", self.manifest_key)

    def test_auth_settings_requires_extension_owners_public_key(self):
        with self.assertRaisesRegex(ValueError, "public manifest key"):
            auth_settings(
                "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth",
                "neondb",
                None,
            )

    def test_auth_settings_rejects_non_der_public_key(self):
        with self.assertRaisesRegex(ValueError, "SubjectPublicKeyInfo"):
            auth_settings(
                "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth",
                "neondb",
                "c3ludGhldGljLW5vdC1hLWRlci1rZXk=",
            )

    def test_auth_settings_rejects_truncated_der(self):
        with self.assertRaisesRegex(ValueError, "truncated DER"):
            auth_settings(
                "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth",
                "neondb",
                "MA==",
            )

    def test_disabled_package_does_not_claim_trusted_origin(self):
        self.evidence["trusted_chrome_origin"] = "chrome-extension://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        self.save()
        with self.assertRaisesRegex(ValueError, "Disabled Auth package"):
            verify(self.archive, self.sidecar, self.expected)

    def test_trusted_origin_must_match_the_recorded_chrome_id(self):
        self.build(auth_enabled=True)
        self.evidence["trusted_chrome_origin"] = "chrome-extension://bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        self.save()
        with self.assertRaisesRegex(ValueError, "Trusted Chrome origin"):
            verify(self.archive, self.sidecar, self.expected)

    def test_verified_chrome_origin_pair_is_reported(self):
        self.build(auth_enabled=True)
        extension_id = chrome_extension_id(self.manifest_key)
        origin = f"chrome-extension://{extension_id}"
        self.evidence["chrome_extension_id"] = extension_id
        self.evidence["trusted_chrome_origin"] = origin
        self.save()
        self.assertEqual(verify(self.archive, self.sidecar, self.expected)["trusted_chrome_origin"], origin)

    def test_auth_overlay_builds_separate_package_without_source_edits(self):
        source_config = (Path(__file__).resolve().parents[2] / "extension/js/auth-config.js").read_bytes()
        source_manifest = json.loads((Path(__file__).resolve().parents[2] / "extension/manifest.json").read_text())
        auth_url = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth"
        # The source manifest carries the approved public key; the overlay must reuse it.
        manifest_key = source_manifest.get("key", self.manifest_key)
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "PhishLens-Staging-Auth.zip"
            evidence = Path(directory) / "auth-evidence.json"
            sha = checkout_revision(Path(__file__).resolve().parents[2])
            built = build_package(
                Path(__file__).resolve().parents[2], archive, evidence, sha,
                auth_url=auth_url, auth_database="neondb", manifest_key=manifest_key,
            )
            verified = verify(archive, evidence, sha)
            with ZipFile(archive) as package:
                config = package.read("js/auth-config.js")
                manifest = json.loads(package.read("manifest.json"))
                embedded = json.loads(package.read(IN_ARCHIVE_EVIDENCE))
            self.assertTrue(built["auth_enabled"])
            self.assertTrue(verified["auth_enabled"])
            self.assertEqual(manifest["key"], manifest_key)
            self.assertEqual(verified["source_commit"], sha)
            self.assertEqual(embedded["source_commit"], sha)
            self.assertEqual(verified["chrome_extension_id"], chrome_extension_id(manifest_key))
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

    def test_https_bridge_overlay_records_and_verifies_the_required_https_domain(self):
        root = Path(__file__).resolve().parents[2]
        manifest_key = json.loads((root / "extension/manifest.json").read_text())["key"]
        auth_url = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth"
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "PhishLens-Staging-Auth.zip"
            evidence = Path(directory) / "evidence.json"
            sha = checkout_revision(root)
            built = build_package(root, archive, evidence, sha, auth_url=auth_url,
                                  auth_database="neondb", manifest_key=manifest_key, auth_transport="https-bridge",
                                  candidate_only=True)
            verify(archive, evidence, sha)
            self.assertIsNone(built["observed_staging_commit"])
            self.assertFalse(built["hosted_acceptance_verified"])
            self.assertEqual(built["required_neon_trusted_origin"], STAGING_ORIGIN)
            self.assertIsNone(built["trusted_chrome_origin"])
            with ZipFile(archive) as package:
                self.assertIn("js/neon-bridge-client.js", package.namelist())
                config = package.read("js/auth-config.js").decode()
                self.assertIn('"transport":"https-bridge"', config)
                self.assertIn('"bridgeUrl":"' + STAGING_ORIGIN + '/auth/bridge"', config)
            built["auth_bridge_url"] = "https://attacker.example.test/auth/bridge"
            evidence.write_text(json.dumps(built))
            with self.assertRaisesRegex(ValueError, "bridge does not match"):
                verify(archive, evidence, sha)

    def test_auth_overlay_rejects_a_key_that_differs_from_the_source_manifest(self):
        root = Path(__file__).resolve().parents[2]
        source_manifest = json.loads((root / "extension/manifest.json").read_text())
        self.assertIn("key", source_manifest, "The source manifest must carry the approved public key")
        self.assertNotEqual(source_manifest["key"], VALID_TEST_PUBLIC_KEY)
        auth_url = "https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "does not match the source manifest key"):
                build_package(
                    root, Path(directory) / "PhishLens-Staging-Auth.zip", Path(directory) / "auth-evidence.json",
                    checkout_revision(root), auth_url=auth_url, auth_database="neondb",
                    manifest_key=VALID_TEST_PUBLIC_KEY,
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

