"""Fail-closed validation for immutable PhishLens release candidates.

This module deliberately does not deploy, tag, or publish anything. It verifies
the identities and evidence that a separately protected promotion workflow must
provide before it can perform those actions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from zipfile import BadZipFile, ZipFile

try:
    from .manifest_key import chrome_extension_id, decode_manifest_public_key
except ImportError:
    from manifest_key import chrome_extension_id, decode_manifest_public_key


REQUIRED_CHECKS = {
    "Backend checks": 15368,
    "Extension checks": 15368,
    "Staging integration": 15368,
    "CodeQL": 57789,
    "Secretary staging": 15368,
    "Deterministic AI Evaluation": 15368,
    "Dependency security": 15368,
    "Workflow lint": 15368,
}
STAGING_ORIGIN = "https://phishlens-staging.onrender.com"
PRODUCTION_ORIGIN = "https://phishlens-api-ocvt.onrender.com"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PRODUCT_CHECKS = (
    "sign_in", "create", "list", "read", "update", "delete",
    "persistence_after_reload", "user_isolation", "ownership_checks", "cleanup",
)
UX_CHECKS = ("loading", "success", "authentication_failure", "api_error", "timeout")


class GateError(ValueError):
    """An identity or acceptance precondition failed."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GateError(f"Expected a JSON object in {path}")
    return value


def check_required_statuses(payload: dict[str, Any], expected_sha: str) -> dict[str, Any]:
    """Verify checks on the exact merged PR tree used to produce the main SHA."""
    if not SHA40.fullmatch(expected_sha or ""):
        raise GateError("A full lowercase source commit SHA is required")

    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        raise GateError("The release commit is not linked to a verified merged pull request")
    tested_sha = pull_request.get("head_sha")
    tree_sha = pull_request.get("tree_sha")
    pull_request_number = pull_request.get("number")
    pull_request_author = pull_request.get("author")
    if (pull_request.get("merge_commit_sha") != expected_sha
            or pull_request.get("merged_at") in (None, "")
            or pull_request.get("base_ref") != "main"
            or pull_request.get("head_repository") != payload.get("repository")
            or not isinstance(pull_request_number, int) or pull_request_number <= 0
            or not isinstance(pull_request_author, str) or not pull_request_author.strip()
            or not SHA40.fullmatch(tested_sha or "")
            or not SHA40.fullmatch(tree_sha or "")
            or pull_request.get("merge_tree_sha") != tree_sha):
        raise GateError("Merged PR identity or tested source tree does not match the release commit")

    run_payload = payload.get("check_runs")
    status_payload = payload.get("statuses")
    runs = run_payload.get("check_runs") if isinstance(run_payload, dict) else None
    statuses = status_payload.get("statuses") if isinstance(status_payload, dict) else None
    if not isinstance(runs, list) or not isinstance(statuses, list):
        raise GateError("GitHub PR check evidence is malformed")

    failures: list[str] = []
    passed: dict[str, dict[str, Any]] = {}
    for name, app_id in REQUIRED_CHECKS.items():
        named_runs = [run for run in runs if isinstance(run, dict) and run.get("name") == name]
        exact_runs = [
            run for run in named_runs
            if run.get("head_sha") == tested_sha
            and isinstance(run.get("app"), dict)
            and run["app"].get("id") == app_id
        ]
        if named_runs and not exact_runs:
            failures.append(f"{name}: check run has the wrong SHA or GitHub App")
            continue
        if exact_runs:
            if len(exact_runs) != 1:
                failures.append(f"{name}: expected one latest exact-PR-SHA run, found {len(exact_runs)}")
                continue
            run = exact_runs[0]
            if run.get("status") != "completed" or run.get("conclusion") != "success":
                failures.append(
                    f"{name}: expected completed/success, observed "
                    f"{run.get('status')}/{run.get('conclusion')}"
                )
                continue
            passed[name] = {
                "state": "success", "tested_sha": tested_sha,
                "app_id": app_id, "source": "check_run",
            }
            continue

        # Secretary staging is a GitHub commit status produced by the same
        # configured Actions app, not a check-run. Its explicit N/A status is
        # acceptable here only because the release flow separately performs
        # the protected live staging acceptance before production promotion.
        exact_statuses = [
            status for status in statuses
            if isinstance(status, dict) and status.get("context") == name
        ]
        if len(exact_statuses) != 1 or exact_statuses[0].get("state") != "success":
            observed = exact_statuses[0].get("state") if len(exact_statuses) == 1 else "missing/ambiguous"
            failures.append(f"{name}: expected successful exact-PR-SHA status, observed {observed}")
            continue
        passed[name] = {
            "state": "success", "tested_sha": tested_sha,
            "app_id": app_id, "source": "commit_status",
            "description": (exact_statuses[0].get("description")
                            if isinstance(exact_statuses[0].get("description"), str) else ""),
        }

    if failures:
        raise GateError("Required GitHub checks did not pass:\n- " + "\n- ".join(failures))
    return {
        "candidate_sha": expected_sha,
        "tested_sha": tested_sha,
        "tree_sha": tree_sha,
        "candidate_tree_sha": pull_request.get("merge_tree_sha"),
        "pull_request": pull_request_number,
        "author": pull_request_author,
        "checks": passed,
    }


def _require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate_staging_acceptance(
    evidence: dict[str, Any], *, source_sha: str, image_digest: str,
    extension_sha256: str, branch_id: str,
) -> None:
    """Verify product acceptance describes a clean isolated staging run."""
    failures: list[str] = []
    _require(evidence.get("status") == "passed", "Staging acceptance did not pass", failures)
    _require(evidence.get("environment") == "staging", "Evidence is not from staging", failures)
    _require(evidence.get("source_sha") == source_sha, "Staging source SHA does not match", failures)
    _require(evidence.get("backend_image_digest") == image_digest,
             "Staging backend image digest does not match", failures)
    _require(evidence.get("extension_zip_sha256") == extension_sha256,
             "Staging extension ZIP digest does not match", failures)
    _require(evidence.get("extension_environment") == "staging",
             "Staging acceptance did not select the staging configuration in the release ZIP", failures)
    _require(evidence.get("production_requests") == 0,
             "Acceptance evidence records production requests", failures)
    _require(evidence.get("production_writes") == 0,
             "Acceptance evidence records production writes", failures)
    _require(evidence.get("production_auth_requests") == 0,
             "Acceptance evidence records production Auth requests", failures)

    database = evidence.get("database")
    _require(isinstance(database, dict), "Staging database identity is missing", failures)
    if isinstance(database, dict):
        _require(database.get("project_id"), "Staging Neon project ID is missing", failures)
        _require(database.get("branch_id") == branch_id, "Staging Neon branch ID does not match", failures)
        _require(database.get("branch_id") != database.get("production_branch_id"),
                 "Staging points at the production Neon branch", failures)
        _require(database.get("branch_kind") == "schema-only",
                 "Staging branch is not verified as schema-only", failures)
        _require(database.get("parent_id") is None,
                 "Schema-only staging branch must be an independent root", failures)
        _require(database.get("production_rows_present") is False,
                 "Staging database is not confirmed free of production rows", failures)

    auth = evidence.get("auth")
    _require(isinstance(auth, dict) and auth.get("mode") == "neon-auth"
             and auth.get("enabled") is True,
             "Staging evidence does not confirm enabled Neon Auth", failures)

    product = evidence.get("product")
    _require(isinstance(product, dict), "Authenticated product acceptance is missing", failures)
    if isinstance(product, dict):
        for check in PRODUCT_CHECKS:
            _require(product.get(check) is True, f"Product acceptance failed: {check}", failures)

    ux = evidence.get("user_experience")
    _require(isinstance(ux, dict), "Extension UX acceptance is missing", failures)
    if isinstance(ux, dict):
        for check in UX_CHECKS:
            _require(ux.get(check) is True, f"Extension UX acceptance failed: {check}", failures)

    ai = evidence.get("ai_acceptance")
    _require(isinstance(ai, dict) and ai.get("status") == "passed",
             "Approved model/provider acceptance is blocked or missing", failures)
    if isinstance(ai, dict):
        _require(ai.get("provider") not in (None, "", "disabled", "mock"),
                 "Mock or disabled inference cannot pass release acceptance", failures)
        _require(ai.get("model_revision"), "Accepted model revision is missing", failures)
        _require(ai.get("evaluation_sha256") and SHA256.fullmatch(ai.get("evaluation_sha256", "")),
                 "Reviewed AI evaluation digest is missing or invalid", failures)
        _require(ai.get("approved") is True,
                 "AI evaluation does not record explicit reviewed approval", failures)

    if failures:
        raise GateError("Staging acceptance evidence is incomplete:\n- " + "\n- ".join(failures))


def validate_manifest(
    manifest: dict[str, Any], *, extension_zip: str | Path,
    extension_evidence: dict[str, Any], staging_evidence: dict[str, Any],
    staging_evidence_path: str | Path, changelog_path: str | Path, expected_sha: str,
) -> dict[str, Any]:
    """Recompute artifact hashes and reject any incomplete or unapproved release."""
    failures: list[str] = []
    release = manifest.get("release")
    source = manifest.get("source")
    backend = manifest.get("backend")
    extension = manifest.get("extension")
    model = manifest.get("model")
    auth = manifest.get("auth")
    database = manifest.get("database")
    acceptance = manifest.get("staging_acceptance")
    checks = manifest.get("required_checks")
    approval = manifest.get("approval")
    failure_switch = manifest.get("failure_switch")
    changelog = manifest.get("changelog")
    ai = staging_evidence.get("ai_acceptance")
    production_attestation = manifest.get("external_production_config_attestation")

    _require(manifest.get("format") == "phishlens-release-v1", "Unsupported manifest format", failures)
    _require(isinstance(release, dict), "Release identity is missing", failures)
    _require(isinstance(source, dict), "Source identity is missing", failures)
    _require(isinstance(backend, dict), "Backend artifact identity is missing", failures)
    _require(isinstance(extension, dict), "Extension artifact identity is missing", failures)
    _require(isinstance(model, dict), "Approved model identity is missing", failures)
    _require(isinstance(auth, dict), "Auth mode is missing", failures)
    _require(isinstance(database, dict), "Database identity is missing", failures)
    _require(isinstance(acceptance, dict), "Staging acceptance reference is missing", failures)
    _require(isinstance(approval, dict), "Independent release approval is missing", failures)
    _require(isinstance(failure_switch, dict), "Failure switch record is missing", failures)
    _require(isinstance(changelog, dict), "Changelog identity is missing", failures)

    if not all(isinstance(item, dict) for item in (release, source, backend, extension, model, auth,
                                                   database, acceptance, approval, failure_switch, changelog)):
        raise GateError("Release manifest is incomplete:\n- " + "\n- ".join(failures))

    _require(SHA40.fullmatch(expected_sha or "") is not None,
             "Expected source SHA must be full and lowercase", failures)
    _require(source.get("sha") == expected_sha, "Manifest source SHA does not match candidate", failures)
    version = release.get("version")
    _require(isinstance(version, str) and SEMVER.fullmatch(version) is not None,
             "Release version must be semantic version X.Y.Z", failures)
    _require(release.get("tag") == (f"v{version}" if isinstance(version, str) else None),
             "Release tag must equal v<version>", failures)

    image_digest = backend.get("digest")
    image_ref = backend.get("image")
    _require(isinstance(image_digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", image_digest) is not None,
             "Backend image digest is invalid", failures)
    _require(isinstance(image_ref, str) and image_digest and image_ref.endswith("@" + image_digest),
             "Backend must be pinned to the recorded immutable image digest", failures)
    _require(backend.get("source_sha") == expected_sha,
             "Backend image source SHA does not match candidate", failures)

    actual_extension_sha = sha256_file(extension_zip)
    _require(extension.get("sha256") == actual_extension_sha,
             "Extension ZIP SHA-256 differs from manifest", failures)
    _require(extension_evidence.get("archive_sha256") == actual_extension_sha,
             "Extension sidecar does not match the ZIP", failures)
    _require(extension_evidence.get("source_commit") == expected_sha,
             "Extension package source SHA does not match candidate", failures)
    _require(extension_evidence.get("format") == "phishlens-release-extension-v1"
             and extension_evidence.get("production_default") is True
             and extension_evidence.get("auth_enabled") is True,
             "Candidate ZIP is not the single dual-environment Auth release package", failures)
    _require(extension_evidence.get("api_origins") == {
        "production": PRODUCTION_ORIGIN, "staging": STAGING_ORIGIN,
    }, "Release package API origins do not match the approved fixed services", failures)
    auth_configs = extension_evidence.get("auth_configs")
    _require(isinstance(auth_configs, dict)
             and set(auth_configs) == {"production", "staging"}
             and all(isinstance(auth_configs.get(env), dict)
                     and auth_configs[env].get("enabled") is True
                     and auth_configs[env].get("authUrl")
                     and auth_configs[env].get("database")
                     for env in ("production", "staging")),
             "Release ZIP must bind enabled production and staging Neon Auth endpoints", failures)
    _require(extension.get("version") == extension_evidence.get("extension_version"),
             "Extension version does not match package evidence", failures)
    try:
        verify_release_extension_archive(extension_zip, extension_evidence, expected_sha)
    except GateError as exc:
        failures.append(str(exc))

    model_approved = model.get("approved") is True
    _require(model_approved, "Model/provider quality approval is not recorded", failures)
    _require(model.get("provider") not in (None, "", "disabled", "mock"),
             "Disabled or mock provider cannot be released", failures)
    _require(model.get("revision"), "Model/provider revision is missing", failures)
    eval_sha = model.get("evaluation_sha256")
    _require(isinstance(eval_sha, str) and SHA256.fullmatch(eval_sha) is not None,
             "Approved evaluation SHA-256 is missing or invalid", failures)
    _require(auth.get("mode") == "neon-auth" and auth.get("enabled") is True,
             "Release must use enabled Neon Auth", failures)

    branch_id = database.get("staging_branch_id")
    _require(isinstance(branch_id, str) and branch_id.startswith("br-"),
             "Staging Neon branch ID is invalid", failures)
    _require(database.get("branch_kind") == "schema-only"
             and database.get("production_rows_present") is False,
             "Staging Neon branch must be verified schema-only and contain no production rows", failures)
    _require(database.get("staging_parent_id") is None,
             "Schema-only staging branch must be an independent root", failures)
    _require(database.get("migration_revision"), "Database migration revision is missing", failures)

    _require(acceptance.get("status") == "passed", "Staging acceptance status is not passed", failures)
    _require(acceptance.get("evidence_sha256") == sha256_file(staging_evidence_path),
             "Staging evidence SHA-256 does not match manifest", failures)
    try:
        validate_staging_acceptance(
            staging_evidence, source_sha=expected_sha, image_digest=image_digest,
            extension_sha256=actual_extension_sha, branch_id=branch_id,
        )
    except GateError as exc:
        failures.extend(str(exc).splitlines()[1:] or [str(exc)])
    if isinstance(ai, dict):
        _require(ai.get("provider") == model.get("provider"),
                 "Accepted staging provider differs from the release manifest", failures)
        _require(ai.get("model_revision") == model.get("revision"),
                 "Accepted staging model revision differs from the release manifest", failures)
        _require(ai.get("evaluation_sha256") == model.get("evaluation_sha256"),
                 "Accepted AI evaluation digest differs from the release manifest", failures)

    required_contexts = set(REQUIRED_CHECKS)
    check_evidence = checks if isinstance(checks, dict) else {}
    check_map = check_evidence.get("checks") if isinstance(check_evidence.get("checks"), dict) else {}
    _require(check_evidence.get("candidate_sha") == expected_sha,
             "Required-check evidence is not bound to the release commit", failures)
    tested_check_sha = check_evidence.get("tested_sha")
    check_tree_sha = check_evidence.get("tree_sha")
    candidate_tree_sha = check_evidence.get("candidate_tree_sha")
    _require(isinstance(tested_check_sha, str) and SHA40.fullmatch(tested_check_sha) is not None,
             "Required-check evidence is missing the tested PR SHA", failures)
    _require(isinstance(check_tree_sha, str) and SHA40.fullmatch(check_tree_sha) is not None,
             "Required-check evidence is missing the source tree identity", failures)
    _require(isinstance(candidate_tree_sha, str) and SHA40.fullmatch(candidate_tree_sha) is not None
             and candidate_tree_sha == check_tree_sha,
             "Required checks do not cover the exact release source tree", failures)
    _require(isinstance(check_evidence.get("pull_request"), int)
             and check_evidence.get("pull_request", 0) > 0,
             "Required-check evidence is missing its merged pull request", failures)
    _require(check_evidence.get("author") == source.get("author"),
             "Manifest source author differs from the verified merged pull request", failures)
    _require(set(check_map) == required_contexts,
             "Required check names do not match the protected main-branch contract", failures)
    for name, app_id in REQUIRED_CHECKS.items():
        result = check_map.get(name)
        _require(isinstance(result, dict) and result.get("state") == "success",
                 f"Required check is not successful: {name}", failures)
        if isinstance(result, dict):
            _require(result.get("tested_sha") == check_evidence.get("tested_sha"),
                     f"Required check was not run on the verified PR SHA: {name}", failures)
            _require(result.get("app_id") == app_id,
                     f"Required check came from an unexpected GitHub App: {name}", failures)
            _require(result.get("source") in {"check_run", "commit_status"},
                     f"Required check evidence source is invalid: {name}", failures)

    _require(approval.get("approved") is True and approval.get("mechanism") == "github-environment",
             "Protected production-environment approval is missing", failures)
    _require(approval.get("independent") is True,
             "Production approval must be independent", failures)
    _require(approval.get("approved_by") and approval.get("approved_by") != source.get("author"),
             "Release approval must identify someone other than the source author", failures)
    _require(approval.get("run_id"), "Protected approval run identity is missing", failures)

    _require(failure_switch.get("promotion_enabled") is True,
             "Production promotion failure switch is off", failures)
    _require(failure_switch.get("tested_fail_closed") is True,
             "Failure switch has not been tested fail-closed", failures)
    _require(failure_switch.get("ai_kill_switch") == "AI_ANALYSIS_ENABLED",
             "AI failure switch identity is missing", failures)

    expected_changelog_sha = sha256_file(changelog_path)
    _require(changelog.get("path") == str(changelog_path), "Changelog path differs from manifest", failures)
    _require(changelog.get("sha256") == expected_changelog_sha,
             "Changelog SHA-256 differs from manifest", failures)
    _require(production_attestation == "current",
             "Current production Auth/database/runtime configuration attestation is missing", failures)
    if failures:
        raise GateError("Release manifest rejected:\n- " + "\n- ".join(failures))

    return {
        "status": "passed",
        "version": version,
        "tag": release["tag"],
        "source_sha": expected_sha,
        "backend_image_digest": image_digest,
        "extension_zip_sha256": actual_extension_sha,
        "staging_branch_id": branch_id,
        "required_checks": sorted(required_contexts),
        "staging_acceptance": "passed",
        "independent_approval": True,
    }


def verify_extension_archive(
    archive_path: str | Path, evidence: dict[str, Any], expected_sha: str,
) -> str:
    """Verify the exact candidate ZIP, its embedded staging identity, and sidecar."""
    archive_path = Path(archive_path)
    archive_digest = sha256_file(archive_path)
    if not SHA40.fullmatch(expected_sha or ""):
        raise GateError("Expected source SHA must be a full lowercase commit SHA")
    if evidence.get("archive_sha256") != archive_digest:
        raise GateError("Extension ZIP does not match its evidence SHA-256")
    if evidence.get("source_commit") != expected_sha:
        raise GateError("Extension package source SHA does not match candidate")
    if evidence.get("environment") != "staging" or evidence.get("auth_enabled") is not True:
        raise GateError("Extension ZIP must be an Auth-enabled staging build")
    if evidence.get("api_origin") != STAGING_ORIGIN:
        raise GateError("Extension ZIP does not target the approved staging API")
    try:
        with ZipFile(archive_path) as archive:
            if archive.testzip() is not None:
                raise GateError("Extension ZIP failed its CRC check")
            embedded = json.loads(archive.read("phishlens-build-evidence.json"))
            names = archive.namelist()
            hashes = evidence.get("files_sha256")
            if not isinstance(hashes, dict) or set(names) != set(hashes) or len(names) != len(set(names)):
                raise GateError("Extension ZIP inventory does not match its sidecar")
            for name in names:
                if hashlib.sha256(archive.read(name)).hexdigest() != hashes.get(name):
                    raise GateError(f"Extension archive member hash differs from sidecar: {name}")
    except (OSError, BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise GateError(f"Extension archive could not be verified: {exc}") from exc
    if embedded.get("source_commit") != expected_sha or embedded.get("environment") != "staging":
        raise GateError("Embedded extension identity does not match the staging candidate")
    return archive_digest


def verify_release_extension_archive(
    archive_path: str | Path, evidence: dict[str, Any], expected_sha: str,
) -> str:
    """Verify the single staged-then-released ZIP and both environment bindings."""
    archive_path = Path(archive_path)
    digest = sha256_file(archive_path)
    if not SHA40.fullmatch(expected_sha or ""):
        raise GateError("Expected source SHA must be a full lowercase commit SHA")
    if evidence.get("format") != "phishlens-release-extension-v1":
        raise GateError("Release extension provenance format is not supported")
    if evidence.get("archive_sha256") != digest or evidence.get("source_commit") != expected_sha:
        raise GateError("Release extension ZIP digest or source SHA does not match its sidecar")
    if evidence.get("production_default") is not True or evidence.get("auth_enabled") is not True:
        raise GateError("Release extension must default to production with Auth enabled")
    if evidence.get("api_origins") != {"production": PRODUCTION_ORIGIN, "staging": STAGING_ORIGIN}:
        raise GateError("Release extension has an unexpected API origin")
    auth_configs = evidence.get("auth_configs")
    if not isinstance(auth_configs, dict) or set(auth_configs) != {"production", "staging"}:
        raise GateError("Release extension must bind both Auth environments")
    hosts = [PRODUCTION_ORIGIN + "/*", STAGING_ORIGIN + "/*"]
    for environment in ("production", "staging"):
        config = auth_configs[environment]
        if (not isinstance(config, dict) or config.get("enabled") is not True
                or not config.get("authUrl") or not config.get("database")):
            raise GateError(f"Release extension {environment} Auth configuration is incomplete")
        auth_url = config["authUrl"]
        database = config["database"]
        parsed = urlsplit(auth_url)
        host = parsed.hostname or ""
        if (not isinstance(database, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,63}", database)
                or parsed.scheme != "https" or not host or parsed.netloc != host
                or parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment
                or parsed.path != f"/{database}/auth" or ".neonauth." not in host
                or not host.endswith(".aws.neon.tech")):
            raise GateError(f"Release extension {environment} Auth endpoint is malformed")
        hosts.append(f"https://{host}/*")
    if len(hosts) != len(set(hosts)):
        raise GateError("Release extension environment host permissions overlap")

    try:
        with ZipFile(archive_path) as archive:
            if archive.testzip() is not None:
                raise GateError("Release extension ZIP failed its CRC check")
            names = archive.namelist()
            hashes = evidence.get("files_sha256")
            if (not isinstance(hashes, dict) or set(names) != set(hashes)
                    or len(names) != len(set(names))):
                raise GateError("Release extension ZIP inventory differs from its sidecar")
            for name in names:
                if hashlib.sha256(archive.read(name)).hexdigest() != hashes.get(name):
                    raise GateError(f"Release extension member digest mismatch: {name}")
            manifest = json.loads(archive.read("manifest.json"))
            embedded = json.loads(archive.read("phishlens-build-evidence.json"))
            config_source = archive.read("js/config.js").decode("utf-8")
            auth_source = archive.read("js/auth-config.js").decode("utf-8")
    except (OSError, BadZipFile, KeyError, json.JSONDecodeError, UnicodeError) as exc:
        raise GateError(f"Release extension archive could not be verified: {exc}") from exc
    if manifest.get("host_permissions") != hosts or manifest.get("optional_host_permissions"):
        raise GateError("Release extension host permissions are not the two approved services")
    public_key = manifest.get("key")
    extension_id = evidence.get("chrome_extension_id")
    try:
        valid_extension_id = (isinstance(public_key, str)
                              and chrome_extension_id(public_key) == extension_id)
        decode_manifest_public_key(public_key)
    except (TypeError, ValueError):
        valid_extension_id = False
    if not valid_extension_id or not isinstance(extension_id, str) or not re.fullmatch(r"[a-p]{32}", extension_id):
        raise GateError("Release extension public key and Chrome identity do not match")
    if embedded.get("source_commit") != expected_sha or embedded.get("production_default") is not True:
        raise GateError("Embedded release extension identity is inconsistent")
    if (embedded.get("api_origins") != evidence.get("api_origins")
            or embedded.get("staging_selection") != "popup.html?environment=staging"
            or embedded.get("chrome_extension_id") != extension_id
            or embedded.get("expected_chrome_origin") != f"chrome-extension://{extension_id}"):
        raise GateError("Embedded release environment or extension identity is inconsistent")
    if evidence.get("host_permissions") != hosts or embedded.get("host_permissions") != hosts:
        raise GateError("Release extension host permission provenance differs")
    # The packager uses compact JSON with insertion-ordered environment keys.
    expected_api_source = (
        "export const API_BASE_URLS = Object.freeze("
        + json.dumps({"production": PRODUCTION_ORIGIN, "staging": STAGING_ORIGIN}, separators=(",", ":"))
        + ");\nexport const API_BASE_URL = API_BASE_URLS.production;\n"
    )
    if config_source != expected_api_source:
        raise GateError("Release extension runtime does not bind both API origins")
    runtime_auth_configs = {}
    for environment in ("production", "staging"):
        if auth_configs[environment]["authUrl"] not in auth_source:
            raise GateError(f"Release extension runtime omits {environment} Neon Auth endpoint")
        origin = f"https://{urlsplit(auth_configs[environment]['authUrl']).hostname}"
        runtime_auth_configs[environment] = {
            "enabled": True,
            "authUrl": auth_configs[environment]["authUrl"],
            "database": auth_configs[environment]["database"],
            "apiOrigin": PRODUCTION_ORIGIN if environment == "production" else STAGING_ORIGIN,
            "origin": origin,
        }
    expected_auth_source = (
        "export const AUTH_CONFIGS = Object.freeze("
        + json.dumps(runtime_auth_configs, separators=(",", ":"))
        + ");\nexport const AUTH_CONFIG = AUTH_CONFIGS.production;\n"
    )
    if auth_source != expected_auth_source:
        raise GateError("Release extension Auth runtime differs from its public sidecar")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("verify-checks")
    check_parser.add_argument("--expected-sha", required=True)
    check_parser.add_argument("--input", default="-")
    package_parser = subparsers.add_parser("verify-extension")
    package_parser.add_argument("--archive", required=True)
    package_parser.add_argument("--evidence", required=True)
    package_parser.add_argument("--expected-sha", required=True)
    release_package_parser = subparsers.add_parser("verify-release-extension")
    release_package_parser.add_argument("--archive", required=True)
    release_package_parser.add_argument("--evidence", required=True)
    release_package_parser.add_argument("--expected-sha", required=True)
    manifest_parser = subparsers.add_parser("validate-manifest")
    manifest_parser.add_argument("--manifest", required=True)
    manifest_parser.add_argument("--extension-zip", required=True)
    manifest_parser.add_argument("--extension-evidence", required=True)
    manifest_parser.add_argument("--staging-evidence", required=True)
    manifest_parser.add_argument("--changelog", required=True)
    manifest_parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()

    try:
        if args.command == "verify-checks":
            raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
            result = check_required_statuses(json.loads(raw), args.expected_sha)
            print(json.dumps({"status": "passed", "required_checks": result}, sort_keys=True))
        elif args.command == "verify-extension":
            digest = verify_extension_archive(
                args.archive, _read_json(args.evidence), args.expected_sha,
            )
            print(json.dumps({"status": "passed", "archive_sha256": digest}, sort_keys=True))
        elif args.command == "verify-release-extension":
            digest = verify_release_extension_archive(
                args.archive, _read_json(args.evidence), args.expected_sha,
            )
            print(json.dumps({"status": "passed", "archive_sha256": digest}, sort_keys=True))
        else:
            result = validate_manifest(
                _read_json(args.manifest),
                extension_zip=args.extension_zip,
                extension_evidence=_read_json(args.extension_evidence),
                staging_evidence=_read_json(args.staging_evidence),
                staging_evidence_path=args.staging_evidence,
                changelog_path=args.changelog,
                expected_sha=args.expected_sha,
            )
            print(json.dumps(result, sort_keys=True))
    except (GateError, OSError, json.JSONDecodeError, TypeError) as exc:
        parser.exit(1, f"Release gate failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
