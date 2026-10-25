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
        "error": {
            "code": "analysis_unavailable",
            "message": "Analysis temporarily unavailable",
        }
    }
    assert "GEMINI_API_KEY" not in response.text


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
        "error": {
            "code": "inference_failed",
            "message": "Analysis failed",
        }
    }
    assert "Gemini is temporarily unavailable" not in response.text


def test_subject_sender_and_local_provenance_reach_api(monkeypatch):
    class LocalService:
        def analyze_email(self, *, subject, sender, body):
            assert (subject, sender, body) == (
                "Meeting",
                "team@example.test",
                "Tomorrow at ten",
            )
            return AIAnalysisResult(
                classification="legitimate",
                confidence=0.8,
                model="pinned-test-model",
                explanation_source="rules",
                windows_processed=1,
                input_truncated=False,
            )

    monkeypatch.setattr(main, "get_ai_service", lambda: (LocalService(), "local"))

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={
                "text": "Tomorrow at ten",
                "subject": "Meeting",
                "sender": "team@example.test",
            },
        )

    assert response.status_code == 200
    assert response.json()["mode"] == "local"
    assert response.json()["confidence"] == 0.8
    assert response.json()["risk_level"] == "low"
    assert response.json()["explanation_source"] == "rules"


def test_oversized_and_malformed_requests_never_invoke_ai(monkeypatch):
    def unexpected_call():
        raise AssertionError("Provider should not be requested for invalid input")

    monkeypatch.setattr(main, "get_ai_service", unexpected_call)

    requests = (
        {"text": "a" * 30_001},
        {"text": "Test", "subject": "a" * 321},
        {"text": "Test", "extra": True},
        {"text": None},
        {},
    )

    with TestClient(main.app) as client:
        for request in requests:
            assert client.post("/analyses", json=request).status_code == 422


def test_daily_quota_returns_service_unavailable(monkeypatch):
    from backend.ai.gemini_provider import DailyQuotaExceeded

    class ExhaustedService:
        def analyze_email(self, **_kwargs):
            raise DailyQuotaExceeded(
                "The AI provider's daily request quota is exhausted."
            )

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (ExhaustedService(), "gemini"),
    )

    with TestClient(main.app) as client:
        response = client.post("/analyses", json={"text": "Synthetic mail"})

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "analysis_unavailable",
            "message": "Analysis temporarily unavailable",
        }
    }
    assert "daily request quota" not in response.text