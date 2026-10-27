import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from psycopg import OperationalError
from psycopg.errors import QueryCanceled
from pydantic import ValidationError

from backend.ai.schemas import AIAnalysisResult
from backend.app import analysis_deadlines, analysis_persistence
from backend.app.analysis_deadlines import AnalysisDeadline, AnalysisTimeoutError
from backend.app.analysis_execution import AnalysisUnavailableError
from backend.app.analysis_schemas import CreateSavedAnalysis


@pytest.fixture
def persistence_context(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(
        analysis_deadlines,
        "monotonic",
        lambda: clock[0],
    )

    user_id = uuid4()
    record_id = uuid4()
    row = {
        "id": record_id,
        "user_id": user_id,
        "subject": "",
        "body": "Verify your account today.",
        "prediction": "phishing",
        "confidence": Decimal("0.9300"),
        "risk_level": "high",
        "indicators": [
            {
                "type": "evidence",
                "quote": "Verify your account",
                "detail": "Requests an account action",
            }
        ],
        "explanation": None,
        "notes": None,
        "feedback": None,
        "analysis_mode": "mock",
        "analysis_provenance": {"provider_mode": "mock"},
        "created_at": datetime(2026, 10, 20, 12, 0, tzinfo=UTC),
    }

    user_cursor = SimpleNamespace(
        fetchone=AsyncMock(return_value={"id": user_id})
    )
    insert_cursor = SimpleNamespace(
        fetchone=AsyncMock(return_value=row)
    )
    connection = SimpleNamespace(
        execute=AsyncMock(side_effect=[user_cursor, insert_cursor]),
        commit=AsyncMock(),
    )

    @asynccontextmanager
    async def fake_connection(_deadline):
        yield connection

    connection_factory = Mock(side_effect=fake_connection)
    monkeypatch.setattr(
        analysis_persistence,
        "saved_analysis_connection",
        connection_factory,
    )
    monkeypatch.setattr(
        analysis_persistence,
        "uuid4",
        Mock(return_value=record_id),
    )

    return SimpleNamespace(
        clock=clock,
        deadline=AnalysisDeadline.start(),
        row=row,
        user_id=user_id,
        user_cursor=user_cursor,
        insert_cursor=insert_cursor,
        connection=connection,
        connection_factory=connection_factory,
        request=CreateSavedAnalysis(body=row["body"]),
        result=AIAnalysisResult(
            classification="phishing",
            confidence=0.93,
            evidence=[
                {
                    "text": "Verify your account",
                    "reason": "Requests an account action",
                }
            ],
        ),
    )


def _persist(context, idempotency_key=None):
    return asyncio.run(
        analysis_persistence.persist_saved_analysis(
            context.request,
            context.result,
            mode="mock",
            deadline=context.deadline,
            idempotency_key=idempotency_key,
        )
    )


def test_valid_result_is_committed(persistence_context):
    context = persistence_context

    response = _persist(context)

    assert response.id == context.row["id"]
    assert response.subject == ""
    assert response.prediction == "phishing"
    assert response.confidence == 0.93
    assert response.risk_level == "high"
    assert response.analysis_mode == "mock"
    assert response.threat_indicators[0].quote == "Verify your account"

    parameters = context.connection.execute.await_args_list[1].args[1]
    assert parameters[0] == context.row["id"]
    assert parameters[1] == context.user_id
    assert parameters[2] == ""
    assert parameters[3] == context.request.body
    assert parameters[7].obj == context.row["indicators"]
    assert parameters[10].obj["provider_mode"] == "mock"
    context.connection.commit.assert_awaited_once()


def test_unsupported_evidence_skips_database(persistence_context):
    context = persistence_context
    context.result = AIAnalysisResult(
        classification="phishing",
        evidence=[
            {
                "text": "Text absent from the submitted email",
                "reason": "Synthetic unsupported evidence",
            }
        ],
    )

    with pytest.raises(ValueError, match="Unsupported evidence"):
        _persist(context)

    context.connection_factory.assert_not_called()
    context.connection.commit.assert_not_awaited()


def test_late_inference_skips_database(persistence_context):
    context = persistence_context
    context.clock[0] = 116.0

    with pytest.raises(AnalysisTimeoutError):
        _persist(context)

    context.connection_factory.assert_not_called()
    context.connection.commit.assert_not_awaited()


def test_missing_demo_user_does_not_commit(persistence_context):
    context = persistence_context
    context.user_cursor.fetchone.return_value = None

    with pytest.raises(AnalysisUnavailableError):
        _persist(context)

    assert context.connection.execute.await_count == 1
    context.connection.commit.assert_not_awaited()


def test_missing_inserted_row_does_not_commit(persistence_context):
    context = persistence_context
    context.insert_cursor.fetchone.return_value = None

    with pytest.raises(AnalysisUnavailableError):
        _persist(context)

    context.connection.commit.assert_not_awaited()


def test_invalid_response_is_rejected_before_commit(persistence_context):
    context = persistence_context
    context.row["confidence"] = Decimal("1.5000")

    with pytest.raises(ValidationError):
        _persist(context)

    context.connection.commit.assert_not_awaited()


def test_expired_operation_does_not_start_commit(persistence_context):
    context = persistence_context

    async def finish_late():
        context.clock[0] = 121.0
        return context.row

    context.insert_cursor.fetchone.side_effect = finish_late

    with pytest.raises(AnalysisTimeoutError):
        _persist(context)

    context.connection.commit.assert_not_awaited()


def test_statement_timeout_becomes_safe_timeout(persistence_context):
    context = persistence_context
    context.connection.execute.side_effect = QueryCanceled(
        "private database statement details"
    )

    with pytest.raises(AnalysisTimeoutError) as captured:
        _persist(context)

    assert "private" not in str(captured.value)
    context.connection.commit.assert_not_awaited()


def test_commit_failure_does_not_return_success(persistence_context):
    context = persistence_context
    context.connection.commit.side_effect = OperationalError(
        "Synthetic commit failure"
    )

    with pytest.raises(OperationalError):
        _persist(context)

    context.connection.commit.assert_awaited_once()


def test_expired_budget_after_confirmed_commit_returns_saved_record(
    persistence_context,
):
    context = persistence_context

    async def acknowledge_late():
        context.clock[0] = 121.0

    context.connection.commit.side_effect = acknowledge_late

    response = _persist(context)

    assert response.id == context.row["id"]
    context.connection.commit.assert_awaited_once()


def test_idempotent_lookup_returns_prior_record(persistence_context):
    context = persistence_context
    cursor = SimpleNamespace(fetchone=AsyncMock(return_value=context.row))
    context.connection.execute = AsyncMock(return_value=cursor)

    response = asyncio.run(
        analysis_persistence.find_idempotent_saved_analysis(
            context.request,
            "request-123",
            deadline=context.deadline,
        )
    )

    assert response.id == context.row["id"]
    context.connection.execute.assert_awaited_once_with(
        analysis_persistence._SELECT_IDEMPOTENT_ANALYSIS_FOR_DEMO_USER,
        (analysis_persistence.DEMO_USER_EMAIL, "request-123"),
    )


def test_idempotent_lookup_rejects_different_payload(persistence_context):
    context = persistence_context
    cursor = SimpleNamespace(fetchone=AsyncMock(return_value=context.row))
    context.connection.execute = AsyncMock(return_value=cursor)
    request = CreateSavedAnalysis(body="Different synthetic body")

    with pytest.raises(
        analysis_persistence.AnalysisIdempotencyConflictError,
    ):
        asyncio.run(
            analysis_persistence.find_idempotent_saved_analysis(
                request,
                "request-123",
                deadline=context.deadline,
            )
        )


def test_idempotent_insert_race_returns_prior_record(persistence_context):
    context = persistence_context
    context.insert_cursor.fetchone.return_value = None
    replay_cursor = SimpleNamespace(
        fetchone=AsyncMock(return_value=context.row)
    )
    context.connection.execute = AsyncMock(
        side_effect=[context.user_cursor, context.insert_cursor, replay_cursor]
    )

    response = _persist(context, "request-123")

    assert response.id == context.row["id"]
    insert_call = context.connection.execute.await_args_list[1]
    assert "ON CONFLICT (user_id, idempotency_key) DO NOTHING" in insert_call.args[0]
    assert insert_call.args[1][-1] == "request-123"
    context.connection.commit.assert_not_awaited()


def test_idempotent_insert_race_rejects_different_payload(persistence_context):
    context = persistence_context
    context.insert_cursor.fetchone.return_value = None
    replay_cursor = SimpleNamespace(
        fetchone=AsyncMock(return_value=context.row)
    )
    context.connection.execute = AsyncMock(
        side_effect=[context.user_cursor, context.insert_cursor, replay_cursor]
    )
    context.request = CreateSavedAnalysis(body="Different synthetic body")
    context.result = AIAnalysisResult(classification="phishing")

    with pytest.raises(
        analysis_persistence.AnalysisIdempotencyConflictError,
    ):
        _persist(context, "request-123")

    context.connection.commit.assert_not_awaited()
