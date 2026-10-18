"""Build a separate extension ZIP pointing only at the staging service."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
url = os.environ["STAGING_BASE_URL"].rstrip("/")
parsed = urlsplit(url)
if parsed.scheme != "https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
    raise SystemExit("STAGING_BASE_URL must be an HTTPS origin.")
if parsed.hostname == "phishlens-api-ocvt.onrender.com":
    raise SystemExit("Staging extension must not target production.")
output = root / "output/staging/PhishLens-Staging-Extension.zip"
output.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for source in sorted((root / "extension").rglob("*")):
        if not source.is_file() or "tests" in source.relative_to(root / "extension").parts:
            continue
        relative = source.relative_to(root / "extension").as_posix()
        data = source.read_bytes()
        if relative == "manifest.json":
            manifest = json.loads(data)
            manifest["name"] = "PhishLens Staging"
            manifest["host_permissions"] = [url + "/*"]
            data = json.dumps(manifest, indent=2).encode()
        elif relative == "js/config.js":
            data = ("export const API_BASE_URL = " + json.dumps(url) + ";\n").encode()
        archive.writestr(relative, data)
print("Built separate staging extension ZIP.")
