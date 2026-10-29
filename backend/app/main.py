from functools import lru_cache
from threading import Lock
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.ai.errors import AnalysisUnavailableError
from backend.ai.gemini_provider import DailyQuotaExceeded, GeminiProvider
from backend.ai.mock_provider import MockProvider
from backend.ai.schemas import (
    AnalysisFailureResponse,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisValidationErrorResponse,
)
from backend.ai.service import AIService
from backend.app.routers.history import router as history_router
from backend.core.config import PROJECT_ROOT, get_ai_config

app = FastAPI(title="PhishLens API")
app.include_router(history_router)


def analysis_error(
    status_code: int,
    code: str,
    message: str,
    fields: list[dict[str, str]] | None = None,
) -> JSONResponse:
    error = {"code": code, "message": message}
    if fields is not None:
        error["fields"] = fields

    return JSONResponse(
        status_code=status_code,
        content={"error": error},
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation(
    request: Request,
    exc: RequestValidationError,
):
    if request.method == "POST" and request.url.path == "/analyses":
        fields = []
        for problem in exc.errors()[:10]:
            location = problem.get("loc", ())
            field = next(
                (
                    part
                    for part in reversed(location)
                    if isinstance(part, str)
                    and part in ("text", "subject", "sender")
                ),
                "body",
            )

            error_type = problem.get("type")
            if field == "text" and error_type in ("value_error", "string_too_short"):
                field_code = "blank"
            elif error_type == "missing":
                field_code = "required"
            elif error_type == "string_too_long":
                field_code = "too_long"
            elif error_type == "string_type":
                field_code = "invalid_type"
            elif error_type == "extra_forbidden":
                field_code = "unknown_field"
            elif error_type == "json_invalid":
                field_code = "malformed_json"
            else:
                field_code = "invalid"

            fields.append({"field": field, "code": field_code})

        return analysis_error(
            422,
            "invalid_input",
            "Invalid email input",
            fields,
        )

    return await request_validation_exception_handler(request, exc)


_ai_service_lock = Lock()


def get_ai_service() -> tuple[AIService, Literal["mock", "gemini", "local", "tfidf"]]:
    # Lock outside the cache so concurrent misses cannot create separate providers.
    with _ai_service_lock:
        return _get_cached_ai_service()


@lru_cache(maxsize=1)
def _get_cached_ai_service() -> tuple[AIService, Literal["mock", "gemini", "local", "tfidf"]]:
    mode, api_key, model = get_ai_config()
    if mode == "mock":
        return AIService(MockProvider()), "mock"
    if mode == "tfidf":
        from backend.ai.tfidf_provider import TfidfProvider

        return AIService(TfidfProvider()), "tfidf"
    if mode == "local":
        import os
        from pathlib import Path

        from backend.ai.local_provider import LocalProvider

        cache_dir = Path(os.getenv("MODEL_PATH", "").strip() or PROJECT_ROOT / "models")
        return AIService(LocalProvider(cache_dir=cache_dir)), "local"
    if api_key is None or model is None:
        raise RuntimeError("Gemini configuration is incomplete")
    return AIService(GeminiProvider(api_key=api_key, model=model)), "gemini"


@app.get("/health")
def health():
    return {"status": "ok", "service": "phishlens-api"}


@app.get("/version")
def version():
    """Public deployment identity only; never expose environment or credential values."""
    import os

    return {
        "commit": os.getenv("RENDER_GIT_COMMIT", "unknown"),
        "environment": os.getenv("APP_ENV", "development"),
    }


@app.get("/model-info")
def model_info():
    """Public save capability; no input, database access or private settings."""
    try:
        mode, _, _ = get_ai_config()
        if mode == "tfidf":
            from backend.ai.tfidf_provider import (
                INTERCEPT,
                MODEL_SHA256,
                load_artifact,
                sigmoid,
            )

            load_artifact()
            from backend.ai.live_review import load_live_models

            load_live_models()
            return {"provider_mode": mode, "model_sha256": MODEL_SHA256,
                    "alert_threshold_score": sigmoid(INTERCEPT), "accepts_tfidf_reports": True,
                    "accepts_local_reviews": True}
    except (RuntimeError, OSError, ValueError, KeyError):
        pass
    return {"provider_mode": "unavailable", "accepts_tfidf_reports": False}


@app.post(
    "/analyses",
    response_model=AnalysisResponse,
    response_model_exclude_none=True,
    responses={
        422: {
            "model": AnalysisValidationErrorResponse,
            "description": "Invalid email input",
        },
        502: {
            "model": AnalysisFailureResponse,
            "description": "Analysis failed",
        },
        503: {
            "model": AnalysisFailureResponse,
            "description": "Analysis unavailable",
        },
    },
)
def analyze_email(request: AnalysisRequest) -> AnalysisResponse | JSONResponse:
    try:
        service, mode = get_ai_service()
    except RuntimeError:
        return analysis_error(
            503,
            "analysis_unavailable",
            "Analysis temporarily unavailable",
        )

    try:
        result = service.analyze_email(
            subject=request.subject,
            sender=request.sender,
            body=request.text,
        )
    except AnalysisUnavailableError:
        return analysis_error(
            503,
            "analysis_unavailable",
            "Analysis temporarily unavailable",
        )
    except DailyQuotaExceeded:
        return analysis_error(
            503,
            "analysis_unavailable",
            "Analysis temporarily unavailable",
        )
    except RuntimeError:
        return analysis_error(
            502,
            "inference_failed",
            "Analysis failed",
        )

    risk_level: Literal["low", "medium", "high"] = {
        "legitimate": "low",
        "spam": "medium",
        "phishing": "high",
    }[result.classification]
    return AnalysisResponse(
        **result.model_dump(),
        risk_level=risk_level,
        mode=mode,
    )


def check_database():
    from backend.core.database import engine

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@app.get("/ready")
def readiness():
    try:
        check_database()
    except (SQLAlchemyError, RuntimeError, ValueError):
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unavailable"},
        )

    return {"status": "ready", "database": "connected"}
