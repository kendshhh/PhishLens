"""Exercise packaged popup references without modifying real extension assets."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


class ExtensionAssetValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        scripts = self.root / "scripts"
        scripts.mkdir()
        shutil.copyfile(
            Path(__file__).resolve().parents[1] / "validate_extension.py",
            scripts / "validate_extension.py",
        )
        self.extension = self.root / "extension"
        for asset in (
            "popup.html", "css/popup.css", "js/popup.js", "js/config.js",
            "js/api.js", "js/history.js", "background.js", "popup.js", "popup.css",
            "js/report-client.js", "js/report-workflow.js", "ai/contract.json",
            "ai/local-analyzer.mjs", "ai/core.mjs", "ai/observations.mjs",
            "ai/tfidf_v12a.json", "ai/ATTRIBUTION.md",
            "offscreen.html",
            "offscreen.js",
            "ai/judge-client.mjs",
            "ai/judge-contract.mjs",
            "ai/judge-worker.mjs",
            "ai/live-workflow.mjs",
            "ai/reevaluators.mjs",
            "ai/judge-assets.json",
            "ai/reevaluators/manifest.json",
            "ai/reevaluators/krr.json",
            "ai/reevaluators/lightgbm.json",
            "vendor/ml/transformers.min.js",
            "vendor/ml/structured-output.js",
            "vendor/ml/ort-wasm-simd-threaded.jsep.mjs",
            "vendor/ml/ort-wasm-simd-threaded.jsep.wasm",
            "vendor/ml/ort-wasm-simd-threaded.asyncify.mjs",
            "vendor/ml/ort-wasm-simd-threaded.asyncify.wasm",
            "vendor/ml/LICENSE-transformers.txt",
            "vendor/ml/LICENSE-structured-output.txt",
            "vendor/ml/LICENSE-onnxruntime.txt",
            "vendor/ml/LICENSE-Llama3.2.txt",
            "vendor/ml/THIRD_PARTY_NOTICES.md",
        ):
            target = self.extension / asset
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("", encoding="utf-8")
        (self.extension / "manifest.json").write_text(json.dumps({
            "manifest_version": 3,
            "background": {"service_worker": "background.js", "type": "module"},
            "action": {"default_popup": "popup.html"},
            "host_permissions": ["https://phishlens-api-ocvt.onrender.com/*"],
        }), encoding="utf-8")

    def validate(self, markup):
        (self.extension / "popup.html").write_text(markup, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "validate_extension.py")],
            capture_output=True, text=True, check=False,
        )

    def test_valid_packaged_references(self):
        result = self.validate(
            '<script src="js/popup.js"></script>'
            '<link rel="stylesheet" href="css/popup.css">'
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_referenced_asset_fails(self):
        result = self.validate('<script src="js/missing.js"></script>')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing extension asset", result.stderr)

    def test_external_reference_fails(self):
        result = self.validate('<script src="https://example.com/app.js"></script>')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected packaged local popup asset", result.stderr)

    def test_encoded_traversal_fails(self):
        (self.root / "outside.js").write_text("", encoding="utf-8")
        result = self.validate('<script src="%2e%2e/outside.js"></script>')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Asset escapes extension directory", result.stderr)

    def test_extra_or_wildcard_hosts_fail(self):
        manifest_path = self.extension / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        for extra in ["<all_urls>", "https://*/*", "http://localhost:8000/*",
                      "https://phishlens-staging.onrender.com/*"]:
            with self.subTest(extra=extra):
                manifest["host_permissions"] = ["https://phishlens-api-ocvt.onrender.com/*", extra]
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                result = self.validate('<script src="js/popup.js"></script>')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must grant only", result.stderr)

    def test_package_identity_matches_archive_contents(self):
        source = Path(__file__).resolve().parents[1] / "package_extension.py"
        shutil.copyfile(source, self.root / "scripts/package_extension.py")
        manifest_path = self.extension / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = "0.1.0"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.validate('<script src="js/popup.js"></script>')
        result = subprocess.run([sys.executable, str(self.root / "scripts/package_extension.py")],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = self.root / "output/extension/PhishLens-Extension.zip"
        evidence = json.loads(archive.with_name("evidence.json").read_text())
        self.assertEqual(evidence["archive_sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
        with ZipFile(archive) as package:
            self.assertNotIn("evidence.json", package.namelist())
            self.assertEqual(set(evidence["files_sha256"]), set(package.namelist()))
            for name, digest in evidence["files_sha256"].items():
                self.assertEqual(hashlib.sha256(package.read(name)).hexdigest(), digest)
        self.assertEqual(evidence["chrome_acceptance"], "not performed by packaging")


if __name__ == "__main__":
    unittest.main()
