"""Privacy-safe request correlation and AI metadata logging."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from fastapi import Request
from starlette.responses import Response

logger = logging.getLogger("phishlens.api")


def request_id() -> str:
    """Generate a server-owned correlation ID; never trust caller input."""
    return uuid.uuid4().hex


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
