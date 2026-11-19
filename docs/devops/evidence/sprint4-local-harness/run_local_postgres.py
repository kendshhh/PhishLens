"""One-off isolated local PostgreSQL verification; never uses a hosted target."""
import platform
import hashlib
import json
import os
import pathlib
import secrets
import socket
import subprocess
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "source"
PYTHON = SOURCE / ".review-env/Scripts/python.exe"
BIN = pathlib.Path(os.environ["PHISHLENS_TEST_PG_BIN"]).resolve()
EVIDENCE = ROOT / ("postgres-" + uuid.uuid4().hex)
EVIDENCE.mkdir()
DATA = EVIDENCE / "data"
PASSWORD = secrets.token_hex(24)
with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0))
    PORT = listener.getsockname()[1]
ENV = {key: value for key, value in os.environ.items() if key not in {
    "DATABASE_URL", "MIGRATIONS_DATABASE_URL", "GEMINI_API_KEY", "GOOGLE_API_KEY",
    "NEON_AUTH_BASE_URL", "REPORT_AUTH_MODE", "SOURCE_COMMIT",
}}
ENV.update(PGPASSWORD=PASSWORD, PGHOST="127.0.0.1", PGPORT=str(PORT), PGUSER="phishlens",
           RUN_DATABASE_TESTS="1", AI_MODE="mock", PYTHONDONTWRITEBYTECODE="1",
           APP_ENV="development", REPORT_AUTH_MODE="demo")
ENV["PATH"] = str(BIN) + os.pathsep + ENV.get("PATH", "")
RESULT = {"source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip(),
          "scope": "local-only Sprint 4 web integration; no hosted request",
          "os": platform.platform(), "host": "127.0.0.1", "port": PORT, "commands": []}


def run(args, log, env=ENV, timeout=120, input_bytes=None):
    start = time.perf_counter()
    raw_log = EVIDENCE / (log + ".raw")
    with raw_log.open("wb") as stream:
        process = subprocess.run([str(a) for a in args], cwd=SOURCE, env=env,
                                 stdin=subprocess.DEVNULL if input_bytes is None else None, input=input_bytes, stdout=stream,
                                 stderr=subprocess.STDOUT, timeout=timeout,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
    output = raw_log.read_bytes().decode("utf-8", errors="replace").replace(PASSWORD, "[redacted]")
    (EVIDENCE / log).write_text(output, encoding="utf-8")
    RESULT["commands"].append({"command": [str(a).replace(PASSWORD, "[redacted]") for a in args],
                               "exit_code": process.returncode,
                               "elapsed_seconds": round(time.perf_counter() - start, 3),
                               "log": log})
    if process.returncode:
        raise RuntimeError(f"Local verification failed: {log}")
    return output.strip()


def sql(database, query, log):
    return run([BIN / "psql.exe", "-X", "-A", "-t", "-d", database,
                "-v", "ON_ERROR_STOP=1", "-c", query], log)


started = False
try:
    run([BIN / "initdb.exe", "-D", DATA, "-U", "phishlens", "--pwprompt",
         "--auth=scram-sha-256", "--encoding=UTF8", "--no-locale"], "initdb.log",
        input_bytes=(PASSWORD + "\n" + PASSWORD + "\n").encode("ascii"))
    run([BIN / "pg_ctl.exe", "-D", DATA, "-l", EVIDENCE / "postgres.log", "-w", "-t", "30",
         "-o", f"-h 127.0.0.1 -p {PORT} -F", "start"], "start.log")
    started = True
    RESULT["postgres_version"] = sql("postgres", "select version();", "version.log")
    sql("postgres", "CREATE DATABASE phishlens_s2_t1_test;", "create-test-db.log")
    sql("postgres", "CREATE DATABASE phishlens_dev;", "create-seed-db.log")
    test_env = {**ENV, "DATABASE_URL": f"postgresql+psycopg://phishlens:{PASSWORD}@127.0.0.1:{PORT}/phishlens_s2_t1_test"}
    test_env["MIGRATIONS_DATABASE_URL"] = test_env["DATABASE_URL"]
    run([PYTHON, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"], "migration-1.log", test_env)
    first_head = sql("phishlens_s2_t1_test", "SELECT version_num FROM alembic_version;", "head-1.log")
    run([PYTHON, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"], "migration-2.log", test_env)
    second_head = sql("phishlens_s2_t1_test", "SELECT version_num FROM alembic_version;", "head-2.log")
    assert first_head == second_head == "0004_neon_auth_subject"
    RESULT["migration_head_first"] = first_head
    RESULT["migration_head_second"] = second_head
    run([PYTHON, "-m", "pytest", "backend/tests", "scripts/tests", "-q", "-p", "no:cacheprovider",
         f"--junitxml={EVIDENCE / 'all-tests.xml'}"], "tests.log", test_env, timeout=240)
    counts = sql("phishlens_s2_t1_test", "SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM analyzed_emails);", "post-test-counts.log")
    RESULT["post_test_fixture_counts"] = counts
    assert counts == "0|0", "Test fixtures were not fully cleaned up"
    seed_env = {**ENV, "DATABASE_URL": f"postgresql+psycopg://phishlens:{PASSWORD}@127.0.0.1:{PORT}/phishlens_dev"}
    seed_env["MIGRATIONS_DATABASE_URL"] = seed_env["DATABASE_URL"]
    run([PYTHON, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"], "seed-migration.log", seed_env)
    snapshots = []
    for number in (1, 2):
        run([PYTHON, "scripts/seed_demo.py"], f"seed-{number}.log", seed_env)
        snapshot = sql("phishlens_dev", "SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM analyzed_emails), (SELECT subject FROM analyzed_emails WHERE id='29d80c39-ec0d-4db8-a6e5-87444ba2600c'), (SELECT neon_auth_subject IS NULL FROM users WHERE email='demo@phishlens.test');", f"seed-snapshot-{number}.log")
        fingerprint = sql("phishlens_dev", "SELECT md5(row_to_json(u)::text) FROM users u ORDER BY id; SELECT md5(row_to_json(a)::text) FROM analyzed_emails a ORDER BY id;", f"seed-fingerprint-{number}.log")
        snapshots.append({"summary": snapshot, "fingerprint_sha256": hashlib.sha256(fingerprint.encode()).hexdigest()})
    assert snapshots[0] == snapshots[1]
    assert snapshots[0]["summary"] == "1|1|Synthetic account notice|t"
    RESULT["seed_runs"] = snapshots
    optin_env = {**seed_env, "RUN_AUTH_CLEANUP_TESTS": "1", "RUN_SEED_INTEGRITY_TESTS": "1"}
    run([PYTHON, "-m", "pytest", "backend/tests/test_auth_acceptance_cleanup.py",
         "backend/tests/test_seed_integrity.py", "-q", "-p", "no:cacheprovider"],
        "separate-optin-tests.log", optin_env)
    after_optin = sql("phishlens_dev", "SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM analyzed_emails);", "after-optin-counts.log")
    assert after_optin == "1|1"
    RESULT["separate_optin_tests"] = "2 passed; seed and unrelated fixture preservation verified"
    RESULT["after_optin_seed_counts"] = after_optin
    run([BIN / "pg_dump.exe", "-Fc", "-d", "phishlens_dev", "-f", EVIDENCE / "synthetic.dump"], "dump.log")
    sql("postgres", "CREATE DATABASE phishlens_restore;", "create-restore-db.log")
    run([BIN / "pg_restore.exe", "--exit-on-error", "-d", "phishlens_restore", EVIDENCE / "synthetic.dump"], "restore.log")
    restored = sql("phishlens_restore", "SELECT version_num FROM alembic_version; SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM analyzed_emails); SELECT md5(row_to_json(u)::text) FROM users u ORDER BY id; SELECT md5(row_to_json(a)::text) FROM analyzed_emails a ORDER BY id;", "restore-check.log")
    original = sql("phishlens_dev", "SELECT version_num FROM alembic_version; SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM analyzed_emails); SELECT md5(row_to_json(u)::text) FROM users u ORDER BY id; SELECT md5(row_to_json(a)::text) FROM analyzed_emails a ORDER BY id;", "dump-source-check.log")
    assert restored == original
    RESULT["dump_restore"] = "full migration head, counts and row fingerprints match"
    RESULT["status"] = "passed"
finally:
    if started or (DATA / "postmaster.pid").exists():
        run([BIN / "pg_ctl.exe", "-D", DATA, "-m", "fast", "-w", "stop"], "stop.log")
        RESULT["postgres_stopped"] = True
    (ROOT / "local-postgres-result.json").write_text(json.dumps(RESULT, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": str(EVIDENCE), **{k: v for k, v in RESULT.items() if k != "commands"}}, indent=2))


