"""Persistent analysis creation with safe client-facing errors."""

import re
from collections.abc import Callable, Coroutine
from typing import Any, Literal, cast

from fastapi import APIRouter, Header, Request, Response
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
from backend.app.analysis_persistence import (
    AnalysisIdempotencyConflictError,
    find_idempotent_saved_analysis,
)
from backend.app.analysis_schemas import CreateSavedAnalysis, SavedAnalysisDetail
from backend.app.analysis_service import create_saved_analysis
from backend.core.config import get_ai_config, get_database_url

SavedCreateErrorCode = Literal[
    "invalid_input",
    "analysis_failed",
    "analysis_unavailable",
    "storage_unavailable",
    "analysis_timeout",
    "idempotency_conflict",
    "internal_error",
]

_IDEMPOTENCY_KEY_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,255}")


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
        for status in (409, 422, 500, 502, 503, 504)
    },
)
async def create_analysis(
    request: CreateSavedAnalysis,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
    required_model: str | None = Header(default=None, alias="X-PhishLens-Model", max_length=64),
) -> SavedAnalysisDetail | JSONResponse:
    deadline = AnalysisDeadline.start()

    # An extension save must never silently invoke a cloud/mock provider. Keep
    # the existing body contract server-owned, including when deployment changes.
    if required_model is not None or request.local_review is not None:
        try:
            from backend.ai.tfidf_provider import MODEL_SHA256, load_artifact

            mode, _, _ = get_ai_config()
            if mode != "tfidf" or (required_model is not None and required_model != MODEL_SHA256):
                raise RuntimeError("Model mismatch")
            load_artifact()
        except (RuntimeError, OSError, ValueError, KeyError):
            return _error(503, "analysis_unavailable", "The matching TF-IDF save service is unavailable")

    if idempotency_key is not None and not _IDEMPOTENCY_KEY_PATTERN.fullmatch(
        idempotency_key
    ):
        return _error(422, "invalid_input", "Invalid Idempotency-Key")

    try:
        get_database_url()
    except (RuntimeError, ValueError):
        return _error(
            503,
            "storage_unavailable",
            "Saved analysis storage is temporarily unavailable",
        )

    if idempotency_key is not None:
        try:
            existing = await find_idempotent_saved_analysis(
                request,
                idempotency_key,
                deadline=deadline,
            )
        except AnalysisIdempotencyConflictError:
            return _error(
                409,
                "idempotency_conflict",
                "Idempotency-Key was already used for a different request",
            )
        except AnalysisTimeoutError:
            return _error(504, "analysis_timeout", "Email analysis timed out")
        except DatabaseError:
            return _error(
                503,
                "storage_unavailable",
                "Saved analysis storage is temporarily unavailable",
            )
        except Exception:  # noqa: BLE001
            return _error(
                500,
                "internal_error",
                "Unable to create saved analysis",
            )
        if existing is not None:
            return existing

    try:
        mode, api_key, model = get_ai_config()
    except (RuntimeError, ValueError):
        return _error(
            503,
            "analysis_unavailable",
            "Email analysis is temporarily unavailable",
        )

    if mode not in {"mock", "gemini", "tfidf"}:
        return _error(
            503,
            "analysis_unavailable",
            "Email analysis is temporarily unavailable",
        )

    try:
        return await create_saved_analysis(
            request,
            mode=cast(ProviderMode, mode),
            api_key=api_key,
            model=model,
            deadline=deadline,
            idempotency_key=idempotency_key,
        )
    except AnalysisIdempotencyConflictError:
        return _error(
            409,
            "idempotency_conflict",
            "Idempotency-Key was already used for a different request",
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
