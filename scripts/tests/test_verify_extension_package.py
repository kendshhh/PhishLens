"""Reject altered downloads and stale package identity before installation."""

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from scripts.verify_extension_package import ASSETS, main, verify


class PackageVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "extension.zip"
        self.sidecar = Path(self.temp.name) / "evidence.json"
        self.hosts = ["https://phishlens-api-ocvt.onrender.com/*"]
        self.build()

    def build(self, extra=False, hosts=None):
        manifest = json.dumps({"manifest_version": 3, "version": "0.1.0",
                               "host_permissions": hosts or self.hosts}).encode()
        files = {name: b"synthetic asset" for name in ASSETS}
        files["manifest.json"] = manifest
        with ZipFile(self.archive, "w") as package:
            for name, content in files.items():
                package.writestr(name, content)
            if extra:
                package.writestr("unexpected.js", "untracked")
        self.evidence = {
            "source_commit": "a" * 40, "tested_commit": "b" * 40,
            "environment": "production",
            "runtime_or_packaging_changes": False, "archive": self.archive.name,
            "archive_sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
            "files_sha256": {name: hashlib.sha256(content).hexdigest()
                             for name, content in files.items()},
            "extension_version": "0.1.0", "host_permissions": self.hosts,
        }
        self.save()

    def save(self):
        self.sidecar.write_text(json.dumps(self.evidence), encoding="utf-8")

    def check(self):
        return verify(self.archive, self.sidecar, "a" * 40)

    def test_matching_package_passes(self):
        self.assertEqual(self.check()["files_verified"], len(ASSETS))

    def test_stale_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "source"):
            verify(self.archive, self.sidecar, "b" * 40)

    def test_altered_archive_rejected(self):
        with self.archive.open("ab") as stream:
            stream.write(b"altered")
        with self.assertRaisesRegex(ValueError, "Archive SHA"):
            self.check()

    def test_extra_file_rejected_even_with_matching_archive_digest(self):
        self.build(extra=True)
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.check()

    def test_incorrect_file_digest_rejected(self):
        self.evidence["files_sha256"]["manifest.json"] = "0" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "File SHA"):
            self.check()

    def test_unknown_or_modified_inputs_rejected(self):
        for status in (True, None):
            self.evidence["runtime_or_packaging_changes"] = status
            self.save()
            with self.assertRaisesRegex(ValueError, "modified"):
                self.check()

    def test_wildcard_host_rejected(self):
        self.build(hosts=["https://*/*"])
        with self.assertRaisesRegex(ValueError, "permissions"):
            self.check()

    def test_version_disagreement_rejected(self):
        self.evidence["extension_version"] = "9.9.9"
        self.save()
        with self.assertRaisesRegex(ValueError, "version"):
            self.check()

    def test_short_expected_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "full lowercase"):
            verify(self.archive, self.sidecar, "a" * 7)

    def test_missing_tested_revision_rejected(self):
        del self.evidence["tested_commit"]
        self.save()
        with self.assertRaisesRegex(ValueError, "tested commit"):
            self.check()

    def test_non_object_sidecar_rejected(self):
        self.sidecar.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(TypeError, "JSON object"):
            self.check()

    def test_sidecar_cannot_authorize_extra_runtime_file(self):
        self.build(extra=True)
        self.evidence["files_sha256"]["unexpected.js"] = hashlib.sha256(b"untracked").hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.check()

    def test_missing_asset_rejected_even_with_matching_sidecar(self):
        del self.evidence["files_sha256"]["popup.js"]
        self.save()
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.check()

    def test_corrupt_zip_cli_exits_cleanly(self):
        self.archive.write_bytes(b"not a zip")
        self.evidence["archive_sha256"] = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.save()
        output = io.StringIO()
        argv = ["verify", str(self.archive), str(self.sidecar), "--expected-source", "a" * 40]
        with (patch.object(sys, "argv", argv), redirect_stderr(output),
              self.assertRaises(SystemExit) as error):
            main()
        self.assertEqual(error.exception.code, 1)
        self.assertIn("Package rejected", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_optional_host_permissions_rejected(self):
        with ZipFile(self.archive) as package:
            files = {name: package.read(name) for name in package.namelist()}
        manifest = json.loads(files["manifest.json"])
        manifest["optional_host_permissions"] = ["https://*/*"]
        files["manifest.json"] = json.dumps(manifest).encode()
        with ZipFile(self.archive, "w") as package:
            for name, content in files.items():
                package.writestr(name, content)
        self.evidence["archive_sha256"] = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.evidence["files_sha256"]["manifest.json"] = hashlib.sha256(files["manifest.json"]).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, "Optional host"):
            self.check()
