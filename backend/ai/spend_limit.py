"""Fail-closed Gemini token-cost bounds for requests and bounded evaluations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

MILLION = Decimal(1_000_000)
INPUT_RATE_ENV = "GEMINI_INPUT_USD_PER_MILLION_TOKENS"
OUTPUT_RATE_ENV = "GEMINI_OUTPUT_USD_PER_MILLION_TOKENS"
RATE_MODEL_ENV = "GEMINI_COST_MODEL_ID"


class SpendLimitConfigurationError(RuntimeError):
    """The paid provider must stay disabled until its spend guard is configured."""


class SpendLimitExceeded(RuntimeError):
    """A request would exceed its configured hard cost bound."""


def _positive_decimal(name: str, raw: str | None) -> Decimal:
    try:
        value = Decimal((raw or "").strip())
    except (InvalidOperation, ValueError):
        raise SpendLimitConfigurationError(f"{name} must be a positive decimal") from None
    if not value.is_finite() or value <= 0:
        raise SpendLimitConfigurationError(f"{name} must be a positive decimal")
    return value


@dataclass(frozen=True)
class GeminiRequestEstimate:
    input_token_upper_bound: int
    output_token_upper_bound: int
    cost_upper_bound_usd: Decimal


@dataclass(frozen=True)
class GeminiSpendPolicy:
    """A per-request ceiling, using configured model rates and conservative tokens."""

    cap_usd: Decimal
    input_usd_per_million_tokens: Decimal
    output_usd_per_million_tokens: Decimal
    model_id: str

    @classmethod
    def from_environment(cls, *, cap_variable: str, model_id: str) -> GeminiSpendPolicy:
        configured_model = os.getenv(RATE_MODEL_ENV, "").strip()
        if not model_id or configured_model != model_id:
            raise SpendLimitConfigurationError(
                f"{RATE_MODEL_ENV} must exactly match the selected Gemini model"
            )
        return cls(
            cap_usd=_positive_decimal(cap_variable, os.getenv(cap_variable)),
            input_usd_per_million_tokens=_positive_decimal(INPUT_RATE_ENV, os.getenv(INPUT_RATE_ENV)),
            output_usd_per_million_tokens=_positive_decimal(OUTPUT_RATE_ENV, os.getenv(OUTPUT_RATE_ENV)),
            model_id=model_id,
        )

    def estimate(
        self,
        *,
        contents: str,
        system_instruction: str | None,
        response_schema: dict | None,
        max_output_tokens: int,
    ) -> GeminiRequestEstimate:
        if not isinstance(max_output_tokens, int) or max_output_tokens <= 0:
            raise SpendLimitConfigurationError("Gemini output token maximum must be positive")

        # UTF-8 bytes are a conservative text-token upper bound (one byte per
        # token at worst). Include separate SDK fields and fixed wire overhead;
        # counting them again for Gemma is deliberately conservative.
        input_bytes = len(contents.encode("utf-8"))
        if system_instruction:
            input_bytes += len(system_instruction.encode("utf-8"))
        if response_schema:
            schema = json.dumps(response_schema, sort_keys=True, separators=(",", ":"))
            input_bytes += len(schema.encode("utf-8"))
        input_token_upper_bound = input_bytes + 1_024
        cost = (
            Decimal(input_token_upper_bound) * self.input_usd_per_million_tokens
            + Decimal(max_output_tokens) * self.output_usd_per_million_tokens
        ) / MILLION
        return GeminiRequestEstimate(
            input_token_upper_bound=input_token_upper_bound,
            output_token_upper_bound=max_output_tokens,
            cost_upper_bound_usd=cost,
        )

    def require_within_cap(self, estimate: GeminiRequestEstimate) -> None:
        if estimate.cost_upper_bound_usd > self.cap_usd:
            raise SpendLimitExceeded("Gemini request exceeds the configured USD spend cap")


@dataclass
class GeminiEvaluationBudget:
    """A bounded process-level budget for a finite AI smoke/evaluation run."""

    policy: GeminiSpendPolicy
    max_requests: int
    requests_reserved: int = 0
    cost_upper_bound_reserved_usd: Decimal = Decimal(0)

    @classmethod
    def from_environment(cls, *, expected_requests: int, model_id: str) -> GeminiEvaluationBudget:
        if expected_requests <= 0:
            raise SpendLimitConfigurationError("Expected Gemini request count must be positive")
        configured = os.getenv("GEMINI_MAX_REQUESTS", "").strip()
        if not configured.isdecimal() or int(configured) != expected_requests:
            raise SpendLimitConfigurationError(
                "GEMINI_MAX_REQUESTS must exactly match the evaluation's bounded request count"
            )
        return cls(
            policy=GeminiSpendPolicy.from_environment(
                cap_variable="GEMINI_PER_RUN_COST_CAP_USD",
                model_id=model_id,
            ),
            max_requests=expected_requests,
        )

    def reserve_request(self, **request) -> GeminiRequestEstimate:
        if self.requests_reserved >= self.max_requests:
            raise SpendLimitExceeded("Gemini evaluation request limit reached")
        estimate = self.policy.estimate(**request)
        if self.cost_upper_bound_reserved_usd + estimate.cost_upper_bound_usd > self.policy.cap_usd:
            raise SpendLimitExceeded("Gemini evaluation would exceed the configured USD spend cap")
        self.requests_reserved += 1
        self.cost_upper_bound_reserved_usd += estimate.cost_upper_bound_usd
        return estimate

    def summary(self) -> dict:
        return {
            "guard": "conservative_token_cost_upper_bound",
            "requests_reserved": self.requests_reserved,
            "max_requests": self.max_requests,
            "cost_upper_bound_reserved_usd": str(self.cost_upper_bound_reserved_usd.quantize(Decimal("0.000001"))),
            "per_run_cap_usd": str(self.policy.cap_usd.normalize()),
            "model_id": self.policy.model_id,
            "input_usd_per_million_tokens": str(self.policy.input_usd_per_million_tokens.normalize()),
            "output_usd_per_million_tokens": str(self.policy.output_usd_per_million_tokens.normalize()),
            "block_before_provider_call": True,
        }
