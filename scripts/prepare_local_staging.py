"""Refresh a local UI preview targeting staging; never a release acceptance build."""

import hashlib
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "output/staging-local/extension"
ORIGIN = "https://phishlens-staging.onrender.com"


def write_changed(path, data):
    if path.is_file():
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").digest() == hashlib.sha256(data).digest():
                return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".local-preview-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-models', action='store_true', help='Include verified local judge weights for analysis testing')
    args = parser.parse_args()
    # Retain the production source validation and runtime asset allowlist.
    command = [sys.executable, str(ROOT / "scripts/package_extension.py")]
    if args.include_models:
        command.append('--include-models')
    subprocess.run(command, cwd=ROOT, check=True)
    with ZipFile(ROOT / "output/extension/PhishLens-Extension.zip") as archive:
        for name in archive.namelist():
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or "\\" in name:
                raise ValueError("Unsafe package path")
            destination = TARGET / relative
            if not destination.resolve().is_relative_to(TARGET.resolve()):
                raise ValueError("Preview path escapes its output directory")
            destination.parent.mkdir(parents=True, exist_ok=True)
            write_changed(destination, archive.read(name))

    manifest_path = TARGET / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = "PhishLens Staging (Local UI)"
    manifest["action"]["default_title"] = manifest["name"]
    manifest["host_permissions"] = [ORIGIN + "/*"]
    manifest.pop("optional_host_permissions", None)
    write_changed(manifest_path, (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    write_changed(TARGET / "js/config.js", f"export const API_BASE_URL = {json.dumps(ORIGIN)};\n".encode("utf-8"))

    popup_path = TARGET / "popup.html"
    popup = popup_path.read_text(encoding="utf-8")
    marker = '<header class="app-header">'
    if marker not in popup:
        raise ValueError("Preview header anchor was not found")
    popup = popup.replace(marker, '<p class="shared-notice" role="note"><strong>STAGING · LOCAL UI PREVIEW</strong><br>'
                          'Reports API: phishlens-staging.onrender.com<br>'
                          'Local UI edits · not a release acceptance build.</p>\n' + marker, 1)
    write_changed(popup_path, popup.encode("utf-8"))
    local_info = {
        "kind": "local-development-preview", "api_origin": ORIGIN,
        "contains_uncommitted_ui_edits": True, "release_acceptance": False,
        "includes_local_judge_weights": args.include_models,
        "popup_sha256": hashlib.sha256(popup_path.read_bytes()).hexdigest(),
        "controller_sha256": hashlib.sha256((TARGET / "js/popup.js").read_bytes()).hexdigest(),
    }
    write_changed(TARGET / "local-preview.json", (json.dumps(local_info, indent=2) + "\n").encode("utf-8"))
    print(f"Load or reload this folder in Chrome: {TARGET}")
    print("Preview targets staging. No hosted data or settings were changed.")


if __name__ == "__main__":
    main()
