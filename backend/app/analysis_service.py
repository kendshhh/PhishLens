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
    owner_id=None,
    provider_usage: dict[str, int | str] | None = None,
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

            if provider_usage is not None:
                for name in ("input_tokens", "output_tokens"):
                    value = getattr(result, name, None)
                    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                        provider_usage[name] = value
                if isinstance(result.estimated_cost_usd, str):
                    provider_usage["estimated_cost_usd"] = result.estimated_cost_usd

            deadline.inference_remaining()
            return await persist_saved_analysis(
                request,
                result,
                mode=mode,
                deadline=deadline,
                idempotency_key=idempotency_key,
                **({"owner_id": owner_id} if owner_id is not None else {}),
            )
    except TimeoutError:
        raise AnalysisTimeoutError("Analysis deadline exceeded") from None
    except (TypeError, ValueError):
        raise AnalysisInferenceError("Invalid analysis result") from None
