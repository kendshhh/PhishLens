"""Persist timely, validated inference using the async database connection."""

from uuid import uuid4

from psycopg.errors import QueryCanceled
from psycopg.types.json import Jsonb

from backend.ai.schemas import AIAnalysisResult
from backend.app.analysis_deadlines import (
    AnalysisDeadline,
    AnalysisTimeoutError,
)
from backend.app.analysis_execution import AnalysisUnavailableError
from backend.app.analysis_mapping import (
    ProviderMode,
    build_saved_analysis_fields,
)
from backend.app.analysis_schemas import CreateSavedAnalysis, SavedAnalysisDetail
from backend.app.analysis_serialization import saved_detail_from_record
from backend.core.analysis_database import saved_analysis_connection
from backend.models import AnalyzedEmail

DEMO_USER_EMAIL = "demo@phishlens.test"

_INSERT_ANALYSIS = """
    INSERT INTO analyzed_emails (
        id,
        user_id,
        subject,
        body,
        prediction,
        confidence,
        risk_level,
        indicators,
        explanation,
        analysis_mode,
        analysis_provenance
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING
        id,
        user_id,
        subject,
        body,
        prediction,
        confidence,
        risk_level,
        indicators,
        explanation,
        notes,
        feedback,
        analysis_mode,
        analysis_provenance,
        created_at
"""


async def persist_saved_analysis(
    request: CreateSavedAnalysis,
    result: AIAnalysisResult,
    *,
    mode: ProviderMode,
    deadline: AnalysisDeadline,
) -> SavedAnalysisDetail:
    """Commit one validated record within the remaining operation budget."""
    deadline.inference_remaining()
    fields = build_saved_analysis_fields(
        result,
        mode=mode,
        subject=request.subject,
        body=request.body,
    )
    deadline.inference_remaining()

    try:
        async with saved_analysis_connection(deadline) as connection:
            deadline.operation_remaining()
            user_cursor = await connection.execute(
                "SELECT id FROM users WHERE email = %s",
                (DEMO_USER_EMAIL,),
            )
            user = await user_cursor.fetchone()
            if user is None:
                raise AnalysisUnavailableError(
                    "Saved analysis storage unavailable"
                )

            deadline.operation_remaining()
            insert_cursor = await connection.execute(
                _INSERT_ANALYSIS,
                (
                    uuid4(),
                    user["id"],
                    request.subject,
                    request.body,
                    fields["prediction"],
                    fields["confidence"],
                    fields["risk_level"],
                    Jsonb(fields["indicators"]),
                    fields["explanation"],
                    fields["analysis_mode"],
                    Jsonb(fields["analysis_provenance"]),
                ),
            )
            row = await insert_cursor.fetchone()
            if row is None:
                raise AnalysisUnavailableError(
                    "Saved analysis storage unavailable"
                )

            response = saved_detail_from_record(AnalyzedEmail(**row))
            deadline.operation_remaining()
            await connection.commit()
            deadline.operation_remaining()
            return response
    except QueryCanceled:
        raise AnalysisTimeoutError("Analysis deadline exceeded") from None