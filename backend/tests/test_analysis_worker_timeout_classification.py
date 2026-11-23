"""Regression tests for typed provider timeout handling in saved analysis."""

from backend.ai.errors import AIProviderTimeoutError
from backend.app.analysis_worker import _failure_status


def test_typed_provider_timeout_is_classified_for_saved_analysis():
    error = AIProviderTimeoutError("private provider timeout details")

    assert _failure_status(error) == "timeout"
