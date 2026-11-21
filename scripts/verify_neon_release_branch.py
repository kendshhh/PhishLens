"""Read-only Neon metadata preflight for an independently initialized schema branch."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class NeonReleaseError(RuntimeError):
    pass


def verify_branch(*, project_id: str, branch_id: str, production_branch_id: str,
                  schema_only_attestation: str, expected_parent_id: str = "") -> dict:
    """Read branch metadata only; never query tables or product rows."""
    if not re.fullmatch(r"[a-z0-9-]{8,64}", project_id or ""):
        raise NeonReleaseError("Staging Neon project ID is invalid")
    if not re.fullmatch(r"br-[a-z0-9-]{8,64}", branch_id or ""):
        raise NeonReleaseError("Staging Neon branch ID is invalid")
    if branch_id == production_branch_id:
        raise NeonReleaseError("Staging cannot target the production Neon branch")
    if expected_parent_id:
        raise NeonReleaseError("Schema-only staging branch must be an independent root")
    if schema_only_attestation != "true":
        raise NeonReleaseError("Protected environment must attest this branch was initialized schema-only")

    token = os.environ.get("NEON_API_KEY", "")
    if not token:
        raise NeonReleaseError("Neon metadata credential is not configured")
    request = Request(
        f"https://console.neon.tech/api/v2/projects/{project_id}/branches/{branch_id}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        raise NeonReleaseError("Neon branch metadata request failed; details were suppressed") from None
    branch = payload.get("branch") if isinstance(payload, dict) else None
    if not isinstance(branch, dict):
        raise NeonReleaseError("Neon branch metadata response is malformed")
    if branch.get("id") != branch_id:
        raise NeonReleaseError("Neon branch identity does not match the protected environment")
    parent_id = branch.get("parent_id")
    if parent_id is not None:
        raise NeonReleaseError("Staging Neon branch has a parent and may contain inherited product data")
    if branch.get("current_state") not in (None, "ready"):
        raise NeonReleaseError("Staging Neon branch is not ready")
    return {
        "project_id": project_id,
        "branch_id": branch_id,
        "branch_name": branch.get("name"),
        "parent_id": None,
        "branch_kind": "schema-only",
        "schema_only_attested": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", default=os.getenv("STAGING_NEON_PROJECT_ID", ""))
    parser.add_argument("--branch-id", default=os.getenv("STAGING_NEON_BRANCH_ID", ""))
    parser.add_argument("--production-branch-id", default=os.getenv("PRODUCTION_NEON_BRANCH_ID", ""))
    parser.add_argument("--parent-id", default=os.getenv("STAGING_NEON_PARENT_ID", ""))
    parser.add_argument("--schema-only-attestation", default=os.getenv("STAGING_NEON_SCHEMA_ONLY_ATTESTATION", ""))
    args = parser.parse_args()
    try:
        print(json.dumps(verify_branch(
            project_id=args.project_id, branch_id=args.branch_id,
            production_branch_id=args.production_branch_id,
            schema_only_attestation=args.schema_only_attestation,
            expected_parent_id=args.parent_id,
        ), sort_keys=True))
    except (NeonReleaseError, OSError, ValueError) as exc:
        parser.exit(1, f"Neon release gate failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
