from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_EVIDENCE_TEXT_LENGTH = 2_000


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(
        min_length=1, max_length=MAX_EVIDENCE_TEXT_LENGTH,
        description="Evidence supported by the supplied email text."
    )
    reason: str = Field(
        min_length=1, max_length=1_000,
        description="Why this evidence may indicate phishing."
    )


class AIAnalysisPayload(BaseModel):
    """Only these fields are requested from a generative model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    classification: Literal[
        "legitimate",
        "spam",
        "phishing",
    ]

    tactics: list[str] = Field(default_factory=list, max_length=12)

    evidence: list[EvidenceItem] = Field(
        default_factory=list, max_length=12,
    )

    recommendations: list[str] = Field(
        default_factory=list, max_length=12,
    )

    @field_validator("tactics", "recommendations")
    @classmethod
    def useful_strings(cls, values: list[str]) -> list[str]:
        if any(not v.strip() or len(v) > 1_000 for v in values):
            raise ValueError("Analysis items must contain 1 to 1000 characters")
        return [v.strip() for v in values]


class AIAnalysisResult(AIAnalysisPayload):
    """Provenance is assigned by the backend, never invented by the LLM."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, revalidate_instances="always")

    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    model: str | None = None
    model_revision: str | None = None
    prompt_version: str | None = None
    explanation_source: Literal["model", "rules", "mock"] | None = None
    input_truncated: bool | None = None
    windows_processed: int | None = Field(default=None, ge=1)
    phishing_score: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    raw_margin: float | None = Field(default=None, allow_inf_nan=False)
    alert_threshold_score: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    model_alert: bool | None = None
    assessment: str | None = Field(default=None, max_length=1000)


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=30_000)
    subject: str | None = Field(default=None, max_length=320)
    sender: str | None = Field(default=None, max_length=320)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Email text must not be blank")
        return value

    @field_validator("subject", "sender")
    @classmethod
    def blank_optional_fields_are_omitted(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value


class AnalysisResponse(AIAnalysisResult):
    risk_level: Literal["low", "medium", "high"]
    mode: Literal["mock", "gemini", "local", "tfidf"]


class AnalysisErrorField(BaseModel):
    field: Literal["text", "subject", "sender", "body"]
    code: Literal[
        "blank",
        "required",
        "too_long",
        "invalid_type",
        "unknown_field",
        "malformed_json",
        "invalid",
    ]


class AnalysisValidationErrorBody(BaseModel):
    code: Literal["invalid_input"]
    message: str
    fields: list[AnalysisErrorField] = Field(max_length=10)


class AnalysisValidationErrorResponse(BaseModel):
    error: AnalysisValidationErrorBody


class AnalysisFailureBody(BaseModel):
    code: Literal["inference_failed", "analysis_unavailable"]
    message: str


class AnalysisFailureResponse(BaseModel):
    error: AnalysisFailureBody
