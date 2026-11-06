"""Tests for staging-only extension packaging evidence."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

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

    def build(self, *, hosts=None, config_origin=STAGING_ORIGIN, extra=None):
        files = {name: f"asset:{name}".encode() for name in ASSETS}
        files["manifest.json"] = json.dumps({
            "manifest_version": 3,
            "name": "PhishLens Staging",
            "version": "1.2.3",
            "host_permissions": hosts or STAGING_HOSTS,
        }).encode()
        files["js/config.js"] = (
            f'export const API_BASE_URL = "{config_origin}";\n'.encode()
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
            "host_permissions": STAGING_HOSTS,
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

