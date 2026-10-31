"""Deploy the exact PR merge commit after validating source and Render targets."""

import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.secretary.preview import (
    render_request,
    verify_environment,
    verify_service,
)


def main() -> None:
    key = os.environ.get("RENDER_STAGING_API_KEY")
    service_id = os.environ.get("RENDER_STAGING_SERVICE_ID")
    commit = os.environ.get("STAGING_COMMIT", "").strip()
    expected_commit = os.environ.get("GITHUB_SHA", "").strip()
    migration_revision = os.environ.get("STAGING_MIGRATION_REVISION", "").strip()

    if not key or not service_id:
        raise SystemExit(
            "Configure the protected Render staging key and staging service ID."
        )
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("Refusing deployment without a full Git commit SHA.")
    if expected_commit and commit != expected_commit:
        raise SystemExit("Refusing deployment: requested SHA differs from this workflow run.")
    if not migration_revision:
        raise SystemExit(
            "Refusing deployment: migration lineage was not verified for this source."
        )

    config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
    if service_id != config["staging_service"] or service_id == config["production_service"]:
        raise SystemExit("Refusing deployment to an unapproved or production service.")
    if os.environ.get("STAGING_BASE_URL", "").rstrip("/") != config["staging_origin"]:
        raise SystemExit("Refusing deployment: staging origin does not match the allowlist.")

    service = render_request(f"services/{service_id}")
    verify_service(service, config)
    variables = render_request(f"services/{service_id}/env-vars?limit=100")
    verify_environment(variables)
    print(
        "Staging preflight passed: exact source SHA, migration head, service, "
        "and private database target are validated.",
        flush=True,
    )

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
            print("Exact PR merge commit is live on staging.")
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
