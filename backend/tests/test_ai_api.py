from fastapi.testclient import TestClient

from backend.ai.schemas import AIAnalysisResult
from backend.app import main


def test_analysis_endpoint_uses_ai_service(monkeypatch):
    calls = []

    class FakeService:
        def analyze_email(self, *, subject, sender, body):
            calls.append((subject, sender, body))
            return AIAnalysisResult(
                classification="phishing",
                tactics=["urgency"],
                recommendations=["Verify through a trusted channel."],
            )

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (FakeService(), "gemini"),
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "Your account will be closed today."},
        )

    assert response.status_code == 200
    assert response.json() == {
        "classification": "phishing",
        "tactics": ["urgency"],
        "evidence": [],
        "recommendations": ["Verify through a trusted channel."],
        "risk_level": "high",
        "mode": "gemini",
    }
    assert calls == [(None, None, "Your account will be closed today.")]


def test_analysis_endpoint_returns_mock_mode(monkeypatch):
    from backend.ai.mock_provider import MockProvider
    from backend.ai.service import AIService

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (AIService(MockProvider()), "mock"),
    )

    with TestClient(main.app) as client:
        response = client.post("/analyses", json={"text": "Test email"})

    assert response.status_code == 200
    assert response.json()["mode"] == "mock"
    assert response.json()["risk_level"] == "medium"
    assert "Mock analysis" in response.json()["tactics"][0]


def test_analysis_endpoint_rejects_blank_text():
    with TestClient(main.app) as client:
        response = client.post("/analyses", json={"text": "  \n "})

    assert response.status_code == 422


def test_analysis_endpoint_reports_configuration_error(monkeypatch):
    def fail_configuration():
        raise RuntimeError("GEMINI_API_KEY is required when AI_MODE=gemini")

    monkeypatch.setattr(main, "get_ai_service", fail_configuration)

    with TestClient(main.app) as client:
        response = client.post("/analyses", json={"text": "Test email"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": "GEMINI_API_KEY is required when AI_MODE=gemini"
    }


def test_analysis_endpoint_reports_provider_failure(monkeypatch):
    class FailingService:
        def analyze_email(self, *, subject, sender, body):
            raise RuntimeError(
                "Gemini is temporarily unavailable (HTTP 503). Please try again."
            )

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (FailingService(), "gemini"),
    )

    with TestClient(main.app) as client:
        response = client.post("/analyses", json={"text": "Test email"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Gemini is temporarily unavailable (HTTP 503). Please try again."
    }
