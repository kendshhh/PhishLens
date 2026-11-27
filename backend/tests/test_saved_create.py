import json
import logging
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg import OperationalError

from backend.app.analysis_deadlines import AnalysisDeadline, AnalysisTimeoutError
from backend.app.analysis_execution import (
    AnalysisInferenceError,
    AnalysisUnavailableError,
)
from backend.app.analysis_schemas import SavedAnalysisDetail
from backend.app.main import app
from backend.app.routers import saved_create

PRIVATE_TOKEN = "synthetic-private-token"


@pytest.fixture
def create_context(monkeypatch):
    saved = SavedAnalysisDetail(
        id=uuid4(),
        subject="",
        body="Synthetic email body",
        prediction="spam",
        confidence=None,
        risk_level="medium",
        threat_indicators=[],
        explanation=None,
        notes=None,
        feedback=None,
        analysis_mode="mock",
        analysis_provenance={"provider_mode": "mock"},
        created_at=datetime(2026, 10, 20, 12, 0, tzinfo=UTC),
    )
    service = AsyncMock(return_value=saved)
    ai_config = Mock(return_value=("mock", None, None))
    database_config = Mock(
        return_value=(
            "postgresql+psycopg://127.0.0.1/"
            "phishlens_s2_t1_test"
        )
    )
    monkeypatch.setattr(saved_create, "create_saved_analysis", service)
    monkeypatch.setattr(saved_create, "get_ai_config", ai_config)
    monkeypatch.setattr(
        saved_create,
        "get_database_url",
        database_config,
    )

    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            saved=saved,
            service=service,
            ai_config=ai_config,
            database_config=database_config,
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"body": "Synthetic email body"},
        {"subject": "", "body": "Synthetic email body"},
    ],
    ids=["omitted-subject", "empty-subject"],
)
def test_create_returns_201_saved_detail(create_context, payload, caplog):
    context = create_context
    caplog.set_level(logging.INFO, logger="phishlens.api")

    response = context.client.post(
        "/api/analyses",
        json=payload,
        headers={"X-Request-ID": "caller-controlled"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(context.saved.id)
    assert body["subject"] == ""
    assert body["body"] == "Synthetic email body"
    assert body["prediction"] == "spam"
    assert "confidence" in body
    assert body["confidence"] is None
    assert body["risk_level"] == "medium"
    assert body["analysis_mode"] == "mock"

    context.service.assert_awaited_once()
    call = context.service.await_args
    assert call.args[0].subject == ""
    assert call.args[0].body == "Synthetic email body"
    assert call.kwargs["mode"] == "mock"
    assert isinstance(call.kwargs["deadline"], AnalysisDeadline)
    assert call.kwargs["idempotency_key"] is None
    request_id = response.headers["X-Request-ID"]
    assert request_id != "caller-controlled"
    event = next(
        json.loads(record.message)
        for record in caplog.records
        if record.name == "phishlens.api" and '"event":"http_request"' in record.message
    )
    assert event["request_id"] == request_id
    assert event["route"] == "/analyses"
    assert event["operation"] == "create_analysis"
    assert event["ai"]["provider_mode"] == "mock"
    assert event["ai"]["outcome"] == "success"
    assert "Synthetic email body" not in json.dumps(event)


def test_gemini_saved_create_logs_tokens_without_exposing_them(
    create_context,
    monkeypatch,
    caplog,
):
    from decimal import Decimal

    from backend.ai.spend_limit import GeminiRequestEstimate
    from backend.app.ai_request_quota import AIQuotaReservation

    context = create_context
    context.ai_config.return_value = ("gemini", "synthetic-key", "synthetic-model")
    estimate = GeminiRequestEstimate(100, 128, Decimal("0.001"))
    reservation = AIQuotaReservation(
        input_token_upper_bound=100,
        output_token_upper_bound=128,
        cost_upper_bound_usd=Decimal("0.001"),
        daily_cost_reserved_usd=Decimal("0.001"),
        daily_spend_cap_usd=Decimal(1),
        daily_budget_fraction=Decimal("0.001"),
        alert_threshold_crossed=False,
    )
    monkeypatch.setattr(saved_create, "estimate_gemini_request_cost", lambda *_args: estimate)
    monkeypatch.setattr(saved_create, "reserve_ai_request_quota", lambda *_args, **_kwargs: reservation)

    async def complete_with_usage(*_args, provider_usage=None, **_kwargs):
        assert provider_usage is not None
        provider_usage.update({
            "input_tokens": 17,
            "output_tokens": 9,
            "estimated_cost_usd": "0.000280",
        })
        return context.saved

    context.service.side_effect = complete_with_usage
    caplog.set_level(logging.INFO, logger="phishlens.api")

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == 201
    assert "input_tokens" not in response.json()
    assert "output_tokens" not in response.json()
    event = next(
        json.loads(record.message)
        for record in caplog.records
        if record.name == "phishlens.api" and '"event":"http_request"' in record.message
    )
    assert event["ai"]["input_tokens"] == 17
    assert event["ai"]["output_tokens"] == 9
    assert event["ai"]["estimated_cost_usd"] == "0.000280"
    assert "estimated_cost_usd" not in response.json()


def test_saved_create_per_request_cap_rejects_before_shared_quota_reservation(
    create_context,
    monkeypatch,
):
    context = create_context
    context.ai_config.return_value = ("gemini", "synthetic-key", "synthetic-model")
    monkeypatch.setenv("GEMINI_PER_REQUEST_COST_CAP_USD", "0.000001")
    monkeypatch.setenv("GEMINI_INPUT_USD_PER_MILLION_TOKENS", "1")
    monkeypatch.setenv("GEMINI_OUTPUT_USD_PER_MILLION_TOKENS", "1")
    monkeypatch.setenv("GEMINI_COST_MODEL_ID", "synthetic-model")
    reserve = Mock(side_effect=AssertionError("Over-cap request must not reserve shared quota"))
    monkeypatch.setattr(saved_create, "reserve_ai_request_quota", reserve)

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Email analysis is temporarily unavailable",
        "code": "analysis_unavailable",
    }
    reserve.assert_not_called()
    context.service.assert_not_awaited()


def test_saved_create_kill_switch_stops_before_database_or_inference(
    create_context,
    monkeypatch,
):
    context = create_context
    monkeypatch.setenv("AI_ANALYSIS_ENABLED", "false")

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "analysis_unavailable"
    context.service.assert_not_awaited()
    context.database_config.assert_not_called()
    context.ai_config.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"body": " \n "},
        {"body": "x" * 30_001},
        {"subject": "x" * 321, "body": "Synthetic email body"},
        {"body": {"private": PRIVATE_TOKEN}},
        {"body": "Synthetic email body", "user_id": PRIVATE_TOKEN},
    ],
    ids=[
        "missing-body",
        "blank-body",
        "oversized-body",
        "oversized-subject",
        "wrong-body-type",
        "browser-supplied-owner",
    ],
)
def test_invalid_create_skips_configuration_and_service(
    create_context,
    payload,
):
    context = create_context

    response = context.client.post("/api/analyses", json=payload)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid analysis input",
        "code": "invalid_input",
    }
    assert PRIVATE_TOKEN not in response.text
    context.ai_config.assert_not_called()
    context.database_config.assert_not_called()
    context.service.assert_not_awaited()


@pytest.mark.parametrize(
    ("error_type", "status", "code", "detail"),
    [
        (
            AnalysisTimeoutError,
            504,
            "analysis_timeout",
            "Email analysis timed out",
        ),
        (
            AnalysisUnavailableError,
            503,
            "analysis_unavailable",
            "Email analysis is temporarily unavailable",
        ),
        (
            AnalysisInferenceError,
            502,
            "analysis_failed",
            "Email analysis failed",
        ),
        (
            OperationalError,
            503,
            "storage_unavailable",
            "Saved analysis storage is temporarily unavailable",
        ),
        (
            RuntimeError,
            500,
            "internal_error",
            "Unable to create saved analysis",
        ),
    ],
)
def test_create_failures_return_safe_errors(
    create_context,
    error_type,
    status,
    code,
    detail,
):
    context = create_context
    context.service.side_effect = error_type(PRIVATE_TOKEN)

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == status
    assert response.json() == {"detail": detail, "code": code}
    assert PRIVATE_TOKEN not in response.text
    assert "prediction" not in response.json()


def test_bad_ai_configuration_never_calls_service(create_context):
    context = create_context
    context.ai_config.side_effect = RuntimeError(PRIVATE_TOKEN)

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "analysis_unavailable"
    assert PRIVATE_TOKEN not in response.text
    context.database_config.assert_called_once()
    context.service.assert_not_awaited()


def test_local_create_is_unavailable(create_context):
    context = create_context
    context.ai_config.return_value = ("local", None, None)

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "analysis_unavailable"
    context.database_config.assert_called_once()
    context.service.assert_not_awaited()


def test_tfidf_saved_create_rejects_wrong_model_before_storage_or_replay(
    create_context,
    monkeypatch,
):
    context = create_context
    context.ai_config.return_value = ("tfidf", None, None)
    idempotency_lookup = AsyncMock()
    monkeypatch.setattr(
        saved_create,
        "find_idempotent_saved_analysis",
        idempotency_lookup,
    )

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
        headers={
            "Idempotency-Key": "wrong-model-hash-retry",
            "X-PhishLens-Model": "0" * 64,
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The matching TF-IDF save service is unavailable",
        "code": "analysis_unavailable",
    }
    context.ai_config.assert_called_once_with()
    context.database_config.assert_not_called()
    idempotency_lookup.assert_not_awaited()
    context.service.assert_not_awaited()


def test_bad_database_configuration_never_calls_service(
    create_context,
):
    context = create_context
    context.database_config.side_effect = RuntimeError(PRIVATE_TOKEN)

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "storage_unavailable"
    assert PRIVATE_TOKEN not in response.text
    context.service.assert_not_awaited()


def test_malformed_json_does_not_echo_content(create_context):
    context = create_context

    response = context.client.post(
        "/api/analyses",
        content='{"body": "synthetic-private-token"',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid analysis input",
        "code": "invalid_input",
    }
    assert PRIVATE_TOKEN not in response.text
    context.service.assert_not_awaited()


def test_create_openapi_documents_success_and_errors():
    responses = app.openapi()["paths"]["/api/analyses"]["post"]["responses"]

    success = responses["201"]["content"]["application/json"]["schema"]
    assert success["$ref"].endswith("/SavedAnalysisDetail")

    for status in ("409", "422", "500", "502", "503", "504"):
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/SavedCreateError")


def test_create_documents_optional_idempotency_header():
    parameters = app.openapi()["paths"]["/api/analyses"]["post"]["parameters"]
    assert any(
        parameter["name"] == "Idempotency-Key"
        and parameter["in"] == "header"
        and parameter["required"] is False
        for parameter in parameters
    )


def test_idempotency_replay_returns_saved_result_before_ai_configuration(
    create_context,
    monkeypatch,
):
    context = create_context
    lookup = AsyncMock(return_value=context.saved)
    monkeypatch.setattr(saved_create, "find_idempotent_saved_analysis", lookup)
    context.ai_config.side_effect = RuntimeError(PRIVATE_TOKEN)

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
        headers={"Idempotency-Key": "retry-123"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(context.saved.id)
    lookup.assert_awaited_once()
    assert lookup.await_args.args[0].body == "Synthetic email body"
    assert lookup.await_args.args[1] == "retry-123"
    context.ai_config.assert_not_called()
    context.service.assert_not_awaited()


def test_reusing_idempotency_key_with_different_input_returns_409(
    create_context,
    monkeypatch,
):
    context = create_context
    lookup = AsyncMock(
        side_effect=saved_create.AnalysisIdempotencyConflictError(
            PRIVATE_TOKEN
        )
    )
    monkeypatch.setattr(saved_create, "find_idempotent_saved_analysis", lookup)

    response = context.client.post(
        "/api/analyses",
        json={"body": "Different synthetic body"},
        headers={"Idempotency-Key": "retry-123"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Idempotency-Key was already used for a different request",
        "code": "idempotency_conflict",
    }
    assert PRIVATE_TOKEN not in response.text
    context.ai_config.assert_not_called()
    context.service.assert_not_awaited()


def test_invalid_idempotency_key_is_rejected(create_context):
    context = create_context

    response = context.client.post(
        "/api/analyses",
        json={"body": "Synthetic email body"},
        headers={"Idempotency-Key": "not a safe key"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid Idempotency-Key",
        "code": "invalid_input",
    }
    context.database_config.assert_not_called()
    context.service.assert_not_awaited()
