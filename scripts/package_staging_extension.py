"""Build a staging-only extension ZIP from the exact observed staging checkout."""

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

try:
    from .verify_extension_package import ASSETS
except ImportError:
    from verify_extension_package import ASSETS


STAGING_ORIGIN = "https://phishlens-staging.onrender.com"
PRODUCTION_HOST = "phishlens-api-ocvt.onrender.com"
IN_ARCHIVE_EVIDENCE = "phishlens-build-evidence.json"
ROOT = Path(__file__).resolve().parents[1]


def full_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(root, *arguments):
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Git could not identify {root}: {result.stderr.strip()}")
    return result.stdout.strip()


def checkout_revision(root):
    root = Path(root).resolve(strict=True)
    top = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root:
        raise RuntimeError(f"Package source must be the checkout root ({root})")
    revision = git(root, "rev-parse", "--verify", "HEAD")
    if not full_sha(revision):
        raise RuntimeError("Package checkout does not have a full commit SHA")
    return revision


def assert_clean_extension_checkout(root):
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all", "--", "extension")
    if status:
        raise RuntimeError("Staging checkout has modified or untracked extension inputs")


def chrome_extension_id(public_key):
    """Return Chrome's stable ID for the manifest's base64-encoded public key."""
    try:
        decoded = base64.b64decode(public_key, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Manifest public key must be standard base64") from exc
    if len(decoded) < 32 or base64.b64encode(decoded).decode("ascii") != public_key:
        raise ValueError("Manifest public key must be canonical base64 DER data")
    digest = hashlib.sha256(decoded).digest()[:16]
    return "".join(chr(ord("a") + nibble) for byte in digest for nibble in (byte >> 4, byte & 15))


def auth_settings(auth_url, auth_database, manifest_key):
    """Validate an opt-in Neon Auth target and return package-safe settings."""
    if auth_url is None and auth_database is None and manifest_key is None:
        return None
    if not isinstance(manifest_key, str) or not manifest_key:
        raise ValueError("Auth-enabled staging packages require the extension owner's public manifest key")
    if (not isinstance(auth_database, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,63}", auth_database)):
        raise ValueError("Auth database must be a simple database name")
    if not isinstance(auth_url, str):
        raise ValueError("Auth URL is required when enabling the staging Auth package")
    parsed = urlsplit(auth_url)
    hostname = parsed.hostname or ""
    expected_path = f"/{quote(auth_database, safe='')}/auth"
    if (parsed.scheme != "https" or not hostname or parsed.username or parsed.password
            or parsed.port is not None or parsed.netloc != hostname or parsed.query or parsed.fragment
            or parsed.path != expected_path or hostname == PRODUCTION_HOST
            or ".neonauth." not in hostname or not hostname.endswith(".aws.neon.tech")):
        raise ValueError("Auth URL must be a canonical Neon Auth HTTPS URL for the selected database")
    extension_id = chrome_extension_id(manifest_key)
    return {
        "enabled": True,
        "auth_url": auth_url,
        "database": auth_database,
        "origin": f"https://{hostname}",
        "manifest_key": manifest_key,
        "manifest_key_sha256": hashlib.sha256(base64.b64decode(manifest_key)).hexdigest(),
        "chrome_extension_id": extension_id,
        "expected_chrome_origin": f"chrome-extension://{extension_id}",
        "config": {
            "enabled": True,
            "authUrl": auth_url,
            "database": auth_database,
            "apiOrigin": STAGING_ORIGIN,
        },
    }


def build(source_root, archive_path, evidence_path, expected_staging, *, auth_url=None,
          auth_database=None, manifest_key=None):
    source_root = Path(source_root).resolve(strict=True)
    archive_path = Path(archive_path).resolve()
    evidence_path = Path(evidence_path).resolve()
    if not full_sha(expected_staging):
        raise ValueError("Expected staging revision must be a full lowercase commit SHA")
    auth = auth_settings(auth_url, auth_database, manifest_key)
    if archive_path == evidence_path or archive_path.is_relative_to(source_root) or evidence_path.is_relative_to(source_root):
        raise ValueError("Staging package and evidence outputs must be separate from the source checkout")

    origin = os.environ.get("STAGING_BASE_URL", STAGING_ORIGIN)
    parsed = urlsplit(origin)
    if (origin != STAGING_ORIGIN or parsed.scheme != "https" or parsed.hostname != "phishlens-staging.onrender.com"
            or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password):
        raise ValueError("STAGING_BASE_URL must be the PhishLens staging HTTPS origin")

    package_revision = checkout_revision(source_root)
    if package_revision != expected_staging:
        raise ValueError(
            f"Package checkout {package_revision} does not match observed staging {expected_staging}"
        )
    assert_clean_extension_checkout(source_root)

    packager_revision = checkout_revision(ROOT)
    event_revision = os.environ.get("GITHUB_SHA") or None
    if event_revision is not None and not full_sha(event_revision):
        raise ValueError("GITHUB_SHA must be a full lowercase commit SHA when set")

    extension_root = source_root / "extension"
    file_hashes = {}
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    host_permissions = [STAGING_ORIGIN + "/*"]
    if auth:
        host_permissions.append(auth["origin"] + "/*")
    embedded_evidence = {
        "format": "phishlens-staging-package-v1",
        "environment": "staging",
        "source_commit": package_revision,
        "observed_staging_commit": expected_staging,
        "packager_commit": packager_revision,
        "api_origin": STAGING_ORIGIN,
        "host_permissions": host_permissions,
        "auth_enabled": bool(auth),
        "auth_url": auth["auth_url"] if auth else None,
        "auth_database": auth["database"] if auth else None,
        "auth_origin": auth["origin"] if auth else None,
        "manifest_key_sha256": auth["manifest_key_sha256"] if auth else None,
        "chrome_extension_id": auth["chrome_extension_id"] if auth else None,
        "expected_chrome_origin": auth["expected_chrome_origin"] if auth else None,
    }
    embedded_bytes = (json.dumps(embedded_evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
        for asset in sorted(ASSETS):
            source = extension_root / asset
            if not source.is_file():
                raise FileNotFoundError(f"Staging checkout is missing runtime asset: {asset}")
            data = source.read_bytes()
            if asset == "manifest.json":
                manifest = json.loads(data)
                manifest["name"] = "PhishLens Staging Auth" if auth else "PhishLens Staging"
                manifest["host_permissions"] = host_permissions
                if auth:
                    existing_key = manifest.get("key")
                    if existing_key is not None and existing_key != auth["manifest_key"]:
                        raise ValueError("Supplied public key does not match the source manifest key")
                    manifest["key"] = auth["manifest_key"]
                else:
                    manifest.pop("key", None)
                manifest.pop("optional_host_permissions", None)
                data = json.dumps(manifest, indent=2).encode("utf-8")
            elif asset == "js/config.js":
                data = ("export const API_BASE_URL = " + json.dumps(STAGING_ORIGIN) + ";\n").encode("utf-8")
            elif asset == "js/auth-config.js" and auth:
                data = (
                    "export const AUTH_CONFIG = "
                    + json.dumps(auth["config"], separators=(",", ":"))
                    + ";\n"
                ).encode("utf-8")
            archive.writestr(asset, data)
            file_hashes[asset] = hashlib.sha256(data).hexdigest()

        archive.writestr(IN_ARCHIVE_EVIDENCE, embedded_bytes)
        file_hashes[IN_ARCHIVE_EVIDENCE] = hashlib.sha256(embedded_bytes).hexdigest()

    archive_hash = sha256_file(archive_path)
    evidence = {
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "environment": "staging",
        "api_origin": STAGING_ORIGIN,
        "source_commit": package_revision,
        "in_archive_evidence": IN_ARCHIVE_EVIDENCE,
        "host_permissions": host_permissions,
        "auth_enabled": bool(auth),
        "auth_url": auth["auth_url"] if auth else None,
        "auth_database": auth["database"] if auth else None,
        "auth_origin": auth["origin"] if auth else None,
        "manifest_key_sha256": auth["manifest_key_sha256"] if auth else None,
        "chrome_extension_id": auth["chrome_extension_id"] if auth else None,
        "expected_chrome_origin": auth["expected_chrome_origin"] if auth else None,
        "trusted_chrome_origin": None,
        "observed_staging_commit": expected_staging,
        "package_checkout_commit": package_revision,
        "packager_checkout_commit": packager_revision,
        "workflow_event_sha": event_revision,
        "packager_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "extension_version": json.loads((extension_root / "manifest.json").read_text(encoding="utf-8"))["version"],
        "runtime_inputs_clean": True,
        "includes_local_judge_weights": False,
        "archive": archive_path.name,
        "archive_sha256": archive_hash,
        "files_sha256": file_hashes,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--expected-staging", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument(
        "--auth-url",
        help="Enable Neon Auth in this staging-only package for this confirmed Auth URL",
    )
    parser.add_argument("--auth-database", help="Neon Auth database name; required with --auth-url")
    parser.add_argument(
        "--manifest-key-file", type=Path,
        help="File containing the extension owner's base64 public manifest key (not the private signing key)",
    )
    args = parser.parse_args()
    try:
        evidence = build(
            args.source_root,
            args.output,
            args.evidence,
            args.expected_staging,
            auth_url=args.auth_url,
            auth_database=args.auth_database,
            manifest_key=args.manifest_key_file.read_text(encoding="ascii").strip()
            if args.manifest_key_file else None,
        )
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Staging package rejected: {exc}\n")
    print(json.dumps({
        "archive": evidence["archive"],
        "environment": evidence["environment"],
        "api_origin": evidence["api_origin"],
        "auth_enabled": evidence["auth_enabled"],
        "observed_staging_commit": evidence["observed_staging_commit"],
        "package_checkout_commit": evidence["package_checkout_commit"],
    }, indent=2))


if __name__ == "__main__":
    main()

