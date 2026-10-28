"""Real HTTP/PostgreSQL checks against an isolated migrated test database."""
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.routers import history
from backend.app.routers.history import get_db
from backend.models import AnalyzedEmail, User

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="Requires isolated PostgreSQL test database"
)


def test_history_postgres_read_change_empty_and_isolation(monkeypatch):
    from backend.core.database import engine

    assert engine.url.host in {"localhost", "127.0.0.1"}
    assert engine.url.database.endswith("_test"), (
        "Use a dedicated disposable PostgreSQL database, not phishlens_dev."
    )

    history_email = f"history-{uuid4()}@phishlens.test"
    monkeypatch.setattr(history, "DEMO_USER_EMAIL", history_email)

    # All synthetic records are enclosed in a transaction that always rolls back.
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        previous = app.dependency_overrides.copy()

        def override_db():
            yield session

        try:
            history_user = User(email=history_email)
            other_user = User(email=f"isolation-{uuid4()}@phishlens.test")
            session.add_all([history_user, other_user])
            session.flush()

            history_record = AnalyzedEmail(
                user_id=history_user.id,
                subject="Synthetic history record",
                body="Synthetic history body",
                prediction="phishing",
                confidence=0.93,
                risk_level="high",
                indicators=[],
                explanation="Synthetic test record",
            )
            other_record = AnalyzedEmail(
                user_id=other_user.id,
                subject="Other synthetic user",
                body="Synthetic isolation body",
            )
            session.add_all([history_record, other_record])
            session.flush()

            app.dependency_overrides[get_db] = override_db
            with TestClient(app) as client:
                response = client.get("/api/analyses")
                assert response.status_code == 200
                items = response.json()["items"]
                assert [item["id"] for item in items] == [str(history_record.id)]

                history_record.subject = "Changed synthetic history subject"
                session.flush()
                changed = client.get("/api/analyses")
                assert changed.status_code == 200
                assert changed.json()["items"][0]["subject"] == history_record.subject

                session.delete(history_record)
                session.flush()
                empty = client.get("/api/analyses")
                assert empty.status_code == 200
                assert empty.json() == {"items": []}
        finally:
            app.dependency_overrides = previous
            session.close()
            transaction.rollback()
