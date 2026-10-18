"""Observe existing automatic production delivery; no deploy, rollback or Git writes."""
import datetime as dt
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

from .github_api import GitHub

ROOT = Path(__file__).resolve().parents[2]


def timestamp(value):
    return dt.datetime.fromisoformat(value)


def pipeline_metrics(runs, jobs_by_run):
    # One workflow ID counted once; latest attempt only. Cancelled runs separate.
    unique = {}
    for run in runs:
        key = run["id"]
        if run.get("run_attempt", 1) >= unique.get(key, {}).get("run_attempt", 0):
            unique[key] = run
    periods = {"pr": [], "main": []}
    successes = failures = cancelled = pending = other = 0
    for run in unique.values():
        conclusion = run.get("conclusion")
        if run.get("status") != "completed":
            pending += 1
            continue
        if conclusion == "cancelled":
            cancelled += 1
            continue
        if conclusion == "success":
            successes += 1
        elif conclusion in {"failure", "timed_out", "action_required"}:
            failures += 1
        else:
            other += 1
            continue
        jobs = jobs_by_run.get(run["id"], [])
        ends = [timestamp(j["completed_at"]) for j in jobs if j.get("completed_at")]
        if not ends or not run.get("created_at"):
            continue
        seconds = (max(ends) - timestamp(run["created_at"])).total_seconds()
        if run["event"] == "pull_request":
            periods["pr"].append(seconds)
        elif run["event"] == "push" and run["head_branch"] == "main":
            periods["main"].append(seconds)
    return {"sample_workflows": len(unique), "successes": successes, "failures": failures,
            "cancelled": cancelled, "pending": pending, "other_conclusions": other,
            "success_rate_percent": round(100 * successes / (successes + failures), 2) if successes + failures else None,
            "average_pr_pipeline_seconds": sum(periods["pr"]) / len(periods["pr"]) if periods["pr"] else None,
            "average_main_pipeline_seconds": sum(periods["main"]) / len(periods["main"]) if periods["main"] else None,
            "pr_duration_samples": len(periods["pr"]), "main_duration_samples": len(periods["main"])}


def deployment_metrics(deploys, merged_at):
    unique = {d["id"]: d for d in deploys}
    live = [d for d in unique.values() if d.get("status") == "live" and d.get("finishedAt")]
    leads = [(timestamp(d["finishedAt"]) - timestamp(merged_at[d["commit"]["id"]])).total_seconds()
             for d in live if d.get("commit", {}).get("id") in merged_at
             and timestamp(d["finishedAt"]) >= timestamp(merged_at[d["commit"]["id"]])]
    return {"observed_live_deployments": len(live),
            "failed_deployments": sum(d.get("status") in {"build_failed", "update_failed", "pre_deploy_failed"} for d in unique.values()),
            "average_merge_to_render_live_seconds": sum(leads) / len(leads) if leads else None,
            "merge_to_live_samples": len(leads), "recovery_time": None,
            "limitation": "Render status is a bounded snapshot; historical deactivated successful deploys are not counted as live. Recovery requires incident timestamps. Render-live lead time is not independently verified application availability."}


def deployment_record(deploy):
    return {"id": deploy["id"], "status": deploy["status"], "sha": deploy.get("commit", {}).get("id"),
            **{key: deploy.get(key) for key in ("createdAt", "startedAt", "finishedAt", "trigger")}}


def log_categories(logs):
    """Expose category counts only. Raw log text may contain private mail or secrets."""
    patterns = {"out_of_memory": r"out of memory|oom|memory limit", "missing_dependency": r"modulenotfound|no module named",
                "database_connectivity": r"connection refused|operationalerror|database.*unavailable",
                "port_binding": r"address already in use|no open ports|port.*bind",
                "migration": r"alembic|migration"}
    counts = {name: 0 for name in patterns}
    for entry in logs:
        text = str(entry.get("message", ""))
        for name, pattern in patterns.items():
            counts[name] += bool(re.search(pattern, text, re.IGNORECASE))
    return {"sampled_log_entries": len(logs), "categories": counts,
            "meaning": "Possible signatures only, not confirmed root causes. Raw log text intentionally not retained."}


def main():
    api = GitHub()
    config = json.loads((ROOT / ".github/secretary.json").read_text())
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    triggered = event.get("workflow_run")
    output = ROOT / "output/secretary-production"
    output.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.UTC)
    cutoff = now - dt.timedelta(days=28)
    result = {"period_start": cutoff.isoformat(), "period_end": now.isoformat(), "production": "not available"}
    error = None
    service = config["production_service"]

    def render_get(path):
        key = os.environ.get("RENDER_OBSERVER_API_KEY")
        if not key:
            raise RuntimeError("Production observer key not configured; automatic deployment is unchanged")
        req = urllib.request.Request("https://api.render.com/v1/" + path, headers={"Authorization": "Bearer " + key})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except Exception:  # noqa: BLE001 -- never expose upstream credential/error bodies
            raise RuntimeError("Render observation unavailable; no deployment/rollback attempted") from None

    try:
        runs = api.pages("actions/workflows/ci.yml/runs?created=%3E%3D" + cutoff.strftime("%Y-%m-%d"), "workflow_runs", maximum=10)
        jobs = {r["id"]: api.pages(f"actions/runs/{r['id']}/attempts/{r.get('run_attempt', 1)}/jobs", "jobs") for r in runs}
        result["pipeline"] = pipeline_metrics(runs, jobs)
        result["workflow_sources"] = [r["html_url"] for r in runs]
        if triggered and triggered.get("conclusion") != "success":
            raise RuntimeError("Main CI failed; production must not deploy this revision. Inspect CI before any recovery action")
        sha = triggered["head_sha"] if triggered else api.request("commits/main")["sha"]
        result["expected_sha"] = sha
        # Observe only the exact deployment; never substitute a newer/older successful revision.
        deadline = time.monotonic() + 900
        while True:
            rows = render_get(f"services/{service}/deploys?limit=100")
            deployments = [r["deploy"] for r in rows]
            result["deployments"] = deployment_metrics([d for d in deployments if timestamp(d["createdAt"]) >= cutoff], {})
            matches = [d for d in deployments if d.get("commit", {}).get("id") == sha]
            deploy = max(matches, key=lambda d: d["createdAt"]) if matches else None
            if deploy and deploy["status"] in {"build_failed", "update_failed", "pre_deploy_failed", "canceled"}:
                result["deployment"] = deployment_record(deploy)
                raise RuntimeError("Exact production deployment failed. Inspect linked Render logs; rollback remains a human decision")
            if deploy and deploy["status"] == "live":
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("No exact live production deployment within 15 minutes; check auto-deploy and CI settings")
            time.sleep(15)
        for path in ("/health", "/ready", "/version"):
            with urllib.request.urlopen(config["production_origin"] + path, timeout=30) as response:
                value = json.load(response)
            if path == "/version" and value.get("commit") != sha:
                raise RuntimeError("Production application SHA does not match the expected commit")
            if path == "/health" and value != {"status": "ok", "service": "phishlens-api"}:
                raise RuntimeError("Production health response mismatch")
            if path == "/ready" and value != {"status": "ready", "database": "connected"}:
                raise RuntimeError("Production database readiness mismatch")
        result["production"] = "verified exact SHA, health and readiness"
        result["verified_at"] = dt.datetime.now(dt.UTC).isoformat()
        result["deployment"] = deployment_record(deploy)
        closed = api.pages("pulls?state=closed&sort=updated&direction=desc", maximum=5)
        merged = {p["merge_commit_sha"]: p["merged_at"] for p in closed if p.get("merged_at")}
        window = [d for d in deployments if timestamp(d["createdAt"]) >= cutoff]
        result["deployments"] = deployment_metrics(window, merged)
    except Exception as exc:  # noqa: BLE001 -- preserve a redacted incident artifact on failure
        error = str(exc) if isinstance(exc, RuntimeError) else "Evidence collection failed; inspect workflow and service logs privately"
        result["error"] = error
        result["recovery_time"] = None
        try:
            owner = render_get("services/" + service)["ownerId"]
            query = urlencode({"ownerId": owner, "resource": service, "limit": 50,
                               "startTime": (now - dt.timedelta(hours=1)).isoformat()})
            result["log_evidence"] = log_categories(render_get("logs?" + query).get("logs", []))
            result["log_dashboard"] = "https://dashboard.render.com/web/" + service + "/logs"
        except Exception:  # noqa: BLE001 -- preserve the original failure when logs are unavailable
            result["log_evidence"] = "not available"
        (output / "incident-draft.md").write_text("# Incident draft — human completion required\n\nConfirmed observation: " + error +
            "\n\nImpact: not established. Root cause: not established. Recovery time: not available.\n\n"
            "Inspect failed CI/Render deployment logs privately; do not paste secrets. See metrics.json for bounded log-category counts if retrieval succeeded; categories are possible concerns, not root causes. Record incident start, affected SHA, last good release, mitigation, restored health/version and timestamps. Recommend rollback only after checking schema compatibility; a human executes it.\n")
    (output / "metrics.json").write_text(json.dumps(result, indent=2))
    with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a", encoding="utf-8") as summary:
        summary.write("## Production evidence\n\n" + result["production"] + "\n\n" + (error or "Exact-commit health verification completed.") +
                      "\n\nDownload Veriqo-Production-Evidence for metrics and sources; no rollback was performed.\n")
    if error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
