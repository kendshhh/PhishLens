from fastapi.testclient import TestClient

from backend.ai.errors import ModelUnavailableError
from backend.app import main


def test_blank_text_has_structured_422_error():
    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "   "},
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "invalid_input",
            "message": "Invalid email input",
            "fields": [
                {"field": "text", "code": "blank"},
            ],
        },
    }


def test_inference_failure_has_structured_502_error(monkeypatch):
    class FailingService:
        def analyze_email(self, *, subject, sender, body):
            raise RuntimeError("private provider details")

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (FailingService(), "gemini"),
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "Synthetic email body"},
        )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "inference_failed",
            "message": "Analysis failed",
        },
    }
    assert "private provider details" not in response.text


def test_missing_model_has_structured_503_error(monkeypatch):
    class MissingModelService:
        def analyze_email(self, *, subject, sender, body):
            raise ModelUnavailableError("/private/models/checkpoint")

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (MissingModelService(), "local"),
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "Synthetic email body"},
        )

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "analysis_unavailable",
            "message": "Analysis temporarily unavailable",
        },
    }
    assert "/private/models/checkpoint" not in response.text