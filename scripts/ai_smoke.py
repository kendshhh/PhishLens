"""Run the actual backend AI service on synthetic mail; print results, write no report."""

import argparse
import json
import os
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.ai.evaluation_cases import CASES
from backend.ai.local_provider import DEFAULT_CACHE, download_model
from backend.core.config import get_ai_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["local", "gemini", "mock"])
    parser.add_argument("--model", help="Override the Google-hosted model for this process only")
    parser.add_argument("--download-model", action="store_true")
    args = parser.parse_args()
    if args.mode:
        os.environ["AI_MODE"] = args.mode
    if args.model:
        os.environ["GEMINI_MODEL"] = args.model
    try:
        mode, _, _ = get_ai_config()
        if args.download_model:
            if mode != "local":
                parser.error("--download-model requires --mode local")
            cache = Path(os.getenv("MODEL_PATH", "").strip() or DEFAULT_CACHE)
            download_model(cache)
        from backend.app.main import get_ai_service

        service, mode = get_ai_service()
        if mode == "mock":
            print("Mock mode cannot prove real inference. Select local or gemini.")
            return 1
        for case in (CASES[0], CASES[16], CASES[27]):
            start = perf_counter()
            result = service.analyze_email(subject=None, sender=None, body=case.body)
            print(json.dumps({
                "location": "local backend service", "mode": mode,
                "case": case.id, "expected": case.label,
                "seconds": round(perf_counter() - start, 4),
                "result": result.model_dump(exclude_none=True),
            }), flush=True)
        if hasattr(service.provider, "close"):
            service.provider.close()
        return 0
    except (RuntimeError, ImportError) as exc:
        # Provider RuntimeErrors are sanitized by adapters; never print raw SDK errors.
        print(json.dumps({"status": "unavailable", "error": str(exc)}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
