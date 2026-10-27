from multiprocessing.process import BaseProcess
from threading import BoundedSemaphore
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.app import analysis_deadlines, analysis_execution
from backend.app.analysis_channel import SharedResultChannel
from backend.app.analysis_deadlines import AnalysisDeadline, AnalysisTimeoutError
from backend.app.analysis_execution import (
    AnalysisInferenceError,
    AnalysisUnavailableError,
)


@pytest.fixture
def execution_context(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(
        analysis_deadlines,
        "monotonic",
        lambda: clock[0],
    )

    process = Mock(spec=BaseProcess)
    process.pid = 123
    process.exitcode = 0
    process.is_alive.return_value = False

    process_factory = Mock(return_value=process)
    context = SimpleNamespace(Process=process_factory)
    monkeypatch.setattr(
        analysis_execution,
        "get_context",
        Mock(return_value=context),
    )

    channel = Mock(spec=SharedResultChannel)
    channel.receive.return_value = {
        "status": "ok",
        "result": {"classification": "legitimate"},
    }
    monkeypatch.setattr(
        analysis_execution,
        "SharedResultChannel",
        Mock(return_value=channel),
    )

    slot = BoundedSemaphore(value=1)
    monkeypatch.setattr(analysis_execution, "_INFERENCE_SLOT", slot)

    return SimpleNamespace(
        process=process,
        process_factory=process_factory,
        channel=channel,
        slot=slot,
        clock=clock,
        deadline=AnalysisDeadline.start(),
    )


def _run(context, *, mode="mock"):
    return analysis_execution.run_saved_inference(
        subject="",
        body="Synthetic email body",
        mode=mode,
        api_key=None,
        model=None,
        deadline=context.deadline,
    )


def test_success_closes_worker_and_releases_slot(execution_context):
    context = execution_context

    result = _run(context)

    assert result.classification == "legitimate"
    context.process.start.assert_called_once()
    context.process.close.assert_called_once()
    assert context.slot.acquire(blocking=False)
    context.slot.release()


@pytest.mark.parametrize("mode", ["local", "gemini"])
def test_unavailable_configuration_skips_worker(
    execution_context,
    mode,
):
    context = execution_context

    with pytest.raises(AnalysisUnavailableError):
        _run(context, mode=mode)

    context.process_factory.assert_not_called()


def test_busy_worker_rejects_new_request(execution_context):
    context = execution_context
    assert context.slot.acquire(blocking=False)

    try:
        with pytest.raises(AnalysisUnavailableError):
            _run(context)

        context.process_factory.assert_not_called()
    finally:
        context.slot.release()


@pytest.mark.parametrize(
    ("message", "expected_error"),
    [
        ({"status": "timeout"}, AnalysisTimeoutError),
        ({"status": "unavailable"}, AnalysisUnavailableError),
        ({"status": "failure"}, AnalysisInferenceError),
        (
            {
                "status": "ok",
                "result": {"classification": "unsupported"},
            },
            AnalysisInferenceError,
        ),
    ],
    ids=["timeout", "unavailable", "failure", "invalid-result"],
)
def test_worker_messages_raise_expected_errors(
    execution_context,
    message,
    expected_error,
):
    context = execution_context
    context.channel.receive.return_value = message

    with pytest.raises(expected_error):
        _run(context)

    context.process.close.assert_called_once()


def test_crashed_worker_result_is_not_read(execution_context):
    context = execution_context
    context.process.exitcode = 1

    with pytest.raises(AnalysisInferenceError):
        _run(context)

    context.channel.receive.assert_not_called()


def test_timeout_terminates_worker(execution_context):
    context = execution_context
    context.process.is_alive.side_effect = [True, True, False, False]

    with pytest.raises(AnalysisTimeoutError):
        _run(context)

    context.process.terminate.assert_called_once()
    context.process.kill.assert_not_called()
    context.process.close.assert_called_once()
    context.channel.receive.assert_not_called()
    assert context.slot.acquire(blocking=False)
    context.slot.release()


def test_timeout_kills_worker_if_termination_is_insufficient(
    execution_context,
):
    context = execution_context
    context.process.is_alive.side_effect = [True, True, True, False]

    with pytest.raises(AnalysisTimeoutError):
        _run(context)

    context.process.terminate.assert_called_once()
    context.process.kill.assert_called_once()
    context.process.close.assert_called_once()


def test_failed_cleanup_keeps_admission_closed(execution_context):
    context = execution_context
    context.process.is_alive.return_value = True

    with pytest.raises(AnalysisUnavailableError):
        _run(context)

    context.process.terminate.assert_called_once()
    context.process.kill.assert_called_once()
    context.process.close.assert_not_called()
    assert not context.slot.acquire(blocking=False)


def test_late_result_is_rejected(execution_context):
    context = execution_context
    message = context.channel.receive.return_value

    def finish_late():
        context.clock[0] = 116.0
        return message

    context.channel.receive.side_effect = finish_late

    with pytest.raises(AnalysisTimeoutError):
        _run(context)

    context.process.close.assert_called_once()


def test_invalid_channel_data_returns_safe_error(execution_context):
    context = execution_context
    context.channel.receive.side_effect = ValueError(
        "synthetic-secret"
    )

    with pytest.raises(AnalysisInferenceError) as captured:
        _run(context)

    assert "synthetic-secret" not in str(captured.value)


def test_start_failure_returns_safe_error_and_releases_slot(
    execution_context,
):
    context = execution_context
    context.process.pid = None
    context.process.start.side_effect = OSError("synthetic-secret")

    with pytest.raises(AnalysisUnavailableError) as captured:
        _run(context)

    assert "synthetic-secret" not in str(captured.value)
    context.process.close.assert_called_once()
    assert context.slot.acquire(blocking=False)
    context.slot.release()