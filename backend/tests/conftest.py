"""Shared test configuration. Database tests require explicit opt-in."""

import asyncio
import sys


def pytest_configure():
    """Use Psycopg-compatible event loops in Windows test processes."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )
