import pytest
from fastapi.testclient import TestClient

from backend.ai.service import AIService
from backend.app import main


@pytest.mark.parametrize(
    "model_output",
    [
        {"classification": "unknown"},
        {"classification": "phishing", "confidence": float("nan")},
        {"classification": "phishing", "confidence": 1.1},
        {
            "classification": "phishing",
            "evidence": [
                {
                    "text": "https://not-in-email.example",
                    "reason": "Link in email",
                }
            ],
        },
    ],
)
def test_invalid_model_output_never_becomes_a_verdict(monkeypatch, model_output):
    class FakeProvider:
        def analyze(self, email_text):
            return model_output

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (AIService(FakeProvider()), "gemini"),
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
    assert "classification" not in response.json()
    assert "not-in-email.example" not in response.text