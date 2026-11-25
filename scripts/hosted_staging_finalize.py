"""Trusted, read-only post-deploy identity and Auth-bridge checks."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

from scripts.deploy_staging import live_pr_matches, requested_pr_identity
from scripts.secretary.github_api import APIError, ReadOnlyGitHub
from scripts.secretary.preview import smoke


def finalize() -> dict:
    number, source_sha = requested_pr_identity()
    deployed_sha = os.environ.get("STAGING_COMMIT", "").strip()
    origin = os.environ.get("STAGING_BASE_URL", "").rstrip("/")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    config = json.loads(Path(".github/secretary.json").read_text(encoding="utf-8"))
    if origin != config["staging_origin"]:
        raise RuntimeError("Hosted staging origin differs from the trusted allowlist")
    if deployed_sha != source_sha:
        raise RuntimeError("Deployed staging SHA differs from the source PR SHA")
    package_evidence_path = Path(os.environ.get("RELEASE_EXTENSION_EVIDENCE", ""))
    try:
        package_evidence = json.loads(package_evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise RuntimeError("Exact-SHA extension package evidence is unavailable") from None
    if package_evidence.get("source_commit") != source_sha:
        raise RuntimeError("Extension package does not match the current PR source SHA")
    extension_id = package_evidence.get("chrome_extension_id")
    if not isinstance(extension_id, str) or not extension_id:
        raise RuntimeError("Extension package identity is missing")

    api = ReadOnlyGitHub(repo=repository, token=os.environ.get("GITHUB_TOKEN", ""))

    def current() -> bool:
        try:
            pr = api.request(f"pulls/{number}")
        except APIError:
            raise RuntimeError("GitHub could not confirm the current PR head") from None
        return live_pr_matches(pr, number, source_sha, repository)

    def superseded() -> bool:
        if current():
            return False
        message = "PR closed, advanced, or lost staging eligibility during acceptance"
        print(f"Hosted staging stopped: {message}", file=sys.stderr)
        return True

    if superseded():
        raise RuntimeError("Stale PR head; staging acceptance stopped")

    evidence = smoke(origin, deployed_sha, report_auth_mode="neon")
    bridge_origin = origin
    extension_origin = "chrome-extension://" + extension_id

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, file_pointer, code, message, headers, new_url):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    bridge_checks = {}
    for path, expected_type in (
        ("/auth/bridge", "text/html"),
        ("/auth/bridge/client.js", "javascript"),
        ("/auth/bridge/sdk.mjs", "javascript"),
    ):
        request = urllib.request.Request(
            bridge_origin + path,
            headers={"Cache-Control": "no-cache"},
        )
        try:
            with opener.open(request, timeout=20) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                if response.status != 200 or response.geturl() != bridge_origin + path:
                    raise RuntimeError("unexpected response")
                if expected_type not in content_type:
                    raise RuntimeError("unexpected content type")
                if path == "/auth/bridge":
                    csp = response.headers.get("Content-Security-Policy", "")
                    if "frame-ancestors " + extension_origin not in csp:
                        raise RuntimeError("extension origin is not frame-allowed")
                    body = response.read(65537).decode("utf-8", errors="replace")
                    if len(body) > 65536 or f'data-extension-origin="{extension_origin}"' not in body:
                        raise RuntimeError("bridge document does not bind the expected extension")
                bridge_checks[path] = 200
        except Exception:  # noqa: BLE001 -- report only the bounded check result
            raise RuntimeError("Staging Auth bridge GET failed: " + path) from None

    if superseded():
        raise RuntimeError("Stale PR head; staging acceptance stopped")

    evidence.update({
        "pr": number,
        "sha": source_sha,
        "deployed_commit": deployed_sha,
        "migration_revision": os.environ.get("STAGING_MIGRATION_REVISION", ""),
        "auth_bridge": bridge_checks,
        "automated_checklist": {
            "read_only_preflight": {
                "result": "passed",
                "auth_bridge": "passed",
                "anonymous_saved_report": "authentication_required",
                "seeded_history": "not_checked",
                "application_crud_writes_performed": False,
            },
            "live_auth_acceptance": {"result": "pending"},
            "saved_report_crud": {"result": "pending"},
            "packaged_extension_browser": {
                "result": "pending",
                "source_commit": source_sha,
                "tested_commit": deployed_sha,
            },
        },
    })
    output = Path(os.environ.get("STAGING_PREFLIGHT_EVIDENCE", "output/hosted-staging/preflight.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Read-only exact-SHA preflight passed for PR #{number} at {source_sha}.")
    return evidence


if __name__ == "__main__":
    finalize()
