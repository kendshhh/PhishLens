"""Validate the current extension manifest and required runtime files."""

import json
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
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
    "js/report-client.js",
    "js/report-workflow.js",
    "background.js",
    "popup.js",
    "popup.css",
    "ai/contract.json",
    "ai/local-analyzer.mjs",
    "ai/core.mjs",
    "ai/observations.mjs",
    "ai/tfidf_v12a.json",
    "ai/ATTRIBUTION.md",
):
    require_file(asset)

class PopupAssets(HTMLParser):
    """Verify references in the actual popup, including images and styles."""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        attribute = {"script": "src", "img": "src", "link": "href"}.get(tag)
        if attribute is None or attribute not in attrs:
            return
        reference = attrs[attribute]
        if not reference:
            raise ValueError(f"Empty popup asset reference: {tag}")
        url = urlsplit(reference)
        if url.scheme or url.netloc or not url.path:
            raise ValueError(f"Expected packaged local popup asset: {reference}")
        require_file(unquote(url.path))


PopupAssets().feed(require_file(popup).read_text(encoding="utf-8"))

permissions = manifest.get("host_permissions", [])
if permissions != ["https://phishlens-api-ocvt.onrender.com/*"]:
    raise ValueError("Production package must grant only the public API host permission")

print("Extension manifest and required files passed validation.")
