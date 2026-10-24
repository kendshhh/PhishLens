"""Deadline-aware database connections for saved analysis creation."""

from asyncio import timeout
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from math import ceil
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from backend.app.analysis_deadlines import (
    AnalysisDeadline,
    AnalysisTimeoutError,
)
from backend.core.config import get_database_url


@asynccontextmanager
async def saved_analysis_connection(
    deadline: AnalysisDeadline,
) -> AsyncIterator[AsyncConnection[dict[str, Any]]]:
    """Open one connection within the remaining operation budget."""
    connection: AsyncConnection[dict[str, Any]] | None = None

    try:
        async with timeout(deadline.operation_remaining()):
            database_url = get_database_url().replace(
                "postgresql+psycopg://",
                "postgresql://",
                1,
            )
            connection = await AsyncConnection.connect(
                conninfo=database_url,
                autocommit=False,
                row_factory=dict_row,
                connect_timeout=max(
                    2,
                    ceil(deadline.operation_remaining()),
                ),
            )

            statement_timeout_ms = max(
                1,
                int(deadline.operation_remaining() * 1000),
            )
            await connection.execute(
                "SELECT set_config('statement_timeout', %s, true)",
                (f"{statement_timeout_ms}ms",),
            )

            yield connection
    except TimeoutError:
        raise AnalysisTimeoutError("Analysis deadline exceeded") from None
    finally:
        if connection is not None:
            await connection.close()