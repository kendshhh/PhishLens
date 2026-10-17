"""Synthetic demo history, with lazy database initialization."""
from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.models import AnalyzedEmail, User

router = APIRouter(prefix="/api", tags=["History"])


def get_db():
    # Keep /health available when database configuration is missing or invalid.
    try:
        from backend.core.database import SessionLocal
        with SessionLocal() as session:
            yield session
    except (SQLAlchemyError, RuntimeError, ValueError):
        raise HTTPException(503, "History temporarily unavailable") from None


@router.get("/analyses", responses={503: {"description": "History temporarily unavailable"}})
def get_analyses(db: Annotated[Session, Depends(get_db)]):
    try:
        user = db.scalar(select(User).where(User.email == "demo@phishlens.test"))
        if user is None:
            return {"items": []}
        query = (select(AnalyzedEmail)
                 .where(AnalyzedEmail.user_id == user.id)
                 .order_by(AnalyzedEmail.created_at.desc(), AnalyzedEmail.id.desc())
                 .limit(100))
        analyses = db.scalars(query).all()
    except SQLAlchemyError:
        raise HTTPException(503, "History temporarily unavailable") from None

    return {"items": [{
        "id": str(analysis.id),
        "subject": analysis.subject,
        "prediction": analysis.prediction,
        "confidence": float(analysis.confidence) if analysis.confidence is not None else None,
        "risk_level": analysis.risk_level,
        "threat_indicators": analysis.indicators or [],
        "explanation": analysis.explanation,
        "created_at": analysis.created_at.astimezone(UTC).isoformat(),
    } for analysis in analyses]}
