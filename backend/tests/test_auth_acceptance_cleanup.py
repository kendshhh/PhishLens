"""Opt-in cleanup SQL checks on a disposable loopback phishlens_dev only."""

import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_AUTH_CLEANUP_TESTS") != "1",
    reason="Requires explicit disposable localhost cleanup SQL test opt-in",
)
ROOT = Path(__file__).resolve().parents[2]


def test_cleanup_preview_refusal_and_exact_removal():
    dsn = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
    config = conninfo_to_dict(dsn)
    assert config.get("host") in {"localhost", "127.0.0.1"}
    assert config.get("dbname") == "phishlens_dev"
    assert shutil.which("psql"), "The opted-in cleanup test requires psql"
    subjects = ["cleanup-fixture-" + str(uuid4()) for _ in range(2)]
    ids = [uuid4(), uuid4()]
    report, baseline_user, baseline_report = uuid4(), uuid4(), uuid4()

    def script(name, *, authorize=None, user_a=None, allow_disposable="true"):
        args = ["psql", "-X", "-h", config["host"], "-p", config.get("port", "5432"),
                "-d", config["dbname"], "-v", "allow_disposable=" + allow_disposable,
                "-v", "account_a_subject=" + subjects[0], "-v", "account_b_subject=" + subjects[1],
                "-v", "account_a_user_id=" + str(user_a or ids[0]),
                "-v", "account_b_user_id=" + str(ids[1])]
        if config.get("user"):
            args += ["-U", config["user"]]
        if authorize is not None:
            args += ["-v", "authorize_cleanup=" + authorize]
        args += ["-f", str(ROOT / "scripts" / name)]
        environment = {**os.environ, "PGPASSWORD": config.get("password", "")}
        return subprocess.run(args, check=False, capture_output=True, text=True, env=environment, timeout=20)

    def remaining():
        with psycopg.connect(dsn) as db:
            return db.execute("SELECT count(*) FROM users WHERE id = ANY(%s)", (ids,)).fetchone()[0]

    try:
        with psycopg.connect(dsn) as db:
            for uid, subject in zip(ids, subjects, strict=True):
                db.execute("INSERT INTO users (id,email,neon_auth_subject) VALUES (%s,%s,%s)",
                           (uid, str(uid) + "@phishlens.test", subject))
            db.execute("INSERT INTO users (id,email) VALUES (%s,%s)",
                       (baseline_user, str(baseline_user) + "@phishlens.test"))
            db.execute("INSERT INTO analyzed_emails (id,user_id,subject,body) VALUES (%s,%s,%s,%s)",
                       (baseline_report, baseline_user, "Unrelated baseline", "Synthetic baseline"))
            db.execute("INSERT INTO analyzed_emails (id,user_id,subject,body) VALUES (%s,%s,%s,%s)",
                       (report, ids[0], "Synthetic fixture", "Synthetic fixture"))
        assert script("auth_cleanup_preview.sql").returncode == 0
        assert remaining() == 2
        assert script("auth_cleanup_preview.sql", allow_disposable="false").returncode == 3
        assert script("auth_cleanup_apply.sql").returncode == 3
        assert script("auth_cleanup_apply.sql", authorize="false").returncode == 3
        assert script("auth_cleanup_apply.sql", authorize="true").returncode == 3
        assert remaining() == 2
        with psycopg.connect(dsn) as db:
            db.execute("DELETE FROM analyzed_emails WHERE id=%s", (report,))
        assert script("auth_cleanup_apply.sql", authorize="true", user_a=uuid4()).returncode == 3
        assert remaining() == 2
        result = script("auth_cleanup_apply.sql", authorize="true")
        assert result.returncode == 0, result.stderr
        assert remaining() == 0
        assert script("auth_cleanup_preview.sql").returncode == 0
        with psycopg.connect(dsn) as db:
            assert db.execute("SELECT count(*) FROM analyzed_emails WHERE id=%s",
                              (baseline_report,)).fetchone()[0] == 1
    finally:
        with psycopg.connect(dsn) as db:
            db.execute("DELETE FROM users WHERE id=ANY(%s)", (ids + [baseline_user],))
