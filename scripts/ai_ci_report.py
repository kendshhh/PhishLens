"""Create redacted revision-linked summaries for the deterministic AI gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ai.evaluation_cases import CASES, CASESET_VERSION

REQUIRED_AI_TESTS = frozenset(
    {
        ("test_ai_service", "test_email_fields_stay_data_and_valid_quotes_are_preserved"),
        ("test_ai_service", "test_invented_evidence_fails_instead_of_becoming_a_valid_report"),
        ("test_ai_service", "test_invalid_input_never_reaches_provider"),
        ("test_ai_service", "test_malformed_provider_contract_is_a_controlled_failure"),
        ("test_ai_service", "test_classifier_score_must_be_finite_and_bounded"),
        ("test_ai_service", "test_llm_cannot_supply_classifier_score_or_provenance"),
        ("test_ai_service", "test_benchmark_metrics_count_errors_as_failed_opportunities"),
        ("test_ai_service", "test_evaluation_cases_are_unique_balanced_and_within_api_limits"),
        ("test_ai_service", "test_benchmark_stops_at_daily_quota_without_inventing_missing_scores"),
        ("test_ai_providers", "test_offline_modes_need_no_google_credentials"),
        ("test_ai_providers", "test_invalid_ai_configuration_fails_explicitly"),
        ("test_ai_providers", "test_gemini_uses_raw_json_schema_with_bounded_single_attempt"),
        (
            "test_ai_providers",
            "test_gemma_uses_explicit_prompt_schema_instead_of_unsupported_json_mode",
        ),
        ("test_ai_providers", "test_bad_google_output_is_not_a_safe_verdict"),
        ("test_ai_providers", "test_google_errors_do_not_expose_provider_details"),
        ("test_ai_providers", "test_network_timeout_is_a_controlled_failure"),
        ("test_ai_providers", "test_daily_quota_is_distinct_from_a_temporary_rate_limit"),
        ("test_ai_providers", "test_local_construction_does_not_import_or_load_weights"),
        ("test_ai_providers", "test_local_loading_is_pinned_offline_cased_and_uses_safetensors"),
        ("test_ai_providers", "test_local_label_mismatch_fails_instead_of_guessing"),
        ("test_ai_providers", "test_missing_local_weights_return_an_actionable_failure"),
        ("test_ai_providers", "test_phishing_in_later_window_is_detected"),
        ("test_ai_api", "test_analysis_endpoint_uses_ai_service"),
        ("test_ai_api", "test_analysis_endpoint_returns_mock_mode"),
        ("test_ai_api", "test_analysis_endpoint_rejects_blank_text"),
        ("test_ai_api", "test_analysis_endpoint_reports_configuration_error"),
        ("test_ai_api", "test_analysis_endpoint_reports_provider_failure"),
        ("test_ai_api", "test_subject_sender_and_local_provenance_reach_api"),
        ("test_ai_api", "test_oversized_and_malformed_requests_never_invoke_ai"),
        ("test_ai_api", "test_daily_quota_returns_service_unavailable"),
        ("test_ai_initialization", "test_concurrent_first_requests_share_local_provider"),
        ("test_ai_initialization", "test_failed_initialization_can_be_retried"),
        ("test_provider_error_contract", "test_provider_status_has_safe_endpoint_contract"),
        ("test_provider_error_contract", "test_transport_failure_retains_safe_502_contract"),
        ("test_error_contract", "test_blank_text_has_structured_422_error"),
        ("test_error_contract", "test_inference_failure_has_structured_502_error"),
        ("test_error_contract", "test_missing_model_has_structured_503_error"),
        ("test_output_boundary", "test_invalid_model_output_never_becomes_a_verdict"),
        ("test_safe_errors", "test_provider_failure_does_not_expose_private_details"),
        ("test_safe_errors", "test_invalid_input_does_not_echo_submitted_value"),
        ("test_safe_errors", "test_missing_local_model_is_unavailable_without_a_verdict"),
        ("test_safe_errors", "test_real_local_provider_reports_missing_checkpoint_as_503"),
    }
)
REQUIRED_FAILURE_PATH_TESTS = frozenset(
    {
        ("test_saved_create_postgres", "test_failed_inference_does_not_save"),
        ("test_saved_create_postgres", "test_invalid_saved_response_rolls_back_insert"),
        ("test_saved_create_postgres", "test_create_recovers_after_database_constraint_failure"),
        (
            "test_saved_create_postgres",
            "test_invalid_evidence_does_not_save_and_next_request_succeeds",
        ),
        ("test_saved_create_postgres", "test_database_lock_timeout_does_not_save"),
        ("test_saved_create_postgres", "test_live_analysis_does_not_save_history"),
    }
)
REQUIRED_TESTS = REQUIRED_AI_TESTS | REQUIRED_FAILURE_PATH_TESTS
SAVED_FAILURE_MODULE = "test_saved_create_postgres"

# Historical reference only; this run is not a model-quality acceptance target.
DETERMINISTIC_BASELINE = {
    "workflow_run": "41216421988",
    "source_sha": "cd5687e7884a13e86d0f7c7a96d48163c6dac316",
    "selected_test_instances": 87,
    "passed": 87,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "case_set_version": "synthetic-v1",
    "case_set_sha256": "a755533aa841bc695574196b3147f2c3b408129872a62204c1f4c5f149ab226f",
}
# Proposed deterministic blocker, pending AI-owner approval in issue #93.
BLOCKING_THRESHOLDS = {
    "missing_required_test_ids": 0,
    "skipped_required_test_ids": 0,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
}
# Keep the expected number of cases for parametrized tests explicit so losing
# one parameter case cannot be hidden by the other cases for the same function.
REQUIRED_PARAMETRIZED_CASE_COUNTS = {
    ("test_ai_service", "test_invalid_input_never_reaches_provider"): 3,
    ("test_ai_service", "test_malformed_provider_contract_is_a_controlled_failure"): 4,
    ("test_ai_service", "test_classifier_score_must_be_finite_and_bounded"): 4,
    ("test_ai_service", "test_llm_cannot_supply_classifier_score_or_provenance"): 2,
    ("test_ai_providers", "test_offline_modes_need_no_google_credentials"): 2,
    ("test_ai_providers", "test_invalid_ai_configuration_fails_explicitly"): 3,
    ("test_ai_providers", "test_bad_google_output_is_not_a_safe_verdict"): 5,
    ("test_ai_providers", "test_google_errors_do_not_expose_provider_details"): 7,
    ("test_ai_providers", "test_phishing_in_later_window_is_detected"): 5,
    ("test_provider_error_contract", "test_provider_status_has_safe_endpoint_contract"): 8,
    ("test_provider_error_contract", "test_transport_failure_retains_safe_502_contract"): 2,
    ("test_output_boundary", "test_invalid_model_output_never_becomes_a_verdict"): 4,
    ("test_saved_create_postgres", "test_failed_inference_does_not_save"): 3,
}
SAFE_TEST_ID = re.compile(r"[^A-Za-z0-9_.:\[\]-]+")


def _status(case: ET.Element) -> str:
    if case.find("failure") is not None:
        return "failed"
    if case.find("error") is not None:
        return "error"
    if case.find("skipped") is not None:
        return "skipped"
    return "passed"


def _test_id(case: ET.Element) -> str:
    module = case.get("classname", "unknown")
    # Parametrized IDs may embed arbitrary fixture values. Keep only the test
    # function name in the artifact, never the parameter payload.
    name = case.get("name", "unknown").split("[", 1)[0]
    return SAFE_TEST_ID.sub("_", f"{module}::{name}")


def _test_key(case: ET.Element) -> tuple[str, str]:
    module = case.get("classname", "").rsplit(".", 1)[-1]
    # Match parametrized tests by their function name. Every reported variant
    # still contributes to the skipped/failure counts below.
    name = case.get("name", "").split("[", 1)[0]
    return module, name


def _selected_cases(cases: list[ET.Element]) -> list[ET.Element]:
    return [case for case in cases if _test_key(case) in REQUIRED_TESTS]


def _required_test_id(test: tuple[str, str]) -> str:
    module, name = test
    return SAFE_TEST_ID.sub("_", f"backend.tests.{module}::{name}")


def _coverage(cases: list[ET.Element], required: frozenset[tuple[str, str]]) -> dict:
    observed = Counter(_test_key(case) for case in cases)
    present = {test for test, count in observed.items() if count > 0}
    expected_cases = {
        test: REQUIRED_PARAMETRIZED_CASE_COUNTS.get(test, 1) for test in required
    }
    missing = [
        f"{_required_test_id(test)} (expected {expected}, found {observed[test]})"
        for test, expected in expected_cases.items()
        if observed[test] < expected
    ]
    skipped = {
        _test_key(case) for case in cases if _status(case) == "skipped"
    }
    return {
        "required_test_functions": len(required),
        "present_test_functions": len(required & present),
        "required_test_cases": sum(expected_cases.values()),
        "present_test_cases": sum(
            min(observed[test], expected_cases[test]) for test in required
        ),
        "missing_test_ids": sorted(missing),
        "skipped_test_ids": sorted(_required_test_id(test) for test in required & skipped),
    }


def summarize_junit(junit_path: Path, source_sha: str, ai_mode: str) -> dict:
    label_counts = Counter(case.label for case in CASES)
    cases_sha = hashlib.sha256(
        json.dumps([asdict(case) for case in CASES], sort_keys=True).encode("utf-8")
    ).hexdigest()
    base = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": source_sha,
        "backend_sha": source_sha,
        "ai_mode": ai_mode,
        "model_revision": "mock-fixtures-only",
        "deployment_sha": None,
        "case_set_version": CASESET_VERSION,
        "case_set_sha256": cases_sha,
        "expected_case_counts_by_class": dict(sorted(label_counts.items())),
        "scored_predictions": 0,
        "model_quality_threshold_applied": False,
        "deterministic_gate_policy": {
            "approval_status": "proposed; pending AI-owner review",
            "owner": "Wilberr (@EnviousCoal), identified in issue #92",
            "baseline": DETERMINISTIC_BASELINE,
            "blocking_thresholds": BLOCKING_THRESHOLDS,
        },
        "model_quality_threshold_status": "pending AI-owner agreement in issue #93",
        "live_provider_requests": 0,
        "model_weights_downloaded": False,
        "limitations": [
            "This gate checks deterministic provider/API/failure contracts using mocks and injected faults.",
            "Class counts identify the development case inventory only; no classifier predictions or accuracy are measured.",
            "Held-out evaluation and blocking quality thresholds require AI-owner review; see #92.",
        ],
    }
    if not junit_path.is_file():
        return {**base, "status": "incomplete", "error": "JUnit report was not created", "tests": {}}

    try:
        root = ET.parse(junit_path).getroot()
    except (ET.ParseError, OSError) as exc:
        return {**base, "status": "incomplete", "error": type(exc).__name__, "tests": {}}

    all_cases = root.findall(".//testcase")
    selected = _selected_cases(all_cases)
    ai_coverage = _coverage(all_cases, REQUIRED_AI_TESTS)
    failure_path_coverage = _coverage(all_cases, REQUIRED_FAILURE_PATH_TESTS)
    required_coverage_passed = all(
        len(coverage["missing_test_ids"])
        <= BLOCKING_THRESHOLDS["missing_required_test_ids"]
        and len(coverage["skipped_test_ids"])
        <= BLOCKING_THRESHOLDS["skipped_required_test_ids"]
        for coverage in (ai_coverage, failure_path_coverage)
    )
    if not selected:
        return {
            **base,
            "status": "failed",
            "error": "No required deterministic AI or failure-path tests were found",
            "required_coverage": {
                "ai": ai_coverage,
                "failure_path": failure_path_coverage,
            },
            "tests": {},
        }

    counts = Counter(_status(case) for case in selected)
    by_module: dict[str, Counter] = defaultdict(Counter)
    failures = []
    failure_tests = []
    saved_failure_tests = []
    harness_seconds = 0.0
    for case in selected:
        module = case.get("classname", "unknown").rsplit(".", 1)[-1]
        name = case.get("name", "unknown")
        status = _status(case)
        by_module[module][status] += 1
        try:
            harness_seconds += float(case.get("time", "0"))
        except ValueError:
            pass
        if status in {"failed", "error"}:
            failures.append(_test_id(case))
        lowered = name.lower()
        if any(word in lowered for word in ("failure", "timeout", "quota", "malformed", "unavailable", "rollback", "recover", "does_not_save")):
            failure_tests.append(_test_id(case))
        if module == SAVED_FAILURE_MODULE:
            saved_failure_tests.append(_test_id(case))

    status = (
        "passed"
        if required_coverage_passed
        and counts["failed"] <= BLOCKING_THRESHOLDS["failed"]
        and counts["error"] <= BLOCKING_THRESHOLDS["errors"]
        and counts["skipped"] <= BLOCKING_THRESHOLDS["skipped"]
        else "failed"
    )
    return {
        **base,
        "status": status,
        "required_coverage": {
            "ai": ai_coverage,
            "failure_path": failure_path_coverage,
        },
        "tests": {
            "total": len(selected),
            "passed": counts["passed"],
            "failed": counts["failed"],
            "errors": counts["error"],
            "skipped": counts["skipped"],
            "by_module": {name: dict(sorted(values.items())) for name, values in sorted(by_module.items())},
            "failed_test_ids": failures,
        },
        "offline_failure_drill": {
            "mode": "simulated_only",
            "provider_failure_test_ids": sorted(failure_tests),
            "saved_analysis_failure_test_ids": sorted(saved_failure_tests),
            "provider_requests": 0,
            "production_writes": 0,
            "deployment_sha": None,
            "test_harness_seconds": round(harness_seconds, 6),
            "service_recovery_time_seconds": None,
            "note": "Test execution time is not a live service recovery measurement.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-sha", default=os.getenv("SOURCE_COMMIT", "local"))
    parser.add_argument("--ai-mode", default=os.getenv("AI_MODE", "unknown"))
    args = parser.parse_args()

    report = summarize_junit(args.junit, args.source_sha, args.ai_mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "source_sha": report["source_sha"],
                "required_coverage": report.get("required_coverage", {}),
                "tests": report.get("tests", {}),
            },
            sort_keys=True,
        )
    )

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        tests = report.get("tests", {})
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## Deterministic AI contract regression\n\n")
            summary.write(f"- Status: `{report['status']}`\n")
            summary.write(f"- Tested source SHA: `{report['source_sha']}`\n")
            summary.write(f"- Case set: `{report['case_set_version']}` / `{report['case_set_sha256']}`\n")
            summary.write(f"- Contract tests: {tests.get('passed', 0)} passed, {tests.get('failed', 0)} failed, {tests.get('errors', 0)} errors, {tests.get('skipped', 0)} skipped\n")
            for group, coverage in sorted(report.get("required_coverage", {}).items()):
                summary.write(
                    f"- Required {group} coverage: "
                    f"{coverage.get('present_test_functions', 0)}/"
                    f"{coverage.get('required_test_functions', 0)} functions; "
                    f"{coverage.get('present_test_cases', 0)}/"
                    f"{coverage.get('required_test_cases', 0)} cases\n"
                )
                for missing in coverage.get("missing_test_ids", []):
                    summary.write(f"  - Missing: `{missing}`\n")
                for skipped in coverage.get("skipped_test_ids", []):
                    summary.write(f"  - Skipped: `{skipped}`\n")
            summary.write("- Provider calls and model downloads: 0\n")
            summary.write("- Class counts are inventory only; no predictions or model-quality metrics were produced.\n")

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

