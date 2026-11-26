"""Auth bridge serves local SDK assets, with no hosted requests or DB writes."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

ORIGIN = "https://api.example.test"
AUTH_URL = "https://auth.example.test/neondb/auth"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("REPORT_AUTH_MODE", "neon")
    monkeypatch.setenv("NEON_AUTH_BASE_URL", AUTH_URL)
    monkeypatch.setenv("AUTH_BRIDGE_ORIGIN", ORIGIN)
    with TestClient(app, base_url=ORIGIN) as test_client:
        yield test_client


@pytest.mark.parametrize("path", ["/auth/bridge", "/auth/bridge/client.js", "/auth/bridge/sdk.mjs"])
def test_bridge_assets_are_origin_bound_and_uncached(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    csp = response.headers["content-security-policy"]
    assert "frame-ancestors chrome-extension://ceneonaedddlkdocdapimkfggbjcchlb" in csp
    assert "connect-src https://auth.example.test" in csp
    assert "script-src 'self'" in csp
    assert "'unsafe-inline'" not in csp


def test_bridge_uses_server_configuration_and_only_explicit_assets(client):
    response = client.get("/auth/bridge?authUrl=https://attacker.example")
    assert f'data-auth-url="{AUTH_URL}"' in response.text
    assert "attacker.example" not in response.text
    assert client.get("/auth/bridge/.env").status_code == 404
    assert client.post("/auth/bridge", json={"password": "synthetic"}).status_code == 405


@pytest.mark.parametrize("name,value", [
    ("REPORT_AUTH_MODE", "demo"), ("REPORT_AUTH_MODE", "invalid"),
    ("NEON_AUTH_BASE_URL", "https://[invalid"),
    ("NEON_AUTH_BASE_URL", "https://auth.example.test:invalid/neondb/auth"),
    ("NEON_AUTH_BASE_URL", "http://auth.example.test/neondb/auth"),
    ("NEON_AUTH_BASE_URL", AUTH_URL + "?token=private"),
    ("NEON_AUTH_BASE_URL", "https://user:password@auth.example.test/neondb/auth"),
    ("AUTH_BRIDGE_ORIGIN", ""), ("AUTH_BRIDGE_ORIGIN", "https://other.example.test"),
    ("AUTH_BRIDGE_ORIGIN", "https://api.example.test/other"),
])
def test_invalid_configuration_fails_closed(client, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    response = client.get("/auth/bridge")
    assert response.status_code == 503
    assert "private" not in response.text
    assert "password" not in response.text


def test_render_public_url_is_used_without_an_override(client, monkeypatch):
    monkeypatch.delenv("AUTH_BRIDGE_ORIGIN")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", ORIGIN)
    assert client.get("/auth/bridge").status_code == 200
    assert client.get("/auth/bridge", headers={"host": "other.example.test"}).status_code == 503
