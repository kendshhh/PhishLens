import os
import socket
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from scripts.start_staging import main, pin_ipv4_addresses

DATABASE_URL = "postgresql+psycopg://staging:example-password@ep-round-dew.c-4.ap-southeast-1.aws.neon.tech/phishlens_dev?sslmode=require"
DATABASE_HOST = "ep-round-dew.c-4.ap-southeast-1.aws.neon.tech"


def ipv4_records(*addresses):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, 5432))
        for address in addresses
    ]


class HostedStagingIpv4Tests(unittest.TestCase):
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
                    "STAGING_DATABASE_HOST": DATABASE_HOST,
                    "DATABASE_URL": DATABASE_URL,
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
