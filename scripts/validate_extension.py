"""Validate the current extension manifest and required runtime files."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "extension"


def require_file(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError(f"Asset escapes extension directory: {relative}")
    if not path.is_file():
        raise FileNotFoundError(f"Missing extension asset: {relative}")
    return path


manifest = json.loads(require_file("manifest.json").read_text(encoding="utf-8"))

if manifest.get("manifest_version") != 3:
    raise ValueError("Expected manifest_version 3")

if manifest.get("background") != {"service_worker": "background.js", "type": "module"}:
    raise ValueError("Expected a module background worker for shared API configuration")

popup = manifest.get("action", {}).get("default_popup")
if popup != "popup.html":
    raise ValueError("Expected popup.html as the default popup")

for asset in (
    popup,
    "css/popup.css",
    "js/popup.js",
    "js/config.js",
    "js/api.js",
    "js/history.js",
    "background.js",
    "popup.js",
    "popup.css",
):
    require_file(asset)

permissions = manifest.get("host_permissions", [])
if "https://phishlens-api-ocvt.onrender.com/*" not in permissions:
    raise ValueError("Missing public API host permission")

print("Extension manifest and required files passed validation.")
