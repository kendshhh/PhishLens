"""Check the frozen v12a evaluation record without running inference."""

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "benchmark-records" / "tfidf_false_alarm_v12a"
ASSETS = ROOT / "extension" / "ai"
SYSTEM = "tfidf_v12a"
OVERLAP_FIELDS = ("id", "_full_hash", "_input_hash", "_group")


def checked_bytes(path, expected_hash):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    return data


def verify_saved_predictions(record, metrics, prepared_dir, predictions_dir):
    role_keys = {}
    labels = {}
    for role, metadata in record["data"].items():
        data = checked_bytes(prepared_dir / f"{role}.private.jsonl", metadata["sha256"])
        rows = [json.loads(line) for line in data.splitlines()]
        if len(rows) != metadata["rows"]:
            raise ValueError(f"Unexpected row count for {role}")
        role_keys[role] = {
            field: {row[field] for row in rows if row.get(field)} for field in OVERLAP_FIELDS
        }
        if role == "fresh_source_pair":
            labels = {row["id"]: row["label"] for row in rows}

    for left, right in combinations(role_keys, 2):
        for field in OVERLAP_FIELDS:
            if role_keys[left][field] & role_keys[right][field]:
                raise ValueError(f"Overlap between {left} and {right} on {field}")

    total = 0
    for system, metadata in record["prediction_files"].items():
        recorded = metrics["systems"][system]
        if metadata["sha256"] != recorded["prediction_sha256"]:
            raise ValueError(f"Archived prediction hashes disagree for {system}")
        data = checked_bytes(predictions_dir / f"{system}.jsonl", metadata["sha256"])
        rows = [json.loads(line) for line in data.splitlines()]
        if (
            len(rows) != metadata["rows"]
            or len(rows) != len(labels)
            or {row["id"] for row in rows} != labels.keys()
        ):
            raise ValueError(f"Predictions do not match the frozen cohort for {system}")
        if any(row["valid"] is not True for row in rows):
            raise ValueError(f"Invalid prediction recorded for {system}")
        outcomes = Counter((labels[row["id"]], row["alert"]) for row in rows)
        counts = {
            "tp": outcomes[1, True],
            "fp": outcomes[0, True],
            "tn": outcomes[0, False],
            "fn": outcomes[1, False],
        }
        if counts != recorded["counts"]:
            raise ValueError(f"Confusion counts differ for {system}")
        total += len(rows)

    return {"roles_verified": len(role_keys), "saved_prediction_rows_reconciled": total}


def verify(prepared_dir, predictions_dir):
    record = json.loads((RECORDS / "run_record.json").read_bytes())
    lock = json.loads(
        checked_bytes(RECORDS / "final_lock.json", record["fresh_scoring_lock_sha256"])
    )
    metrics = json.loads(
        checked_bytes(
            RECORDS / "metrics.json", record["report_artifact_hashes"]["metrics.json"]
        )
    )
    model = record["model_versions"][SYSTEM]
    model_hash = model["source_artifact_sha256"]
    checked_bytes(ASSETS / "tfidf_v12a.json", model_hash)
    contract = json.loads((ASSETS / "contract.json").read_bytes())
    expected_contract = {
        "system": SYSTEM,
        "model_id": model["local_id"],
        "model_sha256": model_hash,
        "mapping": model["mapping"],
        "alert_mode": model["alert_threshold_space"],
        "alert_threshold": model["alert_threshold"],
    }
    if contract != expected_contract:
        raise ValueError("Runtime TF-IDF contract differs from the frozen study")
    cohort_hash = lock["fresh_source_pair_sha256"]
    if (
        cohort_hash != metrics["cohort"]["sha256"]
        or cohort_hash != record["data"]["fresh_source_pair"]["sha256"]
    ):
        raise ValueError("Archived cohort hashes disagree")
    result = {
        "model_sha256": model_hash,
        "cohort_sha256": cohort_hash,
        "archived_counts": metrics["systems"][SYSTEM]["counts"],
        "classifier_inferences": 0,
    }
    if prepared_dir is not None:
        result.update(
            verify_saved_predictions(record, metrics, prepared_dir, predictions_dir)
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepared-dir",
        type=Path,
        help="Local directory containing the six frozen data roles",
    )
    parser.add_argument(
        "--predictions-dir",
        type=Path,
        help="Local directory containing the three saved prediction sets",
    )
    args = parser.parse_args()
    if (args.prepared_dir is None) != (args.predictions_dir is None):
        parser.error("Supply both local directories to reconcile archived predictions")
    try:
        result = verify(args.prepared_dir, args.predictions_dir)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Frozen evaluation verification failed: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
