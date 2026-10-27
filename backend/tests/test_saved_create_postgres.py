import asyncio
import os
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.ai.mock_provider import MockProvider
from backend.ai.schemas import AIAnalysisResult
from backend.ai.service import AIService
from backend.app import analysis_deadlines, analysis_persistence, analysis_service, main
from backend.app.analysis_deadlines import AnalysisTimeoutError
from backend.app.analysis_execution import (
    AnalysisInferenceError,
    AnalysisUnavailableError,
)
from backend.app.routers import history, saved_create
from backend.models import AnalyzedEmail, User

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="Requires a disposable local PostgreSQL database",
)


@pytest.fixture
def saved_postgres_context(monkeypatch):
    from backend.core.database import engine

    assert engine.url.host in {"localhost", "127.0.0.1"}
    assert engine.url.database in {
        "phishlens_s2_t1_test",
        "phishlens_dev",
    }

    user_id = uuid4()
    email = f"crud-http-{user_id}@phishlens.test"

    monkeypatch.setattr(analysis_persistence, "DEMO_USER_EMAIL", email)
    monkeypatch.setattr(history, "DEMO_USER_EMAIL", email)
    monkeypatch.setattr(
        saved_create,
        "get_ai_config",
        lambda: ("mock", None, None),
    )

    try:
        with Session(engine) as setup:
            setup.add(User(id=user_id, email=email))
            setup.commit()

        with TestClient(main.app) as client:
            yield client, engine, user_id
    finally:
        # Remove only this test user's records through the database cascade.
        with Session(engine) as cleanup:
            cleanup.execute(delete(User).where(User.id == user_id))
            cleanup.commit()


def test_complete_saved_crud_flow(saved_postgres_context):
    client, engine, user_id = saved_postgres_context
    body = "Synthetic email body"

    created = client.post(
        "/api/analyses",
        json={"body": body},
    )

    assert created.status_code == 201
    result = created.json()
    record_id = UUID(result["id"])
    url = f"/api/analyses/{record_id}"

    assert result["subject"] == ""
    assert result["body"] == body
    assert result["prediction"] == "spam"
    assert result["risk_level"] == "medium"
    assert result["confidence"] is None
    assert result["analysis_mode"] == "mock"
    assert result["analysis_provenance"]["provider_mode"] == "mock"

    # A separate database session must see the acknowledged commit.
    with Session(engine) as verification:
        record = verification.get(AnalyzedEmail, record_id)
        assert record is not None
        assert record.user_id == user_id
        assert record.body == body
        assert record.prediction == "spam"

    listed = client.get("/api/analyses")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [
        str(record_id)
    ]

    detail = client.get(url)
    assert detail.status_code == 200
    assert detail.json()["body"] == body

    updated = client.patch(
        url,
        json={
            "notes": "Reviewed synthetic email",
            "feedback": "false_positive",
        },
    )
    assert updated.status_code == 200

    # Verify PATCH persisted independently of the response object.
    with Session(engine) as verification:
        record = verification.get(AnalyzedEmail, record_id)
        assert record is not None
        assert record.notes == "Reviewed synthetic email"
        assert record.feedback == "false_positive"

    reread = client.get(url)
    assert reread.status_code == 200
    assert reread.json()["notes"] == "Reviewed synthetic email"

    cleared = client.patch(url, json={"notes": None})
    assert cleared.status_code == 200
    assert cleared.json()["notes"] is None
    assert cleared.json()["feedback"] == "false_positive"

    deleted = client.delete(url)
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert client.get(url).status_code == 404
    empty_history = client.get("/api/analyses")
    assert empty_history.status_code == 200
    assert empty_history.json() == {"items": []}

    with Session(engine) as verification:
        assert verification.get(AnalyzedEmail, record_id) is None


def test_create_idempotency_replays_one_committed_record(
    saved_postgres_context,
    monkeypatch,
):
    client, engine, user_id = saved_postgres_context
    inference = Mock(
        return_value=AIAnalysisResult(classification="legitimate")
    )
    monkeypatch.setattr(analysis_service, "run_saved_inference", inference)
    headers = {"Idempotency-Key": "retry-safe-create-001"}
    payload = {"subject": "Synthetic retry test", "body": "Synthetic body"}

    first = client.post("/api/analyses", json=payload, headers=headers)
    retry = client.post("/api/analyses", json=payload, headers=headers)

    assert first.status_code == retry.status_code == 201
    assert first.json()["id"] == retry.json()["id"]
    inference.assert_called_once()

    with Session(engine) as verification:
        records = verification.scalars(
            select(AnalyzedEmail).where(AnalyzedEmail.user_id == user_id)
        ).all()
        assert len(records) == 1
        assert records[0].idempotency_key == headers["Idempotency-Key"]

    conflict = client.post(
        "/api/analyses",
        json={**payload, "body": "Changed synthetic body"},
        headers=headers,
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "idempotency_conflict"
    inference.assert_called_once()


def test_retry_after_commit_acknowledgement_timeout_replays_saved_record(
    saved_postgres_context,
    monkeypatch,
):
    client, engine, user_id = saved_postgres_context
    inference = Mock(
        return_value=AIAnalysisResult(classification="legitimate")
    )
    monkeypatch.setattr(analysis_service, "run_saved_inference", inference)
    monkeypatch.setattr(analysis_deadlines, "OPERATION_BUDGET_SECONDS", 5.0)
    persist = analysis_service.persist_saved_analysis

    async def commit_then_lose_acknowledgement(*args, **kwargs):
        response = await persist(*args, **kwargs)
        # The SQL transaction committed. Keep the application await pending so
        # the request deadline cancels it before the result can be acknowledged.
        await asyncio.Event().wait()
        return response

    monkeypatch.setattr(
        analysis_service,
        "persist_saved_analysis",
        commit_then_lose_acknowledgement,
    )
    headers = {"Idempotency-Key": "commit-ack-timeout-001"}
    payload = {"subject": "Synthetic acknowledgement test", "body": "Synthetic body"}

    timed_out = client.post("/api/analyses", json=payload, headers=headers)

    assert timed_out.status_code == 504
    assert timed_out.json()["code"] == "analysis_timeout"
    with Session(engine) as verification:
        records = verification.scalars(
            select(AnalyzedEmail).where(AnalyzedEmail.user_id == user_id)
        ).all()
        assert len(records) == 1
        committed_id = records[0].id

    # The caller's retry with the same key recovers the committed result and
    # does not invoke inference or insert a second row.
    monkeypatch.setattr(analysis_service, "persist_saved_analysis", persist)
    retried = client.post("/api/analyses", json=payload, headers=headers)

    assert retried.status_code == 201
    assert retried.json()["id"] == str(committed_id)
    inference.assert_called_once()
    with Session(engine) as verification:
        count = verification.scalar(
            select(func.count())
            .select_from(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user_id)
        )
        assert count == 1

@pytest.mark.parametrize(
    ("error_type", "expected_status", "expected_code", "expected_message"),
    [
        (
            AnalysisInferenceError,
            502,
            "analysis_failed",
            "Email analysis failed",
        ),
        (
            AnalysisUnavailableError,
            503,
            "analysis_unavailable",
            "Email analysis is temporarily unavailable",
        ),
        (
            AnalysisTimeoutError,
            504,
            "analysis_timeout",
            "Email analysis timed out",
        ),
    ],
)
def test_failed_inference_does_not_save(
    saved_postgres_context,
    monkeypatch,
    error_type,
    expected_status,
    expected_code,
    expected_message,
):
    client, engine, user_id = saved_postgres_context
    inference = Mock(
        side_effect=error_type(
            "secret-key private@example.invalid"
        )
    )
    monkeypatch.setattr(
        analysis_service,
        "run_saved_inference",
        inference,
    )

    response = client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == expected_status
    assert response.json() == {
        "detail": expected_message,
        "code": expected_code,
    }
    inference.assert_called_once()

    with Session(engine) as verification:
        count = verification.scalar(
            select(func.count())
            .select_from(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user_id)
        )
        assert count == 0


def test_invalid_saved_response_rolls_back_insert(
    saved_postgres_context,
    monkeypatch,
):
    client, engine, user_id = saved_postgres_context
    inserted_ids = []

    def reject_saved_response(record):
        inserted_ids.append(record.id)
        raise ValueError("synthetic-private-response-details")

    serializer = Mock(side_effect=reject_saved_response)
    monkeypatch.setattr(
        analysis_persistence,
        "saved_detail_from_record",
        serializer,
    )

    response = client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Email analysis failed",
        "code": "analysis_failed",
    }
    serializer.assert_called_once()
    assert len(inserted_ids) == 1

    # The serializer received the inserted row, but no commit was allowed.
    with Session(engine) as verification:
        assert verification.get(
            AnalyzedEmail,
            inserted_ids[0],
        ) is None

        count = verification.scalar(
            select(func.count())
            .select_from(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user_id)
        )
        assert count == 0


def test_database_lock_timeout_does_not_save(
    saved_postgres_context,
    monkeypatch,
):
    client, engine, user_id = saved_postgres_context

    monkeypatch.setattr(
        analysis_deadlines,
        "OPERATION_BUDGET_SECONDS",
        1.0,
    )
    monkeypatch.setattr(
        analysis_service,
        "run_saved_inference",
        Mock(
            return_value=AIAnalysisResult(
                classification="legitimate",
            )
        ),
    )

    # Block the INSERT's foreign-key check with a separate transaction.
    with Session(engine) as blocker:
        locked_user = blocker.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
        )
        assert locked_user is not None

        response = client.post(
            "/api/analyses",
            json={"body": "Synthetic email body"},
        )

        blocker.rollback()

    assert response.status_code == 504
    assert response.json() == {
        "detail": "Email analysis timed out",
        "code": "analysis_timeout",
    }

    with Session(engine) as verification:
        count = verification.scalar(
            select(func.count())
            .select_from(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user_id)
        )
        assert count == 0

def test_live_analysis_does_not_save_history(
    saved_postgres_context,
    monkeypatch,
):
    client, engine, user_id = saved_postgres_context

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (AIService(MockProvider()), "mock"),
    )

    response = client.post(
        "/analyses",
        json={"text": "Synthetic live email body"},
    )

    assert response.status_code == 200
    assert response.json()["classification"] == "spam"
    assert "id" not in response.json()

    history_response = client.get("/api/analyses")
    assert history_response.status_code == 200
    assert history_response.json() == {"items": []}

    with Session(engine) as verification:
        count = verification.scalar(
            select(func.count())
            .select_from(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user_id)
        )
        assert count == 0
