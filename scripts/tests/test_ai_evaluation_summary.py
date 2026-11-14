import json
import os
import tempfile
import unittest
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from backend.ai.evaluation_cases import CASES, CASESET_VERSION
from scripts.ai_evaluation_summary import render_summary

COHORT_SHA = sha256(json.dumps(
    [asdict(case) for case in CASES], sort_keys=True,
).encode()).hexdigest()


def write_benchmark(path, summary):
    rows = [{"event": "case", "case": case.id} for case in CASES]
    rows.append(summary)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class AIEvaluationSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.benchmark = Path(self.temp_dir.name) / "benchmark.jsonl"

    def test_renders_complete_provider_free_development_evaluation(self):
        write_benchmark(self.benchmark, {
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

        with unittest.mock.patch.dict(os.environ, {"SOURCE_COMMIT": "c" * 40}):
            summary = render_summary(self.benchmark)

        self.assertIn("Deterministic AI evaluation — complete; quality not approved", summary)
        self.assertIn("40` completed", summary)
        self.assertIn("Gemini/provider requests: `0`", summary)
        self.assertIn("not held-out or production accuracy", summary)
        self.assertIn("not a model-quality pass", summary)

    def test_rejects_incomplete_or_paid_development_evaluation(self):
        base = {
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
        invalid_changes = (
            {"errors": 1},
            {"unattempted_cases": 1},
            {"run_status": "cost_cap_reached"},
            {"spend_guard": {"provider_calls": 1}},
        )
        for changes in invalid_changes:
            with self.subTest(changes=changes):
                data = {**base, **changes}
                write_benchmark(self.benchmark, data)
                with self.assertRaises(ValueError):
                    render_summary(self.benchmark)
