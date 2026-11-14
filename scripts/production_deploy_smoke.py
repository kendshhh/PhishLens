"""Verify an exact production deploy with read-only health and synthetic AI behavior."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"^[0-9a-f]{40}$")
CASES = {
    "p01-credential": "phishing",
    "l01-meeting": "legitimate",
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _json_request(
    url: str,
    *,
    payload: dict | None = None,
    timeout: int = 15,
    extra_headers: dict[str, str] | None = None,
) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    method = "GET"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    if extra_headers:
        headers.update(extra_headers)
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        value = json.loads(response.read(64 * 1024))
    if not isinstance(value, dict):
        raise TypeError("Invalid JSON response")
    return value


def _origin(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Production base URL must be a plain HTTPS origin")
    return f"https://{parsed.netloc}"


def _validate_analysis(result: dict, *, expected: str, model_sha: str, case_id: str) -> dict:
    if result.get("mode") != "tfidf":
        raise RuntimeError(f"{case_id}: production provider mode was not TF-IDF")
    if result.get("model_revision") != model_sha:
        raise RuntimeError(f"{case_id}: response model revision did not match /model-info")
    if result.get("classification") != expected:
        raise RuntimeError(f"{case_id}: synthetic classification did not match the smoke contract")
    risk = "high" if expected == "phishing" else "low"
    if result.get("risk_level") != risk:
        raise RuntimeError(f"{case_id}: synthetic risk level did not match the smoke contract")
    if not isinstance(result.get("evidence"), list) or not isinstance(result.get("tactics"), list):
        raise TypeError(f"{case_id}: analysis response shape was invalid")
    return {"case": case_id, "status": "passed", "classification": expected, "risk_level": risk}


def verify_deployment(
    origin: str,
    expected_sha: str,
    *,
    get_json=_json_request,
    post_json=_json_request,
    timeout_seconds: int = 600,
    sleep=time.sleep,
) -> dict:
    if not SHA.fullmatch(expected_sha or ""):
        raise ValueError("A full 40-character expected production SHA is required")
    base = _origin(origin)
    deadline = time.monotonic() + timeout_seconds
    identity = None
    while identity is None:
        try:
            candidate = get_json(base + "/version")
            if candidate.get("environment") != "production":
                raise RuntimeError("Production target reported a different environment")
            if candidate.get("commit") == expected_sha:
                identity = candidate
        except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError):
            pass
        if identity is not None:
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("Production did not report the expected SHA before the deadline")
        sleep(min(5, remaining))

    health = get_json(base + "/health")
    if health != {"status": "ok", "service": "phishlens-api"}:
        raise RuntimeError("Production health response did not match the API contract")
    ready = get_json(base + "/ready")
    if ready != {"status": "ready", "database": "connected"}:
        raise RuntimeError("Production readiness response did not match the API contract")
    model_info = get_json(base + "/model-info")
    if model_info.get("provider_mode") != "tfidf":
        raise RuntimeError(
            "Safe production behavior smoke requires the non-paid TF-IDF provider "
            f"(provider_mode={model_info.get('provider_mode', 'missing')})"
        )
    model_sha = model_info.get("model_sha256")
    if not isinstance(model_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", model_sha):
        raise RuntimeError("Production model identity was invalid")

    from backend.ai.evaluation_cases import CASES as DEVELOPMENT_CASES

    case_map = {case.id: case for case in DEVELOPMENT_CASES}
    behavior = []
    for case_id, expected in CASES.items():
        case = case_map[case_id]
        result = post_json(
            base + "/analyses",
            payload={"text": case.body},
            timeout=30,
            extra_headers={"X-Require-Provider": "tfidf"},
        )
        behavior.append(_validate_analysis(
            result, expected=expected, model_sha=model_sha, case_id=case_id,
        ))

    final_identity = get_json(base + "/version")
    if final_identity != identity:
        raise RuntimeError("Production deployment changed during the behavior smoke")

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed",
        "environment": "production",
        "deployment_sha": identity["commit"],
        "health": "passed",
        "readiness": "passed",
        "model_sha256": model_sha,
        "behavior_checks": behavior,
        "inference_requests": len(behavior),
        "paid_provider_calls": 0,
        "database_writes": 0,
        "limitations": [
            "Behavior checks use two fixed synthetic TF-IDF development cases.",
            "The /analyses endpoint does not persist a saved report.",
            "This smoke is not a full browser acceptance, held-out accuracy evaluation, or load test.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", default=os.getenv("EXPECTED_SOURCE_SHA", ""))
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--output", type=Path, default=ROOT / "output/production-smoke/summary.json")
    args = parser.parse_args()

    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "failed",
        "environment": "production",
        "deployment_sha": args.expected_sha,
        "paid_provider_calls": 0,
        "database_writes": 0,
    }
    try:
        config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
        report.update(verify_deployment(
            config["production_origin"],
            args.expected_sha.strip().lower(),
            timeout_seconds=args.timeout_seconds,
        ))
    except Exception as exc:  # noqa: BLE001 - keep private transport detail out of artifacts
        report["reason"] = f"{type(exc).__name__}: {str(exc)[:180]}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "status", "environment", "deployment_sha", "health", "readiness",
        "model_sha256", "inference_requests", "paid_provider_calls", "database_writes", "reason",
    ) if key in report}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
