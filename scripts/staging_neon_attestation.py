"""Verify Neon branch metadata in trusted CI and bind the result to a PR head."""

import argparse
import hashlib
import json
import os
import time

from scripts.deploy_staging import live_pr_matches, requested_pr_identity
from scripts.secretary.github_api import APIError, GitHub
from scripts.verify_neon_release_branch import NeonReleaseError, verify_branch


WORKFLOW_PATH = ".github/workflows/staging-neon-preflight.yml"
STATUS_CONTEXT = "Trusted staging Neon"
TARGET_FIELDS = {
    "project_id": "STAGING_NEON_PROJECT_ID",
    "branch_id": "STAGING_NEON_BRANCH_ID",
    "production_project_id": "PRODUCTION_NEON_PROJECT_ID",
    "production_branch_id": "PRODUCTION_NEON_BRANCH_ID",
    "expected_parent_id": "STAGING_NEON_PARENT_ID",
    "schema_only_attestation": "STAGING_NEON_SCHEMA_ONLY_ATTESTATION",
    "production_rows_present": "STAGING_NEON_PRODUCTION_ROWS_PRESENT",
    "expected_host": "STAGING_NEON_EXPECTED_HOST",
}


def current_target(env):
    target = {field: env.get(variable, "").strip() for field, variable in TARGET_FIELDS.items()}
    if not target["expected_host"]:
        raise NeonReleaseError("Expected staging Neon endpoint is missing")
    return target


def describe_target(target):
    digest = hashlib.sha256(json.dumps(target, sort_keys=True).encode()).hexdigest()
    return f"Verified staging Neon target {digest}"


def attempt_url(api, run_id, attempt):
    return f"https://github.com/{api.repo}/actions/runs/{run_id}/attempts/{attempt}"


def has_attestation(api, number, sha, target):
    # Include unfinished and failed runs, which may have published no status.
    # pull_request_target runs use the base SHA, so the run name binds the PR head.
    workflow = WORKFLOW_PATH.rsplit("/", 1)[1]
    recent = api.request(f"actions/workflows/{workflow}/runs?event=pull_request_target&per_page=100")
    latest = max((
        run for run in recent["workflow_runs"]
        if run.get("path") == WORKFLOW_PATH
        and run.get("event") == "pull_request_target"
        and run.get("display_title") == f"Staging Neon PR {number} @ {sha}"
    ), key=lambda run: run["id"], default=None)
    if (latest is None or latest.get("status") != "completed"
            or latest.get("conclusion") != "success" or not latest.get("run_attempt")):
        return False

    url = attempt_url(api, latest["id"], latest["run_attempt"])
    # GitHub returns commit statuses newest first. Use the latest for this
    # exact attempt, including a failure or pending status if one was posted.
    status = next((row for row in api.pages(f"commits/{sha}/statuses")
                   if row.get("context") == STATUS_CONTEXT and row.get("target_url") == url
                   and (row.get("creator") or {}).get("login") == "github-actions[bot]"), {})
    return status.get("state") == "success" and status.get("description") == describe_target(target)


def publish_attestation(api, number, sha):
    if not live_pr_matches(api.request(f"pulls/{number}"), number, sha, api.repo):
        print("Superseded staging preflight")
        return

    url = attempt_url(api, os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"])

    def publish(state, description):
        api.request(f"statuses/{sha}", {
            "state": state, "context": STATUS_CONTEXT,
            "description": description, "target_url": url,
        })

    publish("pending", "Verifying staging Neon target")
    try:
        target = current_target(os.environ)
        verify_branch(**target)
        if not live_pr_matches(api.request(f"pulls/{number}"), number, sha, api.repo):
            print("Superseded staging preflight")
            return
    except Exception as error:
        publish("failure", "Trusted staging Neon verification failed")
        if isinstance(error, (APIError, NeonReleaseError)):
            raise
        raise NeonReleaseError("Trusted staging Neon verification failed unexpectedly") from None
    publish("success", describe_target(target))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["publish", "require"])
    args = parser.parse_args()
    api = GitHub()
    try:
        number, sha = requested_pr_identity()
        if args.operation == "publish":
            publish_attestation(api, number, sha)
        else:
            target = current_target(os.environ)
            for attempt in range(10):
                if has_attestation(api, number, sha, target):
                    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                        output.write(f"branch_id={target['branch_id']}\n")
                    return
                if attempt < 9:
                    time.sleep(5)
            raise NeonReleaseError("No successful trusted Neon preflight matches this head and staging target")
    except (APIError, NeonReleaseError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
