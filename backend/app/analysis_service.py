"""Coordinate supervised inference and persistent analysis creation."""

from asyncio import timeout, to_thread

from backend.app.analysis_deadlines import (
    AnalysisDeadline,
    AnalysisTimeoutError,
)
from backend.app.analysis_execution import (
    AnalysisInferenceError,
    run_saved_inference,
)
from backend.app.analysis_mapping import ProviderMode
from backend.app.analysis_persistence import persist_saved_analysis
from backend.app.analysis_schemas import CreateSavedAnalysis, SavedAnalysisDetail


async def create_saved_analysis(
    request: CreateSavedAnalysis,
    *,
    mode: ProviderMode,
    api_key: str | None,
    model: str | None,
    deadline: AnalysisDeadline,
    idempotency_key: str | None = None,
) -> SavedAnalysisDetail:
    """Run timely inference, then commit one validated saved analysis."""
    try:
        async with timeout(deadline.operation_remaining()):
            async with timeout(deadline.inference_remaining()):
                result = await to_thread(
                    run_saved_inference,
                    subject=request.subject,
                    body=request.body,
                    mode=mode,
                    api_key=api_key,
                    model=model,
                    deadline=deadline,
                )

            deadline.inference_remaining()
            return await persist_saved_analysis(
                request,
                result,
                mode=mode,
                deadline=deadline,
                idempotency_key=idempotency_key,
            )
    except TimeoutError:
        raise AnalysisTimeoutError("Analysis deadline exceeded") from None
    except (TypeError, ValueError):
        raise AnalysisInferenceError("Invalid analysis result") from None
