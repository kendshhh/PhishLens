"""Validate a new held-out cohort and score a separately approved freeze offline."""

import argparse
import hashlib
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.ai.evaluation_cases import CASES
from backend.ai.service import AIService
from backend.ai.tfidf_provider import ASSETS, MODEL_SHA256, TfidfProvider, prepare_plain

LABELS = ("phishing", "legitimate", "spam")
KINDS = ("actual_mail", "synthetic")
SPLITS = ("primary", "context", "stress")
OVERLAP_ROLES = {
    "within_cohort", "synthetic-v1", "training", "calibration", "threshold", "historical_holdout",
}
CRITERIA = {
    "phishing_recall_min": 0.90,
    "legitimate_false_positive_rate_max": 0.03,
    "valid_result_rate_min": 1.0,
    "primary_family_minima": {"phishing": 100, "legitimate": 200, "spam": 100},
    "primary_sources_per_label_minimum": 2,
    "security_notice_minimum": 50,
}
PINNED_FILES = (
    "scripts/evaluate_tfidf_cohort.py", "backend/ai/service.py",
    "backend/ai/schemas.py", "backend/ai/tfidf_provider.py",
    "backend/ai/evaluation_cases.py", "backend/requirements.txt",
    "extension/ai/contract.json", "extension/ai/tfidf_v12a.json",
)
ID = re.compile(r"[a-z0-9][a-z0-9_.-]{0,79}", re.ASCII)
SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)


class CohortError(ValueError):
    """A validation error with a fixed message safe for shared logs."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def require(condition, message):
    if not condition:
        raise CohortError(message)


def read_bundle(bundle):
    names = ("manifest.jsonl", "sources.json", "label-review.json", "overlap.json")
    files = {name: (bundle / name).read_bytes() for name in names}
    manifest_hash = sha256(files["manifest.jsonl"])
    rows = [json.loads(line) for line in files["manifest.jsonl"].splitlines()]
    source_rows = json.loads(files["sources.json"])
    require(isinstance(source_rows, list) and source_rows, "Source inventory must be a nonempty list")
    sources = {}
    for source in source_rows:
        source_id = source["id"]
        require(ID.fullmatch(source_id) and source_id not in sources, "Invalid or duplicate source ID")
        require(source["kind"] in KINDS, "Unknown source kind")
        for key in ("attribution", "revision", "date_range", "permission", "collection", "redistribution"):
            require(isinstance(source[key], str) and source[key].strip(), f"Missing source field: {key}")
        require(source["evaluation_allowed"] is True, "Source lacks evaluation permission")
        sources[source_id] = source

    review = json.loads(files["label-review.json"])
    require(review["manifest_sha256"] == manifest_hash, "Label review is for a different manifest")
    require(
        review["score_blind"] is True and review["unresolved_admitted"] == 0
        and len(review["reviewers"]) >= 2 and len(set(review["reviewers"])) == len(review["reviewers"])
        and all(isinstance(name, str) and name.strip() for name in review["reviewers"]),
        "Score-blind review by two distinct reviewers is required",
    )
    overlap = json.loads(files["overlap.json"])
    require(overlap["manifest_sha256"] == manifest_hash, "Overlap report is for a different manifest")
    require(overlap["unresolved_admitted"] == 0, "Resolve admitted overlap flags before freezing")
    require(overlap["reviewer"].strip() and overlap["method"].strip(), "Overlap review is undocumented")
    require(set(overlap["roles"]) == OVERLAP_ROLES, "Overlap report is missing comparison roles")
    for role in overlap["roles"].values():
        require(role["status"] in ("checked", "limited") and role["reference"].strip(),
                "Each overlap role needs a comparison reference or a documented limitation")

    validate_cases(rows, sources)
    return rows, sources, {name: sha256(data) for name, data in files.items()}, overlap


def validate_cases(rows, sources):
    require(rows, "Manifest is empty")
    case_ids = [row["id"] for row in rows]
    require(all(ID.fullmatch(case_id) for case_id in case_ids), "Invalid case ID")
    require(case_ids == sorted(set(case_ids)), "Manifest must have unique IDs in ascending order")
    raw_hashes = {sha256(case.body.encode()) for case in CASES}
    prepared_hashes = {sha256(prepare_plain(case.body)[0].encode()) for case in CASES}
    families = {}
    representatives = set()
    for row in rows:
        require(all(ID.fullmatch(row[key]) for key in ("family", "scenario")), "Invalid family or scenario ID")
        require(row["label"] in LABELS and row["split"] in SPLITS, "Unknown label or split")
        require(row["context"] in ("self_contained", "external_required"), "Unknown context category")
        require(row["split"] != "primary" or row["context"] == "self_contained",
                "Context-dependent selections are excluded from primary metrics")
        require(row["split"] != "context" or row["context"] == "external_required",
                "The context split requires an external-context classification")
        require(row["context"] != "external_required" or bool(ID.fullmatch(row["context_reason"])),
                "Context-dependent selections need a context-reason code")
        kind = sources[row["source"]]["kind"]
        identity = (kind, row["label"])
        require(families.setdefault(row["family"], identity) == identity,
                "A family cannot span source kinds or conflicting labels")
        representative = (row["family"], row["split"])
        require(row["split"] == "stress" or representative not in representatives,
                "Use one representative per family in the primary and context splits")
        representatives.add(representative)

        body = row["body"]
        require(isinstance(body, str), "A case body must be plain text")
        prepared = prepare_plain(body)[0]
        require(bool(prepared), "Manifest contains an empty prepared selection")
        raw_hash, prepared_hash = sha256(body.encode()), sha256(prepared.encode())
        require(raw_hash not in raw_hashes and prepared_hash not in prepared_hashes,
                "Duplicate selection or exact overlap with synthetic-v1")
        raw_hashes.add(raw_hash)
        prepared_hashes.add(prepared_hash)


def freeze(bundle):
    rows, sources, hashes, overlap = read_bundle(bundle)
    contract = json.loads((ASSETS / "contract.json").read_bytes())
    pins = {name: sha256((ROOT / name).read_bytes()) for name in PINNED_FILES}
    require(contract["model_sha256"] == MODEL_SHA256
            and pins["extension/ai/tfidf_v12a.json"] == MODEL_SHA256
            and contract["alert_mode"] == "raw_margin" and contract["alert_threshold"] == 0,
            "TF-IDF artifact or cutoff mismatch")
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    counts = defaultdict(set)
    for row in rows:
        kind = sources[row["source"]]["kind"]
        counts[f'{kind}/{row["split"]}/{row["label"]}'].add(row["family"])
        counts[f'{kind}/{row["split"]}/{row["label"]}/source/{row["source"]}'].add(row["family"])
        if row["scenario"] == "security_notice" and row["label"] == "legitimate":
            counts[f'{kind}/{row["split"]}/security_notice'].add(row["family"])
        if len(row["body"]) <= 200:
            counts[f'{kind}/{row["split"]}/{row["label"]}/short'].add(row["family"])
    lock = {
        "schema": 1,
        "source_commit": source,
        "python": platform.python_version(),
        "pydantic": version("pydantic"),
        "model": contract,
        "criteria": CRITERIA,
        "bundle_sha256": hashes,
        "implementation_sha256": pins,
        "cases": len(rows),
        "family_counts": {key: len(families) for key, families in counts.items()},
        "limited_overlap_roles": sorted(
            role for role, detail in overlap["roles"].items() if detail["status"] == "limited"
        ),
    }
    return lock, rows, sources


def rate(numerator, denominator, *, intervals=True):
    result = {"numerator": numerator, "denominator": denominator, "value": None, "wilson95": None}
    if not denominator:
        return result
    value = numerator / denominator
    result["value"] = value
    if intervals:
        z = 1.959963984540054
        scale = 1 + z**2 / denominator
        center = (value + z**2 / (2 * denominator)) / scale
        half = z * math.sqrt(value * (1 - value) / denominator + z**2 / (4 * denominator**2)) / scale
        result["wilson95"] = [max(0.0, center - half), min(1.0, center + half)]
    return result


def summarize(rows, *, intervals=True):
    confusion = Counter((row["label"], row["outcome"]) for row in rows)
    counts = Counter(row["outcome"] for row in rows)
    labels = Counter(row["label"] for row in rows)
    successes = counts["alert"] + counts["below_threshold"]
    tp = confusion["phishing", "alert"]
    legit = confusion["legitimate", "alert"]
    spam = confusion["spam", "alert"]
    notices = [row for row in rows if row["label"] == "legitimate" and row["scenario"] == "security_notice"]
    outcomes = ("alert", "below_threshold", "invalid_output", "inference_error", "timeout", "unattempted")
    return {
        "planned": len(rows),
        "attempted": len(rows) - counts["unattempted"],
        "counts": {outcome: counts[outcome] for outcome in outcomes},
        "confusion": {label: {outcome: confusion[label, outcome] for outcome in outcomes}
                      for label in LABELS},
        "phishing_recall": rate(tp, labels["phishing"], intervals=intervals),
        "alert_precision_at_cohort_mix": rate(tp, tp + legit + spam, intervals=intervals),
        "legitimate_false_positive_rate": rate(legit, labels["legitimate"], intervals=intervals),
        "spam_phishing_alert_rate": rate(spam, labels["spam"], intervals=intervals),
        "combined_non_phishing_alert_rate": rate(
            legit + spam, labels["legitimate"] + labels["spam"], intervals=intervals,
        ),
        "legitimate_security_notice_false_positive_rate": rate(
            sum(row["outcome"] == "alert" for row in notices), len(notices), intervals=intervals,
        ),
        "valid_result_rate": rate(successes, len(rows), intervals=intervals),
    }


def evaluate(rows, sources, lock, service_factory):
    try:
        import psutil
    except ImportError:
        psutil = None
    process = psutil.Process() if psutil is not None else None
    sampled_rss = process.memory_info().rss if process is not None else None
    results = []
    service = None
    started = perf_counter()
    interrupted = False
    try:
        service = service_factory()
        for row in rows:
            start = perf_counter() if results else started
            scores = {}
            try:
                result = service.analyze_email(subject=None, sender=None, body=row["body"])
                alert = result.model_alert
                valid = (
                    result.model_revision == MODEL_SHA256 and result.model == lock["model"]["model_id"]
                    and type(alert) is bool and result.raw_margin is not None
                    and math.isfinite(result.raw_margin) and alert == (result.raw_margin >= 0)
                    and result.phishing_score is not None and 0 <= result.phishing_score <= 1
                    and result.classification == ("phishing" if alert else "legitimate")
                )
                outcome = ("alert" if alert else "below_threshold") if valid else "invalid_output"
                if valid:
                    scores = {"raw_margin": result.raw_margin, "phishing_score": result.phishing_score}
            except TimeoutError:
                outcome = "timeout"
            except (RuntimeError, ValueError):
                outcome = "inference_error"
            results.append({"outcome": outcome, "seconds": perf_counter() - start, **scores})
            if process is not None:
                sampled_rss = max(sampled_rss, process.memory_info().rss)
    except KeyboardInterrupt:
        interrupted = True
    except (RuntimeError, ValueError):
        if service is not None:
            raise

    attempted = len(results)
    for index, row in enumerate(rows):
        case = {key: row[key] for key in ("id", "family", "label", "source", "scenario", "split", "context")}
        if row["context"] == "external_required":
            case["context_reason"] = row["context_reason"]
        case["kind"] = sources[row["source"]]["kind"]
        if index >= attempted:
            results.append({"outcome": "unattempted"})
        results[index].update(case)

    groups = defaultdict(list)
    for row in results:
        group = f'{row["kind"]}/{row["split"]}'
        groups[group].append(row)
        for field in ("source", "scenario", "context_reason"):
            if field in row:
                groups[f'{group}/{field}/{row[field]}'].append(row)
    summaries = {group: summarize(items, intervals=items[0]["split"] != "stress")
                 for group, items in groups.items()}
    primary = summaries.get("actual_mail/primary")
    criteria = "unassessed"
    counts = lock["family_counts"]
    primary_sources = defaultdict(set)
    for row in groups.get("actual_mail/primary", []):
        primary_sources[row["label"]].add(row["source"])
    if (primary and not lock["limited_overlap_roles"]
            and all(counts.get(f"actual_mail/primary/{label}", 0) >= minimum
                    for label, minimum in CRITERIA["primary_family_minima"].items())
            and all(len(primary_sources[label]) >= CRITERIA["primary_sources_per_label_minimum"]
                    for label in LABELS)
            and counts.get("actual_mail/primary/security_notice", 0) >= CRITERIA["security_notice_minimum"]):
        passes = (primary["phishing_recall"]["value"] >= CRITERIA["phishing_recall_min"]
                  and primary["legitimate_false_positive_rate"]["value"]
                  <= CRITERIA["legitimate_false_positive_rate_max"]
                  and primary["valid_result_rate"]["value"] >= CRITERIA["valid_result_rate_min"])
        criteria = "met" if passes else "not_met"
    warm = sorted(row["seconds"] for row in results[1:attempted])
    return {
        "lock": lock,
        "run_status": "interrupted" if interrupted else "finished" if service else "initialization_failed",
        "actual_mail_screening": criteria,
        "groups": summaries,
        "cases": results,
        "timing": {
            "first_call_seconds": results[0]["seconds"] if attempted else None,
            "warm_p50_seconds": statistics.median(warm) if warm else None,
            "warm_p95_seconds": warm[math.ceil(.95 * len(warm)) - 1] if warm else None,
            "max_sampled_rss_bytes": sampled_rss,
        },
        "machine": {"os": platform.platform(), "processor": platform.processor(),
                    "logical_cpus": os.cpu_count()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "score"))
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--expected-lock-sha")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "score" and not (args.lock and args.expected_lock_sha and args.output):
        parser.error("score requires --lock, --expected-lock-sha and --output")
    try:
        lock, rows, sources = freeze(args.bundle)
        if args.mode == "preflight":
            sys.stdout.buffer.write(json_bytes(lock))
            return 0
        reviewed = args.lock.read_bytes()
        require(SHA256.fullmatch(args.expected_lock_sha) and sha256(reviewed) == args.expected_lock_sha,
                "Approved lock SHA-256 does not match")
        require(json.loads(reviewed) == lock, "Current bundle, source or runtime differs from the approved lock")
        with args.output.open("xb") as output:
            report = evaluate(rows, sources, lock, lambda: AIService(TfidfProvider()))
            output.write(json_bytes(report))
        return int(any(row["outcome"] not in ("alert", "below_threshold") for row in report["cases"]))
    except CohortError as exc:
        parser.exit(1, f"Cohort validation failed: {exc}\n")
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, AttributeError, subprocess.CalledProcessError):
        # Validation can fail on private inputs. Keep their text and metadata out of shared logs.
        parser.exit(1, "Cohort validation or execution failed. Check the bundle, lock, and output path locally.\n")


if __name__ == "__main__":
    raise SystemExit(main())
