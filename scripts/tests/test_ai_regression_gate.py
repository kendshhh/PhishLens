"""Negative evidence checks for the reviewed deterministic AI gate."""

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from backend.ai.evaluation_cases import CASES, CASESET_VERSION
from scripts import verify_ai_regression as gate


class AIRegressionGateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.report = self.root / "contracts.xml"
        self.benchmark = self.root / "benchmark.jsonl"
        self.required = ["contracts::first", "contracts::second"]

    def write_contracts(self, names=None, outcome=None, suite_errors=0):
        suite = ET.Element("testsuite", errors=str(suite_errors))
        for name in (self.required if names is None else names):
            classname, test = name.split("::", 1)
            case = ET.SubElement(suite, "testcase", classname=classname, name=test)
            if outcome:
                ET.SubElement(case, outcome)
        ET.ElementTree(suite).write(self.report, encoding="utf-8")

    def write_development(self):
        baseline = {
            "schema": 1,
            "model_sha256": sha256(gate.MODEL.read_bytes()).hexdigest(),
            "development": {
                "caseset": CASESET_VERSION,
                "cases": len(CASES),
                "cases_sha256": sha256(json.dumps(
                    [asdict(case) for case in CASES], sort_keys=True,
                ).encode()).hexdigest(),
            },
        }
        summary = {
            "event": "summary", "model": "tfidf", "run_status": "finished",
            "attempts": len(CASES), "requested_cases": len(CASES),
            "errors": 0, "unattempted_cases": 0,
            "binary_accuracy": 0.5, "phishing_recall": 0.5,
            "legitimate_false_positive_rate": 0.5,
            "caseset": CASESET_VERSION,
            "cases_sha256": baseline["development"]["cases_sha256"],
            "model_metadata": {"model_revision": baseline["model_sha256"]},
            "spend_guard": {"provider_calls": 0},
        }
        events = [{"event": "case", "case": case.id} for case in CASES] + [summary]
        self.benchmark.write_text("\n".join(json.dumps(row) for row in events) + "\n", encoding="utf-8")
        return baseline

    def test_accepts_the_exact_complete_contract_inventory(self):
        self.write_contracts()
        self.assertEqual(gate.verify_contracts(self.report, self.required), 2)

    def test_rejects_missing_extra_and_duplicated_contract_tests(self):
        for names in ([], self.required[:1], self.required + ["contracts::extra"],
                      self.required + self.required[:1]):
            with self.subTest(names=names):
                self.write_contracts(names)
                with self.assertRaises(ValueError):
                    gate.verify_contracts(self.report, self.required)

    def test_rejects_failed_errored_and_skipped_required_tests(self):
        for outcome in ("failure", "error", "skipped"):
            with self.subTest(outcome=outcome):
                self.write_contracts(outcome=outcome)
                with self.assertRaises(ValueError):
                    gate.verify_contracts(self.report, self.required)

    def test_rejects_collection_error_even_with_complete_testcase_list(self):
        self.write_contracts(suite_errors=1)
        with self.assertRaises(ValueError):
            gate.verify_contracts(self.report, self.required)

    def test_rejects_empty_or_duplicated_reviewed_inventory(self):
        self.write_contracts()
        for required in ([], self.required + self.required[:1]):
            with self.subTest(required=required), self.assertRaises(ValueError):
                gate.verify_contracts(self.report, required)

    def test_accepts_identity_match_without_imposing_a_quality_cutoff(self):
        baseline = self.write_development()
        self.assertIn("not a model-quality pass", gate.verify_development(self.benchmark, baseline))

    def test_rejects_changed_case_model_and_unknown_baseline(self):
        for field in ("cases", "cases_sha256", "model_sha256", "schema"):
            with self.subTest(field=field):
                baseline = self.write_development()
                if field in ("cases", "cases_sha256"):
                    baseline["development"][field] = 1 if field == "cases" else "b" * 64
                else:
                    baseline[field] = "b" * 64 if field == "model_sha256" else 2
                with self.assertRaises(ValueError):
                    gate.verify_development(self.benchmark, baseline)

    def test_rejects_report_model_substitution_and_paid_calls(self):
        for changes in ({"model_metadata": {"model_revision": "b" * 64}},
                        {"spend_guard": {"provider_calls": 1}}):
            with self.subTest(changes=changes):
                baseline = self.write_development()
                rows = [json.loads(line) for line in self.benchmark.read_text().splitlines()]
                rows[-1].update(changes)
                self.benchmark.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
                with self.assertRaises(ValueError):
                    gate.verify_development(self.benchmark, baseline)


if __name__ == "__main__":
    unittest.main()
