"""Deployment identity must match the host-provided commit without exposing secrets."""
from fastapi.testclient import TestClient

from backend.app.main import app


def test_deployment_identity(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a" * 40)
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("SECRET_KEY", "must-never-be-returned")
    response = TestClient(app).get("/version")
    assert response.status_code == 200
    assert response.json() == {"commit": "a" * 40, "environment": "staging"}
