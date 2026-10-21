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
def test_create_returns_201_saved_detail(create_context, payload):
    context = create_context

    response = context.client.post("/api/analyses", json=payload)

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
    context.database_config.assert_not_called()
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
    context.database_config.assert_not_called()
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

    for status in ("422", "500", "502", "503", "504"):
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/SavedCreateError")