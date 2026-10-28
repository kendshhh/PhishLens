from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.routers.history import get_db
from backend.models import AnalyzedEmail


@pytest.fixture
def client_and_db():
    db = Mock(spec=Session)

    def override_db():
        yield db

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_saved_detail_returns_record(client_and_db):
    client, db = client_and_db
    analysis_id = uuid4()

    db.scalar.return_value = AnalyzedEmail(
        id=analysis_id,
        user_id=uuid4(),
        subject="",
        body="Verify your account today.",
        prediction="phishing",
        confidence=Decimal("0.9300"),
        risk_level="high",
        indicators=[
            {
                "type": "evidence",
                "detail": "Requests an account action",
                "quote": "Verify your account",
            }
        ],
        explanation="Tactics: Account urgency",
        notes=None,
        feedback=None,
        analysis_mode="mock",
        analysis_provenance={"provider_mode": "mock"},
        created_at=datetime(2026, 10, 20, 12, 0, tzinfo=UTC),
    )

    response = client.get(f"/api/analyses/{analysis_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(analysis_id),
        "subject": "",
        "body": "Verify your account today.",
        "prediction": "phishing",
        "confidence": 0.93,
        "risk_level": "high",
        "threat_indicators": [
            {
                "type": "evidence",
                "detail": "Requests an account action",
                "quote": "Verify your account",
            }
        ],
        "explanation": "Tactics: Account urgency",
        "notes": None,
        "feedback": None,
        "analysis_mode": "mock",
        "analysis_provenance": {"provider_mode": "mock"},
        "created_at": "2026-10-20T12:00:00Z",
    }


def test_missing_saved_detail_returns_404(client_and_db):
    client, db = client_and_db
    db.scalar.return_value = None

    response = client.get(f"/api/analyses/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Analysis not found"}


def test_saved_detail_database_failure_is_safe(client_and_db):
    client, db = client_and_db
    db.scalar.side_effect = SQLAlchemyError(
        "password=synthetic-secret; private database address"
    )

    response = client.get(f"/api/analyses/{uuid4()}")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "History temporarily unavailable"
    }
    assert "synthetic-secret" not in response.text
    assert "private database address" not in response.text


def test_invalid_saved_detail_id_skips_database(client_and_db):
    client, db = client_and_db

    response = client.get("/api/analyses/not-a-uuid")

    assert response.status_code == 422
    db.scalar.assert_not_called()