"""Enforce the AI owner's reviewed deterministic inventory, without quality claims."""

import argparse
import json
import xml.etree.ElementTree as ET
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from backend.ai.evaluation_cases import CASES, CASESET_VERSION
from scripts.ai_evaluation_summary import render_summary

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "scripts" / "ai-regression-baseline.json"
MODEL = ROOT / "extension" / "ai" / "tfidf_v12a.json"


def verify_contracts(path: Path, required: list[str]) -> int:
    """Require the reviewed tests exactly once; skipped/xfail is not success."""
    if not required or len(required) != len(set(required)):
        raise ValueError("The reviewed contract inventory is empty or duplicated")
    root = ET.parse(path).getroot()
    cases = list(root.iter("testcase"))
    identities = [f"{case.get('classname', '')}::{case.get('name', '')}" for case in cases]
    if len(identities) != len(set(identities)):
        raise ValueError("The contract report contains duplicated tests")
    if set(identities) != set(required):
        raise ValueError("The contract test inventory differs from the reviewed baseline")
    for tag in ("failure", "error", "skipped"):
        if next(root.iter(tag), None) is not None:
            raise ValueError("Required contract tests failed, errored or were skipped")
    for suite in root.iter("testsuite"):
        for field in ("failures", "errors", "skipped"):
            if int(suite.get(field, "0")) != 0:
                raise ValueError("The contract suite reports incomplete execution")
    return len(cases)


def verify_development(path: Path, baseline: dict) -> str:
    """Reuse the complete-run checks, then enforce the owner's frozen identities."""
    if baseline.get("schema") != 1:
        raise ValueError("Unknown deterministic regression baseline schema")
    cohort = baseline["development"]
    actual_hash = sha256(json.dumps(
        [asdict(case) for case in CASES], sort_keys=True,
    ).encode()).hexdigest()
    if (cohort["caseset"] != CASESET_VERSION or cohort["cases"] != len(CASES)
            or cohort["cases_sha256"] != actual_hash):
        raise ValueError("The development cohort differs from the reviewed baseline")
    if sha256(MODEL.read_bytes()).hexdigest() != baseline["model_sha256"]:
        raise ValueError("The bundled model differs from the reviewed baseline")
    rendered = render_summary(path)
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = next(row for row in reversed(events) if row.get("event") == "summary")
    if summary["model_metadata"]["model_revision"] != baseline["model_sha256"]:
        raise ValueError("The evaluated model differs from the reviewed baseline")
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    verify_development(args.benchmark, baseline)
    count = verify_contracts(args.contracts, baseline["required_tests"])
    print(f"Approved deterministic baseline: {count} required tests passed; "
          f"{baseline['development']['cases']} development cases completed; "
          "zero missing/failed/skipped tests and zero external provider calls. "
          "This is not held-out quality or hosted acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
