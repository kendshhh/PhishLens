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
        req = urllib.request.Request("https://api.github.com/repos/" + self.repo + "/" + path,
            data=json.dumps(data).encode() if data is not None else None,
            method=method or ("POST" if data is not None else "GET"),
            headers={"Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read(8_000_001)
                if len(raw) > 8_000_000:
                    raise APIError("GitHub response exceeds safe size")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
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
