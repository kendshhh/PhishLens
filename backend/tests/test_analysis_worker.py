from multiprocessing.connection import Connection
from unittest.mock import Mock

import httpx
import pytest

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
    provider = Mock()
    provider.analyze.return_value = AIAnalysisResult(
        classification="legitimate"
    )
    constructor = Mock(return_value=provider)
    monkeypatch.setattr(
        analysis_worker,
        "GeminiProvider",
        constructor,
    )

    message = _run_worker(channel, mode="gemini")

    assert message["status"] == "ok"
    constructor.assert_called_once_with(
        api_key="synthetic-key",
        model="synthetic-model",
        timeout_ms=15_000,
    )
    provider.close.assert_called_once()


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