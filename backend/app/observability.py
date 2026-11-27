"""Privacy-safe request correlation and AI metadata logging."""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from typing import Any

from fastapi import Request
from starlette.responses import Response

logger = logging.getLogger("phishlens.api")


def request_id() -> str:
    """Generate a server-owned correlation ID; never trust caller input."""
    return uuid.uuid4().hex


def attach_ai_quota_observation(request: Request, reservation: Any) -> None:
    """Attach privacy-safe quota estimates for the request access log."""
    request.state.ai_quota_observation = {
        "input_token_upper_bound": reservation.input_token_upper_bound,
        "output_token_upper_bound": reservation.output_token_upper_bound,
        "cost_upper_bound_usd": str(reservation.cost_upper_bound_usd),
        "daily_cost_reserved_usd": str(reservation.daily_cost_reserved_usd),
        "daily_spend_cap_usd": str(reservation.daily_spend_cap_usd),
        "daily_budget_fraction": str(reservation.daily_budget_fraction),
    }


def attach_ai_usage_observation(request: Request, result: Any) -> None:
    """Attach provider usage and configured-rate cost estimates, not content."""
    usage: dict[str, int | str] = {}
    for name in ("input_tokens", "output_tokens"):
        value = result.get(name) if isinstance(result, dict) else getattr(result, name, None)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            usage[name] = value
    estimated_cost = (
        result.get("estimated_cost_usd")
        if isinstance(result, dict)
        else getattr(result, "estimated_cost_usd", None)
    )
    if isinstance(estimated_cost, str) and re.fullmatch(r"\d+\.\d{6}", estimated_cost):
        usage["estimated_cost_usd"] = estimated_cost
    if usage:
        request.state.ai_usage_observation = usage


def set_ai_observation(
    request: Request,
    *,
    provider_mode: str,
    outcome: str,
    result: Any = None,
    failure_code: str | None = None,
    duration_ms: float | None = None,
    provenance: dict[str, Any] | None = None,
) -> None:
    """Attach allowlisted, non-content inference metadata for the access log."""
    metadata: dict[str, Any] = {
        "provider_mode": provider_mode[:40],
        "outcome": outcome[:40],
    }
    if failure_code:
        metadata["failure_code"] = failure_code[:40]
    if duration_ms is not None:
        metadata["duration_ms"] = round(max(0.0, duration_ms), 3)

    sources = [provenance or {}, result]
    fields = {
        "model_id": "model",
        "model_revision": "model_revision",
        "prompt_version": "prompt_version",
        "explanation_source": "explanation_source",
    }
    for output_name, source_name in fields.items():
        value = None
        for source in sources:
            if isinstance(source, dict):
                value = source.get(source_name)
            elif source is not None:
                value = getattr(source, source_name, None)
            if value is not None:
                break
        if isinstance(value, str) and value:
            metadata[output_name] = value[:120]

    for name in ("input_tokens", "output_tokens"):
        value = None
        for source in sources:
            if isinstance(source, dict):
                value = source.get(name)
            elif source is not None:
                value = getattr(source, name, None)
            if value is not None:
                break
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            metadata[name] = value

    estimated_cost = None
    for source in sources:
        if isinstance(source, dict):
            estimated_cost = source.get("estimated_cost_usd")
        elif source is not None:
            estimated_cost = getattr(source, "estimated_cost_usd", None)
        if estimated_cost is not None:
            break
    if isinstance(estimated_cost, str) and re.fullmatch(r"\d+\.\d{6}", estimated_cost):
        metadata["estimated_cost_usd"] = estimated_cost

    if outcome == "success":
        metadata.update({"validation_result": True, "retries": 0, "fallback_used": False})
    for state_name in ("ai_quota_observation", "ai_usage_observation"):
        context = getattr(request.state, state_name, None)
        if isinstance(context, dict):
            metadata.update(context)
    request.state.ai_observation = metadata


async def request_observability_middleware(request: Request, call_next) -> Response:
    """Log request identity, route, status and safe AI metadata, never payloads."""
    correlation_id = request_id()
    request.state.request_id = correlation_id
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = correlation_id
        return response
    finally:
        route = request.scope.get("route")
        route_name = getattr(route, "path", None) or "unmatched"
        record: dict[str, Any] = {
            "event": "http_request",
            "request_id": correlation_id,
            "method": request.method,
            "route": route_name,
            "operation": getattr(route, "name", "unmatched"),
            "status_code": status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }
        ai_observation = getattr(request.state, "ai_observation", None)
        if isinstance(ai_observation, dict):
            record["ai"] = ai_observation
        logger.info(json.dumps(record, sort_keys=True, separators=(",", ":")))
