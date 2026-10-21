"""Persistent analysis creation with safe client-facing errors."""

from collections.abc import Callable, Coroutine
from typing import Any, Literal, cast

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from psycopg import Error as DatabaseError
from pydantic import BaseModel

from backend.app.analysis_deadlines import AnalysisDeadline, AnalysisTimeoutError
from backend.app.analysis_execution import (
    AnalysisInferenceError,
    AnalysisUnavailableError,
)
from backend.app.analysis_mapping import ProviderMode
from backend.app.analysis_schemas import CreateSavedAnalysis, SavedAnalysisDetail
from backend.app.analysis_service import create_saved_analysis
from backend.core.config import get_ai_config, get_database_url

SavedCreateErrorCode = Literal[
    "invalid_input",
    "analysis_failed",
    "analysis_unavailable",
    "storage_unavailable",
    "analysis_timeout",
    "internal_error",
]


class SavedCreateError(BaseModel):
    detail: str
    code: SavedCreateErrorCode


def _error(
    status_code: int,
    code: SavedCreateErrorCode,
    detail: str,
) -> JSONResponse:
    body = SavedCreateError(detail=detail, code=code)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
    )


class SavedCreateRoute(APIRoute):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_handler = super().get_route_handler()

        async def safe_handler(request: Request) -> Response:
            try:
                return await original_handler(request)
            except RequestValidationError:
                return _error(422, "invalid_input", "Invalid analysis input")
            except ResponseValidationError:
                return _error(
                    500,
                    "internal_error",
                    "Unable to create saved analysis",
                )

        return safe_handler


router = APIRouter(
    tags=["Saved analyses"],
    route_class=SavedCreateRoute,
)


@router.post(
    "/analyses",
    status_code=201,
    response_model=SavedAnalysisDetail,
    responses={
        status: {"model": SavedCreateError}
        for status in (422, 500, 502, 503, 504)
    },
)
async def create_analysis(
    request: CreateSavedAnalysis,
) -> SavedAnalysisDetail | JSONResponse:
    deadline = AnalysisDeadline.start()

    try:
        mode, api_key, model = get_ai_config()
    except (RuntimeError, ValueError):
        return _error(
            503,
            "analysis_unavailable",
            "Email analysis is temporarily unavailable",
        )

    if mode not in {"mock", "gemini"}:
        return _error(
            503,
            "analysis_unavailable",
            "Email analysis is temporarily unavailable",
        )

    try:
        get_database_url()
    except (RuntimeError, ValueError):
        return _error(
            503,
            "storage_unavailable",
            "Saved analysis storage is temporarily unavailable",
        )

    try:
        return await create_saved_analysis(
            request,
            mode=cast(ProviderMode, mode),
            api_key=api_key,
            model=model,
            deadline=deadline,
        )
    except AnalysisTimeoutError:
        return _error(504, "analysis_timeout", "Email analysis timed out")
    except AnalysisUnavailableError:
        return _error(
            503,
            "analysis_unavailable",
            "Email analysis is temporarily unavailable",
        )
    except AnalysisInferenceError:
        return _error(502, "analysis_failed", "Email analysis failed")
    except DatabaseError:
        return _error(
            503,
            "storage_unavailable",
            "Saved analysis storage is temporarily unavailable",
        )
    except Exception:  # noqa: BLE001
        # The HTTP boundary must not expose unexpected exception details.
        return _error(
            500,
            "internal_error",
            "Unable to create saved analysis",
        )