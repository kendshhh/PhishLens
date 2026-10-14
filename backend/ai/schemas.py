from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EvidenceItem(BaseModel):
    text: str = Field(
        description="Evidence supported by the supplied email text."
    )
    reason: str = Field(
        description="Why this evidence may indicate phishing."
    )


class AIAnalysisResult(BaseModel):
    classification: Literal[
        "legitimate",
        "spam",
        "phishing",
    ]

    tactics: list[str] = Field(default_factory=list)

    evidence: list[EvidenceItem] = Field(
        default_factory=list
    )

    recommendations: list[str] = Field(
        default_factory=list
    )


class AnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=30_000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Email text must not be blank")
        return value


class AnalysisResponse(AIAnalysisResult):
    risk_level: Literal["low", "medium", "high"]
    mode: Literal["mock", "gemini"]