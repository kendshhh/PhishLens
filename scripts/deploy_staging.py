"""Deploy the exact current PR head after validating source and Render targets."""

import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.secretary.github_api import APIError, ReadOnlyGitHub
from scripts.secretary.preview import (
    render_request,
    verify_environment,
    verify_service,
)


def requested_pr_identity() -> tuple[int, str]:
    """Validate the requested deployment target against GitHub's PR event payload."""
    number_text = os.environ.get("STAGING_PR", "").strip()
    head_sha = os.environ.get("STAGING_PR_HEAD_SHA", "").strip()
    if not re.fullmatch(r"[1-9][0-9]*", number_text):
        raise SystemExit("Refusing deployment without a valid pull-request number.")
    if not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        raise SystemExit("Refusing deployment without a full pull-request head SHA.")

    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    if not repository or not event_path:
        raise SystemExit("Refusing deployment without the trusted pull-request event context.")
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise SystemExit("Refusing deployment because the pull-request event context is unreadable.") from None
    if not isinstance(event, dict):
        raise SystemExit("Refusing deployment because the pull-request event context is invalid.")

    number = int(number_text)
    event_repository = event.get("repository")
    if not isinstance(event_repository, dict) or event_repository.get("full_name") != repository:
        raise SystemExit("Refusing deployment: event repository does not match the trusted checkout.")

    pull_request = event.get("pull_request")
    if isinstance(pull_request, dict):
        head = pull_request.get("head")
        head_repo = head.get("repo") if isinstance(head, dict) else None
        if (
            event.get("number") != number
            or pull_request.get("number") != number
            or not isinstance(head, dict)
            or head.get("sha") != head_sha
            or not isinstance(head_repo, dict)
            or head_repo.get("full_name") != repository
        ):
            raise SystemExit("Refusing deployment: requested PR identity does not match the trusted event.")
        return number, head_sha

    # The privileged controller can also run after a trusted workflow_run.
    # It still binds the exact source run SHA and the current PR is re-read via
    # the API immediately before Render is mutated.
    source_run = event.get("workflow_run")
    if (
        not isinstance(source_run, dict)
        or source_run.get("event") != "pull_request"
        or source_run.get("head_sha") != head_sha
        or source_run.get("conclusion") != "success"
    ):
        raise SystemExit("Refusing deployment: source CI run does not match the requested PR SHA.")
    source_repo = source_run.get("head_repository")
    if isinstance(source_repo, dict) and source_repo.get("full_name") != repository:
        raise SystemExit("Refusing deployment from an untrusted fork head.")
    linked = source_run.get("pull_requests") or []
    linked_numbers = {
        row.get("number") for row in linked if isinstance(row, dict)
    }
    if linked_numbers and number not in linked_numbers:
        raise SystemExit("Refusing deployment: requested PR is not linked to the completed CI run.")
    return number, head_sha


def live_pr_matches(
    current: dict,
    number: int,
    expected_head_sha: str,
    expected_repository: str,
) -> bool:
    """Return whether the live PR is open, eligible, and still at the requested head."""
    if not isinstance(current, dict):
        return False
    labels_raw = current.get("labels")
    labels = {
        label.get("name") for label in labels_raw
        if isinstance(label, dict)
    } if isinstance(labels_raw, list) else set()
    head = current.get("head")
    head_repo = head.get("repo") if isinstance(head, dict) else None
    return (
        current.get("number") == number
        and current.get("state") == "open"
        and isinstance(head, dict)
        and head.get("sha") == expected_head_sha
        and isinstance(head_repo, dict)
        and head_repo.get("full_name") == expected_repository
        and not current.get("draft", False)
        and "needs-hosted-staging" in labels
    )


def require_live_pr(
    api: ReadOnlyGitHub,
    number: int,
    expected_head_sha: str,
    expected_repository: str,
) -> None:
    """Fail closed if GitHub cannot confirm the exact eligible PR head."""
    try:
        current = api.request(f"pulls/{number}")
    except APIError:
        raise SystemExit("Refusing deployment: the live PR head could not be verified with the read-only GitHub token.") from None
    if not live_pr_matches(current, number, expected_head_sha, expected_repository):
        raise SystemExit("Refusing deployment: live PR state, head, or staging eligibility changed.")


def main() -> None:
    key = os.environ.get("RENDER_STAGING_API_KEY")
    service_id = os.environ.get("RENDER_STAGING_SERVICE_ID")
    commit = os.environ.get("STAGING_COMMIT", "").strip()

    if not key or not service_id:
        raise SystemExit(
            "Configure the protected Render staging key and staging service ID."
        )
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("Refusing deployment without a full Git commit SHA.")
    number, head_sha = requested_pr_identity()
    if commit != head_sha:
        raise SystemExit("Refusing deployment: requested SHA differs from the verified PR head.")

    try:
        github = ReadOnlyGitHub(
            repo=os.environ.get("GITHUB_REPOSITORY"),
            token=os.environ.get("GITHUB_TOKEN", ""),
        )
    except APIError:
        raise SystemExit("Refusing deployment: the read-only GitHub token is not available.") from None
    repository = os.environ["GITHUB_REPOSITORY"]
    require_live_pr(github, number, head_sha, repository)

    config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
    if service_id != config["staging_service"] or service_id == config["production_service"]:
        raise SystemExit("Refusing deployment to an unapproved or production service.")
    if os.environ.get("STAGING_BASE_URL", "").rstrip("/") != config["staging_origin"]:
        raise SystemExit("Refusing deployment: staging origin does not match the allowlist.")

    service = render_request(f"services/{service_id}")
    verify_service(service, config)
    variables = render_request(f"services/{service_id}/env-vars?limit=100")
    verify_environment(variables, require_authenticated=True)
    print(
        "Staging preflight passed: exact current PR head, migration head, service, "
        "authenticated report mode, and private database target are validated.",
        flush=True,
    )

    # Recheck immediately before the first mutating Render request.
    require_live_pr(github, number, head_sha, repository)
    deploy = render_request(
        f"services/{service_id}/deploys",
        {"commitId": commit},
    )
    deploy_id = deploy["id"]
    print(f"Waiting for staging deployment {deploy_id} of {commit}", flush=True)
    # Render can spend up to 15 minutes waiting for a web service to bind a
    # port. Leave time for its failure event to reach the deploy API before the
    # hosted-staging job's own timeout expires.
    deadline = time.monotonic() + 1200
    while time.monotonic() < deadline:
        status = render_request(f"services/{service_id}/deploys/{deploy_id}")
        if status["status"] == "live":
            if status.get("commit", {}).get("id") != commit:
                raise SystemExit("Render live commit does not match the requested PR SHA.")
            print("Exact current PR head is live on staging.")
            return
        if status["status"] in {
            "build_failed",
            "update_failed",
            "pre_deploy_failed",
            "canceled",
            "deactivated",
        }:
            raise SystemExit("Staging deployment failed: " + status["status"])
        time.sleep(10)
    raise SystemExit("Staging deployment timed out.")


if __name__ == "__main__":
    main()
