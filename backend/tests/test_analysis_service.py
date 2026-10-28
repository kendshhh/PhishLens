import asyncio
import os
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.ai.schemas import AIAnalysisResult
from backend.app import (
    analysis_deadlines,
    analysis_persistence,
    analysis_service,
)
from backend.app.analysis_deadlines import AnalysisDeadline, AnalysisTimeoutError
from backend.app.analysis_execution import (
    AnalysisInferenceError,
    AnalysisUnavailableError,
)
from backend.app.analysis_schemas import CreateSavedAnalysis, SavedAnalysisDetail
from backend.models import AnalyzedEmail, User


@pytest.fixture
def service_context(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(
        analysis_deadlines,
        "monotonic",
        lambda: clock[0],
    )
    request = CreateSavedAnalysis(body="Synthetic email body")
    result = AIAnalysisResult(classification="legitimate")
    response = SavedAnalysisDetail(
        id=uuid4(),
        subject="",
        body=request.body,
        prediction="legitimate",
        confidence=None,
        risk_level="low",
        threat_indicators=[],
        explanation=None,
        notes=None,
        feedback=None,
        analysis_mode="mock",
        analysis_provenance={"provider_mode": "mock"},
        created_at=datetime(2026, 10, 20, 12, 0, tzinfo=UTC),
    )

    inference = Mock(return_value=result)
    persist = AsyncMock(return_value=response)
    monkeypatch.setattr(
        analysis_service,
        "run_saved_inference",
        inference,
    )
    monkeypatch.setattr(
        analysis_service,
        "persist_saved_analysis",
        persist,
    )

    return SimpleNamespace(
        clock=clock,
        deadline=AnalysisDeadline.start(),
        request=request,
        result=result,
        response=response,
        inference=inference,
        persist=persist,
    )


def _create(context):
    return asyncio.run(
        analysis_service.create_saved_analysis(
            context.request,
            mode="mock",
            api_key=None,
            model=None,
            deadline=context.deadline,
        )
    )


def test_create_reuses_one_deadline(service_context):
    context = service_context

    response = _create(context)

    assert response is context.response
    context.inference.assert_called_once_with(
        subject="",
        body=context.request.body,
        mode="mock",
        api_key=None,
        model=None,
        deadline=context.deadline,
    )
    context.persist.assert_awaited_once_with(
        context.request,
        context.result,
        mode="mock",
        deadline=context.deadline,
        idempotency_key=None,
    )


def test_create_forwards_idempotency_key(service_context):
    context = service_context

    asyncio.run(
        analysis_service.create_saved_analysis(
            context.request,
            mode="mock",
            api_key=None,
            model=None,
            deadline=context.deadline,
            idempotency_key="retry-123",
        )
    )

    assert context.persist.await_args.kwargs["idempotency_key"] == "retry-123"


@pytest.mark.parametrize(
    "error_type",
    [
        AnalysisInferenceError,
        AnalysisUnavailableError,
        AnalysisTimeoutError,
    ],
)
def test_failed_inference_never_saves(service_context, error_type):
    context = service_context
    context.inference.side_effect = error_type("Synthetic failure")

    with pytest.raises(error_type):
        _create(context)

    context.persist.assert_not_awaited()


def test_late_inference_never_saves(service_context):
    context = service_context

    def finish_late(**_kwargs):
        context.clock[0] = 116.0
        return context.result

    context.inference.side_effect = finish_late

    with pytest.raises(AnalysisTimeoutError):
        _create(context)

    context.persist.assert_not_awaited()


def test_invalid_output_returns_safe_failure(service_context):
    context = service_context
    context.persist.side_effect = ValueError("synthetic-private-details")

    with pytest.raises(AnalysisInferenceError) as captured:
        _create(context)

    assert "synthetic-private-details" not in str(captured.value)


def test_inference_wait_has_a_deadline(service_context, monkeypatch):
    context = service_context

    async def never_returns(*_args, **_kwargs):
        await asyncio.Event().wait()

    monkeypatch.setattr(
        analysis_deadlines,
        "INFERENCE_BUDGET_SECONDS",
        0.01,
    )
    monkeypatch.setattr(
        analysis_service,
        "to_thread",
        AsyncMock(side_effect=never_returns),
    )

    with pytest.raises(AnalysisTimeoutError):
        _create(context)

    context.persist.assert_not_awaited()


def test_persistence_wait_has_a_deadline(service_context, monkeypatch):
    context = service_context

    async def never_returns(*_args, **_kwargs):
        await asyncio.Event().wait()

    monkeypatch.setattr(
        analysis_deadlines,
        "OPERATION_BUDGET_SECONDS",
        0.01,
    )
    monkeypatch.setattr(
        analysis_service,
        "to_thread",
        AsyncMock(return_value=context.result),
    )
    context.persist.side_effect = never_returns

    with pytest.raises(AnalysisTimeoutError):
        _create(context)

    context.persist.assert_awaited_once()


@pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="Requires a disposable local PostgreSQL database",
)
def test_valid_analysis_is_committed_for_demo_user(monkeypatch):
    from backend.core.database import engine

    assert engine.url.host in {"localhost", "127.0.0.1"}
    assert engine.url.database == "phishlens_s2_t1_test"

    user_id = uuid4()
    email = f"saved-service-{user_id}@phishlens.test"
    monkeypatch.setattr(
        analysis_persistence,
        "DEMO_USER_EMAIL",
        email,
    )
    monkeypatch.setattr(
        analysis_service,
        "run_saved_inference",
        Mock(
            return_value=AIAnalysisResult(
                classification="phishing",
                confidence=0.93,
                evidence=[
                    {
                        "text": "Verify your account",
                        "reason": "Requests an account action",
                    }
                ],
            )
        ),
    )

    try:
        with Session(engine) as setup:
            setup.add(User(id=user_id, email=email))
            setup.commit()

        response = asyncio.run(
            analysis_service.create_saved_analysis(
                CreateSavedAnalysis(body="Verify your account today."),
                mode="mock",
                api_key=None,
                model=None,
                deadline=AnalysisDeadline.start(),
            )
        )

        # A separate session must see the committed row.
        with Session(engine) as verification:
            saved = verification.get(AnalyzedEmail, response.id)
            assert saved is not None
            assert saved.user_id == user_id
            assert saved.subject == ""
            assert saved.prediction == "phishing"
            assert float(saved.confidence) == 0.93
            assert saved.risk_level == "high"
            assert saved.analysis_mode == "mock"
            assert saved.indicators[0]["quote"] == "Verify your account"
    finally:
        # Deleting this unique test user cascades to its test records only.
        with Session(engine) as cleanup:
            cleanup.execute(delete(User).where(User.id == user_id))
            cleanup.commit()
