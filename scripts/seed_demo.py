"""Ensure the fixed synthetic demo record and its expected subject are present."""

import sys
import uuid
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.models import AnalyzedEmail, User

DEMO_EMAIL = "demo@phishlens.test"
DEMO_ANALYSIS_ID = uuid.UUID("29d80c39-ec0d-4db8-a6e5-87444ba2600c")
DEMO_SUBJECT = "Synthetic account notice"


def ensure_demo_records(session_factory, *, database_name: str) -> None:
    if database_name != "phishlens_dev":
        raise SystemExit("Refusing to seed: DATABASE_URL must point to phishlens_dev.")

    with session_factory.begin() as session:
        user = session.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(email=DEMO_EMAIL)
            session.add(user)
            session.flush()
        if user.neon_auth_subject is not None:
            raise SystemExit("Refusing to seed: demo identity is linked to an Auth account.")

        analysis = session.get(AnalyzedEmail, DEMO_ANALYSIS_ID)
        if analysis is None:
            session.add(
                AnalyzedEmail(
                    id=DEMO_ANALYSIS_ID,
                    user_id=user.id,
                    subject=DEMO_SUBJECT,
                    body=(
                        "This is a made-up demonstration email. Review your account at "
                        "https://login.example.invalid/demo. Do not visit this link."
                    ),
                    prediction="phishing",
                    confidence=Decimal("0.9300"),
                    risk_level="high",
                    indicators=[{"type": "link", "detail": "Synthetic lookalike login link"}],
                    explanation="Demo only: the message requests an account action through a link.",
                    notes="Synthetic seed record; no real inbox data.",
                )
            )
        elif analysis.user_id != user.id:
            raise SystemExit("Refusing to seed: fixed demo record belongs to another user.")
        elif analysis.subject != DEMO_SUBJECT:
            analysis.subject = DEMO_SUBJECT


def main() -> None:
    from backend.core.database import SessionLocal, engine

    ensure_demo_records(SessionLocal, database_name=engine.url.database)
    print("Synthetic demo user and analysis are present with the expected subject.")


if __name__ == "__main__":
    main()
