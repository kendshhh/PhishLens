"""Real HTTP/PostgreSQL checks against the isolated migrated and seeded CI DB."""
import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.routers.history import get_db
from backend.models import AnalyzedEmail, User

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="Requires isolated PostgreSQL test database"
)


def test_history_postgres_read_change_empty_and_isolation():
    from backend.core.database import engine
    assert engine.url.host in {"localhost", "127.0.0.1"}
    assert engine.url.database == "phishlens_dev"
    analysis_id = UUID("29d80c39-ec0d-4db8-a6e5-87444ba2600c")
    # Every write rolls back, including if an assertion fails.
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection)
        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = lambda: session
        try:
            analysis = session.get(AnalyzedEmail, analysis_id)
            assert analysis is not None, "Run migrations and synthetic seed first"
            other_user = User(email=f"isolation-{uuid4()}@phishlens.test")
            session.add(other_user)
            session.flush()
            other = AnalyzedEmail(user_id=other_user.id, subject="Other synthetic user", body="Test")
            session.add(other)
            session.flush()
            with TestClient(app) as client:
                response = client.get("/api/analyses")
                assert response.status_code == 200
                items = response.json()["items"]
                assert any(item["id"] == str(analysis_id) for item in items)
                assert all(item["id"] != str(other.id) for item in items)
                analysis.subject = "Changed synthetic history subject"
                session.flush()
                changed = client.get("/api/analyses")
                assert changed.status_code == 200
                assert next(i for i in changed.json()["items"] if i["id"] == str(analysis_id))["subject"] == analysis.subject
                demo_id = session.scalar(select(User.id).where(User.email == "demo@phishlens.test"))
                session.execute(delete(AnalyzedEmail).where(AnalyzedEmail.user_id == demo_id))
                empty = client.get("/api/analyses")
                assert empty.status_code == 200
                assert empty.json() == {"items": []}
        finally:
            app.dependency_overrides = previous
            session.close()
            transaction.rollback()
