import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from sqlalchemy import UniqueConstraint

from backend.models import User

MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "migrations"
    / "versions"
    / "0004_neon_auth_subject.py"
)


def test_neon_auth_subject_is_nullable_and_uniquely_constrained():
    column = User.__table__.c.neon_auth_subject

    assert column.nullable is True
    unique_constraints = {
        constraint.name: constraint
        for constraint in User.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert "uq_users_neon_auth_subject" in unique_constraints
    assert [
        item.name
        for item in unique_constraints["uq_users_neon_auth_subject"].columns
    ] == ["neon_auth_subject"]


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        "migration_0004_neon_auth_subject",
        MIGRATION_PATH,
    )
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_migration_adds_nullable_subject_and_unique_constraint(monkeypatch):
    migration = _load_migration()
    add_column = Mock()
    create_unique_constraint = Mock()
    monkeypatch.setattr(
        migration,
        "op",
        SimpleNamespace(
            add_column=add_column,
            create_unique_constraint=create_unique_constraint,
        ),
        raising=False,
    )

    migration.upgrade()

    add_column.assert_called_once()
    args, _kwargs = add_column.call_args
    assert args[0] == "users"
    column = args[1]
    assert column.name == "neon_auth_subject"
    assert column.nullable is True
    assert column.type.length == 255
    create_unique_constraint.assert_called_once_with(
        "uq_users_neon_auth_subject",
        "users",
        ["neon_auth_subject"],
    )


def test_migration_downgrade_removes_constraint_and_subject(monkeypatch):
    migration = _load_migration()
    drop_constraint = Mock()
    drop_column = Mock()
    monkeypatch.setattr(
        migration,
        "op",
        SimpleNamespace(
            drop_constraint=drop_constraint,
            drop_column=drop_column,
        ),
        raising=False,
    )

    migration.downgrade()

    drop_constraint.assert_called_once_with(
        "uq_users_neon_auth_subject",
        "users",
        type_="unique",
    )
    drop_column.assert_called_once_with("users", "neon_auth_subject")
