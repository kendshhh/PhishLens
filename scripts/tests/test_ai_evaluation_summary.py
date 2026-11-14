import json
from dataclasses import asdict
from hashlib import sha256

import pytest

from backend.ai.evaluation_cases import CASES, CASESET_VERSION
from scripts.ai_evaluation_summary import render_summary

COHORT_SHA = sha256(json.dumps(
    [asdict(case) for case in CASES], sort_keys=True,
).encode()).hexdigest()


def write_benchmark(path, summary):
    rows = [{"event": "case", "case": case.id} for case in CASES]
    rows.append(summary)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_renders_complete_provider_free_development_evaluation(tmp_path, monkeypatch):
    benchmark = tmp_path / "benchmark.jsonl"
    write_benchmark(benchmark, {
        "event": "summary",
        "model": "tfidf",
        "run_status": "finished",
        "attempts": 40,
        "requested_cases": 40,
        "errors": 0,
        "unattempted_cases": 0,
        "binary_accuracy": 0.8,
        "phishing_recall": 0.75,
        "legitimate_false_positive_rate": 0.1,
        "caseset": CASESET_VERSION,
        "cases_sha256": COHORT_SHA,
        "model_metadata": {"model_revision": "b" * 64},
        "spend_guard": {"provider_calls": 0},
    })
    monkeypatch.setenv("SOURCE_COMMIT", "c" * 40)

    summary = render_summary(benchmark)

    assert "Deterministic AI evaluation — complete; quality not approved" in summary
    assert "40` completed" in summary
    assert "Gemini/provider requests: `0`" in summary
    assert "not held-out or production accuracy" in summary
    assert "not a model-quality pass" in summary


@pytest.mark.parametrize("changes", [
    {"errors": 1},
    {"unattempted_cases": 1},
    {"run_status": "cost_cap_reached"},
    {"spend_guard": {"provider_calls": 1}},
])
def test_rejects_incomplete_or_paid_development_evaluation(tmp_path, changes):
    data = {
        "event": "summary",
        "model": "tfidf",
        "run_status": "finished",
        "attempts": 40,
        "requested_cases": 40,
        "errors": 0,
        "unattempted_cases": 0,
        "caseset": CASESET_VERSION,
        "cases_sha256": COHORT_SHA,
        "binary_accuracy": 0.8,
        "phishing_recall": 0.75,
        "legitimate_false_positive_rate": 0.1,
        "model_metadata": {"model_revision": "b" * 64},
        "spend_guard": {"provider_calls": 0},
    }
    data.update(changes)
    benchmark = tmp_path / "benchmark.jsonl"
    write_benchmark(benchmark, data)

    with pytest.raises(ValueError):
        render_summary(benchmark)
