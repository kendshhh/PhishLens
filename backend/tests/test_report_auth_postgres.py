"""Real PostgreSQL ownership/persistence with locally signed JWTs; no Neon calls."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.app import auth
from backend.app.main import app
from backend.app.routers import saved_create
from backend.models import AnalyzedEmail, User

pytestmark = pytest.mark.skipif(os.getenv("RUN_DATABASE_TESTS") != "1",
                              reason="Requires disposable local PostgreSQL")


@pytest.fixture
def auth_pg(monkeypatch):
    from backend.core.database import engine
    assert engine.url.host in {"localhost", "127.0.0.1"}
    assert engine.url.database == "phishlens_s2_t1_test"
    assert engine.dialect.name == "postgresql"
    prefix = f"pg-auth-{uuid4()}"
    private = Ed25519PrivateKey.generate()
    base = "https://auth.example.test/test/auth"
    monkeypatch.setenv("REPORT_AUTH_MODE", "neon")
    monkeypatch.setenv("NEON_AUTH_BASE_URL", base)
    monkeypatch.setattr(saved_create, "get_ai_config", lambda: ("mock", None, None))
    # Only key retrieval is replaced. Real JWT verification, identity resolution,
    # sync history queries, async create transactions and inference all execute.
    monkeypatch.setattr(auth, "jwks_client", lambda url: SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(key=private.public_key())))
    def claims(name, **changes):
        now = datetime.now(UTC)
        payload = {"sub": f"{prefix}-{name}", "email": f"{prefix}-{name}@example.test",
                   "emailVerified": True, "iss": "https://auth.example.test",
                   "aud": "https://auth.example.test", "iat": now,
                   "exp": now + timedelta(minutes=15)}
        payload.update(changes)
        return {"Authorization": "Bearer " + jwt.encode(payload, private, algorithm="EdDSA")}
    def user(name):
        with Session(engine) as db:
            return db.scalar(select(User).where(User.neon_auth_subject == f"{prefix}-{name}"))
    with Session(engine) as db:
        legacy = User(id=uuid4(), email=f"{prefix}-legacy@example.test")
        db.add(legacy)
        db.flush()
        legacy_id = legacy.id
        record = AnalyzedEmail(id=uuid4(), user_id=legacy_id, body="Synthetic legacy email",
                               subject="Legacy", indicators=[], analysis_mode="mock")
        db.add(record)
        db.commit()
        legacy_record = record.id
    try:
        with TestClient(app) as client:
            yield SimpleNamespace(client=client, headers=claims, user=user, engine=engine,
                                  prefix=prefix, legacy_id=legacy_id, legacy_record=legacy_record)
    finally:
        # Restrict cleanup to this fixture's unique email prefix, including legacy.
        with Session(engine) as db:
            db.execute(delete(User).where(User.email.startswith(prefix)))
            db.commit()


def create(context, name, key="same-key", body="Synthetic PostgreSQL email"):
    response = context.client.post("/api/analyses", headers={**context.headers(name), "Idempotency-Key": key},
                                   json={"body": body})
    assert response.status_code == 201, response.text
    return response.json()


def test_authenticated_create_retry_and_same_key_are_per_user(auth_pg):
    c = auth_pg
    first = create(c, "a")
    replay = create(c, "a")
    second = create(c, "b")
    assert first["id"] == replay["id"]
    assert first["id"] != second["id"]
    for name, report in [("a", first), ("b", second)]:
        with Session(c.engine) as db:
            row = db.get(AnalyzedEmail, UUID(report["id"]))
            assert row.user_id == c.user(name).id
            assert db.scalar(select(func.count()).select_from(AnalyzedEmail).where(
                AnalyzedEmail.user_id == row.user_id)) == 1
    conflict = c.client.post("/api/analyses", headers={**c.headers("a"), "Idempotency-Key": "same-key"},
                             json={"body": "Different synthetic payload"})
    assert conflict.status_code == 409


def test_two_user_crud_and_legacy_separation_survive_fresh_clients(auth_pg):
    c = auth_pg
    reports = {name: create(c, name) for name in ["a", "b"]}
    for name, other in [("a", "b"), ("b", "a")]:
        with TestClient(app) as fresh:
            headers = c.headers(name)
            listed = fresh.get("/api/analyses", headers=headers)
            assert listed.status_code == 200
            assert [r["id"] for r in listed.json()["items"]] == [reports[name]["id"]]
            for record in [reports[other]["id"], str(c.legacy_record)]:
                url = f"/api/analyses/{record}"
                assert fresh.get(url, headers=headers).status_code == 404
                assert fresh.patch(url, headers=headers, json={"notes": "foreign edit"}).status_code == 404
                assert fresh.delete(url, headers=headers).status_code == 404
    url = "/api/analyses/" + reports["a"]["id"]
    updated = c.client.patch(url, headers=c.headers("a"), json={"notes": "Owner note", "feedback": "none"})
    assert updated.status_code == 200
    with TestClient(app) as fresh:
        assert fresh.get(url, headers=c.headers("a")).json()["notes"] == "Owner note"
        assert fresh.delete(url, headers=c.headers("a")).status_code == 204
        assert fresh.get(url, headers=c.headers("a")).status_code == 404
        assert fresh.get("/api/analyses/" + reports["b"]["id"], headers=c.headers("b")).status_code == 200
    with Session(c.engine) as db:
        assert db.get(AnalyzedEmail, c.legacy_record) is not None


def test_unverified_expired_or_missing_token_creates_no_mapping(auth_pg):
    c = auth_pg
    for headers, status in [({}, 401), (c.headers("bad", emailVerified=False), 403),
                            (c.headers("bad", exp=1), 401)]:
        response = c.client.post("/api/analyses", headers=headers, json={"body": "Synthetic email"})
        assert response.status_code == status
    assert c.user("bad") is None


def test_email_collision_does_not_claim_legacy_or_other_subject(auth_pg):
    c = auth_pg
    for email in [f"{c.prefix}-legacy@example.test", f"{c.prefix}-a@example.test"]:
        if email.endswith("-a@example.test"):
            assert c.client.get("/api/analyses", headers=c.headers("a")).status_code == 200
        response = c.client.get("/api/analyses", headers=c.headers("claim", email=email))
        assert response.status_code == 409
    assert c.user("claim") is None
    with Session(c.engine) as db:
        assert db.get(User, c.legacy_id).neon_auth_subject is None


def test_concurrent_first_requests_create_one_subject_mapping(auth_pg):
    c = auth_pg
    headers = c.headers("race")
    def request(_):
        with TestClient(app) as client:
            return client.get("/api/analyses", headers=headers).status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(request, range(4))) == [200] * 4
    with Session(c.engine) as db:
        assert db.scalar(select(func.count()).select_from(User).where(
            User.neon_auth_subject == f"{c.prefix}-race")) == 1


def test_subject_mapping_is_stable_when_email_changes(auth_pg):
    c = auth_pg
    report = create(c, "a")
    owner = c.user("a").id
    response = c.client.get("/api/analyses", headers=c.headers("a", email=f"{c.prefix}-changed@example.test"))
    assert response.status_code == 200
    assert [r["id"] for r in response.json()["items"]] == [report["id"]]
    assert c.user("a").id == owner
