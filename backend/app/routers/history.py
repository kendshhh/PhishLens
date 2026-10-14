from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models import AnalyzedEmail, User

router = APIRouter(prefix="/api", tags=["History"])


@router.get("/analyses")
def get_analyses(db: Annotated[Session, Depends(get_db)]):
  
    user = db.scalar(
        select(User).where(User.email == "demo@phishlens.test")
    )

    if user is None:
        return {"items": []}

    query = select(AnalyzedEmail).where(
        AnalyzedEmail.user_id == user.id
    ).order_by(
        AnalyzedEmail.created_at.desc()
    ).limit(100)

    analyses = db.scalars(query).all()
    history = []

    for analysis in analyses:
        history.append({
            "id": str(analysis.id),
            "subject": analysis.subject,
            "prediction": analysis.prediction,
            "confidence": float(analysis.confidence)
                if analysis.confidence is not None else None,
            "risk_level": analysis.risk_level,
            "threat_indicators": analysis.indicators or [],
            "explanation": analysis.explanation,
            "created_at": analysis.created_at.isoformat()
        })

    return {"items": history}
