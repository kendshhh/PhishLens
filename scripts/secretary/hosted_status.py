"""Report non-runtime staging N/A and fail completed pre-staging CI errors.

For runtime PRs this mirror deliberately publishes no status: the trusted
controller is the sole writer, so a late pending result cannot overwrite its
final authenticated-acceptance result.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .core import application_change
from .github_api import GitHub
from .report import latest_jobs

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CI_JOBS = ("Backend checks", "Extension checks", "Staging integration")


def decision(pr, files, run, jobs, repository, config):
    """Return status and reason without treating a skipped runtime check as green."""
    if pr.get("state") != "open" or pr.get("head", {}).get("sha") != run.get("head_sha"):
        return "stale", "PR is closed or its head changed; this CI result is obsolete"
    if run.get("conclusion") != "success":
        return "failure", "CI did not complete successfully"
    missing = [
        name for name in REQUIRED_CI_JOBS
        if not isinstance(jobs.get(name), dict)
        or jobs[name].get("status") != "completed"
        or jobs[name].get("conclusion") != "success"
    ]
    if missing:
        return "failure", "Required CI jobs did not pass: " + ", ".join(missing)

    runtime = application_change(files)
    if not runtime:
        return "success", "Not applicable: no application/runtime changes; required CI passed"
    if pr.get("draft"):
        return "failure", "Runtime PR is draft; protected staging acceptance has not run"
    head_repo = (pr.get("head", {}).get("repo") or {}).get("full_name")
    if head_repo != repository:
        return "failure", "Fork runtime PR cannot receive staging credentials; bring reviewed work to a trusted branch"
    labels = {
        label.get("name") for label in pr.get("labels", [])
        if isinstance(label, dict) and isinstance(label.get("name"), str)
    }
    label = config.get("preview_opt_in_label")
    if not label or label not in labels:
        return "failure", "Runtime PR requires the needs-hosted-staging label and a fresh CI run"
    return "pending", "Waiting for the trusted controller to deploy and verify this exact PR head"


def publish_status(api, sha, context, state, description, target_url):
    if state not in {"pending", "success", "failure", "error"}:
        raise ValueError("Invalid required staging status")
    api.request("statuses/" + sha, {
        "state": state,
        "context": context,
        "description": description[:140],
        "target_url": target_url,
    })


def main():
    api = GitHub()
    config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    run = event.get("workflow_run")
    if not isinstance(run, dict) or run.get("event") != "pull_request":
        print("Not a completed pull-request CI run; ignored")
        return

    linked = run.get("pull_requests") or []
    numbers = sorted({row.get("number") for row in linked
                      if isinstance(row, dict) and isinstance(row.get("number"), int) and row["number"] > 0})
    if not numbers:
        numbers = sorted({row.get("number") for row in api.pages(
            "commits/" + run["head_sha"] + "/pulls", maximum=2
        ) if isinstance(row, dict) and isinstance(row.get("number"), int) and row["number"] > 0})

    log_url = str(run.get("html_url") or "")
    for number in numbers:
        pr = api.request(f"pulls/{number}")
        if pr.get("state") != "open" or pr.get("head", {}).get("sha") != run.get("head_sha"):
            continue

        jobs, latest = latest_jobs(api, run["head_sha"])
        if (not latest or latest.get("id") != run.get("id")
                or latest.get("run_attempt", 1) != run.get("run_attempt", 1)):
            print("Older CI completion ignored; the latest run owns this status")
            continue

        files = api.pull_request_files(number)
        state, message = decision(pr, files, run, jobs, api.repo, config)
        if state == "stale":
            continue
        if state == "pending":
            print("Runtime PR awaits the trusted controller; no competing status was published")
            continue
        target = log_url
        # Do not claim deployment, CRUD or AI proof in the description. The
        # authoritative evidence is the exact CI job and its uploaded artifact.
        publish_status(api, run["head_sha"], config["preview_check"], state, message, target)
        print(f"PR #{number}: {state}: {message}")


if __name__ == "__main__":
    main()
