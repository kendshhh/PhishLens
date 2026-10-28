import sys
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient

from backend.ai.errors import ModelUnavailableError
from backend.ai.local_provider import LocalProvider
from backend.ai.service import AIService
from backend.app import main


def test_provider_failure_does_not_expose_private_details(monkeypatch):
    class FailingService:
        def analyze_email(self, *, subject, sender, body):
            raise RuntimeError(
                "api_key=secret-key; email=private@example.invalid"
            )

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
    assert "secret-key" not in response.text
    assert "private@example.invalid" not in response.text


def test_invalid_input_does_not_echo_submitted_value():
    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": {"private": "synthetic-private-token"}},
        )

    assert response.status_code == 422
    assert "synthetic-private-token" not in response.text


def test_missing_local_model_is_unavailable_without_a_verdict(monkeypatch):
    class MissingModelProvider:
        def analyze(self, _email_text):
            raise ModelUnavailableError("/private/models/checkpoint")

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (AIService(MissingModelProvider()), "local"),
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "Synthetic email body"},
        )

    assert response.status_code == 503
    assert "classification" not in response.json()
    assert "/private/models/checkpoint" not in response.text


def test_real_local_provider_reports_missing_checkpoint_as_503(
    monkeypatch,
    tmp_path,
):
    tokenizer = Mock()
    tokenizer.from_pretrained.side_effect = OSError(
        "/private/models/checkpoint"
    )

    fake_transformers = SimpleNamespace(
        AutoTokenizer=tokenizer,
        AutoModelForSequenceClassification=Mock(),
    )
    monkeypatch.setitem(sys.modules, "torch", Mock())
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

    service = AIService(LocalProvider(cache_dir=tmp_path))
    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (service, "local"),
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "Synthetic email body"},
        )

    assert response.status_code == 503
    assert "classification" not in response.json()
    assert "/private/models/checkpoint" not in response.text