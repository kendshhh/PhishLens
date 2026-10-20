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
def delete_context(monkeypatch):
    record = AnalyzedEmail(
        id=uuid4(),
        user_id=uuid4(),
        subject="Synthetic notice",
        body="Synthetic email body",
    )

    db = Mock(spec=Session)
    db.scalar.return_value = record

    unexpected_ai = Mock(
        side_effect=AssertionError("DELETE must not request the AI service")
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


def test_delete_returns_empty_204(delete_context):
    client, db, record = delete_context

    response = client.delete(f"/api/analyses/{record.id}")

    assert response.status_code == 204
    assert response.content == b""
    db.delete.assert_called_once_with(record)
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_delete_missing_record_returns_404(delete_context):
    client, db, record = delete_context
    db.scalar.return_value = None

    response = client.delete(f"/api/analyses/{record.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Analysis not found"}
    db.delete.assert_not_called()
    db.commit.assert_not_called()


def test_delete_invalid_id_skips_database(delete_context):
    client, db, _record = delete_context

    response = client.delete("/api/analyses/not-a-uuid")

    assert response.status_code == 422
    db.scalar.assert_not_called()
    db.delete.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize(
    "failed_operation",
    ["scalar", "delete", "commit"],
)
def test_delete_database_failure_is_safe(
    delete_context,
    failed_operation,
):
    client, db, record = delete_context
    getattr(db, failed_operation).side_effect = SQLAlchemyError(
        "password=synthetic-secret; private database address"
    )

    response = client.delete(f"/api/analyses/{record.id}")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "History temporarily unavailable"
    }
    assert "synthetic-secret" not in response.text
    assert "private database address" not in response.text
    db.rollback.assert_called_once()

    if failed_operation != "commit":
        db.commit.assert_not_called()