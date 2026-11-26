"""Wait for trusted staging prerequisites without exposing deploy credentials."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from .core import application_change
from .github_api import APIError, GitHub
from .report import latest_jobs

ROOT = Path(__file__).resolve().parents[2]
SHA40 = re.compile(r"[0-9a-f]{40}")


def _api():
    return GitHub(
        repo=os.environ.get("GITHUB_REPOSITORY"),
        token=os.environ.get("GITHUB_TOKEN", ""),
    )


def _identity():
    from scripts.deploy_staging import requested_pr_identity

    return requested_pr_identity()


def _source_run(event):
    run = event.get("workflow_run")
    if (not isinstance(run, dict) or run.get("event") != "pull_request"
            or not isinstance(run.get("head_sha"), str)
            or not SHA40.fullmatch(run["head_sha"])):
        raise SystemExit("Trusted staging requires a completed pull-request CI run.")
    return run


def _resolve_pr(api, event):
    run = _source_run(event)
    sha = run["head_sha"]
    linked = run.get("pull_requests") or []
    numbers = sorted({row.get("number") for row in linked
                      if isinstance(row, dict) and isinstance(row.get("number"), int)
                      and row["number"] > 0})
    if not numbers:
        numbers = sorted({row.get("number") for row in api.pages(
            f"commits/{sha}/pulls", maximum=2
        ) if isinstance(row, dict) and isinstance(row.get("number"), int)
             and row["number"] > 0})
    matches = []
    for number in numbers:
        pr = api.request(f"pulls/{number}")
        if pr.get("head", {}).get("sha") == sha:
            matches.append((number, pr))
    if len(matches) != 1:
        raise SystemExit("CI run does not resolve to exactly one current pull-request head.")
    number, pr = matches[0]
    return run, number, sha, pr


def _is_current_eligible_pr(api, pr, number, sha, repository, config):
    from scripts.deploy_staging import live_pr_matches

    return (
        live_pr_matches(pr, number, sha, repository)
        and pr.get("base", {}).get("ref") == config.get("base_branch", "main")
    )


def _is_current_pr(pr, number, sha, repository, config):
    return (
        isinstance(pr, dict)
        and pr.get("state") == "open"
        and pr.get("number") == number
        and pr.get("head", {}).get("sha") == sha
        and (pr.get("head", {}).get("repo") or {}).get("full_name") == repository
        and not pr.get("draft", False)
        and pr.get("base", {}).get("ref") == config.get("base_branch", "main")
    )


def _required_check_state(api, sha, required):
    rows = api.pages(f"commits/{sha}/check-runs", key="check_runs")
    by_context = {}
    for row in rows:
        if row.get("head_sha") != sha:
            continue
        name = row.get("name")
        app_id = (row.get("app") or {}).get("id")
        if not isinstance(name, str):
            continue
        by_context.setdefault((name, app_id), []).append(row)

    pending, failures = [], []
    for item in required:
        context, app_id = item["context"], item["app_id"]
        candidates = by_context.get((context, app_id), [])
        if not candidates:
            pending.append(context)
            continue
        latest = max(candidates, key=lambda row: (row.get("id", 0), row.get("started_at") or ""))
        status, conclusion = latest.get("status"), latest.get("conclusion")
        if status != "completed":
            pending.append(context)
        elif conclusion != "success":
            failures.append(f"{context}={conclusion or status}")
    return pending, failures


def wait_for_required_checks(*, timeout=1200, interval=20, api=None, sleep=time.sleep):
    """Wait for every required pre-deployment check on the exact current PR head."""
    api = api or _api()
    number, sha = _identity()
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    run, resolved_number, resolved_sha, pr = _resolve_pr(api, event)
    config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
    if (
        resolved_number != number
        or resolved_sha != sha
        or run.get("conclusion") != "success"
        or not _is_current_eligible_pr(api, pr, number, sha, repository, config)
    ):
        raise SystemExit("Trusted staging controller requires the exact current successful workflow_run PR head.")

    required = config.get("staging_predeployment_checks", [])
    if not required:
        raise SystemExit("No required pre-deployment check contract is configured.")

    deadline = time.monotonic() + timeout
    while True:
        try:
            live = api.request(f"pulls/{number}")
        except APIError:
            raise SystemExit("GitHub could not confirm the staging PR head; deployment blocked.") from None
        from scripts.deploy_staging import live_pr_matches

        if not live_pr_matches(live, number, sha, repository):
            raise SystemExit("PR state, source, label, draft state, or head changed; deployment blocked.")

        pending, failures = _required_check_state(api, sha, required)
        if failures:
            raise SystemExit("Required pre-deployment checks failed: " + ", ".join(failures))
        if not pending:
            print("All required pre-deployment checks passed for the current PR head: "
                  + ", ".join(item["context"] for item in required))
            return
        if time.monotonic() >= deadline:
            raise SystemExit("Required checks did not finish before the staging deployment timeout: "
                             + ", ".join(pending))
        print("Waiting for required checks on the exact PR head: " + ", ".join(pending), flush=True)
        sleep(interval)


def inspect_candidate(*, timeout=1200, interval=20, api=None, sleep=time.sleep):
    """Classify a completed CI run and require every pre-deploy check to pass."""
    api = api or _api()
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    run, number, sha, pr = _resolve_pr(api, event)
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))

    def output(key, value):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as result:
            result.write(f"{key}={value}\n")

    output("pr_number", number)
    output("source_sha", sha)
    output("ci_run_id", run.get("id", ""))
    if not _is_current_pr(pr, number, sha, repository, config):
        raise SystemExit("PR is closed, stale, a draft, from a fork, or does not target main.")

    _, latest = latest_jobs(api, sha)
    if (not latest or latest.get("id") != run.get("id")
            or latest.get("run_attempt", 1) != run.get("run_attempt", 1)):
        output("disposition", "blocked")
        raise SystemExit("A newer CI run owns this PR head; stale staging request ignored.")

    files = api.pull_request_files(number)
    if not application_change(files):
        output("disposition", "not-applicable")
        print("No application/runtime changes; hosted product acceptance is not applicable.")
        return

    labels = {label.get("name") for label in pr.get("labels", []) if isinstance(label, dict)}
    if config.get("preview_opt_in_label") not in labels:
        output("disposition", "blocked")
        raise SystemExit("Runtime PR needs the needs-hosted-staging label before staging can run.")
    if run.get("conclusion") != "success":
        output("disposition", "blocked")
        raise SystemExit("The source CI workflow did not complete successfully.")

    required = config.get("staging_predeployment_checks", [])
    if not required:
        raise SystemExit("No required pre-deployment check contract is configured.")
    deadline = time.monotonic() + timeout
    while True:
        try:
            current = api.request(f"pulls/{number}")
        except APIError:
            raise SystemExit("GitHub could not confirm the live PR; staging is blocked.") from None
        if not _is_current_eligible_pr(api, current, number, sha, repository, config):
            raise SystemExit("PR state, source, base, or staging eligibility changed; staging is blocked.")
        pending, failures = _required_check_state(api, sha, required)
        if failures:
            raise SystemExit("Required pre-deployment checks failed: " + ", ".join(failures))
        if not pending:
            output("disposition", "eligible")
            print("All pre-deployment checks passed on the exact current PR SHA: "
                  + ", ".join(item["context"] for item in required))
            return
        if time.monotonic() >= deadline:
            raise SystemExit("Required checks did not finish before the staging timeout: "
                             + ", ".join(pending))
        print("Waiting for required check results on exact PR SHA: " + ", ".join(pending), flush=True)
        sleep(interval)


def wait_for_exact_staging_sha(*, timeout=1200, interval=10, api=None, sleep=time.sleep):
    """Wait for the trusted controller to deploy the current PR SHA to staging."""
    api = api or _api()
    number, sha = _identity()
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    origin = os.environ.get("STAGING_BASE_URL", "").rstrip("/")
    if not origin.startswith("https://") or not SHA40.fullmatch(sha):
        raise SystemExit("Staging wait requires an HTTPS origin and full PR head SHA.")

    from scripts.deploy_staging import live_pr_matches

    deadline = time.monotonic() + timeout
    while True:
        try:
            live = api.request(f"pulls/{number}")
        except APIError:
            raise SystemExit("GitHub could not confirm the current PR head; acceptance blocked.") from None
        if not live_pr_matches(live, number, sha, repository):
            raise SystemExit("The PR is no longer the eligible current staging head.")
        request = urllib.request.Request(origin + "/version", headers={"Cache-Control": "no-cache"})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                body = json.load(response)
            if body.get("commit") == sha and body.get("environment") == "staging":
                print(f"Trusted controller deployed exact PR head {sha} to staging.")
                return
        except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, ValueError):
            pass
        if time.monotonic() >= deadline:
            raise SystemExit("Trusted staging controller did not deploy the exact current PR SHA in time.")
        print("Waiting for trusted staging controller to deploy the exact current PR SHA.", flush=True)
        sleep(interval)


def report_outcome(*, inspect_result, deploy_result, acceptance_result, api=None):
    """Publish the final required Secretary status for this exact runtime PR."""
    api = api or _api()
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    _run, number, sha, pr = _resolve_pr(api, event)
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
    files = api.pull_request_files(number)
    if not application_change(files):
        print("No application/runtime changes; the CI status mirror owns the N/A result.")
        return
    if not _is_current_pr(pr, number, sha, repository, config):
        print("Stale or ineligible PR outcome ignored; the current PR head owns the required status.")
        return

    # A late attempt for the same SHA must never overwrite the status produced
    # by the latest CI attempt. If GitHub cannot establish ownership, publish a
    # failure so an earlier green status cannot satisfy branch protection.
    latest_confirmed = False
    try:
        _jobs, latest = latest_jobs(api, sha)
        latest_confirmed = bool(
            latest
            and latest.get("id") == _run.get("id")
            and latest.get("run_attempt", 1) == _run.get("run_attempt", 1)
        )
    except APIError:
        latest = None
    if latest and not latest_confirmed:
        print("Stale CI attempt ignored; the latest attempt owns the required status.")
        return

    labels = {label.get("name") for label in pr.get("labels", []) if isinstance(label, dict)}
    eligible = (
        not pr.get("draft", False)
        and config.get("preview_opt_in_label") in labels
    )
    passed = latest_confirmed and eligible and (
        inspect_result == "success"
        and deploy_result == "success"
        and acceptance_result == "success"
    )
    state = "success" if passed else "failure"
    description = (
        "Protected deployment and authenticated product acceptance passed"
        if passed else
        "Staging approval is missing or protected deployment/product acceptance did not pass"
    )
    url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repository}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    api.request("statuses/" + sha, {
        "state": state,
        "context": config["preview_check"],
        "description": description[:140],
        "target_url": url,
    })
    print(f"PR #{number}: {state}: {description}")


def main():
    operation = os.environ.get("TRUSTED_STAGING_OPERATION", "")
    if operation == "inspect":
        inspect_candidate()
    elif operation == "wait-for-checks":
        wait_for_required_checks()
    elif operation == "wait-for-deployment":
        wait_for_exact_staging_sha()
    elif operation == "report":
        report_outcome(
            inspect_result=os.environ.get("INSPECT_RESULT", "failure"),
            deploy_result=os.environ.get("DEPLOY_RESULT", "failure"),
            acceptance_result=os.environ.get("ACCEPTANCE_RESULT", "failure"),
        )
    else:
        raise SystemExit("Set TRUSTED_STAGING_OPERATION to a supported staging wait operation.")


if __name__ == "__main__":
    main()
