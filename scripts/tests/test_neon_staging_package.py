"""Offline import-closure check for the trusted staging archive."""
import base64
import json
import posixpath
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from scripts.secretary.preview import package

ROOT = Path(__file__).resolve().parents[2]
IMPORT = re.compile(r"(?:\bfrom\s*|\bimport\s*\(?\s*)['\"]([^'\"]+)['\"]")


class NeonStagingPackageTests(unittest.TestCase):
    def test_disabled_auth_popup_imports_resolve_in_generated_zip(self):
        sha = "a" * 40
        api = Mock()

        def read(path):
            asset, ref = path.removeprefix("contents/extension/").split("?ref=")
            self.assertEqual(ref, sha)
            data = (ROOT / "extension" / asset).read_bytes()
            return {"encoding": "base64", "size": len(data),
                    "content": base64.b64encode(data).decode()}

        api.request.side_effect = read
        config = json.loads((ROOT / ".github/secretary.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "staging.zip"
            package(api, sha, 168, config, output)
            with ZipFile(output) as archive:
                pending, seen = ["popup.js"], set()
                while pending:
                    module = pending.pop()
                    if module in seen:
                        continue
                    seen.add(module)
                    self.assertIn(module, archive.namelist(), f"Missing popup import: {module}")
                    source = archive.read(module).decode()
                    for specifier in IMPORT.findall(source):
                        if specifier.startswith("."):
                            target = posixpath.normpath(posixpath.join(posixpath.dirname(module), specifier))
                            self.assertFalse(target.startswith("../"))
                            pending.append(target)
                self.assertIn("js/neon-integration.js", seen)
                self.assertIn("js/neon-accounts.js", seen)
                self.assertIn("vendor/neon/sdk.mjs", seen)
                self.assertIn("vendor/neon/THIRD_PARTY_NOTICES.txt", archive.namelist())
                self.assertEqual(archive.read("js/auth-config.js"),
                                 (ROOT / "extension/js/auth-config.js").read_bytes())
                self.assertEqual(json.loads(archive.read("manifest.json"))["host_permissions"],
                                 [config["staging_origin"] + "/*"])


if __name__ == "__main__":
    unittest.main()
