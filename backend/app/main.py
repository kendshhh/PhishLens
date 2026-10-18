from functools import lru_cache
from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.ai.gemini_provider import DailyQuotaExceeded, GeminiProvider
from backend.ai.mock_provider import MockProvider
from backend.ai.schemas import AnalysisRequest, AnalysisResponse
from backend.ai.service import AIService
from backend.app.routers.history import router as history_router
from backend.core.config import PROJECT_ROOT, get_ai_config

app = FastAPI(title="PhishLens API")
app.include_router(history_router)


_ai_service_lock = Lock()


def get_ai_service() -> tuple[AIService, Literal["mock", "gemini", "local"]]:
    # Lock outside the cache so concurrent misses cannot create separate providers.
    with _ai_service_lock:
        return _get_cached_ai_service()


@lru_cache(maxsize=1)
def _get_cached_ai_service() -> tuple[AIService, Literal["mock", "gemini", "local"]]:
    mode, api_key, model = get_ai_config()
    if mode == "mock":
        return AIService(MockProvider()), "mock"
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


@app.post("/analyses", response_model=AnalysisResponse, response_model_exclude_none=True)
def analyze_email(request: AnalysisRequest) -> AnalysisResponse:
    try:
        service, mode = get_ai_service()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        result = service.analyze_email(
            subject=request.subject,
            sender=request.sender,
            body=request.text,
        )
    except DailyQuotaExceeded as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

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
