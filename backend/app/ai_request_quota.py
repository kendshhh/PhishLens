"""Fail-closed shared request and daily-spend limits for Gemini inference."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from math import ceil

import psycopg

from backend.ai.spend_limit import GeminiRequestEstimate
from backend.core.config import get_database_url

logger = logging.getLogger("phishlens.ai.quota")


class AIQuotaConfigurationError(RuntimeError):
    """Gemini must remain unavailable until shared quota policy is configured."""


class AIQuotaStoreUnavailable(RuntimeError):
    """The shared quota store could not safely reserve usage."""


class AIQuotaExceeded(RuntimeError):
    """A configured request or daily spend limit has been reached."""

    def __init__(self, scope: str, retry_after_seconds: int) -> None:
        super().__init__("AI request limit reached")
        self.scope = scope
        self.retry_after_seconds = max(1, retry_after_seconds)


@dataclass(frozen=True)
class AIQuotaSettings:
    hmac_key: bytes
    requests_per_ip_per_minute: int
    requests_per_ip_per_day: int
    requests_per_user_per_day: int
    daily_spend_cap_usd: Decimal
    spend_alert_fraction: Decimal


@dataclass(frozen=True)
class AIQuotaReservation:
    input_token_upper_bound: int
    output_token_upper_bound: int
    cost_upper_bound_usd: Decimal
    daily_cost_reserved_usd: Decimal
    daily_spend_cap_usd: Decimal
    daily_budget_fraction: Decimal
    alert_threshold_crossed: bool


def _positive_integer(name: str) -> int:
    value = os.getenv(name, "").strip()
    if not value.isdecimal() or int(value) <= 0:
        raise AIQuotaConfigurationError(f"{name} must be a positive integer")
    return int(value)


def _positive_decimal(name: str) -> Decimal:
    try:
        value = Decimal(os.getenv(name, "").strip())
    except (InvalidOperation, ValueError):
        raise AIQuotaConfigurationError(f"{name} must be a positive decimal") from None
    if not value.is_finite() or value <= 0:
        raise AIQuotaConfigurationError(f"{name} must be a positive decimal")
    return value


def quota_settings_from_environment() -> AIQuotaSettings:
    """Load explicit per-environment limits; no paid-provider defaults are guessed."""
    raw_key = os.getenv("AI_QUOTA_HMAC_KEY", "").encode("utf-8")
    if len(raw_key) < 32:
        raise AIQuotaConfigurationError("AI_QUOTA_HMAC_KEY must contain at least 32 bytes")

    alert_fraction_raw = os.getenv("GEMINI_DAILY_SPEND_ALERT_FRACTION", "0.8").strip()
    try:
        alert_fraction = Decimal(alert_fraction_raw)
    except (InvalidOperation, ValueError):
        raise AIQuotaConfigurationError(
            "GEMINI_DAILY_SPEND_ALERT_FRACTION must be greater than 0 and at most 1"
        ) from None
    if not alert_fraction.is_finite() or not Decimal(0) < alert_fraction <= Decimal(1):
        raise AIQuotaConfigurationError(
            "GEMINI_DAILY_SPEND_ALERT_FRACTION must be greater than 0 and at most 1"
        )

    return AIQuotaSettings(
        hmac_key=raw_key,
        requests_per_ip_per_minute=_positive_integer("AI_REQUESTS_PER_IP_PER_MINUTE"),
        requests_per_ip_per_day=_positive_integer("AI_REQUESTS_PER_IP_PER_DAY"),
        requests_per_user_per_day=_positive_integer("AI_REQUESTS_PER_USER_PER_DAY"),
        daily_spend_cap_usd=_positive_decimal("GEMINI_DAILY_SPEND_CAP_USD"),
        spend_alert_fraction=alert_fraction,
    )


def _fingerprint(settings: AIQuotaSettings, scope: str, value: str) -> str:
    message = f"{scope}:{value}".encode()
    return hmac.new(settings.hmac_key, message, hashlib.sha256).hexdigest()


def _retry_after(now: datetime, scope: str) -> int:
    if scope == "ip_minute":
        boundary = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    else:
        boundary = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return max(1, ceil((boundary - now).total_seconds()))


def reserve_ai_request_quota(
    client_ip: str | None,
    *,
    user_id: str | None,
    estimate: GeminiRequestEstimate,
    now: datetime | None = None,
) -> AIQuotaReservation:
    """Atomically reserve IP/user requests and conservative daily Gemini spend.

    Raw IP addresses and user IDs are never stored. Database or configuration
    failures stop the paid-provider request rather than bypassing the limits.
    """
    settings = quota_settings_from_environment()
    if client_ip is None:
        raise AIQuotaConfigurationError("A client address is required for AI quotas")
    try:
        address = str(ipaddress.ip_address(client_ip.strip()))
    except ValueError:
        raise AIQuotaConfigurationError("A valid client address is required for AI quotas") from None

    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("Quota timestamps must be timezone-aware")
    current = current.astimezone(UTC)
    minute_start = current.replace(second=0, microsecond=0)
    day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    amount = estimate.cost_upper_bound_usd
    if not amount.is_finite() or amount <= 0:
        raise AIQuotaConfigurationError("A positive Gemini cost estimate is required")
    if amount > settings.daily_spend_cap_usd:
        raise AIQuotaExceeded("daily_spend", _retry_after(current, "daily_spend"))

    limits = [
        ("ip_minute", address, minute_start, settings.requests_per_ip_per_minute),
        ("ip_day", address, day_start, settings.requests_per_ip_per_day),
    ]
    if user_id is not None:
        normalized_user = str(user_id).strip()
        if not normalized_user:
            raise AIQuotaConfigurationError("A valid authenticated user is required")
        limits.append(
            ("user_day", normalized_user, day_start, settings.requests_per_user_per_day)
        )

    reserved_daily_spend = Decimal(0)
    try:
        conninfo = get_database_url().replace(
            "postgresql+psycopg://",
            "postgresql://",
            1,
        )
        with psycopg.connect(conninfo, connect_timeout=3) as connection:
            connection.execute("SET LOCAL lock_timeout = '1000ms'")
            connection.execute("SET LOCAL statement_timeout = '3000ms'")
            with connection.cursor() as cursor:
                for scope, identity, window_start, limit in limits:
                    cursor.execute(
                        """
                        INSERT INTO ai_request_quota_buckets
                            (scope, subject_hash, window_start, request_count)
                        VALUES (%s, %s, %s, 1)
                        ON CONFLICT (scope, subject_hash, window_start)
                        DO UPDATE SET
                            request_count = ai_request_quota_buckets.request_count + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE ai_request_quota_buckets.request_count < %s
                        RETURNING request_count
                        """,
                        (
                            scope,
                            _fingerprint(settings, scope, identity),
                            window_start,
                            limit,
                        ),
                    )
                    if cursor.fetchone() is None:
                        raise AIQuotaExceeded(scope, _retry_after(current, scope))

                cursor.execute(
                    """
                    INSERT INTO ai_request_quota_buckets
                        (scope, subject_hash, window_start, request_count, cost_upper_bound_usd)
                    VALUES ('daily_spend', %s, %s, 1, %s)
                    ON CONFLICT (scope, subject_hash, window_start)
                    DO UPDATE SET
                        request_count = ai_request_quota_buckets.request_count + 1,
                        cost_upper_bound_usd =
                            ai_request_quota_buckets.cost_upper_bound_usd
                            + EXCLUDED.cost_upper_bound_usd,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ai_request_quota_buckets.cost_upper_bound_usd
                        + EXCLUDED.cost_upper_bound_usd <= %s
                    RETURNING cost_upper_bound_usd
                    """,
                    (
                        _fingerprint(settings, "daily_spend", "gemini"),
                        day_start,
                        amount,
                        settings.daily_spend_cap_usd,
                    ),
                )
                spend_row = cursor.fetchone()
                if spend_row is None:
                    raise AIQuotaExceeded(
                        "daily_spend",
                        _retry_after(current, "daily_spend"),
                    )
                reserved_daily_spend = Decimal(spend_row[0])

                # Keep the shared bucket table bounded without a per-request full scan.
                if current.hour == 0 and current.minute < 5:
                    cursor.execute(
                        """
                        DELETE FROM ai_request_quota_buckets
                        WHERE window_start < %s
                        """,
                        (day_start - timedelta(days=2),),
                    )
    except AIQuotaExceeded:
        raise
    except Exception:  # noqa: BLE001 - fail closed for all storage/configuration errors
        raise AIQuotaStoreUnavailable(
            "Shared AI quota storage is unavailable"
        ) from None

    budget_fraction = reserved_daily_spend / settings.daily_spend_cap_usd
    alert_threshold_crossed = (
        reserved_daily_spend - amount
        < settings.daily_spend_cap_usd * settings.spend_alert_fraction
        <= reserved_daily_spend
    )
    if alert_threshold_crossed:
        logger.warning(
            json.dumps(
                {
                    "event": "ai_daily_spend_threshold",
                    "reserved_cost_upper_bound_usd": str(reserved_daily_spend),
                    "daily_spend_cap_usd": str(settings.daily_spend_cap_usd),
                    "budget_fraction": str(budget_fraction),
                    "alert_fraction": str(settings.spend_alert_fraction),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )

    return AIQuotaReservation(
        input_token_upper_bound=estimate.input_token_upper_bound,
        output_token_upper_bound=estimate.output_token_upper_bound,
        cost_upper_bound_usd=amount,
        daily_cost_reserved_usd=reserved_daily_spend,
        daily_spend_cap_usd=settings.daily_spend_cap_usd,
        daily_budget_fraction=budget_fraction,
        alert_threshold_crossed=alert_threshold_crossed,
    )
