"""Small bounded GitHub client. Never print request credentials or API error bodies."""
import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

TRANSIENT_SERVER_ERRORS = {500, 502, 503, 504}
MAX_TRANSIENT_GET_ATTEMPTS = 3


class APIError(RuntimeError):
    pass


class GitHub:
    allow_public_fallback = True

    def __init__(self, repo=None, token=None):
        self.repo = repo or os.environ["GITHUB_REPOSITORY"]
        self.token = token or os.environ["GITHUB_TOKEN"]

    def request(self, path, data=None, method=None):
        url = "https://api.github.com/repos/" + self.repo + "/" + path
        request_method = method or ("POST" if data is not None else "GET")
        headers = {"Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"}
        req = urllib.request.Request(url,
            data=json.dumps(data).encode() if data is not None else None,
            method=request_method, headers=headers)

        def read_response(request):
            attempts = (
                MAX_TRANSIENT_GET_ATTEMPTS
                if request.get_method() == "GET" and request.data is None
                else 1
            )
            for attempt in range(attempts):
                try:
                    with urllib.request.urlopen(request, timeout=30) as response:
                        # A bounded ORT-WASM blob is ~28 MB before base64. Keep other
                        # GitHub API responses under the existing smaller limit.
                        maximum = 44_000_000 if path.startswith("git/blobs/") else 8_000_000
                        raw = response.read(maximum + 1)
                        if len(raw) > maximum:
                            raise APIError("GitHub response exceeds safe size")
                        return json.loads(raw) if raw else None
                except urllib.error.HTTPError as exc:
                    if exc.code not in TRANSIENT_SERVER_ERRORS or attempt + 1 == attempts:
                        raise
                    exc.close()
                    time.sleep(0.25 * (2 ** attempt))

        try:
            return read_response(req)
        except urllib.error.HTTPError as exc:
            # Public repository metadata can be read without a token. Retrying
            # avoids dropping evidence when the Actions token is denied.
            if (
                exc.code == 403
                and request_method == "GET"
                and data is None
                and self.allow_public_fallback
            ):
                public_req = urllib.request.Request(url, method="GET", headers={
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "Content-Type": "application/json",
                })
                try:
                    return read_response(public_req)
                except urllib.error.HTTPError as public_exc:
                    raise APIError(f"GitHub HTTP {public_exc.code} for {path.split('?')[0]}") from None
                except (urllib.error.URLError, TimeoutError):
                    raise APIError("GitHub connection unavailable") from None
            raise APIError(f"GitHub HTTP {exc.code} for {path.split('?')[0]}") from None
        except (urllib.error.URLError, TimeoutError):
            raise APIError("GitHub connection unavailable") from None

    def pages(self, path, key=None, maximum=30, per_page=100):
        if not isinstance(per_page, int) or not 1 <= per_page <= 100:
            raise ValueError("GitHub page size must be between 1 and 100")
        rows = []
        for page in range(1, maximum + 1):
            result = self.request(path + ("&" if "?" in path else "?") + f"per_page={per_page}&page={page}")
            items = result[key] if key else result
            rows.extend(items)
            if len(items) < per_page:
                return rows
        raise APIError("GitHub pagination limit reached; coverage incomplete")

    def pull_request_files(self, number):
        """List PR files in compact pages because REST rows include diff patches."""
        return self.pages(f"pulls/{number}/files", per_page=10)


class ReadOnlyGitHub(GitHub):
    """GitHub client for live PR reads, backed by a narrowly scoped token."""

    allow_public_fallback = False

    def __init__(self, repo=None, token=None):
        token = token if token is not None else os.getenv("SECRETARY_PR_READ_TOKEN", "")
        if not isinstance(token, str) or not token.strip():
            raise APIError("Dedicated read-only PR token is not configured")
        super().__init__(repo=repo, token=token)

    def request(self, path, data=None, method=None):
        request_method = method or ("POST" if data is not None else "GET")
        if data is not None or request_method.upper() != "GET":
            raise APIError("Read-only GitHub client permits GET requests only")
        if not re.fullmatch(r"pulls/[1-9][0-9]*", path):
            raise APIError("Read-only GitHub client permits live pull-request reads only")
        return super().request(path, method="GET")


class PinnedExtensionGitHub(ReadOnlyGitHub):
    """Read only allowlisted extension files at one commit and their proven blobs."""

    def __init__(self, repo, token, sha, asset_limits):
        super().__init__(repo=repo, token=token)
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise APIError("Extension source requires a full commit SHA")
        self._contents = {}
        self._blobs = {}
        for asset, limit in asset_limits.items():
            if (not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", asset)
                    or any(part in {".", ".."} for part in asset.split("/"))
                    or type(limit) is not int or limit <= 0):
                raise APIError("Invalid extension asset allowlist")
            path = "extension/" + asset
            self._contents["contents/" + path + "?ref=" + sha] = (path, limit)

    def request(self, path, data=None, method=None):
        request_method = method or ("POST" if data is not None else "GET")
        if data is not None or request_method.upper() != "GET":
            raise APIError("Read-only extension client permits GET requests only")
        asset = self._contents.get(path)
        blob_size = self._blobs.get(path)
        if asset is None and blob_size is None:
            raise APIError("Extension read is outside the pinned source allowlist")
        # Bypass the PR-only path policy, retaining GET-only requests, bounded
        # responses and disabled public-token fallback from this client.
        value = GitHub.request(self, path, method="GET")
        if not isinstance(value, dict):
            raise APIError("Invalid extension asset metadata")
        size, digest = value.get("size"), value.get("sha", "")
        if type(size) is not int or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{40}", digest):
            raise APIError("Invalid extension asset identity")
        if asset is not None:
            expected_path, limit = asset
            if (value.get("type") != "file" or value.get("path") != expected_path
                    or value.get("target") or value.get("submodule_git_url")
                    or not 0 <= size <= limit):
                raise APIError("Invalid extension asset metadata")
            # Blob capability comes only from a validated file in the pinned
            # commit, never from an arbitrary caller-supplied blob identifier.
            if value.get("encoding") == "none":
                self._blobs["git/blobs/" + digest] = size
            elif value.get("encoding") != "base64":
                raise APIError("Invalid extension asset encoding")
        elif size != blob_size or path != "git/blobs/" + digest or value.get("encoding") != "base64":
            raise APIError("Extension blob identity differs")
        if value.get("encoding") == "base64":
            try:
                content = base64.b64decode(value["content"])
            except (ValueError, TypeError, KeyError):
                raise APIError("Invalid extension asset encoding") from None
            if len(content) != size or hashlib.sha1(f"blob {size}\0".encode() + content).hexdigest() != digest:
                raise APIError("Extension asset digest differs")
        return value
