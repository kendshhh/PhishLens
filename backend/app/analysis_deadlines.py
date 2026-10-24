"""Shared time budgets for persistent analysis creation."""

from dataclasses import dataclass
from time import monotonic

INFERENCE_BUDGET_SECONDS = 15.0
OPERATION_BUDGET_SECONDS = 20.0


class AnalysisTimeoutError(RuntimeError):
    """The analysis operation exhausted its permitted time."""


@dataclass(frozen=True)
class AnalysisDeadline:
    started_at: float

    @classmethod
    def start(cls) -> "AnalysisDeadline":
        """Start one clock for inference and persistence."""
        return cls(started_at=monotonic())

    def inference_remaining(self) -> float:
        """Return the remaining inference and validation budget."""
        return self._remaining(INFERENCE_BUDGET_SECONDS)

    def operation_remaining(self) -> float:
        """Return the remaining total operation budget."""
        return self._remaining(OPERATION_BUDGET_SECONDS)

    def _remaining(self, budget_seconds: float) -> float:
        remaining = self.started_at + budget_seconds - monotonic()
        if remaining <= 0:
            raise AnalysisTimeoutError("Analysis deadline exceeded")
        return remaining