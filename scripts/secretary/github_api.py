"""Small bounded GitHub client. Never print request credentials or API error bodies."""
import json
import os
import urllib.error
import urllib.request


class APIError(RuntimeError):
    pass


class GitHub:
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
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(8_000_001)
                if len(raw) > 8_000_000:
                    raise APIError("GitHub response exceeds safe size")
                return json.loads(raw) if raw else None

        try:
            return read_response(req)
        except urllib.error.HTTPError as exc:
            # Public repository metadata can be read without a token. Retrying
            # avoids dropping evidence when the Actions token is denied.
            if exc.code == 403 and request_method == "GET" and data is None:
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

    def pages(self, path, key=None, maximum=30):
        rows = []
        for page in range(1, maximum + 1):
            result = self.request(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
            items = result[key] if key else result
            rows.extend(items)
            if len(items) < 100:
                return rows
        raise APIError("GitHub pagination limit reached; coverage incomplete")
