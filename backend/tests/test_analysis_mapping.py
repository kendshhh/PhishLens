import pytest

from backend.ai.schemas import AIAnalysisResult
from backend.app.analysis_mapping import build_saved_analysis_fields


def test_maps_valid_ai_result_to_saved_fields():
    result = AIAnalysisResult(
        classification="phishing",
        confidence=0.93,
        evidence=[
            {
                "text": "Verify your account",
                "reason": "Requests an account action",
            }
        ],
        tactics=["Account urgency"],
        recommendations=["Open the service directly"],
        model="synthetic-model",
        explanation_source="model",
    )

    fields = build_saved_analysis_fields(
        result,
        mode="gemini",
        subject="",
        body="Verify your account today.",
    )

    assert fields["prediction"] == "phishing"
    assert fields["confidence"] == 0.93
    assert fields["risk_level"] == "high"
    assert fields["indicators"] == [
        {
            "type": "evidence",
            "quote": "Verify your account",
            "detail": "Requests an account action",
        }
    ]
    assert fields["explanation"] == (
        "Tactics: Account urgency\n"
        "Recommendations: Open the service directly"
    )
    assert fields["analysis_mode"] == "real"
    assert fields["analysis_provenance"]["provider_mode"] == "gemini"
    assert fields["analysis_provenance"]["model"] == "synthetic-model"


def test_missing_confidence_stays_missing_for_saved_spam():
    result = AIAnalysisResult(
        classification="spam",
        confidence=None,
    )

    fields = build_saved_analysis_fields(
        result,
        mode="mock",
        subject="",
        body="Synthetic advertising email.",
    )

    assert fields["prediction"] == "spam"
    assert fields["confidence"] is None
    assert fields["risk_level"] == "medium"
    assert fields["analysis_mode"] == "mock"


def test_rejects_evidence_not_found_in_email():
    result = AIAnalysisResult(
        classification="phishing",
        evidence=[
            {
                "text": "Give us your password",
                "reason": "Requests a secret",
            }
        ],
    )

    with pytest.raises(ValueError, match="Unsupported evidence"):
        build_saved_analysis_fields(
            result,
            mode="local",
            subject="Synthetic notice",
            body="Please review your account.",
        )