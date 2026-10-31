"""Replay existing dev/validation fixtures; never use the fresh final cohort."""

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.ai.tfidf_provider import MODEL_SHA256, score_text  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    args = parser.parse_args()
    items = json.loads(args.fixtures.read_text(encoding="utf-8"))
    expected = {r["id"]: r for r in json.loads(args.expected.read_text(encoding="utf-8"))["tfidf_v12a"]}
    maximum = 0
    for item in items:
        result = score_text(item["text"], prepared=True)
        saved = expected[item["id"]]
        delta = abs(result["raw_margin"] - saved["raw_margin"])
        maximum = max(maximum, delta)
        if not (math.isclose(result["score"], saved["score"], abs_tol=1e-12)
                and delta < 1e-12 and result["alert"] == bool(saved["alert"])):
            raise RuntimeError("Development fixture replay differs; do not enable saved reports")
    # Verify the public adapter separately: these fixtures must not be cleaned a
    # second time and compared directly with prepared benchmark outputs.
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node is required for public-adapter cross-runtime verification")
    program = """
import {readFileSync} from 'node:fs';
import {analyze} from './extension/ai/core.mjs';
const a=JSON.parse(readFileSync('extension/ai/tfidf_v12a.json'));
const c=JSON.parse(readFileSync('extension/ai/contract.json'));
let data='';for await(const s of process.stdin)data+=s;
console.log(JSON.stringify(JSON.parse(data).map(x=>{const r=analyze({text:x.text},a,c);
return {raw_margin:r.raw_margin,score:r.score,alert:r.alert};})));
"""
    replay = subprocess.run([node, "--input-type=module", "-e", program],
                            cwd=Path(__file__).resolve().parents[1], input=json.dumps(items),
                            capture_output=True, text=True, check=True)
    public_maximum = 0
    adapter_changed = 0
    for item, js in zip(items, json.loads(replay.stdout), strict=True):
        py = score_text(item["text"])
        delta = abs(py["raw_margin"] - js["raw_margin"])
        public_maximum = max(public_maximum, delta)
        if delta >= 1e-12 or abs(py["score"] - js["score"]) >= 1e-12 or py["alert"] != js["alert"]:
            raise RuntimeError("Browser/server visible-text preprocessing or scoring differs")
        adapter_changed += abs(py["raw_margin"] - expected[item["id"]]["raw_margin"]) >= 1e-12
    print(json.dumps({"model_sha256": MODEL_SHA256, "prepared_development_fixtures": len(items),
                      "max_prepared_margin_difference": maximum,
                      "public_adapter_cross_runtime_cases": len(items),
                      "max_public_adapter_margin_difference": public_maximum,
                      "cases_changed_by_recleaning_already_prepared_input": adapter_changed,
                      "note": "Production visible text is prepared once; prepared benchmark fixtures bypass re-cleaning.",
                      "new_accuracy_test": False}))


if __name__ == "__main__":
    main()
