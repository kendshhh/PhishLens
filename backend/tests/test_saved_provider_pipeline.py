"""Exercise the provider-to-saved-record contract without live services."""

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.ai.gemini_provider import GeminiProvider
from backend.ai.prompts import PROMPT_VERSION
from backend.ai.service import AIService
from backend.ai.tfidf_provider import MODEL_SHA256
from backend.app import analysis_persistence, analysis_service
from backend.app.analysis_schemas import CreateSavedAnalysis
from backend.app.main import app
from backend.app.routers import saved_create


def test_gemini_output_is_validated_mapped_and_persisted(monkeypatch):
    email_subject = "Verify your account"
    email_body = "Please confirm your account using the secure link."
    provider_payload = {
        "classification": "phishing",
        "tactics": ["Requests account verification"],
        "evidence": [
            {
                "text": "confirm your account",
                "reason": "It asks the recipient to take an account action.",
            }
        ],
        "recommendations": ["Verify through a known official channel."],
    }
    sdk_call = Mock(
        return_value=SimpleNamespace(text=json.dumps(provider_payload))
    )
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.client = SimpleNamespace(
        models=SimpleNamespace(generate_content=sdk_call)
    )
    provider.model = "gemini-test-model"
    provider.spend_policy = None
    provider.evaluation_budget = None

    request = CreateSavedAnalysis(subject=email_subject, body=email_body)
    result = AIService(provider).analyze_email(
        subject=email_subject,
        sender=None,
        body=email_body,
    )
    analysis_service_call = Mock(return_value=result)
    monkeypatch.setattr(
        analysis_service,
        "run_saved_inference",
        analysis_service_call,
    )
    monkeypatch.setattr(saved_create, "get_database_url", lambda: "configured")
    monkeypatch.setattr(
        saved_create,
        "get_ai_config",
        lambda: ("gemini", "synthetic-test-key", "gemini-test-model"),
    )

    record_id = uuid4()
    user_id = uuid4()
    created_at = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    persisted_row = {
        "id": record_id,
        "user_id": user_id,
        "subject": request.subject,
        "body": request.body,
        "prediction": "phishing",
        "confidence": None,
        "risk_level": "high",
        "indicators": [
            {
                "type": "evidence",
                "quote": "confirm your account",
                "detail": "It asks the recipient to take an account action.",
            }
        ],
        "explanation": (
            "Tactics: Requests account verification\n"
            "Recommendations: Verify through a known official channel."
        ),
        "notes": None,
        "feedback": None,
        "analysis_mode": "real",
        "analysis_provenance": {
            "provider_mode": "gemini",
            "model": "gemini-test-model",
            "model_revision": None,
            "prompt_version": PROMPT_VERSION,
            "explanation_source": "model",
            "input_truncated": False,
            "windows_processed": None,
        },
        "created_at": created_at,
    }
    user_cursor = SimpleNamespace(fetchone=AsyncMock(return_value={"id": user_id}))
    insert_cursor = SimpleNamespace(fetchone=AsyncMock(return_value=persisted_row))
    connection = SimpleNamespace(
        execute=AsyncMock(side_effect=[user_cursor, insert_cursor]),
        commit=AsyncMock(),
    )

    @asynccontextmanager
    async def fake_connection(_deadline):
        yield connection

    monkeypatch.setattr(
        analysis_persistence,
        "saved_analysis_connection",
        Mock(side_effect=fake_connection),
    )
    monkeypatch.setattr(analysis_persistence, "uuid4", lambda: record_id)

    with TestClient(app) as client:
        response = client.post(
            "/api/analyses",
            json={"subject": email_subject, "body": email_body},
        )

    sdk_call.assert_called_once()
    analysis_service_call.assert_called_once()
    assert response.status_code == 201
    saved = response.json()
    assert result.model == "gemini-test-model"
    assert result.prompt_version == PROMPT_VERSION
    assert result.explanation_source == "model"
    assert result.evidence[0].text in email_body
    assert saved["id"] == str(record_id)
    assert saved["prediction"] == "phishing"
    assert saved["risk_level"] == "high"
    assert saved["threat_indicators"][0]["quote"] == "confirm your account"
    assert saved["analysis_mode"] == "real"
    assert saved["analysis_provenance"] == persisted_row["analysis_provenance"]

    insert_parameters = connection.execute.await_args_list[1].args[1]
    assert insert_parameters[6] == "high"
    assert insert_parameters[7].obj == persisted_row["indicators"]
    assert insert_parameters[8] == persisted_row["explanation"]
    assert insert_parameters[9] == "real"
    assert insert_parameters[10].obj["provider_mode"] == "gemini"
    assert insert_parameters[10].obj["model"] == "gemini-test-model"
    assert insert_parameters[10].obj["prompt_version"] == PROMPT_VERSION
    connection.commit.assert_awaited_once()


def test_tfidf_saved_post_runs_supervised_provider_and_persists_contract(
    monkeypatch,
):
    """Exercise the real bundled TF-IDF worker through saved creation."""
    subject = "Synthetic account notice"
    body = (
        "Please review this synthetic message about your account. "
        "Verify unexpected requests through a known official channel."
    )
    user_id = uuid4()
    record_id = uuid4()
    created_at = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)

    monkeypatch.setattr(saved_create, "get_database_url", lambda: "configured")
    monkeypatch.setattr(
        saved_create,
        "get_ai_config",
        lambda: ("tfidf", None, None),
    )

    user_cursor = SimpleNamespace(fetchone=AsyncMock(return_value={"id": user_id}))
    insert_cursor = SimpleNamespace(fetchone=AsyncMock())

    async def execute(sql, parameters):
        if "SELECT id FROM users" in sql:
            return user_cursor

        if not sql.lstrip().startswith("INSERT INTO analyzed_emails"):
            return insert_cursor

        insert_cursor.fetchone.return_value = {
            "id": record_id,
            "user_id": parameters[1],
            "subject": parameters[2],
            "body": parameters[3],
            "prediction": parameters[4],
            "confidence": parameters[5],
            "risk_level": parameters[6],
            "indicators": parameters[7].obj,
            "explanation": parameters[8],
            "notes": None,
            "feedback": None,
            "analysis_mode": parameters[9],
            "analysis_provenance": parameters[10].obj,
            "created_at": created_at,
        }
        return insert_cursor

    connection = SimpleNamespace(
        execute=AsyncMock(side_effect=execute),
        commit=AsyncMock(),
    )

    @asynccontextmanager
    async def fake_connection(_deadline):
        yield connection

    monkeypatch.setattr(
        analysis_persistence,
        "saved_analysis_connection",
        Mock(side_effect=fake_connection),
    )
    monkeypatch.setattr(analysis_persistence, "uuid4", lambda: record_id)

    with TestClient(app) as client:
        response = client.post(
            "/api/analyses",
            json={"subject": subject, "body": body},
            headers={"X-PhishLens-Model": MODEL_SHA256},
        )

    assert response.status_code == 201, response.text
    saved = response.json()
    assert saved["id"] == str(record_id)
    assert saved["subject"] == subject
    assert saved["body"] == body
    assert saved["analysis_mode"] == "real"
    expected_prediction = (
        "phishing"
        if saved["analysis_provenance"]["model_alert"]
        else "legitimate"
    )
    assert saved["prediction"] == expected_prediction
    assert saved["confidence"] is None
    assert saved["risk_level"] == (
        "high" if expected_prediction == "phishing" else "low"
    )
    assert saved["explanation"]
    assert saved["analysis_provenance"]["provider_mode"] == "tfidf"
    assert saved["analysis_provenance"]["model"] == "word_plus_char_wb_C1p0"
    assert saved["analysis_provenance"]["model_revision"] == MODEL_SHA256
    assert saved["analysis_provenance"]["explanation_source"] == "rules"
    assert saved["analysis_provenance"]["prompt_version"] is None
    assert saved["analysis_provenance"]["windows_processed"] == 1
    assert isinstance(saved["analysis_provenance"]["phishing_score"], float)
    assert isinstance(saved["analysis_provenance"]["raw_margin"], float)
    assert saved["analysis_provenance"]["assessment"]
    assert all(item["quote"] in body for item in saved["threat_indicators"])

    insert_parameters = connection.execute.await_args_list[1].args[1]
    assert insert_parameters[1] == user_id
    assert insert_parameters[4] == saved["prediction"]
    assert insert_parameters[5] is None
    assert insert_parameters[7].obj == saved["threat_indicators"]
    assert insert_parameters[9] == "real"
    assert insert_parameters[10].obj == saved["analysis_provenance"]
    connection.commit.assert_awaited_once()
