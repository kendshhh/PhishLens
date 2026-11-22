import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routers import neon_auth

EXTENSION_ORIGIN = "chrome-extension://ceneonaedddlkdocdapimkfggbjcchlb"
STAGING_ORIGIN = "https://phishlens-staging.onrender.com"
AUTH_BASE = "https://ep-test.neonauth.c-4.ap-southeast-1.aws.neon.tech/phishlens_dev/auth"


def test_auth_proxy_forwards_to_neon_with_trusted_origin_and_relays_session(monkeypatch):
    monkeypatch.setenv("NEON_AUTH_BASE_URL", AUTH_BASE)
    captured = {}
    transport = httpx.MockTransport(lambda request: _response(request, captured))
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        neon_auth.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=transport, **kwargs),
    )

    response = TestClient(app, base_url=STAGING_ORIGIN).post(
        "/api/auth/sign-in/email?returnTo=%2Faccount",
        headers={"Origin": EXTENSION_ORIGIN, "Cookie": "session=incoming"},
        json={"email": "user@example.test", "password": "synthetic"},
    )

    assert response.status_code == 200
    assert captured["url"] == AUTH_BASE + "/sign-in/email?returnTo=%2Faccount"
    assert captured["origin"] == STAGING_ORIGIN
    assert captured["referer"] == STAGING_ORIGIN + "/"
    assert captured["cookie"] == "session=incoming"
    assert response.headers["Access-Control-Allow-Origin"] == EXTENSION_ORIGIN
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert response.headers["set-auth-jwt"] == "synthetic.jwt.token"
    cookie = response.headers.get_list("set-cookie")[0]
    assert "Domain=" not in cookie
    assert "SameSite=None" in cookie
    assert "Secure" in cookie


def _response(request, captured):
    captured["url"] = str(request.url)
    captured["origin"] = request.headers.get("origin")
    captured["referer"] = request.headers.get("referer")
    captured["cookie"] = request.headers.get("cookie")
    return httpx.Response(
        200,
        json={"user": {"id": "synthetic-user", "emailVerified": True}},
        headers=[
            ("set-cookie", "session=synthetic; Path=/; Domain=auth.example.test; Secure; HttpOnly; SameSite=Lax"),
            ("set-auth-jwt", "synthetic.jwt.token"),
        ],
    )


def test_auth_proxy_rejects_other_origins_before_contacting_neon(monkeypatch):
    calls = []
    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: calls.append(request) or httpx.Response(200))
    monkeypatch.setenv("NEON_AUTH_BASE_URL", AUTH_BASE)
    monkeypatch.setattr(
        neon_auth.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=transport, **kwargs),
    )

    response = TestClient(app, base_url=STAGING_ORIGIN).post(
        "/api/auth/sign-in/email",
        headers={"Origin": "chrome-extension://not-phishlens"},
        json={},
    )

    assert response.status_code == 403
    assert calls == []


def test_auth_proxy_answers_extension_preflight_without_contacting_neon():
    response = TestClient(app, base_url=STAGING_ORIGIN).options(
        "/api/auth/sign-in/email",
        headers={
            "Origin": EXTENSION_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == EXTENSION_ORIGIN
    assert response.headers["Access-Control-Allow-Headers"] == "content-type"


@pytest.mark.parametrize("auth_url", [
    "", "https://[malformed-host", "https://ep-test.neonauth.aws.neon.tech:invalid/neondb/auth",
    "https://ep-test.neonauth.aws.neon.tech:70000/neondb/auth",
    "https://user:secret@ep-test.neonauth.aws.neon.tech/neondb/auth",
    "https://untrusted.example.test/neondb/auth",
])
def test_invalid_proxy_configuration_returns_safe_503_before_network(monkeypatch, auth_url):
    monkeypatch.setenv("NEON_AUTH_BASE_URL", auth_url)
    def unexpected_client(**kwargs):
        pytest.fail("Invalid configuration must not contact Auth")
    monkeypatch.setattr(neon_auth.httpx, "AsyncClient", unexpected_client)
    response = TestClient(app, base_url=STAGING_ORIGIN).post(
        "/api/auth/sign-in/email", headers={"Origin": EXTENSION_ORIGIN}, json={},
    )
    assert response.status_code == 503
    assert response.json() == {"message": "Authentication configuration unavailable"}
    assert response.headers["Access-Control-Allow-Origin"] == EXTENSION_ORIGIN
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
