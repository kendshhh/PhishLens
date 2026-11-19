"""One-off isolated local PostgreSQL verification; never uses a hosted target."""
import platform
import sys
import urllib.request
from datetime import UTC, datetime, timedelta
import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
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
backend_process = None
fixture = ROOT / "web-fixture.private.json"
public_file = ROOT / "web-test-public.pem"
try:
    run([BIN / "initdb.exe", "-D", DATA, "-U", "phishlens", "--pwprompt",
         "--auth=scram-sha-256", "--encoding=UTF8", "--no-locale"], "initdb.log",
        input_bytes=(PASSWORD + "\n" + PASSWORD + "\n").encode("ascii"), env={**ENV, "OSTYPE": "msys"})
    run([BIN / "pg_ctl.exe", "-D", DATA, "-l", EVIDENCE / "postgres.log", "-w", "-t", "30",
         "-o", f"-h 127.0.0.1 -p {PORT} -F", "start"], "start.log")
    started = True
    sql("postgres", "CREATE DATABASE phishlens_s2_t1_test;", "create-test-db.log")
    test_env = {**ENV, "DATABASE_URL": f"postgresql+psycopg://phishlens:{PASSWORD}@127.0.0.1:{PORT}/phishlens_s2_t1_test"}
    test_env["MIGRATIONS_DATABASE_URL"] = test_env["DATABASE_URL"]
    run([PYTHON, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"], "migration.log", test_env)
    private_key = Ed25519PrivateKey.generate()
    public_file.write_bytes(private_key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        api_port = listener.getsockname()[1]
    prefix = "web-local-" + uuid.uuid4().hex
    now = datetime.now(UTC)
    identities = []
    for name in ("a", "b"):
        subject = prefix + "-" + name
        email = subject + "@example.test"
        claims = {"sub": subject, "email": email, "emailVerified": True, "banned": False,
                  "iat": now, "exp": now + timedelta(hours=1), "iss": "https://auth.example.test", "aud": "https://auth.example.test"}
        identities.append({"sub": subject, "email": email, "name": "Synthetic " + name.upper(),
                           "token": jwt.encode(claims, private_key, algorithm="EdDSA")})
    fixture.write_text(json.dumps({"identities": identities, "sourceSha": RESULT["source_sha"],
                                  "apiOrigin": f"http://127.0.0.1:{api_port}", "expiresAt": (now + timedelta(hours=1)).isoformat()}), encoding="utf-8")
    api_env = {**test_env, "AI_MODE": "tfidf", "REPORT_AUTH_MODE": "neon", "NEON_AUTH_BASE_URL": "https://auth.example.test/test/auth",
               "SOURCE_COMMIT": RESULT["source_sha"], "PYTHONPATH": str(SOURCE), "WEB_TEST_PUBLIC_KEY": str(public_file), "WEB_TEST_API_PORT": str(api_port)}
    with (EVIDENCE / "api.log").open("wb") as api_log:
        backend_process = subprocess.Popen([str(PYTHON), str(ROOT / "local_web_backend.py")], cwd=SOURCE,
                                           env=api_env, stdout=api_log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        for attempt in range(60):
            if backend_process.poll() is not None:
                raise RuntimeError("Local backend exited; see redacted local log")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{api_port}/health", timeout=1) as response:
                    assert response.status == 200
                break
            except OSError:
                time.sleep(0.25)
        else:
            raise RuntimeError("Local backend did not become healthy")
        try:
            run(["node", ROOT / "local_web_browser.mjs"], "browser.log", api_env, timeout=150)
        finally:
            sql("phishlens_s2_t1_test", f"DELETE FROM users WHERE neon_auth_subject IN ('{prefix}-a','{prefix}-b');", "mapping-cleanup.log")
            counts = sql("phishlens_s2_t1_test", "SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM analyzed_emails);", "final-counts.log")
            assert counts == "0|0"
            RESULT["cleanup_counts"] = counts
    RESULT["status"] = "passed"
finally:
    if backend_process and backend_process.poll() is None:
        backend_process.terminate()
        backend_process.wait(timeout=15)
    if started or (DATA / "postmaster.pid").exists():
        run([BIN / "pg_ctl.exe", "-D", DATA, "-m", "fast", "-w", "stop"], "stop.log")
        RESULT["postgres_stopped"] = True
    fixture.unlink(missing_ok=True)
    public_file.unlink(missing_ok=True)
    (ROOT / "web-postgres-result.json").write_text(json.dumps(RESULT, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": str(EVIDENCE), "status": RESULT.get("status", "failed"), "cleanup": RESULT.get("cleanup_counts")}, indent=2))

