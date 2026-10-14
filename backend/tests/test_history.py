
import os
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://test:test@localhost/phishlens_dev"
)

from backend.app.routers.history import get_analyses


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
