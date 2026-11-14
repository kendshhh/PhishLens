"""Run the actual backend AI service on synthetic mail; print results, write no report."""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.ai.evaluation_cases import CASES
from backend.ai.gemini_provider import GeminiProvider
from backend.ai.local_provider import DEFAULT_CACHE, download_model
from backend.ai.service import AIService
from backend.ai.spend_limit import GeminiEvaluationBudget
from backend.core.config import get_ai_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["tfidf", "local", "gemini", "mock"])
    parser.add_argument("--model", help="Override the Google-hosted model for this process only")
    parser.add_argument("--download-model", action="store_true")
    parser.add_argument("--output", type=Path, help="Write redacted JSON evidence to this path")
    args = parser.parse_args()
    if args.mode:
        os.environ["AI_MODE"] = args.mode
    if args.model:
        os.environ["GEMINI_MODEL"] = args.model
    cases = (CASES[0], CASES[16], CASES[27])
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_commit": os.getenv("SOURCE_COMMIT", "local"),
        "mode": args.mode or os.getenv("AI_MODE", "mock"),
        "requested_model": os.getenv("GEMINI_MODEL") if (args.mode == "gemini" or os.getenv("AI_MODE") == "gemini") else None,
        "result": "failed",
        "provider_requests": 0,
        "cases": [],
    }
    spend_budget = None
    service = None
    try:
        mode, _, _ = get_ai_config()
        if args.download_model:
            if mode != "local":
                parser.error("--download-model requires --mode local")
            cache = Path(os.getenv("MODEL_PATH", "").strip() or DEFAULT_CACHE)
            download_model(cache)
        if mode == "gemini":
            mode, api_key, model = get_ai_config()
            spend_budget = GeminiEvaluationBudget.from_environment(
                expected_requests=len(cases),
                model_id=model,
            )
            service = AIService(GeminiProvider(
                api_key=api_key,
                model=model,
                evaluation_budget=spend_budget,
            ))
        else:
            from backend.app.main import get_ai_service

            service, mode = get_ai_service()
        report["mode"] = mode
        report["requested_model"] = os.getenv("GEMINI_MODEL") if mode == "gemini" else None
        if mode == "mock":
            raise RuntimeError("Select tfidf, local, or gemini to exercise real inference")
        for case in cases:
            try:
                if mode == "gemini":
                    report["provider_requests"] += 1
                service.analyze_email(subject=None, sender=None, body=case.body)
                report["cases"].append({"case": case.id, "status": "completed", "mode": mode})
            except RuntimeError:
                report["cases"].append({"case": case.id, "status": "failed"})
                raise
        report["result"] = "passed"
    except (RuntimeError, ImportError) as exc:
        # Provider RuntimeErrors are sanitized by adapters; never print raw SDK errors.
        report["error"] = str(exc)
    finally:
        if service is not None and hasattr(service.provider, "close"):
            service.provider.close()
        if spend_budget is not None:
            report["spend_guard"] = spend_budget.summary()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            key: report[key]
            for key in ("result", "source_commit", "mode", "requested_model", "provider_requests", "error")
            if key in report
        }, sort_keys=True), flush=True)
    return 0 if report["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
