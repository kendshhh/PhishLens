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


class AnalysisIdempotencyConflictError(RuntimeError):
    """The same idempotency key was used for a different create request."""


_SAVED_ANALYSIS_COLUMNS = """
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

_SELECT_IDEMPOTENT_ANALYSIS = f"""
    SELECT {_SAVED_ANALYSIS_COLUMNS}
    FROM analyzed_emails
    WHERE user_id = %s AND idempotency_key = %s
"""

_SELECT_IDEMPOTENT_ANALYSIS_FOR_DEMO_USER = """
    SELECT a.id, a.user_id, a.subject, a.body, a.prediction, a.confidence,
        a.risk_level, a.indicators, a.explanation, a.notes, a.feedback,
        a.analysis_mode, a.analysis_provenance, a.created_at
    FROM analyzed_emails AS a
    JOIN users AS u ON u.id = a.user_id
    WHERE u.email = %s AND a.idempotency_key = %s
"""

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
        analysis_provenance,
        idempotency_key
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (user_id, idempotency_key) DO NOTHING
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
    idempotency_key: str | None = None,
) -> SavedAnalysisDetail:
    """Commit one validated record within the remaining operation budget."""
    deadline.inference_remaining()
    fields = build_saved_analysis_fields(
        result,
        mode=mode,
        subject=request.subject,
        body=request.body,
    )
    if request.local_review is not None:
        from backend.ai.live_review import review_request_sha, validate_local_review

        fields["analysis_provenance"]["local_review"] = validate_local_review(request.local_review, result, request.body)
        fields["analysis_provenance"]["local_review_request_sha256"] = review_request_sha(request.local_review)
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
                    idempotency_key,
                ),
            )
            row = await insert_cursor.fetchone()
            if row is None:
                if idempotency_key is not None:
                    replay_cursor = await connection.execute(
                        _SELECT_IDEMPOTENT_ANALYSIS,
                        (user["id"], idempotency_key),
                    )
                    replay = await replay_cursor.fetchone()
                    if replay is not None:
                        return _idempotent_replay(replay, request)
                raise AnalysisUnavailableError(
                    "Saved analysis storage unavailable"
                )

            response = saved_detail_from_record(AnalyzedEmail(**row))
            deadline.operation_remaining()
            await connection.commit()
            # Commit acknowledgement is the persistence success boundary. Do not
            # turn a confirmed save into a timeout response after this point.
            return response
    except QueryCanceled:
        raise AnalysisTimeoutError("Analysis deadline exceeded") from None


async def find_idempotent_saved_analysis(
    request: CreateSavedAnalysis,
    idempotency_key: str,
    *,
    deadline: AnalysisDeadline,
) -> SavedAnalysisDetail | None:
    """Return the prior committed result for a matching key, if present."""
    try:
        async with saved_analysis_connection(deadline) as connection:
            deadline.operation_remaining()
            cursor = await connection.execute(
                _SELECT_IDEMPOTENT_ANALYSIS_FOR_DEMO_USER,
                (DEMO_USER_EMAIL, idempotency_key),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return _idempotent_replay(row, request)
    except QueryCanceled:
        raise AnalysisTimeoutError("Analysis deadline exceeded") from None


def _idempotent_replay(row, request: CreateSavedAnalysis) -> SavedAnalysisDetail:
    if row["subject"] != request.subject or row["body"] != request.body:
        raise AnalysisIdempotencyConflictError(
            "Idempotency key was already used for a different request"
        )
    if request.local_review is not None or (row.get("analysis_provenance") or {}).get("local_review_request_sha256"):
        from backend.ai.live_review import review_request_sha

        if (row.get("analysis_provenance") or {}).get("local_review_request_sha256") != review_request_sha(request.local_review):
            raise AnalysisIdempotencyConflictError("Idempotency key belongs to another local review")
    return saved_detail_from_record(AnalyzedEmail(**row))
