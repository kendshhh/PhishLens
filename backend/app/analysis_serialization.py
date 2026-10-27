"""Convert saved database rows into API response models."""

from datetime import UTC

from backend.app.analysis_schemas import (
    SavedAnalysisDetail,
    SavedAnalysisSummary,
)
from backend.models import AnalyzedEmail


def saved_summary_from_record(
    record: AnalyzedEmail,
) -> SavedAnalysisSummary:
    """Build the fields shared by list and detail responses."""

    if record.created_at is None or record.created_at.tzinfo is None:
        raise ValueError("Saved analysis timestamp must include a timezone")

    return SavedAnalysisSummary(
        id=record.id,
        subject=record.subject,
        prediction=record.prediction,
        confidence=(
            float(record.confidence)
            if record.confidence is not None
            else None
        ),
        risk_level=record.risk_level,
        threat_indicators=record.indicators or [],
        explanation=record.explanation,
        created_at=record.created_at.astimezone(UTC),
    )


def saved_detail_from_record(
    record: AnalyzedEmail,
) -> SavedAnalysisDetail:
    """Add fields needed when reading one saved record."""

    summary = saved_summary_from_record(record)

    return SavedAnalysisDetail(
        **summary.model_dump(),
        body=record.body,
        notes=record.notes,
        feedback=record.feedback,
        analysis_mode=record.analysis_mode,
        analysis_provenance=record.analysis_provenance,
    )