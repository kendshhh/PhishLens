"""Check the generated preview ZIP against the real popup's static imports."""

import base64
import hashlib
import json
import posixpath
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from scripts.secretary.preview import package, read_extension_asset

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40
CONFIG = {
    "staging_origin": "https://phishlens-staging.onrender.com",
    "production_origin": "https://phishlens-api-ocvt.onrender.com",
}
# Static import declarations, side-effect imports and re-exports. Dynamic worker
# imports/assets are covered by the existing scanner allowlist, not this check.
IMPORTS = re.compile(
    r"^\s*(?:import\s+(?:[^;'\"]*?\bfrom\s+)?|"
    r"export\s+(?:\*|\{[^}]*\})\s+from\s+)['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)


def popup_modules(archive):
    names, visited, pending = set(archive.namelist()), set(), ["popup.js"]
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        if name not in names:
            raise AssertionError(f"Missing popup module: {name}")
        visited.add(name)
        if not name.endswith((".js", ".mjs")):
            continue
        for specifier in IMPORTS.findall(archive.read(name).decode()):
            if not specifier.startswith("."):
                raise AssertionError(f"Unbundled popup module: {specifier}")
            dependency = posixpath.normpath(
                posixpath.join(posixpath.dirname(name), specifier)
            )
            if dependency.startswith(("../", "/")):
                raise AssertionError("Module path escapes ZIP")
            pending.append(dependency)
    return visited


class PreviewNeonPackageTests(unittest.TestCase):
    def build(self, *, legacy=False):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        output = Path(directory.name) / "preview.zip"
        api = Mock()
        sdk = (ROOT / "extension/vendor/neon/sdk.mjs").read_bytes()
        sdk_sha = hashlib.sha1(f"blob {len(sdk)}\0".encode() + sdk).hexdigest()

        def read(endpoint):
            if endpoint == "git/blobs/" + sdk_sha:
                return {
                    "sha": sdk_sha,
                    "size": len(sdk),
                    "encoding": "base64",
                    "content": base64.b64encode(sdk).decode(),
                }
            self.assertTrue(endpoint.endswith("?ref=" + SHA))
            relative = endpoint.removeprefix("contents/extension/").split("?", 1)[0]
            if legacy and relative.startswith(
                ("js/neon-", "js/auth-config", "vendor/neon/")
            ):
                self.fail("Legacy account-only source must not require Neon assets")
            if relative == "vendor/neon/sdk.mjs":
                # Exercise GitHub's large-blob path, as well as the new inventory.
                return {"sha": sdk_sha, "size": len(sdk), "encoding": "none"}
            path = ROOT / "extension" / relative
            data = (
                path.read_bytes()
                if path.suffix in {".js", ".mjs", ".html", ".txt"}
                or relative == "manifest.json"
                else b"fixture runtime data"
            )
            if legacy and relative == "popup.js":
                data = (
                    b"import { initializeAccountPopup } from './js/account-popup.js';\n"
                )
            return {
                "size": len(data),
                "encoding": "base64",
                "content": base64.b64encode(data).decode(),
            }

        api.request.side_effect = read
        package(api, SHA, 168, CONFIG, output)
        return output, api, sdk_sha

    def test_real_popup_static_imports_resolve_in_generated_zip(self):
        output, api, sdk_sha = self.build()
        with ZipFile(output) as archive:
            modules = popup_modules(archive)
            for name in (
                "js/neon-integration.js",
                "js/neon-accounts.js",
                "js/auth-config.js",
                "vendor/neon/sdk.mjs",
            ):
                self.assertIn(name, modules)
                self.assertEqual(
                    archive.read(name), (ROOT / "extension" / name).read_bytes()
                )
            self.assertIn("vendor/neon/THIRD_PARTY_NOTICES.txt", archive.namelist())
            self.assertEqual(
                archive.read("vendor/neon/THIRD_PARTY_NOTICES.txt"),
                (ROOT / "extension/vendor/neon/THIRD_PARTY_NOTICES.txt").read_bytes(),
            )
            self.assertEqual(
                json.loads(archive.read("manifest.json"))["host_permissions"],
                [CONFIG["staging_origin"] + "/*"],
            )
            self.assertIn(b"AUTH_CONFIG = null", archive.read("js/auth-config.js"))
        api.request.assert_any_call("git/blobs/" + sdk_sha)

    def test_missing_config_integration_or_sdk_is_detected(self):
        output, _, _ = self.build()
        with ZipFile(output) as original:
            files = {name: original.read(name) for name in original.namelist()}
        for missing in (
            "js/auth-config.js",
            "js/neon-integration.js",
            "vendor/neon/sdk.mjs",
        ):
            with self.subTest(missing=missing):
                broken = output.with_name("broken.zip")
                with ZipFile(broken, "w") as archive:
                    for name, data in files.items():
                        if name != missing:
                            archive.writestr(name, data)
                with (
                    ZipFile(broken) as archive,
                    self.assertRaisesRegex(AssertionError, "Missing popup module"),
                ):
                    popup_modules(archive)

    def test_legacy_account_only_source_still_packages(self):
        output, _, _ = self.build(legacy=True)
        with ZipFile(output) as archive:
            self.assertIn("js/account-popup.js", popup_modules(archive))
            self.assertNotIn("vendor/neon/sdk.mjs", archive.namelist())

    def test_sdk_remains_size_bounded(self):
        api = Mock()
        api.request.return_value = {"size": 1_000_001, "encoding": "base64"}
        with self.assertRaisesRegex(RuntimeError, "too large"):
            read_extension_asset(api, SHA, "vendor/neon/sdk.mjs")


if __name__ == "__main__":
    unittest.main()
