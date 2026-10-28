import os
import uuid

import pytest

RUN_DATABASE_TESTS = os.getenv("RUN_DATABASE_TESTS") == "1"
RUN_SEED_INTEGRITY_TESTS = os.getenv("RUN_SEED_INTEGRITY_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_DATABASE_TESTS or not RUN_SEED_INTEGRITY_TESTS,
    reason=(
        "Seed integrity requires RUN_DATABASE_TESTS=1 and "
        "RUN_SEED_INTEGRITY_TESTS=1 against local phishlens_dev."
    ),
)


def test_seed_records_and_relationship():
    from sqlalchemy import select

    from backend.core.database import SessionLocal, engine
    from backend.models import AnalyzedEmail, User

    assert engine.url.host in {"localhost", "127.0.0.1"}, (
        "This read-only seed check must use local PostgreSQL."
    )
    assert engine.url.database == "phishlens_dev", (
        "This explicit seed-integrity test requires the local phishlens_dev database."
    )

    demo_analysis_id = uuid.UUID(
        "29d80c39-ec0d-4db8-a6e5-87444ba2600c"
    )

    with SessionLocal() as session:
        users = session.scalars(
            select(User).where(User.email == "demo@phishlens.test")
        ).all()

        analyses = session.scalars(
            select(AnalyzedEmail).where(
                AnalyzedEmail.id == demo_analysis_id
            )
        ).all()

        assert len(users) == 1
        assert len(analyses) == 1
        assert analyses[0].user_id == users[0].id
