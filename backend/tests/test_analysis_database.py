import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from psycopg import OperationalError
from psycopg.rows import dict_row

from backend.app import analysis_deadlines
from backend.app.analysis_deadlines import AnalysisDeadline, AnalysisTimeoutError
from backend.core import analysis_database


@pytest.fixture
def database_context(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(
        analysis_deadlines,
        "monotonic",
        lambda: clock[0],
    )

    connection = SimpleNamespace(
        execute=AsyncMock(),
        close=AsyncMock(),
    )
    connector = AsyncMock(return_value=connection)
    monkeypatch.setattr(
        analysis_database,
        "AsyncConnection",
        SimpleNamespace(connect=connector),
    )
    monkeypatch.setattr(
        analysis_database,
        "get_database_url",
        Mock(
            return_value=(
                "postgresql+psycopg://127.0.0.1/"
                "phishlens_s2_t1_test"
            )
        ),
    )

    return SimpleNamespace(
        clock=clock,
        deadline=AnalysisDeadline.start(),
        connection=connection,
        connector=connector,
    )


async def _use_connection(context):
    async with analysis_database.saved_analysis_connection(
        context.deadline
    ) as connection:
        assert connection is context.connection


@pytest.mark.parametrize(
    ("elapsed", "connect_seconds", "statement_ms"),
    [
        (0.0, 20, 20_000),
        (17.0, 3, 3_000),
    ],
)
def test_connection_uses_remaining_budget(
    database_context,
    elapsed,
    connect_seconds,
    statement_ms,
):
    context = database_context
    context.clock[0] += elapsed

    asyncio.run(_use_connection(context))

    context.connector.assert_awaited_once_with(
        conninfo="postgresql://127.0.0.1/phishlens_s2_t1_test",
        autocommit=False,
        row_factory=dict_row,
        connect_timeout=connect_seconds,
    )
    context.connection.execute.assert_awaited_once_with(
        "SELECT set_config('statement_timeout', %s, true)",
        (f"{statement_ms}ms",),
    )
    context.connection.close.assert_awaited_once()


def test_connection_closes_when_calling_code_fails(database_context):
    context = database_context

    async def fail_inside_connection():
        async with analysis_database.saved_analysis_connection(
            context.deadline
        ):
            raise ValueError("Synthetic caller failure")

    with pytest.raises(ValueError, match="Synthetic caller failure"):
        asyncio.run(fail_inside_connection())

    context.connection.close.assert_awaited_once()


def test_statement_setup_failure_closes_connection(database_context):
    context = database_context
    context.connection.execute.side_effect = OperationalError(
        "Synthetic setup failure"
    )

    with pytest.raises(OperationalError):
        asyncio.run(_use_connection(context))

    context.connection.close.assert_awaited_once()


def test_connect_failure_does_not_close_missing_connection(
    database_context,
):
    context = database_context
    context.connector.side_effect = OperationalError(
        "Synthetic connection failure"
    )

    with pytest.raises(OperationalError):
        asyncio.run(_use_connection(context))

    context.connection.close.assert_not_awaited()


def test_expired_budget_skips_connection(database_context):
    context = database_context
    context.clock[0] = 121.0

    with pytest.raises(AnalysisTimeoutError):
        asyncio.run(_use_connection(context))

    context.connector.assert_not_awaited()


def test_timeout_inside_connection_closes_it(
    database_context,
    monkeypatch,
):
    context = database_context
    monkeypatch.setattr(
        analysis_deadlines,
        "OPERATION_BUDGET_SECONDS",
        0.01,
    )

    async def wait_inside_connection():
        async with analysis_database.saved_analysis_connection(
            context.deadline
        ):
            await asyncio.Event().wait()

    with pytest.raises(AnalysisTimeoutError):
        asyncio.run(wait_inside_connection())

    context.connection.close.assert_awaited_once()


def test_timeout_while_connecting_returns_timeout(
    database_context,
    monkeypatch,
):
    context = database_context
    monkeypatch.setattr(
        analysis_deadlines,
        "OPERATION_BUDGET_SECONDS",
        0.01,
    )

    async def stalled_connect(**_kwargs):
        await asyncio.Event().wait()

    context.connector.side_effect = stalled_connect

    with pytest.raises(AnalysisTimeoutError):
        asyncio.run(_use_connection(context))

    context.connection.close.assert_not_awaited()