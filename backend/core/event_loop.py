"""Event-loop factory compatible with async PostgreSQL on Windows."""

import asyncio
import sys


def new_event_loop() -> asyncio.AbstractEventLoop:
    """Use Selector on Windows and the platform default elsewhere."""
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()

    return asyncio.new_event_loop()