"""Map validated AI output to fields for a saved analysis."""

from typing import Any, Literal

from backend.ai.schemas import AIAnalysisResult

ProviderMode = Literal["mock", "gemini", "local"]

RISK_BY_CLASSIFICATION = {
    "legitimate": "low",
    "spam": "medium",
    "phishing": "high",
}


def build_saved_analysis_fields(
    result: AIAnalysisResult,
    *,
    mode: ProviderMode,
    subject: str,
    body: str,
) -> dict[str, Any]:
    """Validate an AI result and prepare fields for AnalyzedEmail."""

    validated = AIAnalysisResult.model_validate(result)

    if mode not in ("mock", "gemini", "local"):
        raise ValueError("Unsupported provider mode")

    sources = [
        " ".join(value.split())
        for value in (subject, body)
        if value
    ]
    for item in validated.evidence:
        quote = " ".join(item.text.split())
        if not any(quote in source for source in sources):
            raise ValueError("Unsupported evidence")

    indicators = [
        {
            "type": "evidence",
            "quote": item.text,
            "detail": item.reason,
        }
        for item in validated.evidence
    ]

    explanation_parts = []
    if validated.tactics:
        explanation_parts.append("Tactics: " + "; ".join(validated.tactics))
    if validated.recommendations:
        explanation_parts.append(
            "Recommendations: " + "; ".join(validated.recommendations)
        )

    return {
        "prediction": validated.classification,
        "confidence": validated.confidence,
        "risk_level": RISK_BY_CLASSIFICATION[validated.classification],
        "indicators": indicators,
        "explanation": "\n".join(explanation_parts) or None,
        "analysis_mode": "mock" if mode == "mock" else "real",
        "analysis_provenance": {
            "provider_mode": mode,
            "model": validated.model,
            "model_revision": validated.model_revision,
            "prompt_version": validated.prompt_version,
            "explanation_source": validated.explanation_source,
            "input_truncated": validated.input_truncated,
            "windows_processed": validated.windows_processed,
        },
    }