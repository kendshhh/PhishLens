"""Run backend CI and require the real PostgreSQL checks to pass, not skip."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DATABASE_TESTS = {
    ("backend.tests.test_seed_integrity", "test_seed_records_and_relationship"),
    ("backend.tests.test_history_postgres", "test_history_postgres_read_change_empty_and_isolation"),
    (
        "backend.tests.test_saved_crud_postgres",
        "test_read_update_and_delete_with_postgres",
    ),
    (
        "backend.tests.test_saved_crud_postgres",
        "test_other_users_record_is_not_accessible",
    ),
    (
        "backend.tests.test_saved_create_postgres",
        "test_complete_saved_crud_flow",
    ),
    (
        "backend.tests.test_saved_create_postgres",
        "test_failed_inference_does_not_save[AnalysisInferenceError-502-analysis_failed-Email analysis failed]",
    ),
    (
        "backend.tests.test_saved_create_postgres",
        "test_failed_inference_does_not_save[AnalysisUnavailableError-503-analysis_unavailable-Email analysis is temporarily unavailable]",
    ),
    (
        "backend.tests.test_saved_create_postgres",
        "test_failed_inference_does_not_save[AnalysisTimeoutError-504-analysis_timeout-Email analysis timed out]",
    ),
    (
        "backend.tests.test_saved_create_postgres",
        "test_invalid_saved_response_rolls_back_insert",
    ),
    (
        "backend.tests.test_saved_create_postgres",
        "test_database_lock_timeout_does_not_save",
    ),
    (
        "backend.tests.test_saved_create_postgres",
        "test_live_analysis_does_not_save_history",
    ),
}


def check_environment(env):
    """Reject cloud/default configuration before any imports or migrations."""
    try:
        url = urlsplit(env.get("DATABASE_URL", ""))
        valid = (
            url.scheme == "postgresql+psycopg"
            and url.hostname in {"localhost", "127.0.0.1"}
            and url.port == 5432
            and url.path == "/phishlens_dev"
            and url.username == "phishlens"
            and url.password == "ci-only-password"
            and not url.query and not url.fragment
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Backend CI requires the explicit disposable PostgreSQL service configuration.")
    if env.get("RUN_DATABASE_TESTS") != "1":
        raise ValueError("RUN_DATABASE_TESTS=1 is required; database skips cannot pass CI.")
    if env.get("AI_MODE") != "mock":
        raise ValueError("AI_MODE=mock is required; ordinary CI must not call a real provider.")


def verify_report(path, required=REQUIRED_DATABASE_TESTS):
    root = ET.parse(path).getroot()
    cases = root.findall(".//testcase")
    if not cases:
        raise ValueError("Backend test report contains no tests.")
    passed = set()
    for case in cases:
        if any(case.find(tag) is not None for tag in ("skipped", "failure", "error")):
            continue
        passed.add((case.get("classname", ""), case.get("name", "")))
    missing = required - passed
    if missing:
        names = ", ".join(f"{module}::{name}" for module, name in sorted(missing))
        raise ValueError(f"Required PostgreSQL tests did not pass (missing/skipped/failed): {names}")
    skipped = sum(case.find("skipped") is not None for case in cases)
    return {"tests": len(cases), "skipped": skipped,
            "required_database_tests_passed": len(required),
            "crud_acceptance": "verified against disposable local PostgreSQL with mock inference; hosted acceptance not established"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-environment", action="store_true")
    args = parser.parse_args()
    try:
        check_environment(os.environ)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.check_environment:
        print("Disposable database and mock AI configuration verified.")
        return 0
    output = ROOT / "output/backend-ci"
    output.mkdir(parents=True, exist_ok=True)
    # A fresh report prevents a stale passing XML file from satisfying this run.
    with tempfile.TemporaryDirectory(prefix="report-", dir=output) as temporary:
        report = Path(temporary) / "pytest.xml"
        result = subprocess.run([
            sys.executable, "-m", "pytest", "backend/tests", "-q", "-p", "no:cacheprovider",
            f"--junitxml={report}",
        ], cwd=ROOT, check=False)
        summary = {"commit": os.getenv("GITHUB_SHA", "local"),
                   "source_commit": os.getenv("SOURCE_COMMIT", "local"),
                   "pytest_exit_code": result.returncode,
                   "database_target": "disposable local PostgreSQL", "ai_mode": "mock"}
        try:
            summary.update(verify_report(report))
        except (ValueError, OSError, ET.ParseError) as exc:
            summary["gate_error"] = str(exc)
        if report.exists():
            (output / "pytest.xml").write_bytes(report.read_bytes())
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 1 if result.returncode or "gate_error" in summary else 0


if __name__ == "__main__":
    raise SystemExit(main())
