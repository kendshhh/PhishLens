from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from backend.app import main


def test_readiness_success(monkeypatch):
    monkeypatch.setattr(main, "check_database", lambda: None)

    with TestClient(main.app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
    }


def test_readiness_database_failure(monkeypatch):
    def fail_database():
        raise SQLAlchemyError("private connection details")

    monkeypatch.setattr(main, "check_database", fail_database)

    with TestClient(main.app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "database": "unavailable",
    }
    assert "private connection details" not in response.text