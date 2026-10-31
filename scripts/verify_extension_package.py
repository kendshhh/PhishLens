"""Verify a production ZIP against its sidecar before manual installation."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ASSETS = {
    "manifest.json", "popup.html", "css/popup.css", "js/api.js", "js/config.js",
    "js/history.js", "js/popup.js", "background.js", "popup.js", "popup.css",
    "js/report-client.js", "js/report-workflow.js", "ai/contract.json",
    "ai/local-analyzer.mjs", "ai/core.mjs", "ai/observations.mjs",
    "ai/tfidf_v12a.json", "ai/ATTRIBUTION.md",
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
}


def full_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def verify(archive, evidence_path, expected_source):
    if not full_sha(expected_source):
        raise ValueError("Expected source must be a full lowercase 40-character commit SHA")
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise TypeError("Evidence must be a JSON object")
    if not full_sha(evidence.get("tested_commit")):
        raise ValueError("Evidence must identify the full tested commit")
    if evidence.get("source_commit") != expected_source:
        raise ValueError("Package source does not match expected source commit")
    if evidence.get("environment") != "production":
        raise ValueError("Expected production package evidence")
    if evidence.get("runtime_or_packaging_changes") is not False:
        raise ValueError("Package inputs were modified or their status is unknown")
    archive = Path(archive)
    if evidence.get("archive") != archive.name:
        raise ValueError("Archive filename does not match evidence")
    with archive.open("rb") as stream:
        archive_sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
    if archive_sha256 != evidence.get("archive_sha256"):
        raise ValueError("Archive SHA-256 does not match evidence")
    with ZipFile(archive) as package:
        names = package.namelist()
        hashes = evidence.get("files_sha256", {})
        expected_assets = set(ASSETS)
        pinned_models = {}
        if evidence.get("includes_local_judge_weights") is True:
            judge = json.loads(package.read("ai/judge-assets.json"))
            for entry in judge["files"]:
                for part in entry.get("chunks") or [entry]:
                    relative = "model-assets/" + part.get("path", entry["path"])
                    if ".." in Path(relative).parts or not relative.startswith("model-assets/llama/"):
                        raise ValueError("Invalid model inventory")
                    pinned_models[relative] = part["sha256"]
            expected_assets.update(pinned_models)
        if (not isinstance(hashes, dict) or set(hashes) != expected_assets
                or len(names) != len(set(names)) or set(names) != expected_assets):
            raise ValueError("Archive file inventory does not match evidence")
        for name in names:
            if hashlib.sha256(package.read(name)).hexdigest() != hashes[name]:
                raise ValueError(f"File SHA-256 does not match evidence: {name}")
            if name in pinned_models and hashes[name] != pinned_models[name]:
                raise ValueError("Model bytes differ from pinned asset manifest")
        manifest = json.loads(package.read("manifest.json"))
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 3:
        raise ValueError("Expected a Manifest V3 object")
    if manifest.get("version") != evidence.get("extension_version"):
        raise ValueError("Manifest version does not match evidence")
    hosts = ["https://phishlens-api-ocvt.onrender.com/*"]
    if manifest.get("host_permissions") != hosts or evidence.get("host_permissions") != hosts:
        raise ValueError("Production host permissions do not match")
    if manifest.get("optional_host_permissions"):
        raise ValueError("Optional host permissions are not allowed")
    return {"source_commit": expected_source, "environment": "production",
            "archive_sha256": evidence["archive_sha256"], "files_verified": len(names)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-source", required=True)
    args = parser.parse_args()
    try:
        result = verify(args.archive, args.evidence, args.expected_source)
    except (ValueError, TypeError, OSError, KeyError, BadZipFile, UnicodeError, RuntimeError) as exc:
        parser.exit(1, f"Package rejected: {exc}\n")
    print(json.dumps(result, indent=2))
    print("Integrity verified; source identity is asserted by the sidecar, not signed.")
    print("Installed Chrome acceptance remains a separate manual check.")


if __name__ == "__main__":
    main()
