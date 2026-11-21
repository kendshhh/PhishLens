import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from scripts.release_readiness import (
    REQUIRED_CHECKS,
    GateError,
    check_required_statuses,
    validate_manifest,
    verify_release_extension_archive,
)
from scripts.manifest_key import chrome_extension_id
from scripts.migrate_release_staging import validate_target
from scripts.release_notes import extract_notes
from scripts.verify_github_environment import EnvironmentGateError, validate_environment
from scripts.verify_neon_release_branch import NeonReleaseError, verify_branch


SOURCE_SHA = "a" * 40
PR_HEAD_SHA = "d" * 40
TREE_SHA = "e" * 40
IMAGE_DIGEST = "sha256:" + "b" * 64
EVALUATION_SHA = "c" * 64


def check_runs(conclusion="success"):
    return {
        "repository": "kendshhh/PhishLens",
        "pull_request": {
            "number": 264,
            "merged_at": "2026-11-20T17:03:50Z",
            "merge_commit_sha": SOURCE_SHA,
            "base_ref": "main",
            "head_repository": "kendshhh/PhishLens",
            "head_sha": PR_HEAD_SHA,
            "tree_sha": TREE_SHA,
            "merge_tree_sha": TREE_SHA,
            "author": "source-author",
        },
        "check_runs": {"check_runs": [
            {
                "name": name,
                "head_sha": PR_HEAD_SHA,
                "status": "completed",
                "conclusion": conclusion,
                "app": {"id": app_id},
            }
            for name, app_id in REQUIRED_CHECKS.items() if name != "Secretary staging"
        ]},
        "statuses": {"statuses": [{
            "context": "Secretary staging",
            "state": "success",
            "description": "Preview not applicable: no application/runtime files changed",
        }]},
    }


def staging_evidence(path, *, overrides=None):
    values = {
        "status": "passed",
        "environment": "staging",
        "source_sha": SOURCE_SHA,
        "backend_image_digest": IMAGE_DIGEST,
        "extension_zip_sha256": None,
        "extension_environment": "staging",
        "production_requests": 0,
        "production_writes": 0,
        "production_auth_requests": 0,
        "database": {
            "project_id": "patient-bird-25428852",
            "branch_id": "br-release-schema-123456",
            "production_branch_id": "br-production-123456",
            "branch_kind": "schema-only",
            "parent_id": None,
            "production_rows_present": False,
        },
        "auth": {"mode": "neon-auth", "enabled": True},
        "product": {
            "sign_in": True,
            "create": True,
            "list": True,
            "read": True,
            "update": True,
            "delete": True,
            "persistence_after_reload": True,
            "user_isolation": True,
            "ownership_checks": True,
            "cleanup": True,
        },
        "user_experience": {
            "loading": True,
            "success": True,
            "authentication_failure": True,
            "api_error": True,
            "timeout": True,
        },
        "ai_acceptance": {
            "status": "passed",
            "approved": True,
            "provider": "tfidf",
            "model_revision": "a" * 64,
            "evaluation_sha256": EVALUATION_SHA,
        },
        "evidence_path": str(path),
    }
    values.update(overrides or {})
    return values


class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive = self.root / "PhishLens-Staging-Extension.zip"
        auth_configs = {
            "production": {"enabled": True, "authUrl": "https://ep-production.neonauth.aws.neon.tech/phishlens/auth",
                           "database": "phishlens"},
            "staging": {"enabled": True, "authUrl": "https://ep-staging.neonauth.aws.neon.tech/phishlens/auth",
                        "database": "phishlens"},
        }
        hosts = [
            "https://phishlens-api-ocvt.onrender.com/*",
            "https://phishlens-staging.onrender.com/*",
            "https://ep-production.neonauth.aws.neon.tech/*",
            "https://ep-staging.neonauth.aws.neon.tech/*",
        ]
        public_key = json.loads((Path(__file__).resolve().parents[2] / "extension/manifest.json").read_text())["key"]
        extension_id = chrome_extension_id(public_key)
        api_origins = {
            "production": "https://phishlens-api-ocvt.onrender.com",
            "staging": "https://phishlens-staging.onrender.com",
        }
        embedded = {
            "source_commit": SOURCE_SHA,
            "production_default": True,
            "staging_selection": "popup.html?environment=staging",
            "api_origins": api_origins,
            "chrome_extension_id": extension_id,
            "expected_chrome_origin": "chrome-extension://" + extension_id,
            "host_permissions": hosts,
        }
        members = {
            "manifest.json": json.dumps({"key": public_key, "host_permissions": hosts}, sort_keys=True).encode(),
            "js/config.js": (
                'export const API_BASE_URLS = Object.freeze({"production":"https://phishlens-api-ocvt.onrender.com",'
                '"staging":"https://phishlens-staging.onrender.com"});\n'
                'export const API_BASE_URL = API_BASE_URLS.production;\n'
            ).encode(),
            "js/auth-config.js": (
                'export const AUTH_CONFIGS = Object.freeze({"production":{"enabled":true,'
                '"authUrl":"https://ep-production.neonauth.aws.neon.tech/phishlens/auth",'
                '"database":"phishlens","apiOrigin":"https://phishlens-api-ocvt.onrender.com",'
                '"origin":"https://ep-production.neonauth.aws.neon.tech"},"staging":{"enabled":true,'
                '"authUrl":"https://ep-staging.neonauth.aws.neon.tech/phishlens/auth",'
                '"database":"phishlens","apiOrigin":"https://phishlens-staging.onrender.com",'
                '"origin":"https://ep-staging.neonauth.aws.neon.tech"}});\n'
                'export const AUTH_CONFIG = AUTH_CONFIGS.production;\n'
            ).encode(),
        }
        embedded_bytes = json.dumps(embedded, sort_keys=True).encode()
        with ZipFile(self.archive, "w", ZIP_DEFLATED) as archive:
            for name, data in members.items():
                archive.writestr(name, data)
            archive.writestr("phishlens-build-evidence.json", embedded_bytes)
        self.extension_evidence = {
            "format": "phishlens-release-extension-v1",
            "archive_sha256": self.digest(self.archive),
            "source_commit": SOURCE_SHA,
            "production_default": True,
            "auth_enabled": True,
            "api_origins": api_origins,
            "auth_configs": auth_configs,
            "host_permissions": hosts,
            "extension_version": "0.1.0",
            "files_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in members.items()},
        }
        self.extension_evidence["files_sha256"]["phishlens-build-evidence.json"] = hashlib.sha256(embedded_bytes).hexdigest()
        self.extension_evidence["host_permissions"] = hosts
        self.extension_evidence["chrome_extension_id"] = extension_id
        self.staging_path = self.root / "staging-evidence.json"
        self.staging = staging_evidence(self.staging_path)
        self.staging["extension_zip_sha256"] = self.digest(self.archive)
        self.staging_path.write_text(json.dumps(self.staging), encoding="utf-8")
        self.changelog = self.root / "CHANGELOG.md"
        self.changelog.write_text("# Changelog\n\n## 1.2.3\n- Synthetic acceptance.\n", encoding="utf-8")
        self.manifest = {
            "format": "phishlens-release-v1",
            "release": {"version": "1.2.3", "tag": "v1.2.3"},
            "source": {"sha": SOURCE_SHA, "author": "source-author"},
            "backend": {
                "image": "ghcr.io/kendshhh/phishlens-api@" + IMAGE_DIGEST,
                "digest": IMAGE_DIGEST,
                "source_sha": SOURCE_SHA,
            },
            "extension": {
                "sha256": self.digest(self.archive),
                "version": "0.1.0",
            },
            "model": {
                "approved": True,
                "provider": "tfidf",
                "revision": "a" * 64,
                "evaluation_sha256": EVALUATION_SHA,
            },
            "auth": {"mode": "neon-auth", "enabled": True},
            "database": {
                "staging_branch_id": "br-release-schema-123456",
                "branch_kind": "schema-only",
                "production_rows_present": False,
                "staging_parent_id": None,
                "migration_revision": "0004_neon_auth_subject",
            },
            "staging_acceptance": {
                "status": "passed",
                "evidence_sha256": self.digest(self.staging_path),
            },
            "required_checks": {
                "candidate_sha": SOURCE_SHA,
                "tested_sha": PR_HEAD_SHA,
                "tree_sha": TREE_SHA,
                "candidate_tree_sha": TREE_SHA,
                "pull_request": 264,
                "author": "source-author",
                "checks": {
                    name: {
                        "state": "success", "tested_sha": PR_HEAD_SHA, "app_id": app_id,
                        "source": "commit_status" if name == "Secretary staging" else "check_run",
                    }
                    for name, app_id in REQUIRED_CHECKS.items()
                },
            },
            "approval": {
                "approved": True,
                "mechanism": "github-environment",
                "independent": True,
                "approved_by": "release-reviewer",
                "run_id": "123456789",
            },
            "failure_switch": {
                "promotion_enabled": True,
                "tested_fail_closed": True,
                "ai_kill_switch": "AI_ANALYSIS_ENABLED",
            },
            "changelog": {
                "path": str(self.changelog),
                "sha256": self.digest(self.changelog),
            },
            "external_production_config_attestation": "current",
        }

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def digest(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def validate(self, manifest=None, evidence=None):
        evidence = evidence or self.staging
        return validate_manifest(
            manifest or self.manifest,
            extension_zip=self.archive,
            extension_evidence=self.extension_evidence,
            staging_evidence=evidence,
            staging_evidence_path=self.staging_path,
            changelog_path=self.changelog,
            expected_sha=SOURCE_SHA,
        )

    def test_all_eight_exact_sha_required_statuses_pass(self):
        passed = check_required_statuses(check_runs(), SOURCE_SHA)
        self.assertEqual(passed["candidate_sha"], SOURCE_SHA)
        self.assertEqual(passed["tested_sha"], PR_HEAD_SHA)
        self.assertEqual(set(passed["checks"]), set(REQUIRED_CHECKS))
        self.assertEqual(passed["checks"]["Secretary staging"]["source"], "commit_status")

    def test_skipped_status_is_not_a_pass_for_promotion(self):
        with self.assertRaisesRegex(GateError, "expected completed/success"):
            check_required_statuses(check_runs("skipped"), SOURCE_SHA)

    def test_required_check_missing_wrong_app_wrong_sha_and_duplicate_fail_closed(self):
        payload = check_runs()
        payload["check_runs"]["check_runs"] = payload["check_runs"]["check_runs"][1:]
        with self.assertRaisesRegex(GateError, "successful exact-PR-SHA status"):
            check_required_statuses(payload, SOURCE_SHA)

        payload = check_runs()
        payload["check_runs"]["check_runs"][0]["app"]["id"] = 999
        with self.assertRaisesRegex(GateError, "wrong SHA or GitHub App"):
            check_required_statuses(payload, SOURCE_SHA)

        payload = check_runs()
        payload["check_runs"]["check_runs"][0]["head_sha"] = "f" * 40
        with self.assertRaisesRegex(GateError, "wrong SHA or GitHub App"):
            check_required_statuses(payload, SOURCE_SHA)

        payload = check_runs()
        first_run = payload["check_runs"]["check_runs"][0]
        payload["check_runs"]["check_runs"].append(dict(first_run))
        with self.assertRaisesRegex(GateError, "expected one latest exact-PR-SHA run"):
            check_required_statuses(payload, SOURCE_SHA)

    def test_failed_secretary_status_and_source_tree_mismatch_fail_closed(self):
        payload = check_runs()
        payload["statuses"]["statuses"][0]["state"] = "failure"
        with self.assertRaisesRegex(GateError, "successful exact-PR-SHA status"):
            check_required_statuses(payload, SOURCE_SHA)

        payload = check_runs()
        payload["pull_request"]["merge_tree_sha"] = "f" * 40
        with self.assertRaisesRegex(GateError, "tested source tree"):
            check_required_statuses(payload, SOURCE_SHA)

    def test_required_context_names_and_app_ids_are_pinned(self):
        self.assertEqual(REQUIRED_CHECKS, {
            "Backend checks": 15368,
            "Extension checks": 15368,
            "Staging integration": 15368,
            "CodeQL": 57789,
            "Secretary staging": 15368,
            "Deterministic AI Evaluation": 15368,
            "Dependency security": 15368,
            "Workflow lint": 15368,
        })

    def test_exact_extension_archive_and_sidecar_pass(self):
        digest = verify_release_extension_archive(self.archive, self.extension_evidence, SOURCE_SHA)
        self.assertEqual(digest, self.extension_evidence["archive_sha256"])

    def test_extension_archive_mismatch_fails(self):
        evidence = dict(self.extension_evidence, source_commit="d" * 40)
        with self.assertRaisesRegex(GateError, "source SHA"):
            verify_release_extension_archive(self.archive, evidence, SOURCE_SHA)

    def test_complete_manifest_passes_and_returns_bound_identities(self):
        result = self.validate()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["source_sha"], SOURCE_SHA)
        self.assertEqual(result["backend_image_digest"], IMAGE_DIGEST)
        self.assertEqual(result["staging_branch_id"], "br-release-schema-123456")

    def test_mutable_image_reference_is_rejected(self):
        candidate = json.loads(json.dumps(self.manifest))
        candidate["backend"]["image"] = "ghcr.io/kendshhh/phishlens-api:latest"
        with self.assertRaisesRegex(GateError, "immutable image digest"):
            self.validate(candidate)

    def test_disabled_or_unapproved_provider_blocks_release(self):
        candidate = json.loads(json.dumps(self.manifest))
        candidate["model"]["approved"] = False
        candidate["model"]["provider"] = "disabled"
        with self.assertRaisesRegex(GateError, "quality approval is not recorded"):
            self.validate(candidate)

    def test_schema_copy_of_production_data_blocks_release(self):
        bad = dict(self.staging)
        bad["database"] = dict(self.staging["database"], branch_kind="standard", production_rows_present=True)
        with self.assertRaisesRegex(GateError, "schema-only"):
            self.validate(evidence=bad)

    def test_missing_crud_ownership_or_user_isolation_blocks_release(self):
        bad = dict(self.staging)
        bad["product"] = dict(self.staging["product"], update=False, user_isolation=False)
        with self.assertRaisesRegex(GateError, "update"):
            self.validate(evidence=bad)

    def test_required_check_skip_and_missing_release_approval_block(self):
        candidate = json.loads(json.dumps(self.manifest))
        candidate["required_checks"]["checks"]["Secretary staging"]["state"] = "skipped"
        candidate["approval"]["approved"] = False
        with self.assertRaisesRegex(GateError, "Required check is not successful: Secretary staging"):
            self.validate(candidate)

    def test_changelog_digest_change_blocks_release(self):
        candidate = json.loads(json.dumps(self.manifest))
        candidate["changelog"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(GateError, "Changelog SHA-256"):
            self.validate(candidate)

    def test_manifest_cannot_choose_its_own_staging_evidence_file(self):
        candidate = json.loads(json.dumps(self.manifest))
        candidate["staging_acceptance"]["evidence_sha256"] = "0" * 64
        candidate["staging_acceptance"]["evidence_path"] = str(self.changelog)
        with self.assertRaisesRegex(GateError, "Staging evidence SHA-256"):
            self.validate(candidate)

    def test_unattested_production_runtime_auth_or_database_blocks_release(self):
        candidate = json.loads(json.dumps(self.manifest))
        candidate.pop("external_production_config_attestation")
        with self.assertRaisesRegex(GateError, "production Auth/database/runtime"):
            self.validate(candidate)

    def test_neon_preflight_requires_schema_only_attestation_and_root_branch(self):
        with self.assertRaisesRegex(NeonReleaseError, "attest"):
            verify_branch(project_id="patient-bird-25428852", branch_id="br-release-schema-123456",
                          production_branch_id="br-production-123456", schema_only_attestation="false")
        with self.assertRaisesRegex(NeonReleaseError, "independent root"):
            verify_branch(project_id="patient-bird-25428852", branch_id="br-release-schema-123456",
                          production_branch_id="br-production-123456", schema_only_attestation="true",
                          expected_parent_id="br-production-123456")
        with self.assertRaisesRegex(NeonReleaseError, "production Neon branch"):
            verify_branch(project_id="patient-bird-25428852", branch_id="br-production-123456",
                          production_branch_id="br-production-123456", schema_only_attestation="true")

    def test_staging_migration_target_rejects_production_and_unsafe_overrides(self):
        test_password = "synthetic-only"
        environment = {
            "STAGING_NEON_SCHEMA_ONLY_ATTESTATION": "true",
            "STAGING_NEON_PARENT_ID": "",
            "STAGING_NEON_BRANCH_ID": "br-release-schema-123456",
            "PRODUCTION_NEON_BRANCH_ID": "br-production-123456",
            "STAGING_NEON_EXPECTED_HOST": "ep-staging.ap-southeast-1.aws.neon.tech",
            "PRODUCTION_NEON_EXPECTED_HOST": "ep-production.ap-southeast-1.aws.neon.tech",
            "STAGING_NEON_DATABASE_NAME": "phishlens_dev",
            "STAGING_NEON_MIGRATION_ROLE": "neondb_owner",
            "STAGING_MIGRATION_DATABASE_URL": (
                "postgresql://neondb_owner:" + test_password
                + "@ep-staging.ap-southeast-1.aws.neon.tech/phishlens_dev?sslmode=require"
            ),
        }
        self.assertEqual(validate_target(environment), environment["STAGING_MIGRATION_DATABASE_URL"])
        unsafe = dict(environment, STAGING_MIGRATION_DATABASE_URL=environment["STAGING_MIGRATION_DATABASE_URL"].replace("ep-staging", "ep-production"))
        with self.assertRaisesRegex(ValueError, "host does not match"):
            validate_target(unsafe)
        unsafe = dict(environment, STAGING_MIGRATION_DATABASE_URL=environment["STAGING_MIGRATION_DATABASE_URL"] + "&options=-csearch_path%3Dpublic")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            validate_target(unsafe)

    def test_release_notes_publish_only_the_matching_candidate_section(self):
        changelog = "# Changelog\n\n## [0.1.0] - Candidate, not released\n\n- Exact notes.\n\n## [Unreleased]\n- Next work.\n"
        self.assertEqual(extract_notes(changelog, "0.1.0"), "# PhishLens v0.1.0\n\n- Exact notes.\n")
        with self.assertRaisesRegex(ValueError, "no matching"):
            extract_notes(changelog, "1.2.3")

    def test_protected_environments_require_reviewer_and_prevent_self_review(self):
        payload = {"name": "production", "protection_rules": [{
            "type": "required_reviewers", "reviewers": [{"type": "User", "id": 123}],
            "prevent_self_review": True,
        }]}
        self.assertTrue(validate_environment(payload, "production")["prevent_self_review"])
        with self.assertRaisesRegex(EnvironmentGateError, "reviewer"):
            validate_environment({"name": "production", "protection_rules": []}, "production")
        bad = json.loads(json.dumps(payload))
        bad["protection_rules"][0]["prevent_self_review"] = False
        with self.assertRaisesRegex(EnvironmentGateError, "self-review"):
            validate_environment(bad, "production")


if __name__ == "__main__":
    unittest.main()
