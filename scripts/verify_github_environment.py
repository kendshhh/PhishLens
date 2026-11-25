"""Fail-closed validation for protected GitHub Actions deployment environments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class EnvironmentGateError(ValueError):
    pass


def validate_environment(payload: dict[str, Any], expected_name: str) -> dict[str, Any]:
    if payload.get("name") != expected_name:
        raise EnvironmentGateError("GitHub deployment environment identity does not match")
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
    return {"name": expected_name, "required_reviewers": len(rule["reviewers"]),
            "prevent_self_review": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("environment", choices=("release-staging", "production"))
    parser.add_argument("--input", type=Path, default=Path("-"))
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if str(args.input) == "-" else args.input.read_text(encoding="utf-8")
        result = validate_environment(json.loads(raw), args.environment)
    except (EnvironmentGateError, OSError, json.JSONDecodeError, TypeError) as exc:
        parser.exit(1, f"GitHub environment gate failed: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
