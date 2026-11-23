"""Build one dual-environment Auth package for staging and production promotion.

The package defaults to production. Automated staging acceptance opens the
same ZIP at popup.html?environment=staging. Both API and Auth endpoints are
fixed public origins in the package; credentials are supplied only by users.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

try:
    from .manifest_key import chrome_extension_id
    from .verify_extension_package import ASSETS
except ImportError:
    from manifest_key import chrome_extension_id
    from verify_extension_package import ASSETS


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_API = "https://phishlens-api-ocvt.onrender.com"
STAGING_API = "https://phishlens-staging.onrender.com"
EVIDENCE_MEMBER = "phishlens-build-evidence.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("Unable to verify the release package checkout")
    return result.stdout.strip()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _auth_config(auth_url: str, database: str, api_origin: str) -> dict[str, object]:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,63}", database or ""):
        raise ValueError("Auth database name is invalid")
    parsed = urlsplit(auth_url or "")
    host = parsed.hostname or ""
    if (parsed.scheme != "https" or not host or parsed.username or parsed.password
            or parsed.port is not None or parsed.netloc != host or parsed.query or parsed.fragment
            or parsed.path != f"/{quote(database, safe='')}/auth"
            or ".neonauth." not in host or not host.endswith(".aws.neon.tech")):
        raise ValueError("Auth URL must be a canonical Neon Auth HTTPS endpoint")
    return {
        "enabled": True,
        "authUrl": auth_url,
        "database": database,
        # Keep the Auth SDK in a same-site HTTPS frame. Direct requests from
        # chrome-extension:// can lose the Auth cookie when third-party
        # cookies are blocked by the browser.
        "apiOrigin": api_origin,
        "transport": "https-bridge",
        "bridgeUrl": api_origin + "/auth/bridge",
    }


def build(*, expected_sha: str, production_auth_url: str, production_auth_database: str,
          staging_auth_url: str, staging_auth_database: str, output: Path,
          evidence_path: Path) -> dict[str, object]:
    if not SHA40.fullmatch(expected_sha or ""):
        raise ValueError("Source SHA must be a full lowercase commit SHA")
    if _git("rev-parse", "--verify", "HEAD") != expected_sha:
        raise ValueError("Package checkout does not match the expected source SHA")
    if _git("status", "--porcelain=v1", "--untracked-files=all", "--", "extension"):
        raise ValueError("Release extension runtime inputs are modified or untracked")
    manifest_path = ROOT / "extension/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    public_key = manifest.get("key")
    if not isinstance(public_key, str) or not public_key:
        raise ValueError("The pinned Chrome extension public key is required")
    extension_id = chrome_extension_id(public_key)

    production = _auth_config(production_auth_url, production_auth_database, PRODUCTION_API)
    staging = _auth_config(staging_auth_url, staging_auth_database, STAGING_API)
    if production["authUrl"] == staging["authUrl"]:
        raise ValueError("Production and staging Auth endpoints must be different")

    hosts = [PRODUCTION_API + "/*", STAGING_API + "/*"]
    for config in (production, staging):
        origin = urlsplit(str(config["authUrl"])).scheme + "://" + str(urlsplit(str(config["authUrl"])).hostname)
        config["origin"] = origin

    runtime_config = (
        "export const API_BASE_URLS = Object.freeze(" + json.dumps(
            {"production": PRODUCTION_API, "staging": STAGING_API}, separators=(",", ":")
        ) + ");\nexport const API_BASE_URL = API_BASE_URLS.production;\n"
    )
    auth_config = (
        "export const AUTH_CONFIGS = Object.freeze(" + json.dumps(
            {"production": production, "staging": staging}, separators=(",", ":")
        ) + ");\nexport const AUTH_CONFIG = AUTH_CONFIGS.production;\n"
    )
    manifest["host_permissions"] = hosts
    manifest.pop("optional_host_permissions", None)
    embedded = {
        "format": "phishlens-release-extension-v1",
        "source_commit": expected_sha,
        "production_default": True,
        "staging_selection": "popup.html?environment=staging",
        "api_origins": {"production": PRODUCTION_API, "staging": STAGING_API},
        "auth_enabled": True,
        "chrome_extension_id": extension_id,
        "expected_chrome_origin": f"chrome-extension://{extension_id}",
        "host_permissions": hosts,
    }
    files: dict[str, bytes] = {}
    for name in sorted(ASSETS):
        path = ROOT / "extension" / name
        if not path.is_file():
            raise FileNotFoundError(f"Release extension input is missing: {name}")
        data = path.read_bytes()
        if name == "manifest.json":
            data = (json.dumps(manifest, indent=2) + "\n").encode()
        elif name == "js/config.js":
            data = runtime_config.encode()
        elif name == "js/auth-config.js":
            data = auth_config.encode()
        files[name] = data
    files[EVIDENCE_MEMBER] = (json.dumps(embedded, sort_keys=True, indent=2) + "\n").encode()

    output = output.resolve()
    evidence_path = evidence_path.resolve()
    if output == evidence_path or output.is_relative_to(ROOT) or evidence_path.is_relative_to(ROOT):
        raise ValueError("Release package and evidence outputs must be outside the source checkout")
    output.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with ZipFile(output) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(files):
            raise RuntimeError("Release extension archive integrity check failed")

    evidence = {
        **embedded,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_commit": expected_sha,
        "archive": output.name,
        "archive_sha256": _sha256(output.read_bytes()),
        "extension_version": manifest["version"],
        "manifest_key_sha256": hashlib.sha256(public_key.encode()).hexdigest(),
        "runtime_inputs_clean": True,
        "auth_configs": {
            name: {key: value for key, value in config.items() if key != "apiOrigin"}
            for name, config in (("production", production), ("staging", staging))
        },
        "files_sha256": {name: _sha256(data) for name, data in files.items()},
    }
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--production-auth-url", required=True)
    parser.add_argument("--production-auth-database", required=True)
    parser.add_argument("--staging-auth-url", required=True)
    parser.add_argument("--staging-auth-database", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(
            expected_sha=args.expected_sha,
            production_auth_url=args.production_auth_url,
            production_auth_database=args.production_auth_database,
            staging_auth_url=args.staging_auth_url,
            staging_auth_database=args.staging_auth_database,
            output=args.output,
            evidence_path=args.evidence,
        )
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Release extension package rejected: {exc}\n")
    print(json.dumps({key: result[key] for key in (
        "source_commit", "archive", "archive_sha256", "extension_version", "chrome_extension_id"
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
