"""Insert repeatable synthetic demo records into the configured development database."""

import sys
import uuid
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core.database import SessionLocal, engine  # noqa: E402
from backend.models import AnalyzedEmail, User  # noqa: E402


DEMO_EMAIL = "demo@phishlens.test"
DEMO_ANALYSIS_ID = uuid.UUID("29d80c39-ec0d-4db8-a6e5-87444ba2600c")


def main() -> None:
    if engine.url.database != "phishlens_dev":
        raise SystemExit("Refusing to seed: DATABASE_URL must point to phishlens_dev.")

    with SessionLocal.begin() as session:
        user = session.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(email=DEMO_EMAIL)
            session.add(user)
            session.flush()

        analysis = session.get(AnalyzedEmail, DEMO_ANALYSIS_ID)
        if analysis is None:
            session.add(
                AnalyzedEmail(
                    id=DEMO_ANALYSIS_ID,
                    user_id=user.id,
                    subject="Synthetic account notice",
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
    print("Synthetic demo user and analysis are present.")


if __name__ == "__main__":
    main()
