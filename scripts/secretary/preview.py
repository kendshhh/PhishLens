"""Trusted shared-staging controller. Never checks out, imports or executes PR code."""
import base64
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from .core import application_change
from .github_api import GitHub
from .report import latest_jobs

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ("manifest.json", "popup.html", "popup.js", "popup.css", "background.js",
          "css/popup.css", "js/config.js", "js/api.js", "js/history.js", "js/popup.js")


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
    if service.get("repo", "").rstrip("/") != "https://github.com/" + os.environ.get("GITHUB_REPOSITORY", "kendshhh/PhishLens"):
        raise RuntimeError("Staging repository mismatch")
    runtime = details.get("envSpecificDetails", {})
    if runtime.get("startCommand") != "python scripts/start_staging.py":
        raise RuntimeError("Unexpected staging startup command")


def verify_environment(rows):
    values = {row["envVar"]["key"]: row["envVar"]["value"] for row in rows}
    expected = os.getenv("SECRETARY_STAGING_DB_HOST", "")
    production = os.getenv("SECRETARY_PRODUCTION_DB_HOST", "")
    database = urlsplit(values.get("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://"))
    if not expected or not production or expected == production:
        raise RuntimeError("Declare distinct staging and production database hosts privately in environment variables")
    if database.hostname != expected or database.path != "/phishlens_dev" or values.get("STAGING_DATABASE_HOST") != expected:
        raise RuntimeError("Staging database host/name does not match the isolated allowlist")
    if values.get("APP_ENV") != "staging" or values.get("AI_MODE", "mock") != "mock":
        raise RuntimeError("Pilot requires APP_ENV=staging and AI_MODE=mock; no live provider costs")


def smoke(origin, sha):
    # No production writes and no live-provider inference. Retry startup only.
    deadline = time.monotonic() + 180
    while True:
        try:
            values = {}
            for path in ("/health", "/ready", "/version", "/api/analyses"):
                req = urllib.request.Request(origin + path, headers={"Cache-Control": "no-cache"})
                with urllib.request.urlopen(req, timeout=20) as response:
                    values[path] = json.load(response)
            assert values["/health"] == {"status": "ok", "service": "phishlens-api"}
            assert values["/ready"] == {"status": "ready", "database": "connected"}
            assert values["/version"]["commit"] == sha
            assert values["/version"]["environment"] == "staging"
            assert any(x["subject"] == "Synthetic account notice" for x in values["/api/analyses"]["items"])
            return {"health": "passed", "ready": "passed", "version": sha, "history": "passed", "ai": "not exercised"}
        except Exception:  # noqa: BLE001 -- bounded retry of startup/contract evidence
            if time.monotonic() >= deadline:
                raise RuntimeError("Staging smoke failed: health/readiness/version/seeded history not established") from None
            time.sleep(5)


def package(api, sha, number, config, output):
    files = {}
    for asset in ASSETS:
        value = api.request("contents/extension/" + asset + "?ref=" + sha)
        if value.get("encoding") != "base64" or value.get("size", 0) > 512000:
            raise RuntimeError("Extension asset missing, too large, or not a regular inline file")
        files[asset] = base64.b64decode(value["content"], validate=False)
    origin = config["staging_origin"]
    files["js/config.js"] = ("export const API_BASE_URL = " + json.dumps(origin) + ";\n").encode()
    worker = files["background.js"].decode()
    # Compatibility with main before PR #32: rewrite only the exact known localhost constant.
    worker = worker.replace('const API_URL = "http://127.0.0.1:8000";', "const API_URL = " + json.dumps(origin) + ";")
    if "127.0.0.1" in worker or "localhost" in worker or config["production_origin"] in worker:
        raise RuntimeError("Worker still references a non-staging backend; use shared configuration")
    if "API_BASE_URL" not in worker and origin not in worker:
        raise RuntimeError("Worker backend origin cannot be established")
    files["background.js"] = worker.encode()
    manifest = json.loads(files["manifest.json"])
    manifest["name"] = "Veriqo STAGING PR " + str(number)
    manifest["host_permissions"] = [origin + "/*"]
    if 'import { API_BASE_URL }' in worker:
        manifest["background"]["type"] = "module"
    files["manifest.json"] = json.dumps(manifest, indent=2).encode()
    banner = f'<div style="background:#fff0b3;color:#111;padding:10px;font:12px sans-serif">STAGING · PR #{number} · {html.escape(sha)} · Synthetic data only</div>'
    page = files["popup.html"].decode()
    page, count = re.subn(r"(<body\b[^>]*>)", lambda m: m[0] + banner, page, count=1, flags=re.IGNORECASE)
    if count != 1:
        raise RuntimeError("Cannot place staging banner in popup")
    files["popup.html"] = page.encode()
    files["preview-info.json"] = json.dumps({"pr": number, "sha": sha, "origin": origin}).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Invalid extension archive")


def eligibility(pr, files, run, repo):
    if not current_pr_head_matches(pr, run["head_sha"]):
        return "stale", "PR closed or newer head exists; old event ignored"
    if pr["draft"]:
        return "action_required", "Draft: mark ready for review to request staging"
    if pr["head"]["repo"]["full_name"] != repo:
        return "action_required", "Fork: reviewed work must be brought into a trusted branch; no preview secrets granted"
    if not application_change(files):
        return "success", "Preview not applicable: no application/runtime files changed"
    if run["conclusion"] != "success":
        return "failure", "CI did not succeed; staging not deployed"
    return "deploy", "CI passed; exact-head staging requested"


def current_pr_head_matches(pr, expected_head_sha):
    """Whether the open PR still matches the head captured by this CI run."""
    return (
        pr.get("state") == "open"
        and pr.get("head", {}).get("sha") == expected_head_sha
    )


def invalidate_previous(api, config, sha):
    """A displaced shared preview must not retain a green required staging check."""
    rows = api.request("deployments?environment=" + config["preview_environment"] + "&per_page=30")
    for row in rows:
        if row["sha"] == sha or row.get("creator", {}).get("login") != "github-actions[bot]":
            continue
        if not isinstance(row.get("payload"), dict) or row["payload"].get("secretary") != 1:
            continue
        checks = api.pages("commits/" + row["sha"] + "/check-runs?check_name=" + quote(config["preview_check"]) + "&filter=latest", "check_runs")
        for check in checks:
            if check.get("app", {}).get("slug") == "github-actions" and check.get("conclusion") == "success":
                api.request(f"check-runs/{check['id']}", {"status": "completed", "conclusion": "action_required",
                    "output": {"title": "Shared staging replaced", "summary": "Another PR is deploying. Rerun CI for this PR before manual testing; previous preview evidence is stale."}}, "PATCH")


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
    candidates = api.pages("pulls?state=open", maximum=2)
    assess = "--assess" in sys.argv
    if assess:
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("deploy=false\n")
    for candidate in candidates:
        pr = api.request(f"pulls/{candidate['number']}")
        if not current_pr_head_matches(pr, run["head_sha"]):
            continue
        files = api.pages(f"pulls/{pr['number']}/files")
        action, message = eligibility(pr, files, run, api.repo)
        if action == "deploy":
            jobs, latest = latest_jobs(api, run["head_sha"])
            if not latest or latest["id"] != run["id"] or latest.get("run_attempt", 1) != run.get("run_attempt", 1):
                continue  # An older completion must not override a newer CI attempt.
            if any(jobs.get(name, {}).get("conclusion") != "success" for name in config["required_ci_jobs"]):
                action, message = "failure", "Required CI jobs are missing, pending or unsuccessful"
            elif completed_event(api, config, run):
                print("Identical CI completion already has the current verified preview; no redeployment")
                continue
        if action == "stale":
            continue
        if assess and action == "deploy":
            with open(os.environ["GITHUB_OUTPUT"], "a") as output:
                output.write("deploy=true\n")
            continue
        check = api.request("check-runs", {"name": config["preview_check"], "head_sha": run["head_sha"], "status": "in_progress",
            "details_url": f"https://github.com/{api.repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"})
        deployment = None
        evidence = {"sha": run["head_sha"], "pr": pr["number"], "result": action}
        try:
            if action == "deploy":
                if not preview_gate_enabled():
                    raise RuntimeError("Preview gate is off; SECRETARY_PREVIEW_ENABLED must resolve to true after trimming whitespace and case")
                # No PR scripts execute with this token/key. Render runs the PR with approved staging-only runtime data.
                verify_service(render_request("services/" + config["staging_service"]), config)
                # Read values only for validation. Never write environment values to logs/artifacts.
                verify_environment(render_request("services/" + config["staging_service"] + "/env-vars?limit=100"))
                invalidate_previous(api, config, run["head_sha"])
                deployment = api.request("deployments", {"ref": run["head_sha"], "environment": config["preview_environment"],
                    "auto_merge": False, "required_contexts": [], "production_environment": False, "transient_environment": True,
                    "description": f"PR #{pr['number']} exact-head staging", "payload": {"secretary": 1, "pr": pr["number"], "run_id": run["id"], "run_attempt": run.get("run_attempt", 1)}})
                log = f"https://github.com/{api.repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
                api.request(f"deployments/{deployment['id']}/statuses", {"state": "in_progress", "log_url": log, "auto_inactive": False})
                deployed = render_request(f"services/{config['staging_service']}/deploys", {"commitId": run["head_sha"]})
                evidence["render_deployment"] = deployed["id"]
                deadline = time.monotonic() + 900
                while True:
                    live = render_request(f"services/{config['staging_service']}/deploys/{deployed['id']}")
                    if live["status"] == "live":
                        if live.get("commit", {}).get("id") != run["head_sha"]:
                            raise RuntimeError("Render reported the wrong commit")
                        break
                    if live["status"] in {"build_failed", "update_failed", "pre_deploy_failed", "canceled", "deactivated"}:
                        raise RuntimeError("Render staging deployment failed: " + live["status"])
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Render staging deployment timed out")
                    time.sleep(10)
                evidence["smoke"] = smoke(config["staging_origin"], run["head_sha"])
                current = api.request(f"pulls/{pr['number']}")
                if not current_pr_head_matches(current, run["head_sha"]):
                    # The deployment worked, but it is no longer evidence for the current PR head.
                    action = "action_required"
                    message = "PR head advanced during staging; this run was superseded. The latest CI run must own staging."
                    api.request(f"deployments/{deployment['id']}/statuses", {"state": "success",
                        "description": "Deployment passed; PR head advanced, so this preview is superseded",
                        "log_url": log, "auto_inactive": False})
                else:
                    package(api, run["head_sha"], pr["number"], config, ROOT / "output/secretary/Veriqo-Staging-Extension.zip")
                    api.request(f"deployments/{deployment['id']}/statuses", {"state": "success", "log_url": log,
                        "environment_url": config["staging_origin"] + "/docs", "auto_inactive": True})
                    action, message = "success", "Exact commit live; health, readiness, version, seeded history and extension package passed. AI and Chrome manual testing not performed."
        except Exception as exc:  # noqa: BLE001 -- fail the exact-SHA check without exposing API bodies
            action = "failure"
            # Only controlled errors are exposed, not upstream exception bodies.
            message = str(exc) if isinstance(exc, RuntimeError) else "Preview controller failed; inspect trusted workflow and Render dashboard"
            if deployment:
                api.request(f"deployments/{deployment['id']}/statuses", {"state": "failure", "description": "Deployment or verification failed", "auto_inactive": False})
        finally:
            evidence.update({"result": action, "message": message, "recorded_at": dt.datetime.now(dt.UTC).isoformat()})
            output = ROOT / "output/secretary"
            output.mkdir(parents=True, exist_ok=True)
            (output / "preview-evidence.json").write_text(json.dumps(evidence, indent=2))
            api.request(f"check-runs/{check['id']}", {"status": "completed", "conclusion": action,
                "output": {"title": "Staging: " + action, "summary": message}}, "PATCH")
            with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a", encoding="utf-8") as out:
                out.write(f"## Preview PR #{pr['number']}\n\nSHA `{run['head_sha']}`\n\n{message}\n")
            if action == "failure":
                raise SystemExit(1)


if __name__ == "__main__":
    main()
