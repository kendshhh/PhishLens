"""Offline asset capability tests; never contact GitHub or a deployment service."""
import base64
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from scripts.secretary.github_api import (
    APIError,
    GitHub,
    PinnedExtensionGitHub,
    ReadOnlyGitHub,
)
from scripts.secretary.preview import package

SHA = "a" * 40
ASSET = "vendor/ml/model.wasm"
PATH = "contents/extension/" + ASSET + "?ref=" + SHA
DATA = b"synthetic model"
DIGEST = hashlib.sha1(f"blob {len(DATA)}\0".encode() + DATA).hexdigest()


def reader():
    return PinnedExtensionGitHub("owner/repo", "synthetic", SHA, {ASSET: 100})


def metadata(**changes):
    value = {
        "type": "file",
        "path": "extension/" + ASSET,
        "size": len(DATA),
        "sha": DIGEST,
        "encoding": "base64",
        "content": base64.b64encode(DATA).decode(),
    }
    value.update(changes)
    return value


class PinnedExtensionReaderTests(unittest.TestCase):
    def test_inline_read_is_pinned_and_validates_digest(self):
        api = reader()
        with patch.object(GitHub, "request", return_value=metadata()) as network:
            self.assertEqual(api.request(PATH)["sha"], DIGEST)
        network.assert_called_once_with(api, PATH, method="GET")
        self.assertFalse(api.allow_public_fallback)

    def test_unapproved_paths_stop_before_network(self):
        paths = [
            "contents/extension/" + ASSET,
            PATH.replace(SHA, "b" * 40),
            PATH.replace(SHA, "main"),
            PATH + "&other=true",
            "contents/.env?ref=" + SHA,
            "contents/extension/../.env?ref=" + SHA,
            "contents/extension/%2e%2e/.env?ref=" + SHA,
            "contents/extension/other.js?ref=" + SHA,
            "git/blobs/" + DIGEST,
            "pulls/251",
            "deployments",
            "statuses/" + SHA,
        ]
        for path in paths:
            with self.subTest(path=path):
                api = reader()
                with patch.object(GitHub, "request") as network:
                    with self.assertRaises(APIError):
                        api.request(path)
                network.assert_not_called()

    def test_methods_and_payloads_stop_before_network(self):
        api = reader()
        with patch.object(GitHub, "request") as network:
            for method in ("POST", "PUT", "PATCH", "DELETE", "HEAD"):
                with self.subTest(method=method):
                    with self.assertRaises(APIError):
                        api.request(PATH, method=method)
            with self.assertRaises(APIError):
                api.request(PATH, data={}, method="GET")
        network.assert_not_called()

    def test_blob_requires_metadata_from_the_pinned_file(self):
        api = reader()
        blob = "git/blobs/" + DIGEST
        with patch.object(
            GitHub, "request", side_effect=[metadata(encoding="none"), metadata()]
        ):
            api.request(PATH)
            self.assertEqual(api.request(blob)["sha"], DIGEST)
        with patch.object(GitHub, "request") as network:
            with self.assertRaises(APIError):
                api.request("git/blobs/" + "b" * 40)
        network.assert_not_called()

    def test_invalid_metadata_or_content_is_rejected(self):
        cases = [
            {"type": "dir"},
            {"type": "symlink", "target": "../.env"},
            {"submodule_git_url": "https://example.test/repo"},
            {"path": "extension/other"},
            {"size": 101},
            {"size": -1},
            {"size": True},
            {"sha": "not-a-sha"},
            {"content": base64.b64encode(b"changed payload").decode()},
            {"encoding": "unsupported"},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                with patch.object(GitHub, "request", return_value=metadata(**changes)):
                    with self.assertRaises(APIError):
                        reader().request(PATH)

    def test_blob_response_cannot_change_identity(self):
        cases = [
            {"sha": "b" * 40},
            {"size": 1},
            {"content": ""},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                api = reader()
                with patch.object(
                    GitHub, "request", return_value=metadata(encoding="none")
                ):
                    api.request(PATH)
                with patch.object(
                    GitHub, "request", return_value=metadata(**changes)
                ):
                    with self.assertRaises(APIError):
                        api.request("git/blobs/" + DIGEST)

    def test_commit_must_be_full_sha(self):
        for sha in ("main", "a" * 39, SHA + "&other=true"):
            with self.subTest(sha=sha):
                with self.assertRaises(APIError):
                    PinnedExtensionGitHub("owner/repo", "synthetic", sha, {ASSET: 100})

    def test_original_pr_reader_remains_restricted(self):
        with patch.object(GitHub, "request") as network:
            with self.assertRaises(APIError):
                ReadOnlyGitHub("owner/repo", "synthetic").request(PATH)
        network.assert_not_called()

    def test_package_uses_scoped_reader_and_archive_records_the_source(self):
        root = Path(__file__).resolve().parents[2]
        seen = []

        def response(client, path, **kwargs):
            self.assertIsInstance(client, PinnedExtensionGitHub)
            self.assertEqual(kwargs, {"method": "GET"})
            self.assertTrue(path.startswith("contents/extension/"))
            self.assertTrue(path.endswith("?ref=" + SHA))
            relative = path.split("?", 1)[0].removeprefix("contents/")
            data = (root / relative).read_bytes()
            seen.append(path)
            return {
                "type": "file",
                "path": relative,
                "size": len(data),
                "sha": hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
                "encoding": "base64",
                "content": base64.b64encode(data).decode(),
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "extension.zip"
            with patch.object(GitHub, "request", side_effect=response):
                package(
                    ReadOnlyGitHub("owner/repo", "synthetic"),
                    SHA,
                    251,
                    {
                        "staging_origin": "https://phishlens-staging.onrender.com",
                        "production_origin": "https://phishlens-api-ocvt.onrender.com",
                    },
                    output,
                )
            self.assertTrue(seen)
            with ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn(SHA.encode(), archive.read("popup.html"))


if __name__ == "__main__":
    unittest.main()
