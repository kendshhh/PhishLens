import json
from multiprocessing.connection import Connection
from unittest.mock import Mock

import httpx
import pytest

from backend.ai import gemini_provider
from backend.ai.gemini_provider import DailyQuotaExceeded
from backend.ai.schemas import AIAnalysisResult
from backend.app import analysis_worker


@pytest.fixture
def channel():
    return Mock(spec=Connection)


def _run_worker(channel, *, mode="mock"):
    analysis_worker.run_analysis_worker(
        channel,
        mode=mode,
        api_key="synthetic-key",
        model="synthetic-model",
        subject="",
        body="Synthetic email body",
    )

    channel.send.assert_called_once()
    channel.close.assert_called_once()
    return channel.send.call_args.args[0]


def test_mock_worker_returns_valid_result(channel):
    message = _run_worker(channel)

    assert message["status"] == "ok"

    result = AIAnalysisResult.model_validate(message["result"])
    assert result.classification == "spam"
    assert result.confidence is None


def test_local_worker_is_unavailable(channel):
    message = _run_worker(channel, mode="local")

    assert message == {"status": "unavailable"}


def test_provider_initialization_failure_is_safe(
    channel,
    monkeypatch,
):
    monkeypatch.setattr(
        analysis_worker,
        "_build_provider",
        Mock(
            side_effect=RuntimeError(
                "api_key=synthetic-secret; private configuration"
            )
        ),
    )

    message = _run_worker(channel)

    assert message == {"status": "unavailable"}


def test_gemini_uses_requested_timeout_and_closes_provider(
    channel,
    monkeypatch,
):
    monkeypatch.setenv("GEMINI_PER_REQUEST_COST_CAP_USD", "1")
    monkeypatch.setenv("GEMINI_INPUT_USD_PER_MILLION_TOKENS", "0.4")
    monkeypatch.setenv("GEMINI_OUTPUT_USD_PER_MILLION_TOKENS", "1.2")
    monkeypatch.setenv("GEMINI_COST_MODEL_ID", "synthetic-model")
    provider_client = Mock()
    provider_client.models.generate_content.return_value.text = json.dumps({
        "classification": "legitimate",
        "tactics": [],
        "evidence": [],
        "recommendations": [],
    })
    constructor = Mock(return_value=provider_client)
    monkeypatch.setattr(
        gemini_provider.genai,
        "Client",
        constructor,
    )

    message = _run_worker(channel, mode="gemini")

    assert message["status"] == "ok"
    http_options = constructor.call_args.kwargs["http_options"]
    assert http_options.timeout == 15_000
    assert http_options.retry_options.attempts == 1
    provider_client.models.generate_content.assert_called_once()
    provider_client.close.assert_called_once()


@pytest.mark.parametrize(
    ("configuration", "expected_status", "client_created"),
    [
        ("missing-cap", "unavailable", False),
        ("invalid-rate", "unavailable", False),
        ("model-mismatch", "unavailable", False),
        ("insufficient-cap", "unavailable", True),
    ],
)
def test_saved_gemini_worker_fails_closed_before_sdk_call(
    channel,
    monkeypatch,
    configuration,
    expected_status,
    client_created,
):
    for name in (
        "GEMINI_PER_REQUEST_COST_CAP_USD",
        "GEMINI_INPUT_USD_PER_MILLION_TOKENS",
        "GEMINI_OUTPUT_USD_PER_MILLION_TOKENS",
        "GEMINI_COST_MODEL_ID",
    ):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("GEMINI_INPUT_USD_PER_MILLION_TOKENS", "1")
    monkeypatch.setenv("GEMINI_OUTPUT_USD_PER_MILLION_TOKENS", "1")
    monkeypatch.setenv("GEMINI_COST_MODEL_ID", "synthetic-model")
    monkeypatch.setenv("GEMINI_PER_REQUEST_COST_CAP_USD", "1")

    if configuration == "missing-cap":
        monkeypatch.delenv("GEMINI_PER_REQUEST_COST_CAP_USD")
    elif configuration == "invalid-rate":
        monkeypatch.setenv("GEMINI_INPUT_USD_PER_MILLION_TOKENS", "0")
    elif configuration == "model-mismatch":
        monkeypatch.setenv("GEMINI_COST_MODEL_ID", "another-model")
    elif configuration == "insufficient-cap":
        monkeypatch.setenv("GEMINI_PER_REQUEST_COST_CAP_USD", "0.000001")

    client = Mock()
    constructor = Mock(return_value=client)
    monkeypatch.setattr(gemini_provider.genai, "Client", constructor)

    message = _run_worker(channel, mode="gemini")

    assert message == {"status": expected_status}
    client.models.generate_content.assert_not_called()
    assert constructor.called is client_created
    if client_created:
        client.close.assert_called_once()


@pytest.mark.parametrize(
    ("exception", "expected_status"),
    [
        (
            RuntimeError("api_key=synthetic-secret"),
            "failure",
        ),
        (
            TimeoutError("private timeout details"),
            "timeout",
        ),
        (
            DailyQuotaExceeded("private quota details"),
            "unavailable",
        ),
    ],
    ids=["unexpected-failure", "timeout", "quota"],
)
def test_provider_errors_return_only_safe_status(
    channel,
    monkeypatch,
    exception,
    expected_status,
):
    provider = Mock()
    provider.analyze.side_effect = exception
    monkeypatch.setattr(
        analysis_worker,
        "_build_provider",
        Mock(return_value=provider),
    )

    message = _run_worker(channel)

    assert message == {"status": expected_status}
    provider.close.assert_called_once()


def test_wrapped_http_timeout_remains_a_timeout(
    channel,
    monkeypatch,
):
    exception = RuntimeError("Provider request failed")
    exception.__cause__ = httpx.ReadTimeout(
        "private connection details"
    )

    provider = Mock()
    provider.analyze.side_effect = exception
    monkeypatch.setattr(
        analysis_worker,
        "_build_provider",
        Mock(return_value=provider),
    )

    message = _run_worker(channel)

    assert message == {"status": "timeout"}
    provider.close.assert_called_once()


def test_invalid_provider_result_is_rejected(
    channel,
    monkeypatch,
):
    provider = Mock()
    provider.analyze.return_value = {
        "classification": "unsupported"
    }
    monkeypatch.setattr(
        analysis_worker,
        "_build_provider",
        Mock(return_value=provider),
    )

    message = _run_worker(channel)

    assert message == {"status": "failure"}
    provider.close.assert_called_once()
