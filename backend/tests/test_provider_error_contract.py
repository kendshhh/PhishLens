from decimal import Decimal
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from google.genai import errors

from backend.ai import gemini_provider
from backend.ai.service import AIService
from backend.ai.spend_limit import GeminiSpendPolicy
from backend.app import main


@pytest.fixture
def failing_gemini(monkeypatch):
    sdk_client = Mock()
    monkeypatch.setattr(
        gemini_provider.genai,
        "Client",
        Mock(return_value=sdk_client),
    )

    provider = gemini_provider.GeminiProvider(
        api_key="synthetic-key",
        model="gemini-test",
        spend_policy=GeminiSpendPolicy(
            cap_usd=Decimal(1),
            input_usd_per_million_tokens=Decimal(1),
            output_usd_per_million_tokens=Decimal(1),
            model_id="gemini-test",
        ),
    )
    service = AIService(provider)
    monkeypatch.setattr(
        main,
        "get_ai_service",
        lambda: (service, "gemini"),
    )
    # Keep provider error contracts isolated from the shared quota database.
    monkeypatch.setattr(main, "reserve_ai_request_quota", lambda *_a, **_k: None)
    monkeypatch.setattr(main, "attach_ai_quota_observation", lambda *_a, **_k: None)

    yield sdk_client

    provider.close()


@pytest.mark.parametrize(
    ("provider_status", "expected_status", "expected_code", "expected_message"),
    [
        (401, 503, "analysis_unavailable", "Analysis temporarily unavailable"),
        (403, 503, "analysis_unavailable", "Analysis temporarily unavailable"),
        (404, 503, "analysis_unavailable", "Analysis temporarily unavailable"),
        (429, 503, "analysis_unavailable", "Analysis temporarily unavailable"),
        (503, 503, "analysis_unavailable", "Analysis temporarily unavailable"),
        (500, 502, "inference_failed", "Analysis failed"),
        (502, 502, "inference_failed", "Analysis failed"),
        (504, 502, "inference_failed", "Analysis failed"),
    ],
)
def test_provider_status_has_safe_endpoint_contract(
    failing_gemini,
    provider_status,
    expected_status,
    expected_code,
    expected_message,
):
    failing_gemini.models.generate_content.side_effect = errors.APIError(
        code=provider_status,
        response_json={
            "error": {
                "message": "secret-key private@example.invalid",
            },
        },
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "Synthetic email body"},
        )

    assert response.status_code == expected_status
    if expected_status == 504:
        assert response.headers["Retry-After"] == "5"
    assert response.json() == {
        "error": {
            "code": expected_code,
            "message": expected_message,
        },
    }
    failing_gemini.models.generate_content.assert_called_once()


@pytest.mark.parametrize(
    "exception_type",
    [httpx.ConnectError, httpx.ReadTimeout],
)
def test_transport_failure_retains_safe_502_contract(
    failing_gemini,
    exception_type,
):
    """Keep the reviewed inventory ID while asserting typed timeout behavior."""
    failing_gemini.models.generate_content.side_effect = exception_type(
        "secret-key private@example.invalid"
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/analyses",
            json={"text": "Synthetic email body"},
        )

    if exception_type is httpx.ReadTimeout:
        assert response.status_code == 504
        assert response.headers["Retry-After"] == "5"
        expected_message = "Analysis timed out"
    else:
        assert response.status_code == 502
        assert "Retry-After" not in response.headers
        expected_message = "Analysis failed"
    assert response.json() == {
        "error": {
            "code": "inference_failed",
            "message": expected_message,
        },
    }
    assert "secret-key" not in response.text
    failing_gemini.models.generate_content.assert_called_once()
