import asyncio
import os
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.ai.mock_provider import MockProvider
from backend.ai.schemas import AIAnalysisResult, EvidenceItem
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
    assert engine.url.database == "phishlens_s2_t1_test"

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
    "patch",
    [
        {"notes": "Synthetic reviewer notes"},
        {"feedback": "false_positive"},
    ],
    ids=["notes-only", "feedback-only"],
)
def test_patch_preserves_analysis_and_inference_count(
    saved_postgres_context,
    monkeypatch,
    patch,
):
    client, engine, user_id = saved_postgres_context
    inference = Mock(
        return_value=AIAnalysisResult(
            classification="phishing",
            confidence=0.91,
        )
    )
    monkeypatch.setattr(analysis_service, "run_saved_inference", inference)
    created = client.post(
        "/api/analyses",
        json={"subject": "Synthetic notice", "body": "Synthetic email body"},
    )
    assert created.status_code == 201
    record_id = UUID(created.json()["id"])
    url = f"/api/analyses/{record_id}"
    inference.assert_called_once()

    protected_fields = (
        "user_id", "subject", "body", "prediction", "confidence", "risk_level",
        "indicators", "explanation", "analysis_mode", "analysis_provenance", "created_at",
    )
    with Session(engine) as verification:
        original = verification.get(AnalyzedEmail, record_id)
        assert original is not None
        assert original.user_id == user_id
        before = {name: getattr(original, name) for name in protected_fields}

    updated = client.patch(url, json=patch)
    assert updated.status_code == 200
    inference.assert_called_once()

    with Session(engine) as verification:
        saved = verification.get(AnalyzedEmail, record_id)
        assert saved is not None
        assert {name: getattr(saved, name) for name in protected_fields} == before
        assert saved.notes == patch.get("notes")
        assert saved.feedback == patch.get("feedback")

    reread = client.get(url)
    assert reread.status_code == 200
    assert reread.json()["notes"] == patch.get("notes")
    assert reread.json()["feedback"] == patch.get("feedback")
    assert reread.json()["prediction"] == "phishing"
    assert reread.json()["confidence"] == 0.91
    inference.assert_called_once()


@pytest.mark.parametrize(
    ("method", "payload"),
    [
        ("post", {}),
        ("post", {"body": " \n "}),
        ("post", {"body": "x" * 30_001}),
        ("post", {"subject": "x" * 321, "body": "Synthetic body"}),
        ("post", {"body": {"unexpected": "object"}}),
        ("post", {"body": "Synthetic body", "user_id": str(uuid4())}),
        ("post", {"body": "Synthetic body", "prediction": "legitimate"}),
        ("post", {"body": "Synthetic body", "analysis_mode": "real"}),
        ("post", {"body": "Synthetic body", "unexpected": "field"}),
        ("patch", {}),
        ("patch", {"feedback": "unsupported"}),
        ("patch", {"notes": "x" * 2001}),
        ("patch", {"notes": {"unexpected": "object"}}),
        ("patch", {"user_id": str(uuid4())}),
        ("patch", {"prediction": "legitimate"}),
        ("patch", {"unexpected": "field"}),
    ],
    ids=[
        "create-missing-body", "create-blank-body", "create-oversized-body",
        "create-oversized-subject", "create-wrong-body-type", "create-owner",
        "create-verdict", "create-mode", "create-unknown-field", "patch-empty",
        "patch-invalid-feedback", "patch-oversized-notes", "patch-wrong-notes-type",
        "patch-owner", "patch-verdict", "patch-unknown-field",
    ],
)
def test_rejected_request_leaves_postgres_unchanged(
    saved_postgres_context,
    monkeypatch,
    method,
    payload,
):
    client, engine, user_id = saved_postgres_context
    inference = Mock(
        return_value=AIAnalysisResult(classification="legitimate")
    )
    monkeypatch.setattr(analysis_service, "run_saved_inference", inference)
    created = client.post(
        "/api/analyses",
        json={"body": "Synthetic record that rejected requests must preserve"},
    )
    assert created.status_code == 201
    record_id = UUID(created.json()["id"])

    statement = select(AnalyzedEmail.__table__).where(
        AnalyzedEmail.user_id == user_id
    )
    with engine.connect() as verification:
        before = [dict(row) for row in verification.execute(statement).mappings()]
    assert len(before) == 1

    url = "/api/analyses" if method == "post" else f"/api/analyses/{record_id}"
    response = client.request(method.upper(), url, json=payload)

    assert response.status_code == 422
    inference.assert_called_once()
    with engine.connect() as verification:
        after = [dict(row) for row in verification.execute(statement).mappings()]
    assert after == before

    reread = client.get(f"/api/analyses/{record_id}")
    assert reread.status_code == 200
    assert reread.json()["notes"] is None
    assert reread.json()["feedback"] is None


def test_malformed_json_does_not_write_and_next_create_succeeds(
    saved_postgres_context,
    monkeypatch,
):
    client, engine, user_id = saved_postgres_context
    inference = Mock(
        return_value=AIAnalysisResult(classification="legitimate")
    )
    monkeypatch.setattr(analysis_service, "run_saved_inference", inference)

    malformed = client.post(
        "/api/analyses",
        content='{"body": "synthetic-private-token"',
        headers={"Content-Type": "application/json"},
    )

    assert malformed.status_code == 422
    assert malformed.json() == {
        "detail": "Invalid analysis input",
        "code": "invalid_input",
    }
    assert "synthetic-private-token" not in malformed.text
    inference.assert_not_called()
    with Session(engine) as verification:
        assert verification.scalar(
            select(func.count())
            .select_from(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user_id)
        ) == 0

    accepted = client.post(
        "/api/analyses",
        json={"body": "Synthetic healthy request after invalid JSON"},
    )

    assert accepted.status_code == 201
    assert inference.call_count == 1
    with Session(engine) as verification:
        rows = verification.scalars(
            select(AnalyzedEmail).where(AnalyzedEmail.user_id == user_id)
        ).all()
        assert len(rows) == 1
        assert rows[0].body == "Synthetic healthy request after invalid JSON"


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


def test_invalid_evidence_does_not_save_and_next_request_succeeds(
    saved_postgres_context,
    monkeypatch,
):
    client, engine, user_id = saved_postgres_context
    inference = Mock(
        side_effect=[
            AIAnalysisResult(
                classification="phishing",
                evidence=[
                    EvidenceItem(
                        text="private phrase absent from the email",
                        reason="Synthetic unsupported evidence",
                    )
                ],
            ),
            AIAnalysisResult(classification="legitimate"),
        ]
    )
    monkeypatch.setattr(analysis_service, "run_saved_inference", inference)
    body = "Synthetic email with no evidence quote."

    rejected = client.post("/api/analyses", json={"body": body})

    assert rejected.status_code == 502
    assert rejected.json() == {
        "detail": "Email analysis failed",
        "code": "analysis_failed",
    }
    assert "private phrase" not in rejected.text
    inference.assert_called_once()
    with Session(engine) as verification:
        assert verification.scalar(
            select(func.count())
            .select_from(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user_id)
        ) == 0

    accepted = client.post("/api/analyses", json={"body": body})

    assert accepted.status_code == 201
    record_id = UUID(accepted.json()["id"])
    assert accepted.json()["prediction"] == "legitimate"
    assert accepted.json()["threat_indicators"] == []
    assert inference.call_count == 2
    with Session(engine) as verification:
        rows = verification.scalars(
            select(AnalyzedEmail).where(AnalyzedEmail.user_id == user_id)
        ).all()
        assert len(rows) == 1
        assert rows[0].id == record_id
        assert rows[0].prediction == "legitimate"
        assert rows[0].body == body


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


def test_create_recovers_after_database_constraint_failure(
    saved_postgres_context,
    monkeypatch,
):
    client, engine, user_id = saved_postgres_context
    inference = Mock(
        return_value=AIAnalysisResult(classification="legitimate")
    )
    monkeypatch.setattr(analysis_service, "run_saved_inference", inference)
    build_fields = analysis_persistence.build_saved_analysis_fields

    def invalid_storage_fields(*args, **kwargs):
        fields = build_fields(*args, **kwargs)
        # Inject a persistence fault: real PostgreSQL must reject this INSERT.
        fields["confidence"] = 2
        return fields

    with monkeypatch.context() as fault:
        fault.setattr(
            analysis_persistence,
            "build_saved_analysis_fields",
            invalid_storage_fields,
        )
        failed = client.post(
            "/api/analyses",
            json={"body": "Synthetic constraint failure body"},
        )

    assert failed.status_code == 503
    assert failed.json() == {
        "detail": "Saved analysis storage is temporarily unavailable",
        "code": "storage_unavailable",
    }
    for private_detail in (
        "Synthetic constraint failure body",
        "ck_analyzed_emails_confidence_range",
        "INSERT INTO",
        "Traceback",
    ):
        assert private_detail not in failed.text

    with Session(engine) as verification:
        assert verification.scalar(
            select(func.count())
            .select_from(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user_id)
        ) == 0

    healthy = client.post(
        "/api/analyses",
        json={"body": "Synthetic healthy request after rollback"},
    )
    assert healthy.status_code == 201
    record_id = UUID(healthy.json()["id"])
    assert inference.call_count == 2

    with Session(engine) as verification:
        rows = verification.scalars(
            select(AnalyzedEmail).where(AnalyzedEmail.user_id == user_id)
        ).all()
        assert len(rows) == 1
        assert rows[0].id == record_id
        assert rows[0].body == "Synthetic healthy request after rollback"
        assert rows[0].prediction == "legitimate"

    reread = client.get(f"/api/analyses/{record_id}")
    assert reread.status_code == 200
    assert reread.json()["body"] == "Synthetic healthy request after rollback"


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

def test_local_review_saved_fresh_session_read_delete(saved_postgres_context, monkeypatch):
    """Actual disposable PostgreSQL; the audit itself is a software schema fixture."""
    from backend.ai.tfidf_provider import MODEL_SHA256
    from backend.tests.test_live_review import BODY, payload

    client, engine, user_id = saved_postgres_context
    monkeypatch.setattr(saved_create, "get_ai_config", lambda: ("tfidf", None, None))
    _, local_review = payload()
    created = client.post("/api/analyses", json={"subject": "Local review software fixture", "body": BODY,
                                               "local_review": local_review},
                          headers={"Idempotency-Key": "local-review-fixture", "X-PhishLens-Model": MODEL_SHA256})
    assert created.status_code == 201
    saved = created.json(); identifier = saved["id"]
    assert saved["review_status"] == local_review["status"]
    with TestClient(main.app) as fresh_client:
        reread = fresh_client.get("/api/analyses/" + identifier)
        assert reread.status_code == 200
        provenance = reread.json()["analysis_provenance"]["local_review"]
        assert provenance["origin"] == "browser_reported_LLM_audit_not_server_LLM_inference"
        assert len(provenance["server_replayed_classifiers"]) == 3
        assert fresh_client.delete("/api/analyses/" + identifier).status_code == 204
        assert fresh_client.get("/api/analyses/" + identifier).status_code == 404
    with Session(engine) as verification:
        assert verification.scalar(select(func.count()).select_from(AnalyzedEmail).where(AnalyzedEmail.user_id == user_id)) == 0


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
