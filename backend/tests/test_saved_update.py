from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app import main
from backend.app.routers.history import get_db
from backend.models import AnalyzedEmail


@pytest.fixture
def update_context(monkeypatch):
    record = AnalyzedEmail(
        id=uuid4(),
        user_id=uuid4(),
        subject="Synthetic notice",
        body="Synthetic email body",
        prediction="legitimate",
        confidence=None,
        risk_level="low",
        indicators=[],
        explanation=None,
        notes="Original notes",
        feedback="none",
        analysis_mode="mock",
        analysis_provenance={"provider_mode": "mock"},
        created_at=datetime(2026, 10, 20, 12, 0, tzinfo=UTC),
    )

    db = Mock(spec=Session)
    db.scalar.return_value = record

    unexpected_ai = Mock(
        side_effect=AssertionError("PATCH must not request the AI service")
    )
    monkeypatch.setattr(main, "get_ai_service", unexpected_ai)

    def override_db():
        yield db

    previous_overrides = main.app.dependency_overrides.copy()
    main.app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(main.app) as client:
            yield client, db, record
        unexpected_ai.assert_not_called()
    finally:
        main.app.dependency_overrides.clear()
        main.app.dependency_overrides.update(previous_overrides)


def test_update_notes_preserves_feedback(update_context):
    client, db, record = update_context

    response = client.patch(
        f"/api/analyses/{record.id}",
        json={"notes": "Reviewed manually"},
    )

    assert response.status_code == 200
    assert response.json()["notes"] == "Reviewed manually"
    assert response.json()["feedback"] == "none"
    assert response.json()["prediction"] == "legitimate"
    assert response.json()["confidence"] is None
    db.flush.assert_called_once()
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_update_feedback_preserves_notes(update_context):
    client, db, record = update_context

    response = client.patch(
        f"/api/analyses/{record.id}",
        json={"feedback": "false_negative"},
    )

    assert response.status_code == 200
    assert response.json()["feedback"] == "false_negative"
    assert response.json()["notes"] == "Original notes"
    db.commit.assert_called_once()


def test_update_can_clear_notes(update_context):
    client, db, record = update_context

    response = client.patch(
        f"/api/analyses/{record.id}",
        json={"notes": None},
    )

    assert response.status_code == 200
    assert response.json()["notes"] is None
    assert response.json()["feedback"] == "none"
    db.commit.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"prediction": "phishing"},
        {"feedback": "unsupported"},
        {"notes": "x" * 2001},
    ],
    ids=[
        "empty-patch",
        "protected-field",
        "invalid-feedback",
        "oversized-notes",
    ],
)
def test_invalid_update_skips_database(update_context, payload):
    client, db, record = update_context

    response = client.patch(
        f"/api/analyses/{record.id}",
        json=payload,
    )

    assert response.status_code == 422
    db.scalar.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


def test_update_missing_record_returns_404(update_context):
    client, db, record = update_context
    db.scalar.return_value = None

    response = client.patch(
        f"/api/analyses/{record.id}",
        json={"notes": "Reviewed"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Analysis not found"}
    db.flush.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize("failed_operation", ["flush", "commit"])
def test_failed_update_rolls_back_safely(
    update_context,
    failed_operation,
):
    client, db, record = update_context
    getattr(db, failed_operation).side_effect = SQLAlchemyError(
        "password=synthetic-secret; private database address"
    )

    response = client.patch(
        f"/api/analyses/{record.id}",
        json={"notes": "Reviewed"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "History temporarily unavailable"
    }
    assert "synthetic-secret" not in response.text
    assert "private database address" not in response.text
    db.rollback.assert_called_once()

    if failed_operation == "flush":
        db.commit.assert_not_called()