"""Offline signed-token and API ownership tests; no hosted Auth calls."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jwt.exceptions import PyJWKClientConnectionError
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app import auth
from backend.app.main import app
from backend.app.routers.history import get_db
from backend.models import AnalyzedEmail, Base, User

BASE = "https://auth.example.test/test/auth"
ORIGIN = "https://auth.example.test"

@pytest.fixture
def signed(monkeypatch):
    monkeypatch.setenv("REPORT_AUTH_MODE", "neon")
    monkeypatch.setenv("NEON_AUTH_BASE_URL", BASE)
    key = Ed25519PrivateKey.generate()
    monkeypatch.setattr(auth, "jwks_client", lambda base: SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key())))
    def token(**changes):
        now = datetime.now(UTC)
        claims = {"sub": "subject-a", "email": "a@example.test", "emailVerified": True,
                      "iss": ORIGIN, "aud": ORIGIN, "iat": now, "exp": now + timedelta(minutes=15)}
        claims.update(changes)
        return jwt.encode(claims, key, algorithm="EdDSA", headers={"kid": "offline-test"})
    return token

def test_valid_signed_identity(signed):
    assert auth.verify_identity(signed()) == ("subject-a", "a@example.test")

@pytest.mark.parametrize("changes,status", [
    ({"exp": 1}, 401), ({"iat": 9999999999}, 401),
    ({"iss": "https://other.test"}, 401), ({"aud": "other"}, 401),
    ({"sub": ""}, 401), ({"email": None}, 401),
    ({"emailVerified": False}, 403), ({"emailVerified": "true"}, 403),
    ({"banned": True}, 403),
])
def test_rejected_claims(signed, changes, status):
    with pytest.raises(HTTPException) as error:
        auth.verify_identity(signed(**changes))
    assert error.value.status_code == status

def test_missing_claim_and_wrong_signature(signed):
    token = signed()
    claims = jwt.decode(token, options={"verify_signature": False})
    del claims["exp"]
    forged = jwt.encode(claims, Ed25519PrivateKey.generate(), algorithm="EdDSA")
    for value in [forged, "not-a-token", jwt.encode(claims, "x" * 32, algorithm="HS256")]:
        with pytest.raises(HTTPException) as error:
            auth.verify_identity(value)
        assert error.value.status_code == 401

def test_jwks_outage_is_not_invalid_credentials(signed, monkeypatch):
    fail = Mock(side_effect=PyJWKClientConnectionError("internal detail"))
    monkeypatch.setattr(auth, "jwks_client", lambda base: SimpleNamespace(get_signing_key_from_jwt=fail))
    with pytest.raises(HTTPException) as error:
        auth.verify_identity(signed())
    assert error.value.status_code == 503
    assert "internal detail" not in error.value.detail

@pytest.mark.parametrize("method,path,body", [
    ("GET", "/api/analyses", None),
    ("GET", "/api/analyses/00000000-0000-0000-0000-000000000001", None),
    ("POST", "/api/analyses", {"body": "Synthetic email"}),
    ("PATCH", "/api/analyses/00000000-0000-0000-0000-000000000001", {"notes": "test"}),
    ("DELETE", "/api/analyses/00000000-0000-0000-0000-000000000001", None),
])
def test_all_crud_requires_authentication(signed, method, path, body):
    old = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.request(method, path, json=body)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    finally:
        app.dependency_overrides = old


@pytest.mark.parametrize("method,path,body", [
    ("GET", "/api/analyses", None),
    ("GET", "/api/analyses/00000000-0000-0000-0000-000000000001", None),
    ("POST", "/api/analyses", {"body": "Synthetic email"}),
    ("PATCH", "/api/analyses/00000000-0000-0000-0000-000000000001", {"notes": "test"}),
    ("DELETE", "/api/analyses/00000000-0000-0000-0000-000000000001", None),
])
@pytest.mark.parametrize("kind,status", [
    ("malformed", 401), ("expired", 401), ("unverified", 403), ("banned", 403),
])
def test_rejected_bearers_block_all_crud_before_mapping(signed, monkeypatch, method, path, body, kind, status):
    tokens = {
        "malformed": "not-a-signed-token",
        "expired": signed(exp=1),
        "unverified": signed(emailVerified=False),
        "banned": signed(banned=True),
    }
    token = tokens[kind]
    resolve = Mock(side_effect=AssertionError("Rejected bearer reached user mapping"))
    monkeypatch.setattr(auth, "resolve_user", resolve)
    old = app.dependency_overrides.copy()
    # A route reaching storage with this dependency would fail, rather than
    # silently passing against an unrelated local or hosted database.
    app.dependency_overrides[get_db] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.request(method, path, json=body,
                                      headers={"Authorization": "Bearer " + token})
        assert response.status_code == status
        resolve.assert_not_called()
        assert token not in response.text
        assert "a@example.test" not in response.text
        if status == 401:
            assert response.headers["www-authenticate"] == "Bearer"
    finally:
        app.dependency_overrides = old

# SQLite exercises actual owner filters without a hosted database. PostgreSQL
# locks, migrations, grants and pooled contexts need separate integration tests.
@compiles(JSONB, "sqlite")
def sqlite_json(element, compiler, **kw):
    return "JSON"

@pytest.fixture
def storage(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        users = [User(id=uuid4(), email=f"{name}@example.test", neon_auth_subject=name)
                 for name in ["subject-a", "subject-b"]]
        demo = User(id=uuid4(), email="demo@phishlens.test")
        db.add_all([*users, demo])
        records = [AnalyzedEmail(id=uuid4(), user_id=u.id, subject=u.email, body="Synthetic email",
            prediction="legitimate", risk_level="low", indicators=[], analysis_mode="mock",
            analysis_provenance={"provider_mode": "mock"}, created_at=datetime.now(UTC)) for u in [*users, demo]]
        db.add_all(records)
        db.commit()
        old = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = lambda: db
        monkeypatch.setattr(auth, "resolve_user", lambda sub, email: next(u.id for u in users if u.neon_auth_subject == sub))
        try:
            yield db, users, records
        finally:
            app.dependency_overrides = old
    engine.dispose()

def test_two_users_cannot_read_edit_delete_each_others_or_demo_records(signed, storage):
    db, users, records = storage
    with TestClient(app) as client:
        for index, user in enumerate(users):
            headers = {"Authorization": "Bearer " + signed(sub=user.neon_auth_subject, email=user.email)}
            listing = client.get("/api/analyses", headers=headers)
            assert listing.status_code == 200
            assert [r["id"] for r in listing.json()["items"]] == [str(records[index].id)]
            assert client.get(f"/api/analyses/{records[index].id}", headers=headers).status_code == 200
            for other in records:
                if other.user_id == user.id:
                    continue
                url = f"/api/analyses/{other.id}"
                assert client.get(url, headers=headers).status_code == 404
                assert client.patch(url, headers=headers, json={"notes": "attack"}).status_code == 404
                assert client.delete(url, headers=headers).status_code == 404
                assert db.get(AnalyzedEmail, other.id) is not None
        headers = {"Authorization": "Bearer " + signed()}
        url = f"/api/analyses/{records[0].id}"
        assert client.patch(url, headers=headers, json={"notes": "My note"}).status_code == 200
        assert client.delete(url, headers=headers).status_code == 204
        assert client.get(url, headers=headers).status_code == 404

def test_owner_cannot_be_supplied_in_body(signed, storage):
    with TestClient(app) as client:
        response = client.post("/api/analyses", headers={"Authorization": "Bearer " + signed()},
                               json={"body": "Synthetic email", "owner_id": str(uuid4())})
    assert response.status_code == 422


def test_identity_mapping_never_links_by_email(monkeypatch):
    import sys
    from unittest.mock import MagicMock

    from sqlalchemy.exc import IntegrityError
    db = MagicMock()
    db.scalar.side_effect = [None, None]
    db.commit.side_effect = IntegrityError("insert", {}, Exception("email already exists"))
    factory = MagicMock()
    factory.return_value.__enter__.return_value = db
    monkeypatch.setitem(sys.modules, "backend.core.database", SimpleNamespace(SessionLocal=factory))
    with pytest.raises(HTTPException) as error:
        auth.resolve_user("new-subject", "demo@phishlens.test")
    assert error.value.status_code == 409
    added = db.add.call_args.args[0]
    assert added.neon_auth_subject == "new-subject"
    assert db.rollback.call_count == 1


def test_concurrent_first_login_resolves_winner(monkeypatch):
    import sys
    from unittest.mock import MagicMock

    from sqlalchemy.exc import IntegrityError
    owner = uuid4()
    db = MagicMock()
    db.scalar.side_effect = [None, SimpleNamespace(id=owner)]
    db.commit.side_effect = IntegrityError("insert", {}, Exception("concurrent subject"))
    factory = MagicMock()
    factory.return_value.__enter__.return_value = db
    monkeypatch.setitem(sys.modules, "backend.core.database", SimpleNamespace(SessionLocal=factory))
    assert auth.resolve_user("new-subject", "new@example.test") == owner


def test_unknown_mode_never_falls_back_to_demo(monkeypatch):
    monkeypatch.setenv("REPORT_AUTH_MODE", "invalid")
    with pytest.raises(HTTPException) as error:
        auth.report_owner(None)
    assert error.value.status_code == 503


def test_expiry_claim_is_required(signed):
    with pytest.raises(HTTPException) as error:
        auth.verify_identity(signed(exp=None))
    assert error.value.status_code == 401


def test_auth_mode_loads_local_settings_before_first_request(monkeypatch, tmp_path):
    from backend.core import config
    settings = tmp_path / "auth-test.env"
    settings.write_text("REPORT_AUTH_MODE=neon\n")
    monkeypatch.setattr(config, "ENV_FILE", settings)
    monkeypatch.setenv("REPORT_AUTH_MODE", "demo")
    monkeypatch.delenv("REPORT_AUTH_MODE")
    assert auth.auth_mode() == "neon"
    with pytest.raises(HTTPException) as error:
        auth.report_owner(None)
    assert error.value.status_code == 401


def test_deployment_auth_mode_takes_precedence_over_local_file(monkeypatch, tmp_path):
    from backend.core import config
    settings = tmp_path / "auth-test.env"
    settings.write_text("REPORT_AUTH_MODE=demo\n")
    monkeypatch.setattr(config, "ENV_FILE", settings)
    monkeypatch.setenv("REPORT_AUTH_MODE", "neon")
    assert auth.auth_mode() == "neon"
