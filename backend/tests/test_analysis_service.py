import os
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.ai.schemas import AIAnalysisResult
from backend.ai.service import AIService
from backend.app.analysis_schemas import CreateSavedAnalysis
from backend.app.analysis_service import (
    DEMO_USER_EMAIL,
    DemoUserUnavailableError,
    create_saved_analysis,
)
from backend.models import AnalyzedEmail, User


def test_failed_inference_never_touches_database():
    service = Mock(spec=AIService)
    service.analyze_email.side_effect = RuntimeError("Synthetic AI failure")
    session = Mock(spec=Session)

    with pytest.raises(RuntimeError, match="Synthetic AI failure"):
        create_saved_analysis(
            session,
            CreateSavedAnalysis(body="Synthetic email body"),
            service=service,
            mode="mock",
        )

    session.scalar.assert_not_called()
    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_missing_demo_user_never_commits():
    service = Mock(spec=AIService)
    service.analyze_email.return_value = AIAnalysisResult(
        classification="legitimate"
    )
    session = Mock(spec=Session)
    session.scalar.return_value = None

    with pytest.raises(DemoUserUnavailableError):
        create_saved_analysis(
            session,
            CreateSavedAnalysis(body="Synthetic email body"),
            service=service,
            mode="mock",
        )

    session.add.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_called_once()


@pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="Requires a disposable local PostgreSQL database",
)
def test_valid_analysis_is_committed_for_demo_user():
    from backend.core.database import engine

    # Refuse to write if this test points at a cloud or production database.
    assert engine.url.host in {"localhost", "127.0.0.1"}
    assert engine.url.database in {
        "phishlens_s2_t1_test",
        "phishlens_dev",
    }

    service = Mock(spec=AIService)
    service.analyze_email.return_value = AIAnalysisResult(
        classification="phishing",
        confidence=0.93,
        evidence=[
            {
                "text": "Verify your account",
                "reason": "Requests an account action",
            }
        ],
    )

    # The outer transaction lets us inspect the saved row, then remove all
    # changes made by this test, even though the service calls commit().
    with engine.connect() as connection:
        outer_transaction = connection.begin()
        session = Session(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            user = session.scalar(
                select(User).where(User.email == DEMO_USER_EMAIL)
            )
            if user is None:
                user = User(email=DEMO_USER_EMAIL)
                session.add(user)
                session.flush()

            record = create_saved_analysis(
                session,
                CreateSavedAnalysis(
                    subject="Synthetic notice",
                    body="Verify your account today.",
                ),
                service=service,
                mode="mock",
            )

            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as verification_session:
                saved = verification_session.get(
                    AnalyzedEmail, record.id
                )
                assert saved is not None
                assert saved.user_id == user.id
                assert saved.subject == "Synthetic notice"
                assert saved.prediction == "phishing"
                assert saved.risk_level == "high"
                assert saved.analysis_mode == "mock"
                assert saved.indicators == [
                    {
                        "type": "evidence",
                        "quote": "Verify your account",
                        "detail": "Requests an account action",
                    }
                ]
        finally:
            session.close()
            outer_transaction.rollback()