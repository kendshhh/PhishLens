"""Exercise packaged popup references without modifying real extension assets."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


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


if __name__ == "__main__":
    unittest.main()
