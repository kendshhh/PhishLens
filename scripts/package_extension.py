"""Package approved runtime files with manifest.json at the ZIP root."""

import runpy
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
