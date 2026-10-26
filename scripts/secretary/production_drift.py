"""Read-only scheduled check for production health and main-commit drift."""
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

from .github_api import GitHub

ROOT = Path(__file__).resolve().parents[2]
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def fetch_json(url, attempts=3):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code < 500 or attempt == attempts - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts - 1:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("Production endpoint remained unavailable after retries")


def inspect_production(api, origin, get_json=fetch_json):
    findings = []
    try:
        expected_sha = api.request("commits/main").get("sha", "").lower()
        if not SHA_PATTERN.fullmatch(expected_sha):
            raise ValueError
    except Exception:  # noqa: BLE001 -- report a bounded diagnostic, never response bodies
        expected_sha = None
        findings.append("Could not read a valid current main SHA from GitHub.")

    observed = {}
    for path in ("/version", "/health", "/ready"):
        try:
            value = get_json(urljoin(origin.rstrip("/") + "/", path.lstrip("/")))
            if not isinstance(value, dict):
                raise TypeError
            observed[path] = value
        except Exception:  # noqa: BLE001 -- endpoint errors may contain private response data
            observed[path] = None
            findings.append(f"Production {path} could not be read as JSON.")

    version = observed["/version"]
    if version is not None and expected_sha is not None:
        deployed_sha = str(version.get("commit", "")).lower()
        if deployed_sha != expected_sha:
            findings.append("Production /version does not match the current main SHA.")

    health = observed["/health"]
    if health is not None and health != {"status": "ok", "service": "phishlens-api"}:
        findings.append("Production /health returned an unexpected response.")

    readiness = observed["/ready"]
    if readiness is not None and readiness != {"status": "ready", "database": "connected"}:
        findings.append("Production /ready returned an unexpected response.")

    return {"expected_sha": expected_sha, "observed": observed, "findings": findings}


def main():
    config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
    origin = config["production_origin"]
    result = inspect_production(GitHub(), origin)
    expected = result["expected_sha"] or "unavailable"
    observed_sha = (result["observed"].get("/version") or {}).get("commit", "unavailable")

    lines = ["## Production drift check", "", f"- GitHub main: `{expected}`",
             f"- Production: `{observed_sha}`"]
    lines.extend(f"- Finding: {finding}" for finding in result["findings"])
    if not result["findings"]:
        lines.append("- Production SHA, health, and readiness match the expected values.")
    report = "\n".join(lines) + "\n"
    print(report, end="")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write(report)
    if result["findings"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
