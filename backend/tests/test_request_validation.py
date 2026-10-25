import pytest
from fastapi.testclient import TestClient

from backend.ai.schemas import AIAnalysisResult
from backend.app import main


@pytest.mark.parametrize(
    ("subject", "sender"),
    [
        ("", "   "),
        (" \t ", "\n"),
    ],
)
def test_blank_optional_fields_are_omitted(monkeypatch, subject, sender):
    received = []

    class FakeService:
        def analyze_email(self, *, subject, sender, body):
            received.append((subject, sender, body))
            return AIAnalysisResult(classification="legitimate")

    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (FakeService(), "mock"),
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={
                "text": "Synthetic email body",
                "subject": subject,
                "sender": sender,
            },
        )

    assert response.status_code == 200
    assert received == [(None, None, "Synthetic email body")]