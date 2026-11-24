"""Verify Neon branch metadata in trusted CI and bind the result to a PR head."""

import argparse
import hashlib
import json
import os
import re
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


def has_attestation(api, number, sha, target):
    run_prefix = f"https://github.com/{api.repo}/actions/runs/"
    for status in api.pages(f"commits/{sha}/statuses"):
        if (status.get("context") != STATUS_CONTEXT or status.get("state") != "success"
                or status.get("description") != describe_target(target)
                or (status.get("creator") or {}).get("login") != "github-actions[bot]"):
            continue
        run_url = status.get("target_url") or ""
        run_id = run_url.removeprefix(run_prefix)
        if not run_url.startswith(run_prefix) or not re.fullmatch(r"[1-9][0-9]*", run_id):
            continue
        run = api.request(f"actions/runs/{run_id}")
        if (run.get("path") == WORKFLOW_PATH
                and run.get("event") == "pull_request_target"
                and run.get("display_title") == f"Staging Neon PR {number} @ {sha}"
                and run.get("conclusion") == "success"):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["publish", "require"])
    args = parser.parse_args()
    api = GitHub()
    try:
        number, sha = requested_pr_identity()
        target = current_target(os.environ)
        if args.operation == "publish":
            if not live_pr_matches(api.request(f"pulls/{number}"), number, sha, api.repo):
                print("Superseded staging preflight")
                return
            verify_branch(**target)
            if not live_pr_matches(api.request(f"pulls/{number}"), number, sha, api.repo):
                print("Superseded staging preflight")
                return
            api.request(f"statuses/{sha}", {
                "state": "success",
                "context": STATUS_CONTEXT,
                "description": describe_target(target),
                "target_url": f"https://github.com/{api.repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
            })
        else:
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
