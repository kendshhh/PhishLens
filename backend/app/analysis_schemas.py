"""Request and response models for saved analysis records."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_SUBJECT_LENGTH = 320
MAX_BODY_LENGTH = 30_000
MAX_NOTES_LENGTH = 2_000


class CreateSavedAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(default="", max_length=MAX_SUBJECT_LENGTH)
    body: str = Field(min_length=1, max_length=MAX_BODY_LENGTH)

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


class SavedAnalysisDetail(SavedAnalysisSummary):
    body: str
    notes: str | None
    feedback: Literal["none", "false_positive", "false_negative"] | None
    analysis_mode: Literal["mock", "real", "unknown"] | None
    analysis_provenance: dict[str, Any] | None = None


class SavedAnalysisList(BaseModel):
    items: list[SavedAnalysisSummary]