"""Trusted shared-staging controller. Never checks out, imports or executes PR code."""
import base64
import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from .core import application_change
from .github_api import GitHub, PinnedExtensionGitHub, ReadOnlyGitHub
from .report import latest_jobs

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ("manifest.json", "popup.html", "popup.js", "popup.css", "background.js",
          "css/popup.css", "js/config.js", "js/api.js", "js/history.js", "js/popup.js")
ACCOUNT_UI_ASSETS = ("js/account-popup.js", "js/account-session.js", "js/account-ui.js")
NEON_AUTH_ASSETS = (
    "js/neon-bridge-client.js",
    "js/neon-integration.js", "js/neon-accounts.js", "js/auth-config.js",
    "vendor/neon/sdk.mjs", "vendor/neon/THIRD_PARTY_NOTICES.txt",
)
LOCAL_SCANNER_ASSETS = (
    "js/report-client.js", "js/report-workflow.js", "ai/contract.json",
    "ai/core.mjs", "ai/observations.mjs", "ai/local-analyzer.mjs",
    "ai/tfidf_v12a.json", "ai/ATTRIBUTION.md", "offscreen.html", "offscreen.js",
    "ai/judge-client.mjs", "ai/judge-contract.mjs", "ai/judge-worker.mjs",
    "ai/live-workflow.mjs", "ai/reevaluators.mjs", "ai/judge-assets.json",
    "ai/reevaluators/manifest.json", "ai/reevaluators/krr.json",
    "ai/reevaluators/lightgbm.json", "vendor/ml/transformers.min.js",
    "vendor/ml/structured-output.js", "vendor/ml/ort-wasm-simd-threaded.jsep.mjs",
    "vendor/ml/ort-wasm-simd-threaded.jsep.wasm",
    "vendor/ml/ort-wasm-simd-threaded.asyncify.mjs",
    "vendor/ml/ort-wasm-simd-threaded.asyncify.wasm",
    "vendor/ml/LICENSE-transformers.txt", "vendor/ml/LICENSE-structured-output.txt",
    "vendor/ml/LICENSE-onnxruntime.txt", "vendor/ml/LICENSE-Llama3.2.txt",
    "vendor/ml/THIRD_PARTY_NOTICES.md",
)
ASSET_SIZE_LIMITS = {
    "vendor/neon/sdk.mjs": 1_000_000,
    "ai/tfidf_v12a.json": 3_000_000,
    "ai/reevaluators/krr.json": 1_000_000,
    "vendor/ml/transformers.min.js": 1_000_000,
    "vendor/ml/ort-wasm-simd-threaded.asyncify.wasm": 32_000_000,
    "vendor/ml/ort-wasm-simd-threaded.jsep.wasm": 32_000_000,
}


def read_extension_asset(api, sha, asset):
    """Read one bounded asset from the exact source commit, verifying large blobs."""
    value = api.request("contents/extension/" + asset + "?ref=" + sha)
    limit = ASSET_SIZE_LIMITS.get(asset, 512_000)
    size = value.get("size", 0)
    if not isinstance(size, int) or not 0 <= size <= limit:
        raise RuntimeError("Extension asset missing, too large, or not a regular inline file")

    blob_sha = None
    if value.get("encoding") != "base64" and limit > 512_000:
        blob_sha = value.get("sha", "")
        if not re.fullmatch(r"[0-9a-f]{40}", blob_sha):
            raise RuntimeError("Invalid model blob identity")
        value = api.request("git/blobs/" + blob_sha)
        if value.get("sha") != blob_sha or value.get("size") != size:
            raise RuntimeError("Model blob identity differs")
    if value.get("encoding") != "base64":
        raise RuntimeError("Extension asset missing or not a regular inline file")

    data = base64.b64decode(value["content"], validate=False)
    if len(data) != size:
        raise RuntimeError("Extension asset size differs from metadata")
    if blob_sha and hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() != blob_sha:
        raise RuntimeError("Model blob digest differs")
    return data


def render_request(path, data=None):
    req = urllib.request.Request("https://api.render.com/v1/" + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": "Bearer " + os.environ["RENDER_STAGING_API_KEY"], "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except Exception:  # noqa: BLE001 -- redact upstream API errors at the credential boundary
        raise RuntimeError("Render API unavailable; inspect the service dashboard (no credential details logged)") from None


def verify_service(service, config):
    """Service ID alone is not sufficient: assert origin, repo, start command and auto-deploy."""
    details = service.get("serviceDetails", {})
    if service.get("id") != config["staging_service"] or service.get("id") == config["production_service"]:
        raise RuntimeError("Not the allowlisted staging service")
    if details.get("url", "").rstrip("/") != config["staging_origin"]:
        raise RuntimeError("Staging service origin mismatch")
    if service.get("autoDeploy") != "no":
        raise RuntimeError("Disable staging auto-deploy; only this serialized controller may deploy")
    expected_branch = config.get("staging_branch")
    if expected_branch and service.get("branch") != expected_branch:
        raise RuntimeError(
            f"Staging service must be linked to {expected_branch!r}; "
            "the old bootstrap branch can deploy code without the stamped migration."
        )
    if service.get("repo", "").rstrip("/") != "https://github.com/" + os.environ.get("GITHUB_REPOSITORY", "kendshhh/PhishLens"):
        raise RuntimeError("Staging repository mismatch")
    runtime = details.get("envSpecificDetails", {})
    if runtime.get("startCommand") != "python scripts/start_staging.py":
        raise RuntimeError("Unexpected staging startup command")


def normalize_neon_host(host):
    """Treat Neon pooled and direct endpoint names as the same branch host."""
    host = str(host or "").strip().rstrip(".").lower()
    return re.sub(r"-pooler(?=\.)", "", host)


def verify_environment(rows, *, require_authenticated=False):
    values = {row["envVar"]["key"]: row["envVar"]["value"] for row in rows}
    expected = os.getenv("SECRETARY_STAGING_DB_HOST", "")
    production = os.getenv("SECRETARY_PRODUCTION_DB_HOST", "")
    expected_host = normalize_neon_host(expected)
    production_host = normalize_neon_host(production)
    database = urlsplit(values.get("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://"))
    migration = urlsplit(values.get("STAGING_MIGRATION_DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://"))
    app_role = values.get("STAGING_APP_DATABASE_ROLE", "")
    if not expected_host or not production_host or expected_host == production_host:
        raise RuntimeError("Declare distinct staging and production database hosts privately in environment variables")
    if (normalize_neon_host(database.hostname) != expected_host
            or database.path != "/phishlens_dev"
            or normalize_neon_host(values.get("STAGING_DATABASE_HOST")) != expected_host):
        raise RuntimeError("Staging database host/name does not match the isolated allowlist")
    if database.username != app_role or app_role != "phishlens_staging_app":
        raise RuntimeError("Staging runtime must use the phishlens_staging_app role")
    if (normalize_neon_host(migration.hostname) != expected_host
            or migration.path != "/phishlens_dev"
            or migration.username != "neondb_owner"):
        raise RuntimeError("Staging migration credential must target the isolated branch with the owner role")
    if migration.username == database.username:
        raise RuntimeError("Staging migration and runtime credentials must use separate roles")
    if values.get("APP_ENV") != "staging" or values.get("AI_MODE", "mock") not in {"mock", "tfidf"}:
        raise RuntimeError("Pilot requires APP_ENV=staging and AI_MODE=mock or tfidf; external providers are blocked")
    report_auth_mode = values.get("REPORT_AUTH_MODE", "demo")
    if report_auth_mode not in {"demo", "neon"}:
        raise RuntimeError("Staging report authentication must use demo or neon mode")
    if require_authenticated and report_auth_mode != "neon":
        raise RuntimeError(
            "Hosted staging requires explicit REPORT_AUTH_MODE=neon; demo mode "
            "cannot satisfy authenticated acceptance"
        )
    if require_authenticated:
        expected_auth_url = os.getenv("STAGING_AUTH_URL", "").strip().rstrip("/")
        expected_auth_database = os.getenv("STAGING_AUTH_DATABASE", "").strip()
        configured_auth_url = values.get("NEON_AUTH_BASE_URL", "").strip().rstrip("/")
        parsed_auth_url = urlsplit(expected_auth_url)
        if (
            not expected_auth_database
            or parsed_auth_url.scheme != "https"
            or not parsed_auth_url.hostname
            or parsed_auth_url.username
            or parsed_auth_url.password
            or parsed_auth_url.port is not None
            or parsed_auth_url.query
            or parsed_auth_url.fragment
            or ".neonauth." not in parsed_auth_url.hostname
            or not parsed_auth_url.hostname.endswith(".aws.neon.tech")
            or parsed_auth_url.path != f"/{expected_auth_database}/auth"
        ):
            raise RuntimeError("Hosted staging requires a valid isolated Neon Auth URL and database")
        if configured_auth_url != expected_auth_url:
            raise RuntimeError(
                "Render staging Neon Auth URL does not match the isolated staging branch"
            )
    return report_auth_mode


def smoke(origin, sha, *, report_auth_mode="demo"):
    # No production writes and no live-provider inference. Retry startup only.
    uses_neon = report_auth_mode == "neon"
    paths = ("/health", "/ready", "/version")
    if not uses_neon:
        paths += ("/api/analyses",)
    deadline = time.monotonic() + 180
    while True:
        try:
            values = {}
            for path in paths:
                req = urllib.request.Request(origin + path, headers={"Cache-Control": "no-cache"})
                with urllib.request.urlopen(req, timeout=20) as response:
                    values[path] = json.load(response)
            assert values["/health"] == {"status": "ok", "service": "phishlens-api"}
            assert values["/ready"] == {"status": "ready", "database": "connected"}
            assert values["/version"]["commit"] == sha
            assert values["/version"]["environment"] == "staging"
            if not uses_neon:
                assert any(x["subject"] == "Synthetic account notice" for x in values["/api/analyses"]["items"])
            break
        except Exception:  # noqa: BLE001 -- bounded retry of startup/contract evidence
            if time.monotonic() >= deadline:
                required = "health/readiness/version" if uses_neon else "health/readiness/version/seeded history"
                raise RuntimeError(f"Staging smoke failed: {required} not established") from None
            time.sleep(5)

    evidence = {"health": "passed", "ready": "passed", "version": sha, "history": "passed"}
    if uses_neon:
        url = origin + "/api/analyses"
        request = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
        try:
            with urllib.request.urlopen(request, timeout=20):
                raise RuntimeError("Neon staging did not reject an anonymous saved-report request")
        except urllib.error.HTTPError as exc:
            with exc:
                challenge = exc.headers.get("WWW-Authenticate", "").lower()
                if exc.code != 401 or exc.geturl() != url or challenge != "bearer":
                    raise RuntimeError("Neon staging did not return the expected saved-report authentication challenge") from None
        evidence["history"] = "authentication_required"
        evidence["seeded_history"] = "not_checked"
        evidence["anonymous_saved_report"] = {
            "path": "/api/analyses",
            "status_code": 401,
            "challenge": "Bearer",
            "redirected": False,
        }
    return evidence


def verify_saved_report(origin, sha):
    """Verify exact-staging CRUD/provenance; preserve whether its provider is mock."""
    command = [
        "node", str(ROOT / "scripts/verify_crud.mjs"),
        "--base-url", origin, "--environment", "staging",
        "--expected-sha", sha, "--allow-writes",
    ]
    try:
        completed = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=180
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Synthetic saved-report verification could not complete") from exc
    if completed.returncode != 0:
        raise RuntimeError("Synthetic saved-report AI/CRUD verification failed")
    try:
        result = json.loads(completed.stdout)
        provenance = result["analysisProvenance"]
        passed = result.get("result") == "passed" and result.get("cleanedUp") is True
        analysis_mode = result.get("analysisMode")
        provider_mode = provenance.get("providerMode")
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
        raise RuntimeError("Synthetic saved-report verification returned invalid evidence") from exc
    if not passed:
        raise RuntimeError("Synthetic saved-report verification did not confirm cleanup and provider mode")
    valid_provenance = (
        analysis_mode == "mock" and provider_mode == "mock"
    ) or (
        analysis_mode == "real" and provider_mode in {"gemini", "local", "tfidf"}
    )
    if not valid_provenance:
        raise RuntimeError("Synthetic saved-report verification returned inconsistent AI provenance")
    return result


def package(api, sha, number, config, output):
    if isinstance(api, ReadOnlyGitHub):
        api = PinnedExtensionGitHub(
            repo=api.repo, token=api.token, sha=sha,
            asset_limits={asset: ASSET_SIZE_LIMITS.get(asset, 512_000)
                          for asset in ASSETS + ACCOUNT_UI_ASSETS + NEON_AUTH_ASSETS + LOCAL_SCANNER_ASSETS},
        )
    files = {asset: read_extension_asset(api, sha, asset) for asset in ASSETS}
    worker = files["background.js"].decode()
    local_scanner = bool(re.search(
        r"from\s+['\"]\./ai/(?:local-analyzer|live-workflow)\.mjs['\"]", worker
    ))
    if local_scanner:
        for asset in LOCAL_SCANNER_ASSETS:
            files[asset] = read_extension_asset(api, sha, asset)
    if b"./js/account-popup.js" in files["popup.js"]:
        for asset in ACCOUNT_UI_ASSETS:
            files[asset] = read_extension_asset(api, sha, asset)
    # Decorative side-panel companion; present in sources after the sidebar redesign.
    if b"./js/ghost.js" in files["popup.js"]:
        files["js/ghost.js"] = read_extension_asset(api, sha, "js/ghost.js")
    if any(marker in files["popup.js"] for marker in (b"./js/neon-integration.js", b"./js/auth-config.js")):
        for asset in NEON_AUTH_ASSETS:
            files[asset] = read_extension_asset(api, sha, asset)

    origin = config["staging_origin"]
    files["js/config.js"] = ("export const API_BASE_URL = " + json.dumps(origin) + ";\n").encode()
    # Compatibility with main before PR #32: rewrite only the exact known localhost constant.
    worker = worker.replace('const API_URL = "http://127.0.0.1:8000";', "const API_URL = " + json.dumps(origin) + ";")
    if "127.0.0.1" in worker or "localhost" in worker or config["production_origin"] in worker:
        raise RuntimeError("Worker still references a non-staging backend; use shared configuration")
    if "API_BASE_URL" not in worker and origin not in worker and not local_scanner:
        raise RuntimeError("Worker backend origin cannot be established")
    if local_scanner and b"API_BASE_URL" not in files["js/popup.js"]:
        raise RuntimeError("Saved-report backend origin cannot be established")
    files["background.js"] = worker.encode()
    manifest = json.loads(files["manifest.json"])
    manifest["name"] = "Veriqo STAGING PR " + str(number)
    manifest["host_permissions"] = [origin + "/*"]
    if 'import { API_BASE_URL }' in worker:
        manifest["background"]["type"] = "module"
    files["manifest.json"] = json.dumps(manifest, indent=2).encode()
    package_label = "PARTIAL · Local Llama weights excluded · " if local_scanner else ""
    banner = f'<div style="background:#fff0b3;color:#111;padding:10px;font:12px sans-serif">{package_label}STAGING · PR #{number} · {html.escape(sha)} · Synthetic data only</div>'
    page = files["popup.html"].decode()
    page, count = re.subn(r"(<body\b[^>]*>)", lambda m: m[0] + banner, page, count=1, flags=re.IGNORECASE)
    if count != 1:
        raise RuntimeError("Cannot place staging banner in popup")
    files["popup.html"] = page.encode()
    preview_info = {"pr": number, "sha": sha, "origin": origin}
    if local_scanner:
        # The source-commit package cannot contain ignored model weights; expose that limit in the artifact.
        preview_info.update({
            "package_status": "partial",
            "includes_local_llama_weights": False,
            "excluded_assets": ["model-assets/llama/"],
            "reason": (
                "Pinned Llama weights are Git-ignored and are not included by the trusted "
                "source-commit allowlist. Remote model downloads are disabled, so offline "
                "Llama inference is unavailable in this preview."
            ),
            "full_local_package": (
                "Provision with npm run phishlens -- setup-models --download, then run "
                "python scripts/package_extension.py --include-models."
            ),
            "documentation": "docs/ai/live-workflow.md",
        })
        files["STAGING_PACKAGE_NOTICE.txt"] = (
            b"PARTIAL STAGING PACKAGE\\n\\n"
            b"This trusted preview includes local scanner/judge code and runtime assets, "
            b"but omits the pinned Llama weights under model-assets/llama/. Those weights "
            b"are Git-ignored and are not available from the PR source commit used by the "
            b"staging controller. Remote model downloads are disabled, so offline Llama "
            b"inference is unavailable in this artifact. The preview validates tracked "
            b"asset packaging and staging saved-report/API-origin wiring; it does not "
            b"verify offline Llama inference.\\n\\n"
            b"To build a full local package, provision the pinned weights once with "
            b"npm run phishlens -- setup-models --download, then run "
            b"python scripts/package_extension.py --include-models. See "
            b"docs/ai/live-workflow.md.\\n"
        )
    files["preview-info.json"] = json.dumps(preview_info).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Invalid extension archive")
    # GitHub's artifact digest covers the enclosing upload archive, not this inner ZIP.
    # Publish a conventional sidecar so acceptance reviewers can verify the ZIP itself.
    package_digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{package_digest}  {output.name}\n", encoding="ascii"
    )


def eligibility(pr, files, run, repo, opt_in_label=None):
    if not current_pr_head_matches(pr, run["head_sha"]):
        return "stale", "PR closed or newer head exists; old event ignored"
    if pr["draft"]:
        return "action_required", "Draft: mark ready for review to request staging"
    if pr["head"]["repo"]["full_name"] != repo:
        return "action_required", "Fork: reviewed work must be brought into a trusted branch; no preview secrets granted"
    if not application_change(files):
        return "success", "Preview not applicable: no application/runtime files changed"
    if not opt_in_label:
        return "failure", "Hosted staging request label is not configured"
    labels = {label.get("name") for label in pr.get("labels", []) if isinstance(label, dict)}
    if opt_in_label not in labels:
        return "failure", (
            "Application/runtime changes require the `" + opt_in_label
            + "` label and an exact-head hosted staging verification. Add the label "
            "and rerun CI for this PR head."
        )
    if run["conclusion"] != "success":
        return "failure", "CI did not succeed; staging not deployed"
    return "deploy", "CI passed; exact-head staging requested"


def current_pr_head_matches(pr, expected_head_sha):
    """Whether the open PR still matches the head captured by this CI run."""
    return (
        pr.get("state") == "open"
        and pr.get("head", {}).get("sha") == expected_head_sha
    )


def workflow_pr_identity(run, requested_number, requested_head_sha):
    """Bind controller inputs to the exact PR identity captured by workflow_run."""
    if not isinstance(requested_number, str) or not re.fullmatch(r"[1-9][0-9]*", requested_number):
        raise RuntimeError("Trusted workflow did not provide a valid PR number")
    if not isinstance(requested_head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", requested_head_sha):
        raise RuntimeError("Trusted workflow did not provide a valid PR head SHA")
    number = int(requested_number)
    if run.get("head_sha") != requested_head_sha:
        raise RuntimeError("Requested staging SHA differs from the completed PR CI head")
    linked = run.get("pull_requests") or []
    if not any(
        isinstance(row, dict)
        and row.get("number") == number
        and isinstance(row.get("head"), dict)
        and row["head"].get("sha") == requested_head_sha
        for row in linked
    ):
        raise RuntimeError("Requested PR and head are not associated with this workflow run")
    return number, requested_head_sha


def require_live_pr_eligibility(api, number, sha, files, run, repo, opt_in_label):
    """Fail closed unless the live PR still qualifies for this exact deployment."""
    current = api.request(f"pulls/{number}")
    if current.get("number") != number or not current_pr_head_matches(current, sha):
        raise RuntimeError("Live PR state or head changed; staging deployment was not started")
    action, _message = eligibility(current, files, run, repo, opt_in_label)
    if action != "deploy":
        raise RuntimeError("Live PR is no longer eligible for staging; deployment was not started")
    return current


def preview_check_run_name(config):
    """Keep detailed evidence separate from the required commit-status context."""
    return config["preview_check"] + " verification"


def publish_preview_status(api, sha, config, state, description, target_url=None):
    """Publish the required check as a commit status on the exact PR head SHA."""
    if state not in {"pending", "success", "failure", "error"}:
        raise ValueError("Invalid Secretary staging status")
    payload = {
        "state": state,
        "context": config["preview_check"],
        "description": description[:140],
    }
    if target_url:
        payload["target_url"] = target_url
    api.request("statuses/" + sha, payload)


def invalidate_previous(api, config, sha):
    """A displaced shared preview must not retain a green required staging check."""
    rows = api.request("deployments?environment=" + config["preview_environment"] + "&per_page=30")
    for row in rows:
        if row["sha"] == sha or row.get("creator", {}).get("login") != "github-actions[bot]":
            continue
        if not isinstance(row.get("payload"), dict) or row["payload"].get("secretary") != 1:
            continue
        publish_preview_status(
            api, row["sha"], config, "failure",
            "Shared staging changed; rerun CI for current preview",
        )
        names = {config["preview_check"], preview_check_run_name(config)}
        for name in names:
            checks = api.pages(
                "commits/" + row["sha"] + "/check-runs?check_name=" + quote(name) + "&filter=latest",
                "check_runs",
            )
            for check in checks:
                if check.get("app", {}).get("slug") == "github-actions" and check.get("conclusion") == "success":
                    api.request(f"check-runs/{check['id']}", {"status": "completed", "conclusion": "action_required",
                        "output": {"title": "Shared staging replaced", "summary": "Another PR successfully replaced shared staging. Rerun CI for this PR before using its automated evidence; previous preview evidence is stale."}}, "PATCH")


def confirm_live_deployment(api, config, live, expected_sha):
    """Invalidate earlier preview evidence only after Render confirms a live replacement."""
    if live.get("status") != "live":
        return False
    commit = live.get("commit")
    live_sha = commit.get("id") if isinstance(commit, dict) else None
    if not isinstance(live_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", live_sha):
        raise RuntimeError("Render reported the wrong commit")
    invalidate_previous(api, config, live_sha)
    if live_sha != expected_sha:
        raise RuntimeError("Render reported the wrong commit")
    return True


def completed_event(api, config, run):
    rows = api.request("deployments?environment=" + config["preview_environment"] + "&per_page=1")
    if not rows:
        return False
    row = rows[0]
    payload = row.get("payload") or {}
    if row.get("creator", {}).get("login") != "github-actions[bot]" or not isinstance(payload, dict):
        return False
    if row["sha"] != run["head_sha"] or payload.get("run_id") != run["id"] or payload.get("run_attempt") != run.get("run_attempt", 1):
        return False
    statuses = api.request(f"deployments/{row['id']}/statuses?per_page=1")
    return bool(statuses and statuses[0]["state"] == "success")


def preview_gate_enabled():
    """Parse the opt-in flag robustly across GitHub Actions variable formatting."""
    return os.getenv("SECRETARY_PREVIEW_ENABLED", "").strip().lower() == "true"


def main():
    api = GitHub()
    config = json.loads((ROOT / ".github/secretary.json").read_text())
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    run = event.get("workflow_run", {})
    if run.get("event") != "pull_request":
        print("Not a PR CI completion; ignored")
        return
    read_api = ReadOnlyGitHub(repo=api.repo)
    pr_number, staging_sha = workflow_pr_identity(
        run,
        os.getenv("SECRETARY_PR_NUMBER", ""),
        os.getenv("SECRETARY_PR_HEAD_SHA", ""),
    )
    assess = "--assess" in sys.argv
    if assess:
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("deploy=false\n")
    for number in (pr_number,):
        pr = read_api.request(f"pulls/{number}")
        if pr.get("number") != number or not current_pr_head_matches(pr, staging_sha):
            print("Live PR is closed or has advanced; this CI completion is stale")
            continue
        jobs, latest = latest_jobs(api, staging_sha)
        if (
            not latest
            or latest["id"] != run["id"]
            or latest.get("run_attempt", 1) != run.get("run_attempt", 1)
        ):
            print("Older CI completion ignored; a newer run or attempt exists")
            continue
        files = api.pull_request_files(pr["number"])
        action, message = eligibility(
            pr, files, run, api.repo, config.get("preview_opt_in_label")
        )
        log = f"https://github.com/{api.repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
        if action == "deploy":
            if any(jobs.get(name, {}).get("conclusion") != "success" for name in config["required_ci_jobs"]):
                action, message = "failure", "Required CI jobs are missing, pending or unsuccessful"
            elif not preview_gate_enabled():
                action, message = (
                    "action_required",
                    "Hosted staging is disabled. Set SECRETARY_PREVIEW_ENABLED=true, then rerun CI for this PR head.",
                )
            else:
                message = "Required CI jobs passed; exact-head staging requested"
                if completed_event(api, config, run):
                    publish_preview_status(
                        api, staging_sha, config, "success",
                        "Staging verification passed", log,
                    )
                    print("Identical CI completion already has the current verified preview; no redeployment")
                    continue
        if action == "stale":
            continue
        if assess:
            if action == "deploy":
                with open(os.environ["GITHUB_OUTPUT"], "a") as output:
                    output.write("deploy=true\n")
            else:
                state = "success" if action == "success" else "failure"
                publish_preview_status(api, staging_sha, config, state, message, log)
                print(message)
            continue
        publish_preview_status(
            api, staging_sha, config, "pending",
            "Staging verification running", log,
        )
        check = api.request("check-runs", {"name": preview_check_run_name(config), "head_sha": staging_sha, "status": "in_progress",
            "details_url": log})
        deployment = None
        evidence = {"sha": staging_sha, "pr": pr_number, "result": action}
        try:
            if action == "deploy":
                if not preview_gate_enabled():
                    raise RuntimeError("Preview gate is off; SECRETARY_PREVIEW_ENABLED must resolve to true after trimming whitespace and case")
                # No PR scripts execute with this token/key. Render runs the PR with approved staging-only runtime data.
                verify_service(render_request("services/" + config["staging_service"]), config)
                # Read values only for validation. Never write environment values to logs/artifacts.
                report_auth_mode = verify_environment(
                    render_request("services/" + config["staging_service"] + "/env-vars?limit=100"),
                    require_authenticated=True,
                )
                evidence["report_auth_mode"] = report_auth_mode
                # The queue may have waited while the PR changed; re-read its live state
                # immediately before creating the GitHub deployment or calling Render.
                require_live_pr_eligibility(
                    read_api, pr_number, staging_sha, files, run, api.repo,
                    config.get("preview_opt_in_label"),
                )
                deployment = api.request("deployments", {"ref": staging_sha, "environment": config["preview_environment"],
                    "auto_merge": False, "required_contexts": [], "production_environment": False, "transient_environment": True,
                    "description": f"PR #{pr_number} exact-head staging", "payload": {"secretary": 1, "pr": pr_number, "run_id": run["id"], "run_attempt": run.get("run_attempt", 1)}})
                log = f"https://github.com/{api.repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
                api.request(f"deployments/{deployment['id']}/statuses", {"state": "in_progress", "log_url": log, "auto_inactive": False})
                require_live_pr_eligibility(
                    read_api, pr_number, staging_sha, files, run, api.repo,
                    config.get("preview_opt_in_label"),
                )
                deployed = render_request(f"services/{config['staging_service']}/deploys", {"commitId": staging_sha})
                evidence["render_deployment"] = deployed["id"]
                deadline = time.monotonic() + 1200
                while True:
                    live = render_request(f"services/{config['staging_service']}/deploys/{deployed['id']}")
                    if live["status"] == "live":
                        confirm_live_deployment(api, config, live, staging_sha)
                        break
                    if live["status"] in {"build_failed", "update_failed", "pre_deploy_failed", "canceled", "deactivated"}:
                        raise RuntimeError("Render staging deployment failed: " + live["status"])
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Render staging deployment timed out")
                    time.sleep(10)
                evidence["smoke"] = smoke(config["staging_origin"], staging_sha, report_auth_mode=report_auth_mode)
                current = read_api.request(f"pulls/{pr_number}")
                if current.get("number") != pr_number or not current_pr_head_matches(current, staging_sha):
                    # The deployment worked, but it is no longer evidence for the current PR head.
                    action = "action_required"
                    message = "PR head advanced during staging; this run was superseded. The latest CI run must own staging."
                    state = "pending" if report_auth_mode == "neon" else "success"
                    api.request(f"deployments/{deployment['id']}/statuses", {"state": state,
                        "description": "Deployment passed; PR head advanced, so this preview is superseded",
                        "log_url": log, "auto_inactive": False})
                elif report_auth_mode == "neon":
                    action = "action_required"
                    evidence["preflight_passed"] = True
                    evidence["authenticated_saved_report"] = "pending"
                    evidence["live_auth_acceptance"] = "pending"
                    message = (
                        "- [x] Exact-head staging preflight verified health, readiness, version, and the anonymous saved-report `401` Bearer challenge.\n"
                        "- Seeded history was not checked in Neon mode.\n"
                        "- [ ] Authenticated saved-report history and CRUD remain pending. No CRUD or staging package was produced.\n"
                        "- [ ] Live Auth acceptance remains pending and requires a separately approved run."
                    )
                    api.request(f"deployments/{deployment['id']}/statuses", {"state": "pending",
                        "description": "Staging infrastructure verified; authenticated acceptance pending",
                        "log_url": log, "auto_inactive": False})
                else:
                    crud = verify_saved_report(config["staging_origin"], staging_sha)
                    evidence["saved_report_ai_crud"] = crud
                    evidence["packaged_browser_acceptance"] = {
                        "result": "passed",
                        "ci_run_id": run["id"],
                        "source_commit": staging_sha,
                        "artifact": "Extension-Browser-Acceptance",
                    }
                    current = read_api.request(f"pulls/{pr_number}")
                    if current.get("number") != pr_number or not current_pr_head_matches(current, staging_sha):
                        action = "action_required"
                        message = "PR head advanced during staging verification; the latest CI run must own staging."
                        api.request(f"deployments/{deployment['id']}/statuses", {"state": "success",
                            "description": "Verification passed; PR head advanced, so this preview is superseded",
                            "log_url": log, "auto_inactive": False})
                    else:
                        package(api, staging_sha, pr_number, config, ROOT / "output/secretary/Veriqo-Staging-Extension.zip")
                        description = (
                            f"secretary-crud=passed;analysis={crud['analysisMode']};"
                            f"provider={crud['analysisProvenance']['providerMode']};cleanup=confirmed"
                        )
                        api.request(f"deployments/{deployment['id']}/statuses", {"state": "success", "description": description, "log_url": log,
                            "environment_url": config["staging_origin"] + "/docs", "auto_inactive": True})
                        provider_mode = crud["analysisProvenance"]["providerMode"]
                        analysis_mode = crud["analysisMode"]
                        action = "success"
                        message = "- [x] Exact PR SHA live; health, readiness, version, and seeded history passed.\n"
                        message += f"- [x] Synthetic saved-report provenance and CRUD lifecycle passed (`{provider_mode}` provider); record cleaned up.\n"
                        if analysis_mode == "real":
                            message += f"- [x] Non-mock AI acceptance passed with `{provider_mode}`.\n"
                        else:
                            message += "- [ ] Real AI acceptance is not checked: staging used `mock`. Mock output is not AI acceptance.\n"
                        message += f"- [x] Packaged extension browser acceptance passed in CI run `{run['id']}`; see `Extension-Browser-Acceptance`."
        except Exception as exc:  # noqa: BLE001 -- fail the exact-SHA check without exposing API bodies
            action = "failure"
            # Only controlled errors are exposed, not upstream exception bodies.
            message = str(exc) if isinstance(exc, RuntimeError) else "Preview controller failed; inspect trusted workflow and Render dashboard"
            if deployment:
                api.request(f"deployments/{deployment['id']}/statuses", {"state": "failure", "description": "Deployment or verification failed", "auto_inactive": False})
        finally:
            auth_acceptance_pending = action == "action_required" and evidence.get("preflight_passed") is True
            # The required status records infrastructure preflight; the separate check run
            # remains action_required until Auth acceptance is independently approved.
            status_passed = action == "success" or auth_acceptance_pending
            status_state = "success" if status_passed else "failure"
            if auth_acceptance_pending:
                status_description = "Authenticated staging acceptance pending"
            else:
                status_description = (
                    "Staging verification passed"
                    if status_state == "success"
                    else "Staging verification did not pass"
                )
            evidence.update({
                "result": action,
                "required_status": status_state,
                "message": message,
                "recorded_at": dt.datetime.now(dt.UTC).isoformat(),
            })
            output = ROOT / "output/secretary"
            output.mkdir(parents=True, exist_ok=True)
            (output / "preview-evidence.json").write_text(json.dumps(evidence, indent=2))
            if auth_acceptance_pending:
                title = "Preflight passed; Auth acceptance pending"
            else:
                title = (
                    "Hosted staging not requested"
                    if action == "success" and message.startswith("Hosted staging not requested.")
                    else "Staging: " + action
                )
            api.request(f"check-runs/{check['id']}", {"status": "completed", "conclusion": action,
                "output": {"title": title, "summary": message}}, "PATCH")
            with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a", encoding="utf-8") as out:
                out.write(f"## Preview PR #{pr_number}\n\nSHA `{staging_sha}`\n\n{message}\n")
            publish_preview_status(
                api, staging_sha, config, status_state,
                status_description, log,
            )
            if action == "failure" or (action == "action_required" and not auth_acceptance_pending):
                print("Preview did not pass: " + message, file=sys.stderr)
                raise SystemExit(1)


if __name__ == "__main__":
    main()
