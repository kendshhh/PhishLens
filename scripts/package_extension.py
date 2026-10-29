"""Package approved runtime files with manifest.json at the ZIP root."""

import datetime as dt
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
EXTENSION = ROOT / "extension"

runpy.run_path(str(SCRIPTS / "validate_extension.py"))

assets = (
    "manifest.json",
    "popup.html",
    "css/popup.css",
    "js/api.js",
    "js/config.js",
    "js/history.js",
    "js/report-client.js",
    "js/report-workflow.js",
    "js/popup.js",
    "background.js",
    "popup.js",
    "popup.css",
    "ai/contract.json",
    "ai/local-analyzer.mjs",
    "ai/core.mjs",
    "ai/observations.mjs",
    "ai/tfidf_v12a.json",
    "ai/ATTRIBUTION.md",
    "offscreen.html",
    "offscreen.js",
    "ai/judge-client.mjs",
    "ai/judge-contract.mjs",
    "ai/judge-worker.mjs",
    "ai/live-workflow.mjs",
    "ai/reevaluators.mjs",
    "ai/judge-assets.json",
    "ai/reevaluators/manifest.json",
    "ai/reevaluators/krr.json",
    "ai/reevaluators/lightgbm.json",
    "vendor/ml/transformers.min.js",
    "vendor/ml/structured-output.js",
    "vendor/ml/ort-wasm-simd-threaded.jsep.mjs",
    "vendor/ml/ort-wasm-simd-threaded.jsep.wasm",
    "vendor/ml/ort-wasm-simd-threaded.asyncify.mjs",
    "vendor/ml/ort-wasm-simd-threaded.asyncify.wasm",
    "vendor/ml/LICENSE-transformers.txt",
    "vendor/ml/LICENSE-structured-output.txt",
    "vendor/ml/LICENSE-onnxruntime.txt",
    "vendor/ml/LICENSE-Llama3.2.txt",
    "vendor/ml/THIRD_PARTY_NOTICES.md",
)

output = ROOT / "output" / "extension"
output.mkdir(parents=True, exist_ok=True)
archive = output / "PhishLens-Extension.zip"
runtime_assets = assets
include_models = "--include-models" in sys.argv
if include_models:
    model_manifest = json.loads((EXTENSION / "ai/judge-assets.json").read_text())
    added = []
    for entry in model_manifest["files"]:
        for part in entry.get("chunks") or [entry]:
            relative = "model-assets/" + part.get("path", entry["path"])
            source = (EXTENSION / relative).resolve()
            if not source.is_relative_to((EXTENSION / "model-assets").resolve()):
                raise ValueError("Model path escapes provisioned directory")
            with source.open("rb") as stream:
                sha = hashlib.file_digest(stream, "sha256").hexdigest()
            if source.stat().st_size != part["bytes"] or sha != part["sha256"]:
                raise ValueError("Provisioned model integrity failed")
            added.append(relative)
    assets = (*assets, *added)

with ZipFile(archive, "w", compression=ZIP_DEFLATED) as package:
    for asset in assets:
        # Quantized binary data is already compact; storing it avoids a long,
        # memory-intensive recompression pass for local offline bundles.
        compression = ZIP_STORED if asset.startswith("model-assets/llama/onnx/") else ZIP_DEFLATED
        package.write(EXTENSION / asset, arcname=asset, compress_type=compression)

with ZipFile(archive) as package:
    if set(package.namelist()) != set(assets):
        raise RuntimeError("Unexpected package contents")
    if package.testzip() is not None:
        raise RuntimeError("Package integrity check failed")

print(f"Package created: {archive}")
print("Verified: manifest.json at ZIP root; tests excluded.")

def checkout_identity() -> tuple[str | None, bool | None]:
    """Trust Git metadata only for this checkout and its tracked build inputs."""
    def git(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False,
        )

    try:
        top = git("rev-parse", "--show-toplevel")
        if top.returncode or Path(top.stdout.strip()).resolve() != ROOT.resolve():
            return None, None

        revision = git("rev-parse", "--verify", "HEAD")
        if revision.returncode:
            return None, None
        local_revision = revision.stdout.strip()
        inputs = [f"extension/{asset}" for asset in runtime_assets] + [
            "scripts/package_extension.py", "scripts/validate_extension.py",
        ]
        tracked = git("ls-files", "--error-unmatch", "--", *inputs)
        if tracked.returncode:
            return local_revision, None

        dirty = git("diff", "--quiet", "HEAD", "--", *inputs)
        if dirty.returncode not in (0, 1):
            return local_revision, None
        return local_revision, bool(dirty.returncode)
    except OSError:
        return None, None


# Keep identity evidence alongside the ZIP, outside the installable package.
# GITHUB_SHA is the tested merge revision on PRs; SOURCE_COMMIT is the PR head.
# An enclosing repository or missing/untracked inputs cannot establish a clean build.
local_revision, input_changes = checkout_identity()
with archive.open("rb") as stream:
    archive_sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
evidence = {
    "recorded_at": dt.datetime.now(dt.UTC).isoformat(),
    "source_commit": os.getenv("SOURCE_COMMIT") or local_revision,
    "tested_commit": os.getenv("GITHUB_SHA") or local_revision,
    "runtime_or_packaging_changes": input_changes,
    "extension_version": json.loads((EXTENSION / "manifest.json").read_text())["version"],
    "environment": "production",
    "includes_local_judge_weights": include_models,
    "full_workflow_assets_provisioned_in_archive": include_models,
    "archive": archive.name,
    "archive_sha256": archive_sha256,
    "host_permissions": ["https://phishlens-api-ocvt.onrender.com/*"],
    "files_sha256": {
        asset: hashlib.sha256((EXTENSION / asset).read_bytes()).hexdigest() for asset in assets
    },
    "chrome_acceptance": "not performed by packaging",
}
(output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print("Package identity and SHA-256 evidence written alongside the ZIP.")
