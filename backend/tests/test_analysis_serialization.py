from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.analysis_serialization import (
    saved_detail_from_record,
    saved_summary_from_record,
)
from backend.models import AnalyzedEmail


def test_new_analysis_serializes_for_detail_response():
    record = AnalyzedEmail(
        id=uuid4(),
        user_id=uuid4(),
        subject="",
        body="Verify your account today.",
        prediction="phishing",
        confidence=Decimal("0.9300"),
        risk_level="high",
        indicators=[
            {
                "type": "evidence",
                "detail": "Requests an account action",
                "quote": "Verify your account",
            }
        ],
        explanation="Tactics: Account urgency",
        notes=None,
        feedback=None,
        analysis_mode="real",
        analysis_provenance={"provider_mode": "gemini"},
        created_at=datetime(2026, 10, 20, 12, 0, tzinfo=UTC),
    )

    response = saved_detail_from_record(record).model_dump(mode="json")

    assert response["id"] == str(record.id)
    assert response["subject"] == ""
    assert response["body"] == record.body
    assert response["prediction"] == "phishing"
    assert response["confidence"] == 0.93
    assert response["risk_level"] == "high"
    assert response["threat_indicators"] == [
        {
            "type": "evidence",
            "detail": "Requests an account action",
            "quote": "Verify your account",
        }
    ]
    assert response["analysis_mode"] == "real"
    assert response["analysis_provenance"] == {"provider_mode": "gemini"}
    assert response["created_at"] == "2026-10-20T12:00:00Z"


def test_legacy_summary_omits_missing_indicator_quote():
    record = AnalyzedEmail(
        id=uuid4(),
        user_id=uuid4(),
        subject="Older saved email",
        body="Synthetic body",
        prediction=None,
        confidence=None,
        risk_level=None,
        indicators=[
            {
                "type": "legacy",
                "detail": "Older indicator without a quote",
            }
        ],
        explanation=None,
        created_at=datetime(2026, 10, 20, 12, 0, tzinfo=UTC),
    )

    response = saved_summary_from_record(record).model_dump(mode="json")

    assert response["prediction"] is None
    assert response["confidence"] is None
    assert response["risk_level"] is None
    assert response["threat_indicators"] == [
        {
            "type": "legacy",
            "detail": "Older indicator without a quote",
        }
    ]
    assert "body" not in response