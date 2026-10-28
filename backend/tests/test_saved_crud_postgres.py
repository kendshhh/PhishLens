import os
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import analysis_service, main
from backend.app.routers.history import DEMO_USER_EMAIL, get_db
from backend.models import AnalyzedEmail, User

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="Requires a disposable local PostgreSQL database",
)


@pytest.fixture
def postgres_context(monkeypatch):
    from backend.core.database import engine

    assert engine.url.host in {"localhost", "127.0.0.1"}
    assert engine.url.database == "phishlens_s2_t1_test"

    unexpected_ai = Mock(
        side_effect=AssertionError(
            "Read, update, and delete must not request the AI service"
        )
    )
    monkeypatch.setattr(main, "get_ai_service", unexpected_ai)

    with engine.connect() as connection:
        outer_transaction = connection.begin()
        session = Session(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        previous_overrides = main.app.dependency_overrides.copy()

        def override_db():
            yield session

        try:
            demo_user = session.scalar(
                select(User).where(User.email == DEMO_USER_EMAIL)
            )
            if demo_user is None:
                demo_user = User(email=DEMO_USER_EMAIL)
                session.add(demo_user)
                session.flush()

            main.app.dependency_overrides[get_db] = override_db

            with TestClient(main.app) as client:
                yield client, session, demo_user.id

            unexpected_ai.assert_not_called()
        finally:
            main.app.dependency_overrides.clear()
            main.app.dependency_overrides.update(previous_overrides)
            session.close()
            outer_transaction.rollback()


def test_read_update_and_delete_with_postgres(postgres_context):
    client, session, demo_user_id = postgres_context

    record = AnalyzedEmail(
        user_id=demo_user_id,
        subject="",
        body="Synthetic PostgreSQL test email",
        prediction="legitimate",
        confidence=None,
        risk_level="low",
        indicators=[],
        explanation=None,
        notes="Original notes",
        feedback="none",
        analysis_mode="mock",
        analysis_provenance={"provider_mode": "mock"},
    )
    session.add(record)
    session.flush()

    record_id = record.id
    url = f"/api/analyses/{record_id}"

    detail = client.get(url)
    assert detail.status_code == 200
    assert detail.json()["subject"] == ""
    assert detail.json()["body"] == record.body
    assert detail.json()["confidence"] is None

    updated = client.patch(
        url,
        json={"notes": "Reviewed using PostgreSQL"},
    )
    assert updated.status_code == 200
    assert updated.json()["feedback"] == "none"

    # Discard cached attributes so the next read uses PostgreSQL.
    session.expire_all()

    reread = client.get(url)
    assert reread.status_code == 200
    assert reread.json()["notes"] == "Reviewed using PostgreSQL"
    assert reread.json()["feedback"] == "none"

    cleared = client.patch(url, json={"notes": None})
    assert cleared.status_code == 200

    session.expire_all()

    cleared_reread = client.get(url)
    assert cleared_reread.status_code == 200
    assert cleared_reread.json()["notes"] is None

    deleted = client.delete(url)
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert session.get(AnalyzedEmail, record_id) is None
    assert client.get(url).status_code == 404


def test_other_users_record_is_not_accessible(postgres_context):
    client, session, _demo_user_id = postgres_context

    other_user = User(email=f"isolation-{uuid4()}@phishlens.test")
    session.add(other_user)
    session.flush()

    record = AnalyzedEmail(
        user_id=other_user.id,
        subject="Another user's synthetic record",
        body="Synthetic isolation test",
        notes="Must remain unchanged",
        feedback="none",
    )
    session.add(record)
    session.flush()

    record_id = record.id
    url = f"/api/analyses/{record_id}"

    responses = [
        client.get(url),
        client.patch(url, json={"notes": "Unauthorized change"}),
        client.delete(url),
    ]

    for response in responses:
        assert response.status_code == 404
        assert response.json() == {"detail": "Analysis not found"}

    session.expire_all()

    existing = session.get(AnalyzedEmail, record_id)
    assert existing is not None
    assert existing.notes == "Must remain unchanged"

    history = client.get("/api/analyses")
    assert history.status_code == 200
    assert all(
        item["id"] != str(record_id)
        for item in history.json()["items"]
    )


def test_legacy_record_with_null_provenance_is_readable(postgres_context):
    client, session, demo_user_id = postgres_context
    record = AnalyzedEmail(
        user_id=demo_user_id,
        subject="Legacy synthetic record",
        body="Synthetic legacy email from before provenance fields existed",
        prediction="legitimate",
        confidence=None,
        risk_level="low",
        indicators=[],
        explanation=None,
        analysis_mode=None,
        analysis_provenance=None,
    )
    session.add(record)
    session.flush()

    record_id = record.id
    listed = client.get("/api/analyses")
    assert listed.status_code == 200
    summaries = {
        item["id"]: item for item in listed.json()["items"]
    }
    assert str(record_id) in summaries
    assert summaries[str(record_id)]["confidence"] is None
    assert "analysis_mode" not in summaries[str(record_id)]
    assert "analysis_provenance" not in summaries[str(record_id)]

    detail = client.get(f"/api/analyses/{record_id}")
    assert detail.status_code == 200
    assert detail.json()["body"] == record.body
    assert detail.json()["analysis_mode"] is None
    assert detail.json()["analysis_provenance"] is None


def test_invalid_ids_are_rejected_without_changing_postgres(
    postgres_context,
    monkeypatch,
):
    client, session, demo_user_id = postgres_context
    statement = (
        select(AnalyzedEmail.__table__)
        .where(AnalyzedEmail.user_id == demo_user_id)
        .order_by(AnalyzedEmail.id)
    )
    before = [dict(row) for row in session.execute(statement).mappings()]
    inference = Mock(
        side_effect=AssertionError("Invalid IDs must not trigger inference")
    )
    monkeypatch.setattr(analysis_service, "run_saved_inference", inference)

    responses = [
        client.get("/api/analyses/not-a-uuid"),
        client.patch(
            "/api/analyses/not-a-uuid",
            json={"notes": "Must not be saved"},
        ),
        client.delete("/api/analyses/not-a-uuid"),
    ]

    assert [response.status_code for response in responses] == [422, 422, 422]
    session.expire_all()
    after = [dict(row) for row in session.execute(statement).mappings()]
    assert after == before
    inference.assert_not_called()
