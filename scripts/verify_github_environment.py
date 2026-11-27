"""Fail-closed validation for protected GitHub Actions deployment environments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class EnvironmentGateError(ValueError):
    pass


def validate_environment(
    payload: dict[str, Any],
    expected_name: str,
    deployment_branch_policies: dict[str, Any] | None = None,
) -> dict[str, Any]:
    supported = {"staging-neon-preflight", "release-staging", "staging", "production"}
    if expected_name not in supported:
        raise EnvironmentGateError("Unsupported GitHub deployment environment")
    if payload.get("name") != expected_name:
        raise EnvironmentGateError("GitHub deployment environment identity does not match")
    if payload.get("can_admins_bypass") is not False:
        raise EnvironmentGateError("Environment must prevent administrator bypass")
    rules = payload.get("protection_rules")
    if not isinstance(rules, list):
        raise EnvironmentGateError("Environment protection rules could not be verified")
    reviewers = [rule for rule in rules if isinstance(rule, dict)
                 and rule.get("type") == "required_reviewers"]
    if len(reviewers) != 1:
        raise EnvironmentGateError("Environment must have exactly one required-reviewer protection rule")
    rule = reviewers[0]
    if not rule.get("reviewers"):
        raise EnvironmentGateError("Environment required-reviewer list is empty")
    if rule.get("prevent_self_review") is not True:
        raise EnvironmentGateError("Environment must prevent self-review")
    branch_policy = payload.get("deployment_branch_policy")
    if expected_name == "production":
        if branch_policy != {"protected_branches": True, "custom_branch_policies": False}:
            raise EnvironmentGateError("Production must be limited to protected branches")
    else:
        if branch_policy != {"protected_branches": False, "custom_branch_policies": True}:
            raise EnvironmentGateError(f"{expected_name} must use explicit custom branch restrictions")
        rows = (deployment_branch_policies or {}).get("branch_policies")
        names = [row.get("name") for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
        if names != ["main"]:
            raise EnvironmentGateError(f"{expected_name} must allow only the main branch")
    return {"name": expected_name, "required_reviewers": len(rule["reviewers"]),
            "prevent_self_review": True, "can_admins_bypass": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "environment",
        choices=("staging-neon-preflight", "release-staging", "staging", "production"),
    )
    parser.add_argument("--input", type=Path, default=Path("-"))
    parser.add_argument("--branch-policies", type=Path)
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if str(args.input) == "-" else args.input.read_text(encoding="utf-8")
        branch_policies = (json.loads(args.branch_policies.read_text(encoding="utf-8"))
                           if args.branch_policies else None)
        result = validate_environment(json.loads(raw), args.environment, branch_policies)
    except (EnvironmentGateError, OSError, json.JSONDecodeError, TypeError) as exc:
        parser.exit(1, f"GitHub environment gate failed: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
