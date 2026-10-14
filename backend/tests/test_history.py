
import os
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://test:test@localhost/phishlens_dev"
)

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routers.history import get_analyses
from backend.core.database import get_db


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
        created_at=datetime(2026, 10, 14, tzinfo=UTC)
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
