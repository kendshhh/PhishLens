"""Run saved-analysis inference without accessing the database."""

from contextlib import suppress
from typing import Any

import httpx
from google.genai import errors

from backend.ai.gemini_provider import DailyQuotaExceeded, GeminiProvider
from backend.ai.mock_provider import MockProvider
from backend.ai.service import AIProvider, AIService
from backend.app.analysis_channel import ResultChannel


def _build_provider(
    *,
    mode: str,
    api_key: str | None,
    model: str | None,
) -> AIProvider:
    if mode == "mock":
        return MockProvider()
    if mode == "tfidf":
        from backend.ai.tfidf_provider import TfidfProvider

        return TfidfProvider()

    if mode == "gemini" and api_key and model:
        return GeminiProvider(
            api_key=api_key,
            model=model,
            timeout_ms=15_000,
        )

    raise RuntimeError("Provider unavailable for saved analysis")


def _failure_status(exception: Exception) -> str:
    """Classify known failures without exposing their messages."""
    current: BaseException | None = exception
    seen: set[int] = set()

    while current is not None and id(current) not in seen:
        seen.add(id(current))

        if isinstance(current, (TimeoutError, httpx.TimeoutException)):
            return "timeout"

        if isinstance(current, DailyQuotaExceeded):
            return "unavailable"

        if isinstance(current, errors.APIError):
            if current.code == 504:
                return "timeout"
            if current.code in {401, 403, 404, 429, 503}:
                return "unavailable"

        current = current.__cause__

    return "failure"


def run_analysis_worker(
    connection: ResultChannel,
    *,
    mode: str,
    api_key: str | None,
    model: str | None,
    subject: str,
    body: str,
) -> None:
    """Send one result or safe failure status to the parent process."""
    provider: AIProvider | None = None
    message: dict[str, Any] = {"status": "failure"}

    try:
        try:
            provider = _build_provider(
                mode=mode,
                api_key=api_key,
                model=model,
            )
        except Exception:  # noqa: BLE001
            # Provider initialization failures become a fixed safe status.
            message = {"status": "unavailable"}
        else:
            try:
                result = AIService(provider).analyze_email(
                    subject=subject or None,
                    sender=None,
                    body=body,
                )
                message = {
                    "status": "ok",
                    "result": result.model_dump(mode="json"),
                }
            except Exception as exception:  # noqa: BLE001
                # Unexpected inference failures must not expose exception text.
                message = {"status": _failure_status(exception)}
    finally:
        if provider is not None:
            close = getattr(provider, "close", None)
            if callable(close):
                with suppress(Exception):
                    close()

        try:
            with suppress(OSError):
                connection.send(message)
        finally:
            connection.close()
