from datetime import UTC, datetime
from decimal import Decimal

import pytest

from backend.ai.spend_limit import GeminiRequestEstimate
from backend.app import ai_request_quota as quota


def configure_limits(monkeypatch, **overrides):
    values = {
        "AI_QUOTA_HMAC_KEY": "test-only-hmac-secret-that-is-at-least-32-bytes",
        "AI_REQUESTS_PER_IP_PER_MINUTE": "5",
        "AI_REQUESTS_PER_IP_PER_DAY": "100",
        "AI_REQUESTS_PER_USER_PER_DAY": "30",
        "GEMINI_DAILY_SPEND_CAP_USD": "0.05",
        "GEMINI_DAILY_SPEND_ALERT_FRACTION": "0.8",
    }
    values.update(overrides)
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def estimate(cost="0.045"):
    return GeminiRequestEstimate(
        input_token_upper_bound=250,
        output_token_upper_bound=2048,
        cost_upper_bound_usd=Decimal(cost),
    )


class FakeCursor:
    def __init__(self, *, fail_scope=None, daily_total="0.045"):
        self.fail_scope = fail_scope
        self.daily_total = Decimal(daily_total)
        self.result = None
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        if "INSERT INTO ai_request_quota_buckets" not in query:
            return
        self.calls.append((query, params))
        if "VALUES ('daily_spend'" in query:
            self.result = (self.daily_total,)
        elif params[0] == self.fail_scope:
            self.result = None
        else:
            self.result = (1,)

    def fetchone(self):
        result = self.result
        self.result = None
        return result


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_args):
        self.committed = exc_type is None
        self.rolled_back = exc_type is not None
        return False

    def execute(self, *_args):
        return None

    def cursor(self):
        return self.fake_cursor


def install_fake_db(monkeypatch, connection):
    monkeypatch.setattr(
        quota,
        "get_database_url",
        lambda: "postgresql+psycopg://unit-test/unused",
    )
    monkeypatch.setattr(
        quota.psycopg,
        "connect",
        lambda *_args, **_kwargs: connection,
    )


def test_reservation_hashes_ip_and_user_and_logs_budget_threshold(monkeypatch, caplog):
    configure_limits(monkeypatch)
    cursor = FakeCursor(daily_total="0.045")
    connection = FakeConnection(cursor)
    install_fake_db(monkeypatch, connection)
    caplog.set_level("WARNING", logger="phishlens.ai.quota")

    reservation = quota.reserve_ai_request_quota(
        "203.0.113.24",
        user_id="synthetic-user-123",
        estimate=estimate(),
        now=datetime(2026, 11, 23, 12, 0, 30, tzinfo=UTC),
    )

    scopes = [params[0] for _, params in cursor.calls[:-1]]
    assert scopes == ["ip_minute", "ip_day", "user_day"]
    serialized_params = repr([params for _, params in cursor.calls])
    assert "203.0.113.24" not in serialized_params
    assert "synthetic-user-123" not in serialized_params
    for query, params in cursor.calls:
        fingerprint = params[0] if "VALUES ('daily_spend'" in query else params[1]
        assert len(fingerprint) == 64
    assert reservation.daily_budget_fraction == Decimal("0.9")
    assert reservation.alert_threshold_crossed is True
    assert connection.committed is True
    assert '"event":"ai_daily_spend_threshold"' in caplog.text


def test_request_limit_fails_closed_and_returns_retry_after(monkeypatch):
    configure_limits(monkeypatch)
    cursor = FakeCursor(fail_scope="ip_minute")
    connection = FakeConnection(cursor)
    install_fake_db(monkeypatch, connection)

    with pytest.raises(quota.AIQuotaExceeded) as caught:
        quota.reserve_ai_request_quota(
            "203.0.113.24",
            user_id=None,
            estimate=estimate(),
            now=datetime(2026, 11, 23, 12, 0, 30, tzinfo=UTC),
        )

    assert caught.value.scope == "ip_minute"
    assert caught.value.retry_after_seconds == 30
    assert connection.rolled_back is True


def test_missing_quota_configuration_blocks_before_database(monkeypatch):
    for name in (
        "AI_QUOTA_HMAC_KEY",
        "AI_REQUESTS_PER_IP_PER_MINUTE",
        "AI_REQUESTS_PER_IP_PER_DAY",
        "AI_REQUESTS_PER_USER_PER_DAY",
        "GEMINI_DAILY_SPEND_CAP_USD",
    ):
        monkeypatch.delenv(name, raising=False)
    called = False

    def connect(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("database should not be contacted")

    monkeypatch.setattr(quota.psycopg, "connect", connect)

    with pytest.raises(quota.AIQuotaConfigurationError):
        quota.reserve_ai_request_quota(
            "203.0.113.24",
            user_id=None,
            estimate=estimate(),
        )

    assert called is False


def test_daily_spend_limit_blocks_without_storing_an_over_cap_request(monkeypatch):
    configure_limits(monkeypatch, GEMINI_DAILY_SPEND_CAP_USD="0.01")
    called = False

    def connect(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("over-cap request must be rejected before storage")

    monkeypatch.setattr(quota.psycopg, "connect", connect)

    with pytest.raises(quota.AIQuotaExceeded) as caught:
        quota.reserve_ai_request_quota(
            "203.0.113.24",
            user_id=None,
            estimate=estimate("0.02"),
            now=datetime(2026, 11, 23, 12, 0, 30, tzinfo=UTC),
        )

    assert caught.value.scope == "daily_spend"
    assert called is False


def test_quota_storage_error_is_redacted_and_fails_closed(monkeypatch):
    configure_limits(monkeypatch)
    monkeypatch.setattr(
        quota,
        "get_database_url",
        lambda: "postgresql+psycopg://unit-test/unused",
    )

    def connect(*_args, **_kwargs):
        raise RuntimeError("private-host-and-password")

    monkeypatch.setattr(quota.psycopg, "connect", connect)

    with pytest.raises(quota.AIQuotaStoreUnavailable) as caught:
        quota.reserve_ai_request_quota(
            "203.0.113.24",
            user_id=None,
            estimate=estimate(),
        )

    assert str(caught.value) == "Shared AI quota storage is unavailable"
    assert "private-host-and-password" not in str(caught.value)
