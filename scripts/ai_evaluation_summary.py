"""Summarize a redacted deterministic benchmark JSONL file for CI evidence."""

import argparse
import json
import os
import re
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from backend.ai.evaluation_cases import CASES, CASESET_VERSION


def render_summary(path: Path) -> str:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    events = [json.loads(line) for line in lines]
    summary = next((row for row in reversed(events) if row.get("event") == "summary"), None)
    if summary is None or summary.get("model") != "tfidf":
        raise ValueError("A completed TF-IDF benchmark summary is required")
    expected_cases = [case.id for case in CASES]
    case_events = [row.get("case") for row in events if row.get("event") == "case"]
    expected_hash = sha256(json.dumps(
        [asdict(case) for case in CASES], sort_keys=True,
    ).encode()).hexdigest()
    if case_events != expected_cases:
        raise ValueError("The deterministic evaluation must run every development case exactly once")
    if (summary.get("run_status") != "finished" or summary.get("attempts") != len(CASES)
            or summary.get("requested_cases") != len(CASES)
            or summary.get("errors") != 0 or summary.get("unattempted_cases") != 0):
        raise ValueError("The deterministic development evaluation was incomplete")
    if summary.get("caseset") != CASESET_VERSION or summary.get("cases_sha256") != expected_hash:
        raise ValueError("The benchmark cohort does not match the versioned development cases")
    revision = (summary.get("model_metadata") or {}).get("model_revision")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision):
        raise ValueError("The deterministic model revision is missing or invalid")
    for metric in ("binary_accuracy", "phishing_recall", "legitimate_false_positive_rate"):
        if not isinstance(summary.get(metric), (int, float)):
            raise TypeError(f"The deterministic benchmark is missing {metric}")
    if summary.get("spend_guard", {}).get("provider_calls") != 0:
        raise ValueError("Deterministic evaluation unexpectedly made a provider call")
    return "\n".join([
        "## Deterministic AI evaluation — complete; quality not approved",
        "",
        f"- Evaluated source: `{os.getenv('SOURCE_COMMIT', 'unknown')}`",
        f"- Model: `{summary.get('model')}` / `{(summary.get('model_metadata') or {}).get('model_revision', 'unknown')}`",
        f"- Development cases: `{summary.get('attempts')}` completed; `{summary.get('errors')}` errors",
        f"- Binary accuracy: `{summary.get('binary_accuracy')}`",
        f"- Phishing recall: `{summary.get('phishing_recall')}`; legitimate false-positive rate: `{summary.get('legitimate_false_positive_rate')}`",
        f"- Case set: `{summary.get('caseset')}` / `{summary.get('cases_sha256')}`",
        "- Gemini/provider requests: `0`; model downloads: `0`.",
        "- This status means the evaluation completed; it is not a model-quality pass. These development-cohort results are not held-out or production accuracy, and no quality threshold is configured pending AI-owner approval.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    args = parser.parse_args()
    summary = render_summary(args.benchmark)
    destination = os.getenv("GITHUB_STEP_SUMMARY")
    if destination:
        with open(destination, "a", encoding="utf-8") as output:
            output.write(summary)
    else:
        print(summary, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
