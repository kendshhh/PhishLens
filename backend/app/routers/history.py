"""Synthetic demo history, with lazy database initialization."""

from datetime import UTC
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.analysis_schemas import (
    SavedAnalysisDetail,
    UpdateSavedAnalysis,
)
from backend.app.analysis_serialization import saved_detail_from_record
from backend.models import AnalyzedEmail, User

router = APIRouter(prefix="/api", tags=["History"])

DEMO_USER_EMAIL = "demo@phishlens.test"
HISTORY_UNAVAILABLE = "History temporarily unavailable"


def get_db():
    # Keep /health available when database configuration is missing or invalid.
    try:
        from backend.core.database import SessionLocal

        with SessionLocal() as session:
            yield session
    except (SQLAlchemyError, RuntimeError, ValueError):
        raise HTTPException(503, HISTORY_UNAVAILABLE) from None


@router.get(
    "/analyses",
    responses={503: {"description": HISTORY_UNAVAILABLE}},
)
def get_analyses(db: Annotated[Session, Depends(get_db)]):
    try:
        user = db.scalar(
            select(User).where(User.email == DEMO_USER_EMAIL)
        )
        if user is None:
            return {"items": []}

        query = (
            select(AnalyzedEmail)
            .where(AnalyzedEmail.user_id == user.id)
            .order_by(
                AnalyzedEmail.created_at.desc(),
                AnalyzedEmail.id.desc(),
            )
            .limit(100)
        )
        analyses = db.scalars(query).all()
    except SQLAlchemyError:
        raise HTTPException(503, HISTORY_UNAVAILABLE) from None

    return {
        "items": [
            {
                "id": str(analysis.id),
                "subject": analysis.subject,
                "prediction": analysis.prediction,
                "confidence": (
                    float(analysis.confidence)
                    if analysis.confidence is not None
                    else None
                ),
                "risk_level": analysis.risk_level,
                "threat_indicators": analysis.indicators or [],
                "explanation": analysis.explanation,
                "created_at": analysis.created_at.astimezone(UTC).isoformat(),
            }
            for analysis in analyses
        ]
    }


@router.get(
    "/analyses/{analysis_id}",
    response_model=SavedAnalysisDetail,
    responses={
        404: {"description": "Analysis not found"},
        503: {"description": HISTORY_UNAVAILABLE},
    },
)
def get_analysis(
    analysis_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> SavedAnalysisDetail:
    try:
        query = (
            select(AnalyzedEmail)
            .join(User)
            .where(
                User.email == DEMO_USER_EMAIL,
                AnalyzedEmail.id == analysis_id,
            )
        )
        record = db.scalar(query)
        if record is None:
            raise HTTPException(404, "Analysis not found")

        return saved_detail_from_record(record)
    except (SQLAlchemyError, ValidationError, ValueError):
        raise HTTPException(503, HISTORY_UNAVAILABLE) from None


@router.patch(
    "/analyses/{analysis_id}",
    response_model=SavedAnalysisDetail,
    responses={
        404: {"description": "Analysis not found"},
        503: {"description": HISTORY_UNAVAILABLE},
    },
)
def update_analysis(
    analysis_id: UUID,
    request: UpdateSavedAnalysis,
    db: Annotated[Session, Depends(get_db)],
) -> SavedAnalysisDetail:
    try:
        query = (
            select(AnalyzedEmail)
            .join(User)
            .where(
                User.email == DEMO_USER_EMAIL,
                AnalyzedEmail.id == analysis_id,
            )
            .with_for_update(of=AnalyzedEmail)
        )
        record = db.scalar(query)
        if record is None:
            raise HTTPException(404, "Analysis not found")

        changes = request.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(record, field, value)

        db.flush()

        # Validate the response before making the update permanent.
        response = saved_detail_from_record(record)
        db.commit()
        return response
    except (SQLAlchemyError, ValidationError, ValueError):
        db.rollback()
        raise HTTPException(503, HISTORY_UNAVAILABLE) from None


@router.delete(
    "/analyses/{analysis_id}",
    status_code=204,
    response_class=Response,
    responses={
        404: {"description": "Analysis not found"},
        503: {"description": HISTORY_UNAVAILABLE},
    },
)
def delete_analysis(
    analysis_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        query = (
            select(AnalyzedEmail)
            .join(User)
            .where(
                User.email == DEMO_USER_EMAIL,
                AnalyzedEmail.id == analysis_id,
            )
            .with_for_update(of=AnalyzedEmail)
        )
        record = db.scalar(query)
        if record is None:
            raise HTTPException(404, "Analysis not found")

        db.delete(record)
        db.commit()
        return Response(status_code=204)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, HISTORY_UNAVAILABLE) from None