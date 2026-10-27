"""Supervise saved-analysis inference in one bounded worker process."""

from multiprocessing import get_context
from multiprocessing.process import BaseProcess
from threading import BoundedSemaphore
from typing import Any

from backend.ai.schemas import AIAnalysisResult
from backend.app.analysis_channel import SharedResultChannel
from backend.app.analysis_deadlines import (
    AnalysisDeadline,
    AnalysisTimeoutError,
)
from backend.app.analysis_mapping import ProviderMode
from backend.app.analysis_worker import run_analysis_worker

_INFERENCE_SLOT = BoundedSemaphore(value=1)
_CLEANUP_WAIT_SECONDS = 0.25


class AnalysisUnavailableError(RuntimeError):
    """Saved inference cannot currently accept work."""


class AnalysisInferenceError(RuntimeError):
    """Inference failed or returned an invalid result."""


def _stop_worker(process: BaseProcess) -> bool:
    """Stop and reap a worker before allowing another request."""
    try:
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
                process.join(timeout=_CLEANUP_WAIT_SECONDS)

            if process.is_alive():
                process.kill()
                process.join(timeout=_CLEANUP_WAIT_SECONDS)

            if process.is_alive():
                return False

            process.join(timeout=0)

        process.close()
        return True
    except (OSError, ValueError):
        return False


def _read_result(message: dict[str, Any]) -> AIAnalysisResult:
    status = message.get("status")

    if status == "timeout":
        raise AnalysisTimeoutError("Analysis deadline exceeded")
    if status == "unavailable":
        raise AnalysisUnavailableError("Analysis provider unavailable")
    if status != "ok" or set(message) != {"status", "result"}:
        raise AnalysisInferenceError("Analysis failed")

    return AIAnalysisResult.model_validate(message["result"])


def run_saved_inference(
    *,
    subject: str,
    body: str,
    mode: ProviderMode,
    api_key: str | None,
    model: str | None,
    deadline: AnalysisDeadline,
) -> AIAnalysisResult:
    """Return timely, validated output without accessing the database."""
    deadline.inference_remaining()

    if mode not in {"mock", "gemini"}:
        raise AnalysisUnavailableError("Analysis provider unavailable")
    if mode == "gemini" and (not api_key or not model):
        raise AnalysisUnavailableError("Analysis provider unavailable")
    if not _INFERENCE_SLOT.acquire(blocking=False):
        raise AnalysisUnavailableError("Analysis worker busy or unavailable")

    process: BaseProcess | None = None

    try:
        context = get_context("spawn")
        channel = SharedResultChannel(context)
        process = context.Process(
            target=run_analysis_worker,
            kwargs={
                "connection": channel,
                "mode": mode,
                "api_key": api_key,
                "model": model,
                "subject": subject,
                "body": body,
            },
            daemon=True,
        )

        deadline.inference_remaining()
        process.start()
        process.join(timeout=deadline.inference_remaining())

        if process.is_alive():
            raise AnalysisTimeoutError("Analysis deadline exceeded")

        deadline.inference_remaining()

        if process.exitcode != 0:
            raise AnalysisInferenceError("Analysis worker failed")

        result = _read_result(channel.receive())
        deadline.inference_remaining()
        return result
    except (OSError, MemoryError):
        raise AnalysisUnavailableError("Analysis worker unavailable") from None
    except (TypeError, ValueError):
        raise AnalysisInferenceError("Invalid analysis result") from None
    finally:
        if process is None or _stop_worker(process):
            _INFERENCE_SLOT.release()
        else:
            raise AnalysisUnavailableError("Analysis worker unavailable")