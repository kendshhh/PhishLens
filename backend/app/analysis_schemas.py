"""Request and response models for saved analysis records."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_SUBJECT_LENGTH = 320
MAX_BODY_LENGTH = 30_000
MAX_NOTES_LENGTH = 2_000


class LocalJudgeReport(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    valid: bool
    audit: Literal["supported", "unsupported", "uncertain"] | None = None
    quote: str | None = Field(default=None, min_length=1, max_length=160)
    reason_code: Literal["request_needs_verification", "protective_or_routine_context", "evidence_too_weak", "missing_context", "inconsistent_finding"] | None = None
    missing_context: bool | None = None
    model_id: str | None = Field(default=None, max_length=120)
    model_revision: str | None = Field(default=None, max_length=64)
    prompt_version: Literal["phishlens-live-judge-1"] | None = None
    seed_passed_to_runtime: bool | None = None
    code: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def complete_valid_report(self):
        if self.valid and any(getattr(self, key) is None for key in (
            "audit", "quote", "reason_code", "missing_context", "model_id", "model_revision", "prompt_version")):
            raise ValueError("A valid local judge report must be complete")
        if not self.valid and any(getattr(self, key) is not None for key in (
            "audit", "quote", "reason_code", "missing_context", "model_id", "model_revision", "prompt_version", "seed_passed_to_runtime")):
            raise ValueError("An unavailable audit may contain only its failure code")
        if self.valid and self.code is not None:
            raise ValueError("A usable audit cannot also claim failure")
        if self.missing_context and self.audit != "uncertain":
            raise ValueError("Missing context requires an uncertain audit")
        return self


class LocalModelCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["tfidf", "krr", "lightgbm"]
    model_id: str = Field(max_length=100)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_margin: float = Field(allow_inf_nan=False)
    score: float = Field(ge=0, le=1, allow_inf_nan=False)
    threshold_score: float = Field(ge=0, le=1, allow_inf_nan=False)
    cutoff: float = Field(allow_inf_nan=False)
    alert: bool
    valid: bool


class LocalReviewReport(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal["phishlens-live-review-1"]
    status: Literal["released", "uncertain"]
    primary_alert: bool
    judge: LocalJudgeReport
    reevaluators: list[LocalModelCheck] = Field(max_length=3)


class CreateSavedAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(default="", max_length=MAX_SUBJECT_LENGTH)
    body: str = Field(min_length=1, max_length=MAX_BODY_LENGTH)
    local_review: LocalReviewReport | None = Field(default=None, exclude_if=lambda v: v is None)

    @field_validator("body")
    @classmethod
    def check_body(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Body must not be blank")
        return value


class UpdateSavedAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(default=None, max_length=MAX_NOTES_LENGTH)
    feedback: Literal["none", "false_positive", "false_negative"] | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> "UpdateSavedAnalysis":
        if not self.model_fields_set.intersection({"notes", "feedback"}):
            raise ValueError("Provide notes or feedback")
        return self


class ThreatIndicator(BaseModel):
    type: str
    detail: str

    # Legacy indicators have no quote; omit it instead of sending quote: null.
    quote: str | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class SavedAnalysisSummary(BaseModel):
    id: UUID
    subject: str
    prediction: Literal["legitimate", "spam", "phishing"] | None
    confidence: float | None = Field(ge=0, le=1, allow_inf_nan=False)
    risk_level: Literal["low", "medium", "high", "critical"] | None
    threat_indicators: list[ThreatIndicator]
    explanation: str | None
    created_at: datetime
    review_status: Literal["released", "uncertain"] | None = Field(default=None, exclude_if=lambda v: v is None)


class SavedAnalysisDetail(SavedAnalysisSummary):
    body: str
    notes: str | None
    feedback: Literal["none", "false_positive", "false_negative"] | None
    analysis_mode: Literal["mock", "real", "unknown"] | None
    analysis_provenance: dict[str, Any] | None = None


class SavedAnalysisList(BaseModel):
    items: list[SavedAnalysisSummary]
