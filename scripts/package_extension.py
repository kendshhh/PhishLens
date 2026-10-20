"""Package approved runtime files with manifest.json at the ZIP root."""

import datetime as dt
import hashlib
import json
import os
import runpy
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

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
    "js/popup.js",
    "background.js",
    "popup.js",
    "popup.css",
)

output = ROOT / "output" / "extension"
output.mkdir(parents=True, exist_ok=True)
archive = output / "PhishLens-Extension.zip"

with ZipFile(archive, "w", compression=ZIP_DEFLATED) as package:
    for asset in assets:
        package.write(EXTENSION / asset, arcname=asset)

with ZipFile(archive) as package:
    if set(package.namelist()) != set(assets):
        raise RuntimeError("Unexpected package contents")
    if package.testzip() is not None:
        raise RuntimeError("Package integrity check failed")

print(f"Package created: {archive}")
print("Verified: manifest.json at ZIP root; tests excluded.")

# Keep identity evidence alongside the ZIP, outside the installable package.
# GITHUB_SHA is the tested merge revision on PRs; SOURCE_COMMIT is the PR head.
revision = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False,
)
local_revision = revision.stdout.strip() if revision.returncode == 0 else None
dirty = subprocess.run(
    ["git", "diff", "--quiet", "HEAD", "--", "extension", "scripts/package_extension.py",
     "scripts/validate_extension.py"], cwd=ROOT, capture_output=True, check=False,
)
evidence = {
    "recorded_at": dt.datetime.now(dt.UTC).isoformat(),
    "source_commit": os.getenv("SOURCE_COMMIT") or local_revision,
    "tested_commit": os.getenv("GITHUB_SHA") or local_revision,
    "runtime_or_packaging_changes": bool(dirty.returncode) if local_revision else None,
    "extension_version": json.loads((EXTENSION / "manifest.json").read_text())["version"],
    "environment": "production",
    "archive": archive.name,
    "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    "host_permissions": ["https://phishlens-api-ocvt.onrender.com/*"],
    "files_sha256": {
        asset: hashlib.sha256((EXTENSION / asset).read_bytes()).hexdigest() for asset in assets
    },
    "chrome_acceptance": "not performed by packaging",
}
(output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print("Package identity and SHA-256 evidence written alongside the ZIP.")
