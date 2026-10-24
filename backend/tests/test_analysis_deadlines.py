import pytest

from backend.app import analysis_deadlines
from backend.app.analysis_deadlines import (
    AnalysisDeadline,
    AnalysisTimeoutError,
)


def test_deadlines_share_one_starting_time(monkeypatch):
    current_time = [100.0]
    monkeypatch.setattr(
        analysis_deadlines,
        "monotonic",
        lambda: current_time[0],
    )

    deadline = AnalysisDeadline.start()

    assert deadline.inference_remaining() == pytest.approx(15.0)
    assert deadline.operation_remaining() == pytest.approx(20.0)

    current_time[0] = 112.0

    assert deadline.inference_remaining() == pytest.approx(3.0)
    assert deadline.operation_remaining() == pytest.approx(8.0)

    current_time[0] = 114.0

    assert deadline.inference_remaining() == pytest.approx(1.0)
    assert deadline.operation_remaining() == pytest.approx(6.0)


@pytest.mark.parametrize("elapsed", [15.0, 16.0])
def test_inference_budget_expires(monkeypatch, elapsed):
    current_time = [100.0]
    monkeypatch.setattr(
        analysis_deadlines,
        "monotonic",
        lambda: current_time[0],
    )
    deadline = AnalysisDeadline.start()

    current_time[0] = 100.0 + elapsed

    with pytest.raises(
        AnalysisTimeoutError,
        match="Analysis deadline exceeded",
    ):
        deadline.inference_remaining()

    assert deadline.operation_remaining() == pytest.approx(
        20.0 - elapsed
    )


@pytest.mark.parametrize("elapsed", [20.0, 21.0])
def test_total_operation_budget_expires(monkeypatch, elapsed):
    current_time = [100.0]
    monkeypatch.setattr(
        analysis_deadlines,
        "monotonic",
        lambda: current_time[0],
    )
    deadline = AnalysisDeadline.start()

    current_time[0] = 100.0 + elapsed

    with pytest.raises(AnalysisTimeoutError):
        deadline.operation_remaining()