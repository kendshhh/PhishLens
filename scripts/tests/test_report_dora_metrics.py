import unittest

from scripts.report_dora_metrics import compute, render


class DoraReportTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "schema_version": 1,
            "current_main_sha": "a" * 40,
            "collected_at_utc": "2026-11-25T00:00:00Z",
            "window_utc": {"start": "2026-10-28T00:00:00Z", "end": "2026-11-25T00:00:00Z", "duration_days": 28},
            "source_urls": {},
            "ci_runs": [
                {"started_at_utc": "2026-11-01T00:00:00Z", "finished_at_utc": "2026-11-01T00:01:00Z", "conclusion": "success"},
                {"started_at_utc": "2026-11-02T00:00:00Z", "finished_at_utc": "2026-11-02T00:02:00Z", "conclusion": "failure"},
            ],
            "merged_pull_requests": [
                {"number": 1, "merge_sha": "b" * 40, "merged_at_utc": "2026-11-02T00:00:00Z"},
            ],
            "production_deployments": [
                {"deploy_id": "d1", "sha": "b" * 40, "status": "deactivated", "finished_at_utc": "2026-11-02T00:10:00Z"},
                {"deploy_id": "d2", "sha": "b" * 40, "status": "live", "finished_at_utc": "2026-11-02T00:20:00Z"},
                {"deploy_id": "d3", "sha": "c" * 40, "status": "build_failed", "finished_at_utc": "2026-11-03T00:00:00Z"},
            ],
            "recovery_events": None,
            "deployment_classifications": None,
        }

    def test_exact_sha_lead_time_and_successful_deploy_rate(self):
        result = compute(self.snapshot)
        self.assertEqual(result["matched_change_count"], 1)
        self.assertEqual(result["change_lead_time_minutes"]["median"], 10)
        self.assertEqual(result["deployment_frequency"]["successful_deployments"], 2)
        self.assertEqual(result["deployment_frequency"]["failed_attempts"], 1)

    def test_unavailable_dora_metrics_are_not_reported_as_zero(self):
        report = render(self.snapshot)
        self.assertIn("Change fail rate | **Not measured**", report)
        self.assertIn("not measured (no qualifying production recovery records)", report)
        self.assertIn("not measured (deployments lack reviewed planned/unplanned classifications)", report)

    def test_optimization_report_distinguishes_job_gain_from_end_to_end_evidence(self):
        report = render(self.snapshot)
        self.assertIn("PR [#119]", report)
        self.assertIn("17.2% lower", report)
        self.assertIn("not end-to-end", report)
        self.assertIn("failure-rate improvement", report)

    def test_rework_requires_complete_classification(self):
        self.snapshot["deployment_classifications"] = [{"classification": "planned"}]
        with self.assertRaisesRegex(ValueError, "every successful deployment"):
            compute(self.snapshot)

    def test_invalid_or_timezone_less_dates_fail(self):
        bad = dict(self.snapshot)
        bad["window_utc"] = {"start": "2026-11-01T00:00:00", "end": "2026-10-01T00:00:00Z"}
        with self.assertRaisesRegex(ValueError, "timezone"):
            compute(bad)

    def test_variable_precision_fractional_seconds_are_normalized(self):
        self.snapshot["production_deployments"][0]["finished_at_utc"] = "2026-11-02T00:10:00.06969Z"
        result = compute(self.snapshot)
        self.assertEqual(result["matched_change_count"], 1)


if __name__ == "__main__":
    unittest.main()
