import json
import logging

import pytest
from fastapi.testclient import TestClient

from backend.ai.schemas import AIAnalysisResult
from backend.app import main
from backend.core import config


@pytest.mark.parametrize(
    "configured, expected",
    [("true", True), (" TRUE ", True), ("false", False), ("yes", False)],
)
def test_ai_analysis_switch_is_explicit_and_fails_closed(
    monkeypatch,
    configured,
    expected,
):
    monkeypatch.setattr(config, "load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("AI_ANALYSIS_ENABLED", configured)

    assert config.ai_analysis_enabled() is expected


def test_ai_analysis_switch_defaults_to_existing_behavior(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.delenv("AI_ANALYSIS_ENABLED", raising=False)

    assert config.ai_analysis_enabled() is True


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


def test_analysis_adds_server_request_id_and_redacted_ai_log(monkeypatch, caplog):
    private_text = "synthetic-private-email-content"

    class FakeService:
        def analyze_email(self, **_kwargs):
            return AIAnalysisResult(
                classification="phishing",
                model="synthetic-model-v1",
                model_revision="synthetic-revision",
                prompt_version="synthetic-prompt-v1",
            )

    monkeypatch.setattr(main, "get_ai_service", lambda: (FakeService(), "gemini"))
    monkeypatch.setenv("AI_ANALYSIS_ENABLED", "true")
    caplog.set_level(logging.INFO, logger="phishlens.api")

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": private_text},
            headers={"X-Request-ID": "caller-controlled"},
        )

    request_id = response.headers["X-Request-ID"]
    assert request_id != "caller-controlled"
    event = next(
        json.loads(record.message)
        for record in caplog.records
        if record.name == "phishlens.api" and '"event":"http_request"' in record.message
    )
    assert event["request_id"] == request_id
    assert event["route"] == "/analyses"
    assert event["operation"] == "analyze_email"
    assert event["ai"]["provider_mode"] == "gemini"
    assert event["ai"]["model_id"] == "synthetic-model-v1"
    assert event["ai"]["model_revision"] == "synthetic-revision"
    assert event["ai"]["prompt_version"] == "synthetic-prompt-v1"
    assert event["ai"]["outcome"] == "success"
    assert private_text not in json.dumps(event)


def test_analysis_kill_switch_disables_inference_and_reports_state(monkeypatch):
    def unexpected_provider_lookup():
        raise AssertionError("The kill switch must stop before provider lookup")

    monkeypatch.setattr(main, "get_ai_service", unexpected_provider_lookup)
    monkeypatch.setenv("AI_ANALYSIS_ENABLED", "false")

    with TestClient(main.app) as client:
        response = client.post("/analyses", json={"text": "Synthetic mail"})
        model_info = client.get("/model-info")

    assert response.status_code == 503
    assert response.headers.get("X-Request-ID")
    assert model_info.status_code == 200
    assert model_info.json() == {
        "provider_mode": "disabled",
        "analysis_enabled": False,
        "supports_required_provider": False,
        "accepts_tfidf_reports": False,
        "accepts_local_reviews": False,
    }


def test_analysis_endpoint_rejects_required_provider_mismatch_before_inference(monkeypatch):
    calls = []

    class GeminiService:
        def analyze_email(self, *, subject, sender, body):
            calls.append((subject, sender, body))
            raise AssertionError("A mismatched provider must not receive the request")

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (GeminiService(), "gemini"),
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "Synthetic smoke input"},
            headers={"X-Require-Provider": "tfidf"},
        )

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "analysis_unavailable",
            "message": "Required analysis provider is unavailable",
        }
    }
    assert calls == []


def test_revision_analysis_rejects_different_deployment_before_provider_lookup(monkeypatch):
    expected_sha = "a" * 40
    serving_sha = "b" * 40
    monkeypatch.setenv("RENDER_GIT_COMMIT", serving_sha)

    def unexpected_provider_lookup():
        raise AssertionError("A mismatched deployment must stop before provider lookup")

    monkeypatch.setattr(main, "get_ai_service", unexpected_provider_lookup)

    with TestClient(main.app) as client:
        response = client.post(
            f"/analyses/revision/{expected_sha}",
            json={"text": "Synthetic smoke input"},
            headers={"X-Require-Provider": "tfidf"},
        )

    assert response.status_code == 409
    assert response.headers["X-PhishLens-Revision"] == serving_sha
    assert response.json() == {
        "error": {
            "code": "deployment_revision_mismatch",
            "message": "Analysis request reached a different deployment revision",
        }
    }


def test_revision_analysis_rejects_non_tfidf_provider_before_inference(monkeypatch):
    serving_sha = "a" * 40
    calls = []
    monkeypatch.setenv("RENDER_GIT_COMMIT", serving_sha)

    class GeminiService:
        def analyze_email(self, *, subject, sender, body):
            calls.append((subject, sender, body))
            raise AssertionError("The revision-scoped route must reject Gemini before inference")

    monkeypatch.setattr(main, "get_ai_service", lambda: (GeminiService(), "gemini"))

    with TestClient(main.app) as client:
        response = client.post(
            f"/analyses/revision/{serving_sha}",
            json={"text": "Synthetic smoke input"},
            headers={"X-Require-Provider": "tfidf"},
        )

    assert response.status_code == 503
    assert response.headers["X-PhishLens-Revision"] == serving_sha
    assert calls == []


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
