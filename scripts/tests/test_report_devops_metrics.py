"""Keep consultation evidence honest and avoid copying sensitive observer fields."""

import unittest

from scripts.report_devops_metrics import render


class ConsultationMetricsTests(unittest.TestCase):
    def test_unknown_and_zero_are_distinct(self):
        report = render({"pipeline": {"successes": 0}})
        self.assertIn("| Successful workflows | 0 |", report)
        self.assertIn("| Average PR pipeline (minutes) | not measured |", report)

    def test_convert_seconds_without_changing_sample_count(self):
        report = render({"pipeline": {"average_pr_pipeline_seconds": 120, "pr_duration_samples": 3}})
        self.assertIn("| Average PR pipeline (minutes) | 2.00 |", report)
        self.assertIn("| PR duration samples | 3 |", report)

    def test_pending_cancelled_and_deploy_scope_are_visible(self):
        report = render({"pipeline": {"cancelled": 2, "pending": 4},
                         "deployments": {"observed_live_deployments": 1}})
        self.assertIn("| Pending workflows (separate) | 4 |", report)
        self.assertIn("not lifetime", report)
        self.assertIn("No optimization gain", report)

    def test_invalid_numbers_fail(self):
        for value in (-1, float("nan"), float("inf"), True, "unknown"):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                render({"pipeline": {"successes": value}})
        with self.assertRaises(ValueError):
            render({"pipeline": {"success_rate_percent": 101}})

    def test_does_not_copy_logs_errors_or_inferred_recovery(self):
        report = render({"error": "private-secret", "log_evidence": "private-email",
                         "deployments": {"recovery_time": "guessed-private-value"}})
        self.assertNotIn("private", report)
        self.assertIn("Recovery time | not measured", report)

    def test_only_canonical_sources_are_linked(self):
        url = "https://github.com/kendshhh/PhishLens/actions/runs/123"
        self.assertIn(url, render({"workflow_sources": [url]}))
        for source in ("https://example.com/private", url + "?token=private", "](javascript:alert(1))"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                render({"workflow_sources": [source]})

    def test_period_is_explicit_and_ordered(self):
        data = {"period_start": "2026-10-20T00:00:00+00:00",
                "period_end": "2026-10-21T00:00:00+00:00"}
        self.assertIn("Reporting period (UTC): 2026-10-20", render(data))
        with self.assertRaises(ValueError):
            render({"period_start": data["period_end"], "period_end": data["period_start"]})

    def test_invalid_shapes_fail(self):
        with self.assertRaises(TypeError):
            render([])
        with self.assertRaises(TypeError):
            render({"pipeline": []})
