import json
import os
import socket
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from scripts.start_staging import (
    main,
    pin_ipv4_addresses,
    validate_hosted_database_urls,
    validate_owner_approved_target,
)

TARGET_CONFIG = json.loads(
    (Path(__file__).resolve().parents[2] / ".github/secretary.json").read_text(encoding="utf-8")
)
DATABASE_HOST = TARGET_CONFIG["staging_database_host"].replace(
    ".ap-southeast-1", "-pooler.ap-southeast-1"
)
DIRECT_DATABASE_HOST = TARGET_CONFIG["staging_database_host"]
DATABASE_URL = f"postgresql+psycopg://phishlens_staging_app:example-password@{DATABASE_HOST}/phishlens_dev?sslmode=require"
MIGRATION_URL = f"postgresql+psycopg://neondb_owner:owner-example-password@{DATABASE_HOST}/phishlens_dev?sslmode=require"
PRODUCTION_DATABASE_HOST = "ep-dawn-band-b37l1bil.c-4.ap-southeast-1.aws.neon.tech"
STAGING_BRANCH_ID = TARGET_CONFIG["staging_neon_branch_id"]
PRODUCTION_BRANCH_ID = "br-production-123456"
STAGING_PROJECT_ID = TARGET_CONFIG["staging_neon_project_id"]
PRODUCTION_PROJECT_ID = "patient-bird-123456"
STAGING_AUTH_URL = (
    f"https://{TARGET_CONFIG['staging_auth_host']}/"
    f"{TARGET_CONFIG['staging_auth_database']}/auth"
)


def validate_hosted_urls(runtime, migration, expected_host, app_role):
    return validate_hosted_database_urls(
        runtime, migration, expected_host, app_role,
        PRODUCTION_DATABASE_HOST, STAGING_PROJECT_ID, PRODUCTION_PROJECT_ID,
        STAGING_BRANCH_ID, PRODUCTION_BRANCH_ID,
    )


def ipv4_records(*addresses):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, 5432))
        for address in addresses
    ]


class HostedStagingIpv4Tests(unittest.TestCase):
    def test_startup_target_pin_rejects_a_different_branch(self):
        validate_owner_approved_target(
            DIRECT_DATABASE_HOST, STAGING_PROJECT_ID, STAGING_BRANCH_ID, STAGING_AUTH_URL
        )
        with self.assertRaisesRegex(SystemExit, "owner-approved Neon project and branch"):
            validate_owner_approved_target(
                DIRECT_DATABASE_HOST, STAGING_PROJECT_ID, "br-delicate-paper-b381z98i", STAGING_AUTH_URL
            )
        with self.assertRaisesRegex(SystemExit, "Auth URL differs"):
            validate_owner_approved_target(
                DIRECT_DATABASE_HOST, STAGING_PROJECT_ID, STAGING_BRANCH_ID,
                f"https://old.neonauth.c-4.ap-southeast-1.aws.neon.tech/{TARGET_CONFIG['staging_auth_database']}/auth",
            )

    def test_pins_ipv4_addresses_and_preserves_hostname_and_tls_options(self):
        resolved = ipv4_records("192.0.2.11", "192.0.2.12", "192.0.2.11")
        with patch("scripts.start_staging.socket.getaddrinfo", return_value=resolved) as lookup:
            pinned = pin_ipv4_addresses(make_url(DATABASE_URL))

        lookup.assert_called_once_with(
            DATABASE_HOST,
            5432,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
        self.assertEqual(pinned.host, f"{DATABASE_HOST},{DATABASE_HOST}")
        self.assertEqual(pinned.query["hostaddr"], "192.0.2.11,192.0.2.12")
        self.assertEqual(pinned.query["sslmode"], "require")

        engine = create_engine(pinned)
        _, arguments = engine.dialect.create_connect_args(engine.url)
        self.assertEqual(arguments["host"], f"{DATABASE_HOST},{DATABASE_HOST}")
        self.assertEqual(arguments["hostaddr"], "192.0.2.11,192.0.2.12")
        engine.dispose()

    def test_hosted_urls_require_same_staging_target_and_separate_roles(self):

        validate_hosted_urls(
            make_url(DATABASE_URL), make_url(MIGRATION_URL), DATABASE_HOST, "phishlens_staging_app"
        )

        with self.assertRaisesRegex(SystemExit, "phishlens_staging_app role"):
            validate_hosted_urls(
                make_url(MIGRATION_URL), make_url(MIGRATION_URL), DATABASE_HOST, "neondb_owner"
            )
        with self.assertRaisesRegex(SystemExit, "match the isolated STAGING_DATABASE_HOST"):
            validate_hosted_urls(
                make_url(DATABASE_URL),
                make_url(MIGRATION_URL.replace(DATABASE_HOST, "production.invalid")),
                DATABASE_HOST,
                "phishlens_staging_app",
            )
        with self.assertRaisesRegex(SystemExit, "owner credential"):
            validate_hosted_urls(
                make_url(DATABASE_URL),
                make_url(MIGRATION_URL.replace("neondb_owner:owner-example-password", "phishlens_staging_app:example-password")),
                DATABASE_HOST,
                "phishlens_staging_app",
            )

    def test_hosted_urls_reject_conninfo_injection_payloads_on_both_credentials(self):

        payloads = (
            (
                "user",
                "&sslmode%3Drequire%20user=neondb_owner",
                "&sslmode%3Drequire%20user=neondb_owner",
            ),
            (
                "dbname",
                "&application_name%3Dx%20dbname=neondb",
                "&application_name%3Dx%20dbname=neondb",
            ),
            (
                "options",
                "&sslmode%3Drequire%20options=-c%20role%3Dneondb_owner",
                "&sslmode%3Drequire%20options=-c%20role%3Dneondb_owner",
            ),
        )
        for field, runtime_payload, migration_payload in payloads:
            for credential, payload in (
                ("runtime", runtime_payload),
                ("migration", migration_payload),
            ):
                runtime = make_url(
                    DATABASE_URL + payload if credential == "runtime" else DATABASE_URL
                )
                migration = make_url(
                    MIGRATION_URL + payload if credential == "migration" else MIGRATION_URL
                )
                with self.subTest(field=field, credential=credential), self.assertRaisesRegex(
                    SystemExit, "unsupported query parameter"
                ):
                    validate_hosted_urls(
                        runtime, migration, DATABASE_HOST, "phishlens_staging_app"
                    )

    def test_hosted_urls_reject_case_encoded_and_repeated_identity_keys(self):

        invalid_queries = (
            "&user=neondb_owner",
            "&USER=neondb_owner",
            "&%75ser=neondb_owner",
            "&user=phishlens_staging_app&user=neondb_owner",
        )
        for credential in ("runtime", "migration"):
            for query in invalid_queries:
                runtime = make_url(
                    DATABASE_URL + query if credential == "runtime" else DATABASE_URL
                )
                migration = make_url(
                    MIGRATION_URL + query if credential == "migration" else MIGRATION_URL
                )
                with self.subTest(credential=credential, query=query), self.assertRaisesRegex(
                    SystemExit, "unsupported query parameter"
                ):
                    validate_hosted_urls(
                        runtime, migration, DATABASE_HOST, "phishlens_staging_app"
                    )

    def test_effective_driver_parameters_reject_conninfo_injection_without_connecting(self):
        from scripts.start_staging import _validate_effective_connection_identity

        payloads = (
            (
                "runtime-user",
                f"{DATABASE_URL}&sslmode%3Drequire%20user=neondb_owner",
                "runtime",
            ),
            (
                "migration-user",
                f"{MIGRATION_URL}&sslmode%3Drequire%20user=phishlens_staging_app",
                "migration",
            ),
            (
                "runtime-dbname",
                f"{DATABASE_URL}&application_name%3Dx%20dbname=neondb",
                "runtime",
            ),
            (
                "migration-dbname",
                f"{MIGRATION_URL}&application_name%3Dx%20dbname=neondb",
                "migration",
            ),
            (
                "runtime-options",
                f"{DATABASE_URL}&sslmode%3Drequire%20options=-c%20role%3Dneondb_owner",
                "runtime",
            ),
            (
                "migration-options",
                f"{MIGRATION_URL}&sslmode%3Drequire%20options=-c%20role%3Dneondb_owner",
                "migration",
            ),
        )
        for name, url, credential in payloads:
            with self.subTest(name=name), self.assertRaises(SystemExit):
                _validate_effective_connection_identity(make_url(url), credential)

    def test_hosted_startup_rejects_query_identity_overrides_before_dns_or_migration(self):
        cases = (
            (
                "runtime",
                f"{DATABASE_URL}&sslmode%3Drequire%20user=neondb_owner",
                MIGRATION_URL,
            ),
            (
                "migration",
                DATABASE_URL,
                f"{MIGRATION_URL}&application_name%3Dx%20dbname=neondb",
            ),
        )
        for credential, runtime_url, migration_url in cases:
            with self.subTest(credential=credential):
                with (
                    patch.dict(
                        os.environ,
                        {
                            "RENDER": "true",
                            "APP_ENV": "staging",
                            "REPORT_AUTH_MODE": "neon",
                            "NEON_AUTH_BASE_URL": STAGING_AUTH_URL,
                            "STAGING_DATABASE_HOST": DATABASE_HOST,
                            "STAGING_NEON_EXPECTED_HOST": DIRECT_DATABASE_HOST,
                            "STAGING_APP_DATABASE_ROLE": "phishlens_staging_app",
                            "PRODUCTION_NEON_EXPECTED_HOST": PRODUCTION_DATABASE_HOST,
                            "STAGING_NEON_PROJECT_ID": STAGING_PROJECT_ID,
                            "PRODUCTION_NEON_PROJECT_ID": PRODUCTION_PROJECT_ID,
                            "STAGING_NEON_BRANCH_ID": STAGING_BRANCH_ID,
                            "PRODUCTION_NEON_BRANCH_ID": PRODUCTION_BRANCH_ID,
                            "DATABASE_URL": runtime_url,
                            "STAGING_MIGRATION_DATABASE_URL": migration_url,
                        },
                        clear=True,
                    ),
                    patch("scripts.start_staging.get_database_url", return_value=runtime_url),
                    patch("scripts.start_staging.socket.getaddrinfo") as lookup,
                    patch("scripts.start_staging.subprocess.run") as run,
                    self.assertRaisesRegex(SystemExit, "unsupported query parameter"),
                ):
                    main()

                lookup.assert_not_called()
                run.assert_not_called()

    def test_direct_and_pooled_hosts_for_verified_staging_endpoint_are_allowed(self):

        direct_runtime = DATABASE_URL.replace(DATABASE_HOST, DIRECT_DATABASE_HOST)
        direct_migration = MIGRATION_URL.replace(DATABASE_HOST, DIRECT_DATABASE_HOST)
        validate_hosted_urls(
            make_url(direct_runtime), make_url(direct_migration), DIRECT_DATABASE_HOST,
            "phishlens_staging_app",
        )

    def test_matching_production_host_is_rejected_even_when_all_vars_agree(self):

        production_runtime = DATABASE_URL.replace(DATABASE_HOST, PRODUCTION_DATABASE_HOST)
        production_migration = MIGRATION_URL.replace(DATABASE_HOST, PRODUCTION_DATABASE_HOST)
        with self.assertRaisesRegex(SystemExit, "verified Neon staging endpoint"):
            validate_hosted_urls(
                make_url(production_runtime), make_url(production_migration),
                PRODUCTION_DATABASE_HOST, "phishlens_staging_app",
            )

    def test_fails_clearly_when_host_has_no_ipv4_address(self):
        with (
            patch("scripts.start_staging.socket.getaddrinfo", return_value=[]),
            self.assertRaisesRegex(SystemExit, "must resolve to an IPv4 address"),
        ):
            pin_ipv4_addresses(make_url(DATABASE_URL))

    def test_fails_clearly_when_ipv4_dns_lookup_fails(self):
        with (
            patch("scripts.start_staging.socket.getaddrinfo", side_effect=socket.gaierror("no A record")),
            self.assertRaisesRegex(SystemExit, "could not resolve an IPv4 address"),
        ):
            pin_ipv4_addresses(make_url(DATABASE_URL))

    def test_render_startup_passes_ipv4_routes_to_migrations_and_api(self):
        resolved = ipv4_records("192.0.2.11", "192.0.2.12")
        with (
            patch.dict(
                os.environ,
                {
                    "RENDER": "true",
                    "APP_ENV": "staging",
                    "REPORT_AUTH_MODE": "neon",
                    "NEON_AUTH_BASE_URL": STAGING_AUTH_URL,
                    "STAGING_DATABASE_HOST": DATABASE_HOST,
                    "STAGING_NEON_EXPECTED_HOST": DIRECT_DATABASE_HOST,
                    "STAGING_APP_DATABASE_ROLE": "phishlens_staging_app",
                    "PRODUCTION_NEON_EXPECTED_HOST": PRODUCTION_DATABASE_HOST,
                            "STAGING_NEON_PROJECT_ID": STAGING_PROJECT_ID,
                            "PRODUCTION_NEON_PROJECT_ID": PRODUCTION_PROJECT_ID,
                    "STAGING_NEON_BRANCH_ID": STAGING_BRANCH_ID,
                    "PRODUCTION_NEON_BRANCH_ID": PRODUCTION_BRANCH_ID,
                    "DATABASE_URL": DATABASE_URL,
                    "STAGING_MIGRATION_DATABASE_URL": MIGRATION_URL,
                    "PORT": "8123",
                },
                clear=True,
            ),
            patch("scripts.start_staging.get_database_url", return_value=DATABASE_URL),
            patch("scripts.start_staging.socket.getaddrinfo", return_value=resolved),
            patch("scripts.start_staging.subprocess.run") as run,
            patch("uvicorn.run") as uvicorn_run,
        ):
            main()

            self.assertEqual(run.call_count, 2)
            migration_environment = run.call_args_list[0].kwargs["env"]
            runtime_environment = run.call_args_list[1].kwargs["env"]
            migration_url = make_url(migration_environment["DATABASE_URL"])
            runtime_url = make_url(runtime_environment["DATABASE_URL"])
            self.assertEqual(migration_url.username, "neondb_owner")
            self.assertEqual(runtime_url.username, "phishlens_staging_app")
            self.assertNotIn("STAGING_MIGRATION_DATABASE_URL", migration_environment)
            self.assertNotIn("STAGING_MIGRATION_DATABASE_URL", runtime_environment)
            self.assertNotIn("STAGING_MIGRATION_DATABASE_URL", os.environ)
            self.assertEqual(migration_url.query["hostaddr"], "192.0.2.11,192.0.2.12")
            self.assertEqual(runtime_url.query["hostaddr"], "192.0.2.11,192.0.2.12")
            deployed = make_url(os.environ["DATABASE_URL"])
            self.assertEqual(deployed.host, f"{DATABASE_HOST},{DATABASE_HOST}")
            self.assertEqual(deployed.query["hostaddr"], "192.0.2.11,192.0.2.12")
            uvicorn_run.assert_called_once_with(
                "backend.app.main:app",
                host="0.0.0.0",
                port=8123,
                loop="backend.core.event_loop:new_event_loop",
            )


if __name__ == "__main__":
    unittest.main()
