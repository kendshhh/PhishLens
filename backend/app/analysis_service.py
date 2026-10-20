"""Create saved analyses through the shared AI service."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.ai.service import AIService
from backend.app.analysis_mapping import (
    ProviderMode,
    build_saved_analysis_fields,
)
from backend.app.analysis_schemas import CreateSavedAnalysis
from backend.models import AnalyzedEmail, User

DEMO_USER_EMAIL = "demo@phishlens.test"


class DemoUserUnavailableError(RuntimeError):
    """The server's synthetic demo account has not been prepared."""


def create_saved_analysis(
    session: Session,
    request: CreateSavedAnalysis,
    *,
    service: AIService,
    mode: ProviderMode,
) -> AnalyzedEmail:
    """Analyze an email, then commit one validated saved record."""

    # No database query or write has happened yet.
    result = service.analyze_email(
        subject=request.subject or None,
        sender=None,
        body=request.body,
    )
    saved_fields = build_saved_analysis_fields(
        result,
        mode=mode,
        subject=request.subject,
        body=request.body,
    )

    try:
        # The browser never chooses the owner of a saved record.
        user = session.scalar(
            select(User).where(User.email == DEMO_USER_EMAIL)
        )
        if user is None:
            raise DemoUserUnavailableError(
                "Synthetic demo user is unavailable"
            )

        record = AnalyzedEmail(
            user_id=user.id,
            subject=request.subject,
            body=request.body,
            **saved_fields,
        )
        session.add(record)

        # Send the INSERT and fetch generated fields such as created_at.
        session.flush()
        session.refresh(record)

        # Only a successful commit makes the saved record durable.
        session.commit()
        return record
    except Exception:
        # A failed query, INSERT, refresh, or commit must not leave an
        # unfinished transaction in this session.
        session.rollback()
        raise