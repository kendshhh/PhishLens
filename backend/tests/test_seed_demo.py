"""Exercise repeatable demo seeding and bounded subject reconciliation locally."""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.orm import sessionmaker

from backend.models import AnalyzedEmail, Base, User
from scripts import seed_demo


@pytest.fixture
def seed_db(tmp_path, monkeypatch):
    # JSONB storage is not under test; keep transaction/ownership checks offline.
    monkeypatch.setattr(SQLiteTypeCompiler, "visit_JSONB", SQLiteTypeCompiler.visit_JSON, raising=False)
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.sqlite'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine)
    yield sessions
    engine.dispose()


def test_reconciles_only_known_subject_and_remains_repeatable(seed_db):
    seed_demo.ensure_demo_records(seed_db, database_name="phishlens_dev")
    unrelated_id = uuid4()
    with seed_db.begin() as db:
        known = db.get(AnalyzedEmail, seed_demo.DEMO_ANALYSIS_ID)
        owner_id, created_at = known.user_id, known.created_at
        known.subject = "Temporary synthetic subject"
        known.notes = "Retain reviewed notes"
        known.prediction = "legitimate"
        db.add(AnalyzedEmail(id=unrelated_id, user_id=owner_id,
                            subject="Leave this subject alone", body="Synthetic other record"))
    seed_demo.ensure_demo_records(seed_db, database_name="phishlens_dev")
    seed_demo.ensure_demo_records(seed_db, database_name="phishlens_dev")
    with seed_db() as db:
        known = db.get(AnalyzedEmail, seed_demo.DEMO_ANALYSIS_ID)
        assert known.subject == seed_demo.DEMO_SUBJECT
        assert known.user_id == owner_id
        assert known.created_at == created_at
        assert known.notes == "Retain reviewed notes"
        assert known.prediction == "legitimate"
        assert db.get(AnalyzedEmail, unrelated_id).subject == "Leave this subject alone"
        assert len(db.scalars(select(AnalyzedEmail)).all()) == 2
        assert len(db.scalars(select(User)).all()) == 1


def test_refuses_fixed_id_owned_by_another_user_and_rolls_back(seed_db):
    with seed_db.begin() as db:
        other = User(email="other@phishlens.test")
        db.add(other)
        db.flush()
        db.add(AnalyzedEmail(id=seed_demo.DEMO_ANALYSIS_ID, user_id=other.id,
                            subject="Do not change", body="Synthetic unrelated owner"))
    with pytest.raises(SystemExit, match="belongs to another user"):
        seed_demo.ensure_demo_records(seed_db, database_name="phishlens_dev")
    with seed_db() as db:
        assert db.get(AnalyzedEmail, seed_demo.DEMO_ANALYSIS_ID).subject == "Do not change"
        assert db.scalar(select(User).where(User.email == seed_demo.DEMO_EMAIL)) is None


def test_refuses_auth_linked_demo_identity(seed_db):
    with seed_db.begin() as db:
        db.add(User(email=seed_demo.DEMO_EMAIL, neon_auth_subject="synthetic-subject"))
    with pytest.raises(SystemExit, match="linked to an Auth account"):
        seed_demo.ensure_demo_records(seed_db, database_name="phishlens_dev")
    with seed_db() as db:
        assert db.get(AnalyzedEmail, seed_demo.DEMO_ANALYSIS_ID) is None


def test_keeps_database_name_guard(seed_db):
    with pytest.raises(SystemExit, match="must point to phishlens_dev"):
        seed_demo.ensure_demo_records(seed_db, database_name="other_database")
    with seed_db() as db:
        assert db.scalars(select(User)).all() == []
