from multiprocessing import active_children, get_context
from threading import BoundedSemaphore
from time import sleep
from types import SimpleNamespace

import pytest

from backend.app import analysis_deadlines, analysis_execution
from backend.app.analysis_deadlines import AnalysisDeadline, AnalysisTimeoutError


@pytest.fixture
def inference_slot(monkeypatch):
    slot = BoundedSemaphore(value=1)
    monkeypatch.setattr(analysis_execution, "_INFERENCE_SLOT", slot)
    return slot


def _run_mock():
    return analysis_execution.run_saved_inference(
        subject="",
        body="Synthetic process test",
        mode="mock",
        api_key=None,
        model=None,
        deadline=AnalysisDeadline.start(),
    )


def test_real_mock_process_returns_valid_result(inference_slot):
    result = _run_mock()

    assert result.classification == "spam"
    assert result.confidence is None
    assert inference_slot.acquire(blocking=False)
    inference_slot.release()


def test_real_timeout_stops_process_and_allows_retry(
    inference_slot,
    monkeypatch,
):
    real_context = get_context("spawn")
    original_stop = analysis_execution._stop_worker
    cleanup_results = []

    def make_sleeping_process(**_kwargs):
        return real_context.Process(
            target=sleep,
            args=(30,),
            daemon=True,
        )

    def stop_and_record(process):
        pid = process.pid
        stopped = original_stop(process)
        cleanup_results.append((pid, stopped))
        return stopped

    context = SimpleNamespace(
        RawArray=real_context.RawArray,
        RawValue=real_context.RawValue,
        Process=make_sleeping_process,
    )

    with monkeypatch.context() as patch:
        patch.setattr(
            analysis_deadlines,
            "INFERENCE_BUDGET_SECONDS",
            0.25,
        )
        patch.setattr(
            analysis_execution,
            "get_context",
            lambda _method: context,
        )
        patch.setattr(
            analysis_execution,
            "_stop_worker",
            stop_and_record,
        )

        with pytest.raises(AnalysisTimeoutError):
            _run_mock()

    assert len(cleanup_results) == 1
    stopped_pid, stopped = cleanup_results[0]
    assert stopped_pid is not None
    assert stopped is True
    assert all(
        child.pid != stopped_pid
        for child in active_children()
    )

    # The original provider and budget are restored for the retry.
    result = _run_mock()

    assert result.classification == "spam"
    assert inference_slot.acquire(blocking=False)
    inference_slot.release()