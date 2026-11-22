"""Read-only Neon metadata preflight for an independent staging branch."""

from __future__ import annotations

import argparse
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class NeonReleaseError(RuntimeError):
    pass


def verify_branch(*, project_id: str, branch_id: str, production_project_id: str,
                  production_branch_id: str,
                  schema_only_attestation: str, production_rows_present: str,
                  expected_parent_id: str = "", expected_host: str = "") -> dict:
    """Read branch metadata only; never query tables or product rows."""
    if not re.fullmatch(r"[a-z0-9-]{8,64}", project_id or ""):
        raise NeonReleaseError("Staging Neon project ID is invalid")
    if not re.fullmatch(r"[a-z0-9-]{8,64}", production_project_id or ""):
        raise NeonReleaseError("Production Neon project ID is invalid")
    if project_id == production_project_id:
        raise NeonReleaseError("Staging must use a separate Neon project from production")
    if not re.fullmatch(r"br-[a-z0-9-]{8,64}", branch_id or ""):
        raise NeonReleaseError("Staging Neon branch ID is invalid")
    if branch_id == production_branch_id:
        raise NeonReleaseError("Staging cannot target the production Neon branch")
    if expected_parent_id:
        raise NeonReleaseError("Staging branch must be an independent root")
    if schema_only_attestation not in {"true", "false"}:
        raise NeonReleaseError("Protected environment must explicitly record the schema-only attestation state")
    if production_rows_present != "false":
        raise NeonReleaseError("Protected environment must attest that production rows are absent")

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
    except HTTPError as exc:
        raise NeonReleaseError(
            f"Neon branch metadata request failed (HTTP {exc.code})"
        ) from None
    except (URLError, TimeoutError, json.JSONDecodeError):
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
    endpoint_host = ""
    if expected_host:
        expected_host = expected_host.strip().rstrip(".").lower()
        if not re.fullmatch(r"[a-z0-9.-]+", expected_host):
            raise NeonReleaseError("Expected staging Neon endpoint host is invalid")
        endpoints_request = Request(
            f"https://console.neon.tech/api/v2/projects/{project_id}/branches/{branch_id}/endpoints",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        try:
            with urlopen(endpoints_request, timeout=20) as response:
                endpoints_payload = json.loads(response.read())
        except HTTPError as exc:
            raise NeonReleaseError(
                f"Neon endpoint metadata request failed (HTTP {exc.code})"
            ) from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise NeonReleaseError("Neon endpoint metadata request failed; details were suppressed") from None
        endpoints = endpoints_payload.get("endpoints") if isinstance(endpoints_payload, dict) else None
        if not isinstance(endpoints, list):
            raise NeonReleaseError("Neon endpoint metadata response is malformed")
        normalized_expected = re.sub(r"-pooler(?=\.)", "", expected_host)
        matching = [
            endpoint for endpoint in endpoints
            if isinstance(endpoint, dict)
            and isinstance(endpoint.get("host"), str)
            and re.sub(r"-pooler(?=\.)", "", endpoint.get("host", "").strip().rstrip(".").lower()) == normalized_expected
            and endpoint.get("branch_id", branch_id) == branch_id
        ]
        if len(matching) != 1:
            raise NeonReleaseError("Expected staging database host is not uniquely attached to this Neon branch")
        endpoint_host = matching[0]["host"].strip().rstrip(".").lower()
    return {
        "project_id": project_id,
        "production_project_id": production_project_id,
        "branch_id": branch_id,
        "branch_name": branch.get("name"),
        "parent_id": None,
        "branch_kind": "schema-only" if schema_only_attestation == "true" else "independent-root",
        "schema_only_attested": schema_only_attestation == "true",
        **({"endpoint_host": endpoint_host} if endpoint_host else {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", default=os.getenv("STAGING_NEON_PROJECT_ID", ""))
    parser.add_argument("--production-project-id", default=os.getenv("PRODUCTION_NEON_PROJECT_ID", ""))
    parser.add_argument("--branch-id", default=os.getenv("STAGING_NEON_BRANCH_ID", ""))
    parser.add_argument("--production-branch-id", default=os.getenv("PRODUCTION_NEON_BRANCH_ID", ""))
    parser.add_argument("--parent-id", default=os.getenv("STAGING_NEON_PARENT_ID", ""))
    parser.add_argument("--expected-host", default=os.getenv("STAGING_NEON_EXPECTED_HOST", ""))
    parser.add_argument("--schema-only-attestation", default=os.getenv("STAGING_NEON_SCHEMA_ONLY_ATTESTATION", ""))
    parser.add_argument("--production-rows-present", default=os.getenv("STAGING_NEON_PRODUCTION_ROWS_PRESENT", ""))
    args = parser.parse_args()
    try:
        print(json.dumps(verify_branch(
            project_id=args.project_id, branch_id=args.branch_id,
            production_project_id=args.production_project_id,
            production_branch_id=args.production_branch_id,
            schema_only_attestation=args.schema_only_attestation,
            production_rows_present=args.production_rows_present,
            expected_parent_id=args.parent_id,
            expected_host=args.expected_host,
        ), sort_keys=True))
    except (NeonReleaseError, OSError, ValueError) as exc:
        parser.exit(1, f"Neon release gate failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
