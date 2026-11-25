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


def test_image_backed_deployment_reports_embedded_source_sha(monkeypatch):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.setenv("PHISHLENS_SOURCE_SHA", "b" * 40)
    monkeypatch.setenv("APP_ENV", "staging")
    response = TestClient(app).get("/version")
    assert response.status_code == 200
    assert response.json() == {"commit": "b" * 40, "environment": "staging"}


def test_render_commit_remains_authoritative_for_git_backed_service(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "c" * 40)
    monkeypatch.setenv("PHISHLENS_SOURCE_SHA", "d" * 40)
    monkeypatch.setenv("APP_ENV", "production")
    response = TestClient(app).get("/version")
    assert response.status_code == 200
    assert response.json() == {"commit": "c" * 40, "environment": "production"}
