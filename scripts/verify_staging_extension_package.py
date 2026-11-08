"""Verify staging ZIP contents and bind them to the revision observed on staging."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

try:
    from .verify_extension_package import ASSETS
except ImportError:
    from verify_extension_package import ASSETS


STAGING_ORIGIN = "https://phishlens-staging.onrender.com"
STAGING_HOSTS = [STAGING_ORIGIN + "/*"]
PRODUCTION_HOST = "phishlens-api-ocvt.onrender.com"


def full_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def full_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(archive_path, evidence_path, expected_staging, staging_evidence_path=None):
    if not full_sha(expected_staging):
        raise ValueError("Expected staging revision must be a full lowercase commit SHA")

    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise TypeError("Package evidence must be a JSON object")
    if evidence.get("environment") != "staging" or evidence.get("api_origin") != STAGING_ORIGIN:
        raise ValueError("Package evidence does not identify the staging API origin")
    if (evidence.get("observed_staging_commit") != expected_staging
            or evidence.get("package_checkout_commit") != expected_staging):
        raise ValueError("Package checkout does not match the observed staging revision")
    for key in ("packager_checkout_commit",):
        if not full_sha(evidence.get(key)):
            raise ValueError(f"Package evidence must record a full {key}")
    event_sha = evidence.get("workflow_event_sha")
    if event_sha is not None and not full_sha(event_sha):
        raise ValueError("Workflow event SHA must be a full commit SHA when present")
    if not full_hash(evidence.get("packager_sha256")):
        raise ValueError("Package evidence must record the packager SHA-256")
    packager = Path(__file__).with_name("package_staging_extension.py")
    if sha256_file(packager) != evidence["packager_sha256"]:
        raise ValueError("Packager SHA-256 does not match the verified packager")
    if evidence.get("runtime_inputs_clean") is not True:
        raise ValueError("Staging extension inputs were modified or their status is unknown")
    if evidence.get("host_permissions") != STAGING_HOSTS:
        raise ValueError("Package evidence host permissions are not staging-only")

    archive_path = Path(archive_path)
    if evidence.get("archive") != archive_path.name:
        raise ValueError("Archive filename does not match package evidence")
    archive_hash = sha256_file(archive_path)
    if archive_hash != evidence.get("archive_sha256"):
        raise ValueError("Archive SHA-256 does not match package evidence")

    with ZipFile(archive_path) as archive:
        names = archive.namelist()
        hashes = evidence.get("files_sha256")
        expected_assets = set(ASSETS)
        if (not isinstance(hashes, dict) or set(hashes) != expected_assets
                or len(names) != len(set(names)) or set(names) != expected_assets):
            raise ValueError("Archive file inventory does not match the staging runtime inventory")
        contents = {}
        for name in names:
            data = archive.read(name)
            contents[name] = data
            if hashlib.sha256(data).hexdigest() != hashes[name]:
                raise ValueError(f"File SHA-256 does not match package evidence: {name}")
        manifest = json.loads(contents["manifest.json"])
        config = contents["js/config.js"].decode("utf-8")

    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 3:
        raise ValueError("Expected a Manifest V3 object")
    if manifest.get("name") != "PhishLens Staging":
        raise ValueError("Manifest does not identify the staging extension")
    if manifest.get("version") != evidence.get("extension_version"):
        raise ValueError("Manifest version does not match package evidence")
    if manifest.get("host_permissions") != STAGING_HOSTS:
        raise ValueError("Manifest host permissions are not staging-only")
    if manifest.get("optional_host_permissions"):
        raise ValueError("Optional host permissions are not allowed in the staging package")
    expected_config = "export const API_BASE_URL = " + json.dumps(STAGING_ORIGIN) + ";\n"
    if config != expected_config:
        raise ValueError("Extension API configuration does not target only staging")
    if any(PRODUCTION_HOST.encode("ascii") in data.lower() for data in contents.values()):
        raise ValueError("Production API hostname appears in the staging package")

    if staging_evidence_path is not None:
        observed = json.loads(Path(staging_evidence_path).read_text(encoding="utf-8"))
        version = observed.get("version", {})
        ready = observed.get("ready", {})
        model = observed.get("model_info", {})
        if (observed.get("environment") != "staging"
                or observed.get("backend_source_commit") != expected_staging
                or version.get("commit") != expected_staging
                or version.get("environment") != "staging"):
            raise ValueError("Read-only staging evidence does not match the package checkout")
        if ready.get("status") != "ready" or ready.get("database") != "connected":
            raise ValueError("Read-only staging evidence does not show a ready service")
        if (model.get("provider_mode") != "tfidf" or not full_hash(model.get("model_sha256"))
                or model.get("accepts_tfidf_reports") is not True
                or model.get("accepts_local_reviews") is not True):
            raise ValueError("Read-only staging evidence does not show the expected TF-IDF model")
        if (observed.get("saved_analysis_crud_performed") is not False
                or observed.get("production_writes_performed") is not False):
            raise ValueError("Read-only staging evidence must confirm that no writes were performed")

    return {
        "environment": "staging",
        "api_origin": STAGING_ORIGIN,
        "observed_staging_commit": expected_staging,
        "package_checkout_commit": evidence["package_checkout_commit"],
        "workflow_event_sha": event_sha,
        "archive_sha256": archive_hash,
        "files_verified": len(names),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-staging", required=True)
    parser.add_argument("--staging-evidence", type=Path)
    args = parser.parse_args()
    try:
        result = verify(
            args.archive,
            args.evidence,
            args.expected_staging,
            args.staging_evidence,
        )
    except (ValueError, TypeError, OSError, KeyError, BadZipFile, UnicodeError, RuntimeError) as exc:
        parser.exit(1, f"Staging package rejected: {exc}\n")
    print(json.dumps(result, indent=2))
    print("Staging origin, manifest permissions, ZIP contents, and checkout identity verified.")


if __name__ == "__main__":
    main()

