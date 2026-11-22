"""Offline asset capability tests; never contact GitHub or a deployment service."""
import base64
import hashlib
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pytest

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
    value = {"type": "file", "path": "extension/" + ASSET, "size": len(DATA),
             "sha": DIGEST, "encoding": "base64", "content": base64.b64encode(DATA).decode()}
    value.update(changes)
    return value


def test_inline_read_is_pinned_and_validates_digest():
    api = reader()
    with patch.object(GitHub, "request", return_value=metadata()) as network:
        assert api.request(PATH)["sha"] == DIGEST
    network.assert_called_once_with(api, PATH, method="GET")
    assert api.allow_public_fallback is False


@pytest.mark.parametrize("path", [
    "contents/extension/" + ASSET, PATH.replace(SHA, "b" * 40),
    PATH.replace(SHA, "main"), PATH + "&other=true",
    "contents/.env?ref=" + SHA, "contents/extension/../.env?ref=" + SHA,
    "contents/extension/%2e%2e/.env?ref=" + SHA,
    "contents/extension/other.js?ref=" + SHA,
    "git/blobs/" + DIGEST, "pulls/251", "deployments", "statuses/" + SHA,
])
def test_unapproved_paths_stop_before_network(path):
    with patch.object(GitHub, "request") as network, pytest.raises(APIError):
        reader().request(path)
    network.assert_not_called()


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "HEAD"])
def test_methods_and_payloads_stop_before_network(method):
    api = reader()
    with patch.object(GitHub, "request") as network:
        with pytest.raises(APIError):
            api.request(PATH, method=method)
        with pytest.raises(APIError):
            api.request(PATH, data={}, method="GET")
    network.assert_not_called()


def test_blob_requires_metadata_from_the_pinned_file():
    api = reader()
    blob = "git/blobs/" + DIGEST
    with patch.object(GitHub, "request", side_effect=[metadata(encoding="none"), metadata()]):
        api.request(PATH)
        assert api.request(blob)["sha"] == DIGEST
    with patch.object(GitHub, "request") as network, pytest.raises(APIError):
        api.request("git/blobs/" + "b" * 40)
    network.assert_not_called()


@pytest.mark.parametrize("changes", [
    {"type": "dir"}, {"type": "symlink", "target": "../.env"},
    {"submodule_git_url": "https://example.test/repo"}, {"path": "extension/other"},
    {"size": 101}, {"size": -1}, {"size": True}, {"sha": "not-a-sha"},
    {"content": base64.b64encode(b"changed payload").decode()},
    {"encoding": "unsupported"},
])
def test_invalid_metadata_or_content_is_rejected(changes):
    with patch.object(GitHub, "request", return_value=metadata(**changes)), pytest.raises(APIError):
        reader().request(PATH)


@pytest.mark.parametrize("changes", [{"sha": "b" * 40}, {"size": 1}, {"content": ""}] )
def test_blob_response_cannot_change_identity(changes):
    api = reader()
    with patch.object(GitHub, "request", return_value=metadata(encoding="none")):
        api.request(PATH)
    with patch.object(GitHub, "request", return_value=metadata(**changes)), pytest.raises(APIError):
        api.request("git/blobs/" + DIGEST)


@pytest.mark.parametrize("sha", ["main", "a" * 39, SHA + "&other=true"])
def test_commit_must_be_full_sha(sha):
    with pytest.raises(APIError):
        PinnedExtensionGitHub("owner/repo", "synthetic", sha, {ASSET: 100})


def test_original_pr_reader_remains_restricted():
    with patch.object(GitHub, "request") as network, pytest.raises(APIError):
        ReadOnlyGitHub("owner/repo", "synthetic").request(PATH)
    network.assert_not_called()


def test_package_uses_scoped_reader_and_archive_records_the_source(tmp_path):
    root = Path(__file__).resolve().parents[2]
    seen = []
    def response(client, path, **kwargs):
        assert isinstance(client, PinnedExtensionGitHub)
        assert kwargs == {"method": "GET"}
        assert path.startswith("contents/extension/") and path.endswith("?ref=" + SHA)
        relative = path.split("?", 1)[0].removeprefix("contents/")
        data = (root / relative).read_bytes()
        seen.append(path)
        return {"type": "file", "path": relative, "size": len(data),
                "sha": hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
                "encoding": "base64", "content": base64.b64encode(data).decode()}
    output = tmp_path / "extension.zip"
    with patch.object(GitHub, "request", side_effect=response):
        package(ReadOnlyGitHub("owner/repo", "synthetic"), SHA, 251,
                {"staging_origin": "https://phishlens-staging.onrender.com",
                 "production_origin": "https://phishlens-api-ocvt.onrender.com"}, output)
    assert seen
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert SHA.encode() in archive.read("popup.html")
