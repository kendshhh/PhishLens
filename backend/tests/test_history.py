from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from backend.app.main import app
from backend.app.routers.history import get_analyses, get_db


def test_empty_history():
    db = Mock()
    db.scalar.return_value = None

    result = get_analyses(db)

    assert result == {"items": []}


def test_saved_history():
    db = Mock()

    demo_user = SimpleNamespace(id=uuid4())
    db.scalar.return_value = demo_user

    analysis = SimpleNamespace(
        id=uuid4(),
        subject="Synthetic account notice",
        prediction="phishing",
        confidence=0.93,
        risk_level="high",
        indicators=[{"type": "link", "detail": "Demo link"}],
        explanation="Synthetic test email",
        created_at=datetime(2026, 10, 14, tzinfo=UTC),
        analysis_provenance=None,
    )

    db.scalars.return_value.all.return_value = [analysis]

    result = get_analyses(db)

    assert len(result["items"]) == 1
    assert result["items"][0]["subject"] == "Synthetic account notice"
    assert result["items"][0]["prediction"] == "phishing"
    assert result["items"][0]["confidence"] == 0.93


def test_history_http_saved():
    db = Mock()
    db.scalar.return_value = SimpleNamespace(id=uuid4())
    analysis_id = uuid4()
    db.scalars.return_value.all.return_value = [SimpleNamespace(
        id=analysis_id,
        subject="Synthetic account notice",
        prediction="phishing",
        confidence=0.93,
        risk_level="high",
        indicators=[{"type": "link", "detail": "Demo link"}],
        explanation="Synthetic test email",
        created_at=datetime(2026, 10, 14, tzinfo=UTC),
        analysis_provenance=None,
    )]

    def override_db():
        yield db

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            response = client.get("/api/analyses")
    finally:
        app.dependency_overrides = previous_overrides

    assert response.status_code == 200
    assert response.json() == {"items": [{
        "id": str(analysis_id),
        "subject": "Synthetic account notice",
        "prediction": "phishing",
        "confidence": 0.93,
        "risk_level": "high",
        "threat_indicators": [{"type": "link", "detail": "Demo link"}],
        "explanation": "Synthetic test email",
        "created_at": "2026-10-14T00:00:00+00:00",
    }]}


def test_history_http_empty():
    db = Mock()
    db.scalar.return_value = SimpleNamespace(id=uuid4())
    db.scalars.return_value.all.return_value = []

    def override_db():
        yield db

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            response = client.get("/api/analyses")
    finally:
        app.dependency_overrides = previous_overrides

    assert response.status_code == 200
    assert response.json() == {"items": []}


@pytest.mark.parametrize("prediction", ["phishing", "legitimate"])
@pytest.mark.parametrize("review_status", [None, "released", "uncertain"])
def test_history_http_preserves_review_status_and_legacy_records(prediction, review_status):
    db = Mock()
    db.scalar.return_value = SimpleNamespace(id=uuid4())
    provenance = {"local_review": {"status": review_status}} if review_status else None
    db.scalars.return_value.all.return_value = [SimpleNamespace(
        id=uuid4(), subject="Software review fixture", prediction=prediction,
        confidence=None, risk_level="low", indicators=[], explanation="Software fixture.",
        created_at=datetime(2026, 10, 31, tzinfo=UTC), analysis_provenance=provenance,
    )]
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            response = client.get("/api/analyses")
    finally:
        app.dependency_overrides = previous_overrides
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["prediction"] == prediction  # Keep the server-owned primary label.
    if review_status is None:
        assert "review_status" not in item
    else:
        assert item["review_status"] == review_status
    assert "analysis_provenance" not in item
    assert "body" not in item


@pytest.mark.parametrize("failed_query", ["scalar", "scalars"])
def test_history_http_database_failure(failed_query):
    db = Mock()
    db.scalar.return_value = SimpleNamespace(id=uuid4())
    getattr(db, failed_query).side_effect = SQLAlchemyError("private database credentials")
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            response = client.get("/api/analyses")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 503
    assert response.json() == {"detail": "History temporarily unavailable"}
    assert "private" not in response.text
