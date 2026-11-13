"""Offline fixtures for the #92 preflight, scoring, and reporting procedure."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.ai.evaluation_cases import CASES
from scripts import evaluate_tfidf_cohort as cohort


def fixture_cases():
    return [
        {
            "id": "a-notice", "source": "original", "family": "account-notice",
            "label": "legitimate", "split": "primary", "scenario": "security_notice",
            "context": "self_contained", "body": "Your scheduled security briefing begins at noon.",
        },
        {
            "id": "b-threat", "source": "original", "family": "account-threat",
            "label": "phishing", "split": "context", "scenario": "credential",
            "context": "external_required", "context_reason": "url_destination",
            "body": "Open the linked page for your account access instructions.",
        },
        {
            "id": "c-spam", "source": "original", "family": "catalog-spam",
            "label": "spam", "split": "primary", "scenario": "promotion",
            "context": "self_contained", "body": "Weekend catalogue offers from the imaginary lamp shop.",
        },
    ]


class CohortTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.bundle = Path(directory.name)
        self.rows = fixture_cases()
        self.source = {
            "id": "original", "kind": "synthetic", "attribution": "Project test authors",
            "revision": "fixture-v1", "date_range": "2026-11-13",
            "permission": "Original test fixtures under repository terms",
            "collection": "Written for this runner test", "redistribution": "Repository fixture",
            "evaluation_allowed": True,
        }

    def write_bundle(self):
        manifest = b"".join((json.dumps(row) + "\n").encode() for row in self.rows)
        (self.bundle / "manifest.jsonl").write_bytes(manifest)
        manifest_hash = cohort.sha256(manifest)
        files = {
            "sources.json": [self.source],
            "label-review.json": {
                "manifest_sha256": manifest_hash, "reviewers": ["fixture-a", "fixture-b"],
                "score_blind": True, "unresolved_admitted": 0,
            },
            "overlap.json": {
                "manifest_sha256": manifest_hash, "reviewer": "fixture-reviewer",
                "method": "Test the review schema with declared comparison limitations",
                "unresolved_admitted": 0,
                "roles": {role: {"status": "limited", "reference": "Fixture exercise only"}
                          for role in cohort.OVERLAP_ROLES},
            },
        }
        for name, data in files.items():
            (self.bundle / name).write_bytes(cohort.json_bytes(data))

    def run_cli(self, mode, *args):
        return subprocess.run(
            [sys.executable, "scripts/evaluate_tfidf_cohort.py", mode, "--bundle", str(self.bundle), *args],
            cwd=cohort.ROOT, capture_output=True, check=False,
        )

    def test_cli_runs_real_adapter_only_after_matching_lock(self):
        self.write_bundle()
        preflight = self.run_cli("preflight")
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        self.assertEqual(json.loads(preflight.stdout)["family_counts"]["synthetic/context/phishing"], 1)
        lock = self.bundle / "lock.json"
        lock.write_bytes(preflight.stdout)
        output = self.bundle / "report.json"
        args = ("--lock", str(lock), "--output", str(output), "--expected-lock-sha")
        denied = self.run_cli("score", *args, "0" * 64)
        self.assertNotEqual(denied.returncode, 0)
        self.assertFalse(output.exists())
        result = self.run_cli("score", *args, cohort.sha256(preflight.stdout))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(output.read_bytes())
        self.assertEqual(report["actual_mail_screening"], "unassessed")
        self.assertEqual(report["groups"]["synthetic/primary"]["attempted"], 2)
        self.assertEqual(report["groups"]["synthetic/context"]["attempted"], 1)
        self.assertNotIn("body", report["cases"][0])
        duplicate = self.run_cli("score", *args, cohort.sha256(preflight.stdout))
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertEqual(json.loads(output.read_bytes()), report)
        self.rows[0]["body"] += " Bring a printed agenda."
        self.write_bundle()
        stale_args = (*args[:2], "--output", str(self.bundle / "stale.json"), args[-1])
        stale = self.run_cli("score", *stale_args, cohort.sha256(preflight.stdout))
        self.assertNotEqual(stale.returncode, 0)
        self.assertFalse((self.bundle / "stale.json").exists())

    def test_rejects_overlap_missing_rights_and_context_in_primary(self):
        for change, message in (
            ({"body": " " + CASES[0].body + " "}, b"overlap with synthetic-v1"),
            ({"context": "external_required", "context_reason": "sender"}, b"excluded from primary"),
        ):
            with self.subTest(message=message):
                self.rows[0] = fixture_cases()[0] | change
                self.write_bundle()
                result = self.run_cli("preflight")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
        self.rows = fixture_cases()
        self.source["evaluation_allowed"] = False
        self.write_bundle()
        result = self.run_cli("preflight")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"lacks evaluation permission", result.stderr)

    def test_reports_failures_and_keeps_source_kinds_separate(self):
        self.write_bundle()
        lock, rows, sources = cohort.freeze(self.bundle)
        sources["test-kind"] = self.source | {"kind": "actual_mail"}
        rows[0]["source"] = "test-kind"
        service = Mock()
        model_id = lock["model"]["model_id"]
        service.analyze_email.side_effect = [
            SimpleNamespace(model_revision=cohort.MODEL_SHA256, model=model_id,
                            model_alert=True, raw_margin=0.4, phishing_score=0.9, classification="phishing"),
            TimeoutError("fixture payload must stay private"),
            SimpleNamespace(model_revision="wrong", model=model_id, model_alert=False,
                            raw_margin=-0.4, phishing_score=0.1, classification="legitimate"),
        ]
        report = cohort.evaluate(rows, sources, lock, lambda: service)
        self.assertEqual(service.analyze_email.call_count, len(rows))
        self.assertEqual(report["groups"]["actual_mail/primary"]["legitimate_false_positive_rate"]["value"], 1)
        context = report["groups"]["synthetic/context"]
        self.assertEqual(context["counts"]["timeout"], 1)
        self.assertEqual(context["phishing_recall"]["value"], 0)
        self.assertIsNone(context["alert_precision_at_cohort_mix"]["value"])
        self.assertEqual(report["groups"]["synthetic/primary"]["counts"]["invalid_output"], 1)
        self.assertNotIn("fixture payload", json.dumps(report))

    def test_initialization_failure_marks_all_cases_unattempted(self):
        self.write_bundle()
        lock, rows, sources = cohort.freeze(self.bundle)
        report = cohort.evaluate(rows, sources, lock, Mock(side_effect=RuntimeError("private")))
        self.assertEqual(report["run_status"], "initialization_failed")
        self.assertEqual({row["outcome"] for row in report["cases"]}, {"unattempted"})
        self.assertEqual(report["groups"]["synthetic/primary"]["attempted"], 0)

    def test_screening_needs_diverse_primary_actual_mail_and_valid_results(self):
        self.write_bundle()
        lock, rows, sources = cohort.freeze(self.bundle)
        sources["original"]["kind"] = "actual_mail"
        rows[1] |= {"split": "primary", "context": "self_contained"}
        lock["limited_overlap_roles"] = []
        for row in rows:
            lock["family_counts"][f'actual_mail/primary/{row["label"]}'] = 1
        lock["family_counts"]["actual_mail/primary/security_notice"] = 1
        model_id = lock["model"]["model_id"]
        alert = SimpleNamespace(model_revision=cohort.MODEL_SHA256, model=model_id,
                                model_alert=True, raw_margin=0.4, phishing_score=0.9, classification="phishing")
        below = SimpleNamespace(model_revision=cohort.MODEL_SHA256, model=model_id,
                                model_alert=False, raw_margin=-0.4, phishing_score=0.1,
                                classification="legitimate")
        service = Mock()
        small_criteria = {
            "primary_family_minima": dict.fromkeys(cohort.LABELS, 1),
            "security_notice_minimum": 1,
        }
        with patch.dict(cohort.CRITERIA, small_criteria):
            service.analyze_email.side_effect = [below, alert, below]
            self.assertEqual(cohort.evaluate(rows, sources, lock, lambda: service)["actual_mail_screening"],
                             "unassessed")
            with patch.dict(cohort.CRITERIA, {"primary_sources_per_label_minimum": 1}):
                service.analyze_email.side_effect = [below, alert, below]
                self.assertEqual(cohort.evaluate(rows, sources, lock, lambda: service)["actual_mail_screening"],
                                 "met")
                service.analyze_email.side_effect = [below, alert, RuntimeError("failed spam fixture")]
                self.assertEqual(cohort.evaluate(rows, sources, lock, lambda: service)["actual_mail_screening"],
                                 "not_met")


if __name__ == "__main__":
    unittest.main()
