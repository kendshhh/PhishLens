"""Compare real AI providers on frozen synthetic cases. JSONL goes only to stdout.

Run from the repository root:
python scripts/benchmark_ai.py --models local gemini-3.1-flash-lite gemini-3.8-flash
Optional: --repeats 2 (paid API usage may apply), --limit 3 for a wiring check.
Use --pause to match the selected model's account quota; five seconds is the default.
Each model runs in a fresh subprocess for separate cold timing and process memory.
Binary metrics treat spam as non-phishing because local DistilBERT has two classes.
No failed call is converted into a legitimate verdict or removed from the denominator.
"""

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from threading import Event, Thread
from time import perf_counter, sleep

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.ai.evaluation_cases import CASES, CASESET_VERSION
from backend.ai.gemini_provider import DailyQuotaExceeded
from backend.ai.prompts import PROMPT_VERSION
from backend.ai.service import AIService
from backend.core.config import get_ai_config


def summarize(rows: list[dict]) -> dict:
    completed = [row for row in rows if row.get("prediction") is not None]
    phishing = [row for row in rows if row["expected"] == "phishing"]
    negatives = [row for row in rows if row["expected"] != "phishing"]
    tp = sum(row.get("prediction") == "phishing" for row in phishing)
    fp = sum(row.get("prediction") == "phishing" for row in negatives)
    correct = sum((r["prediction"] == "phishing") == (r["expected"] == "phishing") for r in completed)
    latencies = sorted(r["seconds"] for r in completed)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / len(phishing) if phishing else None
    # Failed phishing calls count as missed detection opportunities.
    return {
        "attempts": len(rows), "successful": len(completed), "errors": len(rows) - len(completed),
        "binary_correct": correct, "binary_accuracy": correct / len(rows) if rows else None,
        "phishing_tp": tp, "phishing_fp": fp, "phishing_cases": len(phishing),
        "phishing_precision": precision, "phishing_recall": recall,
        "phishing_f1": 2 * precision * recall / (precision + recall) if recall and precision else 0,
        "false_positive_rate": fp / len(negatives) if negatives else None,
        "three_class_accuracy": sum(r["prediction"] == r["expected"] for r in completed) / len(rows) if rows else None,
        "p50_seconds": statistics.median(latencies) if latencies else None,
        "p95_seconds": latencies[math.ceil(.95 * len(latencies)) - 1] if latencies else None,
        "mean_seconds": statistics.mean(latencies) if latencies else None,
        "confusion": dict(Counter(f'{r["expected"]}->{r.get("prediction", "ERROR")}' for r in rows)),
    }


def worker(args) -> int:
    import psutil

    selected = CASES[:args.limit] if args.limit else CASES
    frozen = json.dumps([asdict(case) for case in selected], sort_keys=True).encode()
    if args.worker == "local":
        os.environ["AI_MODE"] = "local"
        get_ai_config()
        from backend.ai.local_provider import DEFAULT_CACHE, LocalProvider
        provider = LocalProvider(cache_dir=Path(os.getenv("MODEL_PATH", "").strip() or DEFAULT_CACHE))
    else:
        from backend.ai.gemini_provider import GeminiProvider
        os.environ["AI_MODE"] = "gemini"
        os.environ["GEMINI_MODEL"] = args.worker
        _, api_key, model = get_ai_config()
        provider = GeminiProvider(api_key=api_key, model=model)
    service = AIService(provider)
    process = psutil.Process()
    peak = [process.memory_info().rss]
    stop = Event()

    def sample_memory():
        while not stop.wait(.02):
            peak[0] = max(peak[0], process.memory_info().rss)

    sampler = Thread(target=sample_memory, daemon=True)
    sampler.start()
    rows = []
    cold_seconds = None
    first_result = None
    aborted = None
    try:
        # Warmup/cold inference is recorded separately and never scored as a test case.
        start = perf_counter()
        try:
            first_result = service.analyze_email(subject=None, sender=None, body="Hello, tomorrow's meeting is at ten. Please bring the agenda.")
            cold_seconds = perf_counter() - start
        except RuntimeError as exc:
            print(json.dumps({"event": "cold_error", "model": args.worker, "error": str(exc)}), flush=True)
            if isinstance(exc, DailyQuotaExceeded):
                aborted = "daily_quota_exhausted"
        for repeat in range(args.repeats):
            if aborted:
                break
            for case in selected:
                if args.pause and args.worker != "local":
                    sleep(args.pause)
                start = perf_counter()
                row = {"case": case.id, "expected": case.label, "repeat": repeat + 1}
                try:
                    result = service.analyze_email(subject=None, sender=None, body=case.body)
                    if first_result is None:
                        first_result = result
                    row.update(prediction=result.classification, confidence=result.confidence,
                               windows=result.windows_processed)
                except RuntimeError as exc:
                    row["error"] = str(exc)
                    if isinstance(exc, DailyQuotaExceeded):
                        aborted = "daily_quota_exhausted"
                row["seconds"] = round(perf_counter() - start, 6)
                rows.append(row)
                print(json.dumps({"event": "case", "model": args.worker, **row}), flush=True)
                if aborted:
                    break
    finally:
        stop.set()
        sampler.join()
        peak[0] = max(peak[0], process.memory_info().rss)
        if hasattr(provider, "close"):
            provider.close()
    summary = summarize(rows)
    requested = len(selected) * args.repeats
    if len(rows) < requested:
        for metric in ("binary_accuracy", "phishing_recall", "phishing_f1", "false_positive_rate", "three_class_accuracy"):
            summary[metric] = None
    print(json.dumps({
        "event": "summary", "model": args.worker,
        "run_status": aborted or "finished", "requested_cases": requested,
        "unattempted_cases": requested - len(rows),
        "model_metadata": first_result.model_dump(include={"model", "model_revision", "prompt_version", "explanation_source"}, exclude_none=True) if first_result else None,
        "caseset": CASESET_VERSION, "cases_sha256": hashlib.sha256(frozen).hexdigest(),
        "prompt_version": PROMPT_VERSION, "repeats": args.repeats,
        "hosted_pause_seconds": args.pause if args.worker != "local" else 0,
        "supported_labels": ["legitimate", "phishing"] if args.worker == "local" else ["legitimate", "spam", "phishing"],
        "cold_seconds": cold_seconds, "peak_process_rss_mb": peak[0] / 1024**2,
        "machine": {"os": platform.platform(), "python": platform.python_version(),
                    "logical_cpus": os.cpu_count(), "ram_gb": round(psutil.virtual_memory().total / 1024**3, 2)},
        "limitations": "Synthetic development suite; English checkpoint; two-class local model; hosted memory measures client only; latency includes network; confidence is uncalibrated classifier softmax only.",
        **summary,
    }), flush=True)
    return 1 if summary["errors"] or aborted else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=["local", "gemini-3.1-flash-lite", "gemini-3.8-flash"])
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--pause", type=float, default=5, help="Seconds between hosted calls; lower values can hit free-tier quotas")
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.repeats < 1 or args.limit < 0 or args.pause < 0:
        parser.error("repeats must be positive; limit and pause must be nonnegative")
    if args.worker:
        try:
            return worker(args)
        except (RuntimeError, ImportError) as exc:
            print(json.dumps({"event": "unavailable", "model": args.worker, "error": str(exc)}), flush=True)
            return 1
    failed = False
    for model in args.models:
        result = subprocess.run(
            [sys.executable, "-u", __file__, "--worker", model, "--repeats", str(args.repeats),
             "--limit", str(args.limit), "--pause", str(args.pause)], cwd=ROOT, check=False,
        )
        failed |= result.returncode != 0
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
