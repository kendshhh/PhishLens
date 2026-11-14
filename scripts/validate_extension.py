"""Validate the current extension manifest and required runtime files."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

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
if manifest.get("minimum_chrome_version") != "127":
    raise ValueError("Opening the popup from the context menu requires Chrome 127 or newer")

if manifest.get("background") != {"service_worker": "background.js", "type": "module"}:
    raise ValueError("Expected a module background worker for shared API configuration")

# Split flow: right-click opens the action popup; the toolbar button opens the side panel.
# The popup URL carries ?surface=popup so the shared page can keep its fixed popup size.
if manifest.get("action", {}).get("default_popup") != "popup.html?surface=popup":
    raise ValueError("Expected popup.html?surface=popup as the action popup opened after right-click analysis")
popup = manifest.get("side_panel", {}).get("default_path")
if popup != "popup.html":
    raise ValueError("Expected the side panel to reuse popup.html")
if "sidePanel" not in manifest.get("permissions", []):
    raise ValueError("Expected sidePanel permission")

for asset in (
    popup,
    "css/popup.css",
    "js/popup.js",
    "js/account-session.js",
    "js/account-ui.js",
    "js/account-popup.js",
    "js/neon-accounts.js", "js/neon-integration.js", "js/auth-config.js", "vendor/neon/sdk.mjs", "vendor/neon/THIRD_PARTY_NOTICES.txt",
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
