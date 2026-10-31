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

AI_MODULES = {
    "test_ai_service",
    "test_ai_providers",
    "test_ai_api",
    "test_ai_initialization",
    "test_provider_error_contract",
    "test_error_contract",
    "test_output_boundary",
    "test_safe_errors",
}
SAVED_FAILURE_MODULE = "test_saved_create_postgres"
SAVED_FAILURE_MARKERS = (
    "failed_inference_does_not_save",
    "invalid_saved_response_rolls_back_insert",
    "create_recovers_after_database_constraint_failure",
    "database_lock_timeout_does_not_save",
    "live_analysis_does_not_save_history",
    "next_request_succeeds",
)
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


def _selected_cases(cases: list[ET.Element]) -> list[ET.Element]:
    selected = []
    for case in cases:
        module = case.get("classname", "").rsplit(".", 1)[-1]
        name = case.get("name", "")
        if module in AI_MODULES:
            selected.append(case)
        elif module == SAVED_FAILURE_MODULE and any(marker in name for marker in SAVED_FAILURE_MARKERS):
            selected.append(case)
    return selected


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
        "model_quality_threshold_status": "pending AI-owner agreement in issues #49/#92",
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
    if not selected:
        return {**base, "status": "incomplete", "error": "No deterministic AI regression tests were found", "tests": {}}

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

    status = "passed" if counts["failed"] == 0 and counts["error"] == 0 and counts["skipped"] == 0 else "failed"
    return {
        **base,
        "status": status,
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
    print(json.dumps({"status": report["status"], "source_sha": report["source_sha"], "tests": report.get("tests", {})}, sort_keys=True))

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        tests = report.get("tests", {})
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## Deterministic AI contract regression\n\n")
            summary.write(f"- Status: `{report['status']}`\n")
            summary.write(f"- Tested source SHA: `{report['source_sha']}`\n")
            summary.write(f"- Case set: `{report['case_set_version']}` / `{report['case_set_sha256']}`\n")
            summary.write(f"- Contract tests: {tests.get('passed', 0)} passed, {tests.get('failed', 0)} failed, {tests.get('errors', 0)} errors, {tests.get('skipped', 0)} skipped\n")
            summary.write("- Provider calls and model downloads: 0\n")
            summary.write("- Class counts are inventory only; no predictions or model-quality metrics were produced.\n")

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

