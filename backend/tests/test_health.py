from fastapi.testclient import TestClient

from backend.app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "phishlens-api",
    }

def test_health_returns_json_content_type():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.headers["content-type"].startswith("application/json")
