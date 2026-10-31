"""Run one guarded synthetic provider request against the exact staging revision."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"^[0-9a-f]{40}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
SYNTHETIC_REQUEST = {
    "subject": "Synthetic PhishLens provider smoke",
    "sender": "smoke@example.invalid",
    "text": (
        "Synthetic test message only. Visit https://example.invalid/verify "
        "to confirm this fictional account. No real person or account is involved."
    ),
}
PROVIDER_REQUEST_ATTEMPTED = False
PROVIDER_CALLS_OBSERVED: int | None = None


class SmokeGateError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class NoRedirect(HTTPRedirectHandler):
    """Refuse redirects so one request cannot silently become another."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _get_json(origin: str, path: str) -> tuple[int, dict]:
    request = Request(origin + path, headers={"Accept": "application/json"})
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            status = response.status
            content = response.read(64 * 1024)
    except HTTPError as exc:
        raise SmokeGateError(f"preflight_http_{exc.code}") from None
    except (URLError, TimeoutError, OSError):
        raise SmokeGateError("preflight_transport_error") from None
    if status != 200:
        raise SmokeGateError("preflight_non_200")
    try:
        value = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise SmokeGateError("preflight_invalid_json") from None
    if not isinstance(value, dict):
        raise SmokeGateError("preflight_invalid_shape")
    return status, value


def _validate_configuration() -> dict:
    try:
        config = json.loads((ROOT / ".github/secretary.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise SmokeGateError("trusted_staging_config_unavailable") from None

    expected_sha = os.getenv("EXPECTED_SOURCE_SHA", "").strip().lower()
    if not SHA.fullmatch(expected_sha):
        raise SmokeGateError("expected_source_sha_must_be_full_commit")
    if os.getenv("AI_PROVIDER_SMOKE_ENABLE_REQUEST", "").lower() != "true":
        raise SmokeGateError("dispatch_enable_confirmation_required")
    if os.getenv("AI_PROVIDER_SMOKE_ENABLED", "").lower() != "true":
        raise SmokeGateError("owner_enable_flag_not_set")
    if os.getenv("AI_PROVIDER_SMOKE_ENV", "") != "staging":
        raise SmokeGateError("protected_staging_environment_required")
    if os.getenv("AI_PROVIDER_SMOKE_PROVIDER", "").lower() != "gemini":
        raise SmokeGateError("owner_provider_not_configured")
    model = os.getenv("AI_PROVIDER_SMOKE_MODEL", "").strip()
    if not SAFE_ID.fullmatch(model):
        raise SmokeGateError("owner_model_not_configured")
    if os.getenv("AI_PROVIDER_SMOKE_MAX_REQUESTS", "") != "1":
        raise SmokeGateError("owner_request_limit_must_be_one")
    if os.getenv("AI_PROVIDER_SMOKE_PROVIDER_BUDGET_ENFORCED", "").lower() != "true":
        raise SmokeGateError("owner_provider_budget_not_confirmed")
    cost_cap = os.getenv("AI_PROVIDER_SMOKE_COST_CAP_USD", "").strip()
    try:
        if not Decimal(cost_cap).is_finite() or Decimal(cost_cap) <= 0:
            raise InvalidOperation
    except InvalidOperation:
        raise SmokeGateError("owner_cost_cap_not_configured") from None

    origin = os.getenv("STAGING_BASE_URL", "").rstrip("/")
    trusted_origin = config.get("staging_origin", "").rstrip("/")
    if not trusted_origin.startswith("https://") or origin != trusted_origin:
        raise SmokeGateError("staging_origin_does_not_match_trusted_config")
    if os.getenv("WORKFLOW_SOURCE_SHA", "") != os.getenv("GITHUB_SHA", ""):
        raise SmokeGateError("workflow_source_identity_mismatch")

    return {
        "expected_source_sha": expected_sha,
        "origin": origin,
        "provider": "gemini",
        "model": model,
        "approved_cost_cap_usd": str(Decimal(cost_cap).normalize()),
    }


def _safe_identity(value) -> str | None:
    return value if isinstance(value, str) and SAFE_ID.fullmatch(value) else None


def run() -> dict:
    values = _validate_configuration()
    workflow_sha = os.getenv("GITHUB_SHA", "")
    if not SHA.fullmatch(workflow_sha):
        raise SmokeGateError("workflow_source_sha_unavailable")

    _, version = _get_json(values["origin"], "/version")
    if version.get("commit") != values["expected_source_sha"]:
        raise SmokeGateError("staging_revision_mismatch")
    if version.get("environment") != "staging":
        raise SmokeGateError("target_is_not_staging")

    _, ready = _get_json(values["origin"], "/ready")
    if ready.get("status") != "ready" or ready.get("database") != "connected":
        raise SmokeGateError("staging_readiness_not_confirmed")

    global PROVIDER_REQUEST_ATTEMPTED
    request = Request(
        values["origin"] + "/analyses",
        data=json.dumps(SYNTHETIC_REQUEST).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    PROVIDER_REQUEST_ATTEMPTED = True
    try:
        with build_opener(NoRedirect()).open(request, timeout=35) as response:
            status = response.status
            content = response.read(64 * 1024)
    except HTTPError as exc:
        raise SmokeGateError(f"provider_request_http_{exc.code}") from None
    except (URLError, TimeoutError, OSError):
        raise SmokeGateError("provider_request_transport_error_no_retry") from None

    if status != 200:
        raise SmokeGateError("provider_request_non_200_no_retry")
    try:
        result = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise SmokeGateError("provider_response_invalid_json_no_retry") from None
    if not isinstance(result, dict):
        raise SmokeGateError("provider_response_invalid_shape_no_retry")

    global PROVIDER_CALLS_OBSERVED
    PROVIDER_CALLS_OBSERVED = 1 if result.get("mode") == "gemini" else 0
    classification = result.get("classification")
    risk_level = result.get("risk_level")
    mode = result.get("mode")
    actual_model = result.get("model")
    if classification not in {"phishing", "legitimate", "spam"}:
        raise SmokeGateError("provider_response_invalid_classification_no_retry")
    if risk_level not in {"high", "low", "medium"}:
        raise SmokeGateError("provider_response_invalid_risk_no_retry")
    if mode != "gemini" or actual_model != values["model"]:
        raise SmokeGateError("provider_or_model_identity_mismatch_no_retry")

    return {
        "status": "passed",
        "deployment_sha": values["expected_source_sha"],
        "workflow_source_sha": workflow_sha,
        "provider": values["provider"],
        "model": values["model"],
        "model_revision": _safe_identity(result.get("model_revision")),
        "prompt_version": _safe_identity(result.get("prompt_version")),
        "provider_mode": mode,
        "analysis_requests": 1,
        "provider_request_attempts": 1,
        "provider_calls_observed": PROVIDER_CALLS_OBSERVED,
        "approved_cost_cap_usd": values["approved_cost_cap_usd"],
        "classification": classification,
        "risk_level": risk_level,
        "database_writes": 0,
        "limitations": [
            "One fixed synthetic request was sent to the non-persisting /analyses endpoint.",
            "The workflow enforces the approved one-request cap; provider billing remains governed by the owner-configured provider budget.",
            "This smoke is not a quality evaluation or held-out accuracy result.",
        ],
    }


def main() -> int:
    output = ROOT / "output/ai-provider-smoke"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "workflow_source_sha": os.getenv("GITHUB_SHA", "unavailable"),
        "target": "staging",
        "analysis_requests": 0,
        "provider_request_attempts": 0,
        "provider_calls_observed": None,
        "database_writes": 0,
        "status": "blocked",
        "limitations": [
            "No request body, response body, credential, or provider error detail is retained.",
            "Only the fixed synthetic input is eligible for a provider request.",
        ],
    }
    try:
        report.update(run())
    except SmokeGateError as exc:
        report["status"] = "failed" if PROVIDER_REQUEST_ATTEMPTED else "blocked"
        report["reason"] = exc.code
        if PROVIDER_REQUEST_ATTEMPTED:
            report["analysis_requests"] = 1
            report["provider_request_attempts"] = 1
            report["provider_calls_observed"] = PROVIDER_CALLS_OBSERVED
    except Exception as exc:  # keep raw exception text out of logs and artifacts
        report["status"] = "failed"
        report["reason"] = f"unexpected_{type(exc).__name__}"
        if PROVIDER_REQUEST_ATTEMPTED:
            report["analysis_requests"] = 1
            report["provider_request_attempts"] = 1
            report["provider_calls_observed"] = PROVIDER_CALLS_OBSERVED

    report_path = output / "summary.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "status", "workflow_run_id", "workflow_source_sha", "deployment_sha",
        "provider", "model", "provider_mode", "reason",
        "analysis_requests", "provider_request_attempts", "provider_calls_observed",
    ) if key in report}, sort_keys=True))

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## Guarded staging provider smoke\n\n")
            summary.write(f"- Status: `{report['status']}`\n")
            summary.write(f"- Workflow source SHA: `{report['workflow_source_sha']}`\n")
            summary.write(f"- Deployment SHA: `{report.get('deployment_sha', 'not verified')}`\n")
            summary.write(f"- Analysis requests: `{report['analysis_requests']}` / `1` maximum\n")
            summary.write(f"- Provider attempts observed: `{report['provider_calls_observed']}`\n")
            if report.get("reason"):
                summary.write(f"- Gate result: `{report['reason']}`\n")
            summary.write("- Payloads and credentials: not logged or stored\n")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

