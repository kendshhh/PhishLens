"""Check the real client against FastAPI errors on a disposable loopback server."""

import json
import os
import secrets
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path
from unittest.mock import patch

import uvicorn

from backend.app.analysis_deadlines import AnalysisTimeoutError
from backend.app.analysis_execution import (
    AnalysisInferenceError,
    AnalysisUnavailableError,
)
from backend.app.analysis_persistence import AnalysisIdempotencyConflictError
from backend.app.main import app
from backend.app.routers import saved_create

ROOT = Path(__file__).resolve().parents[1]


def main():
    node = os.environ.get("NODE_BINARY") or shutil.which("node")
    if not node:
        raise SystemExit("Node is required for the client contract check")
    calls = []
    token = secrets.token_urlsafe(24)

    async def existing(_request, key, **_kwargs):
        if key == "contract-conflict":
            raise AnalysisIdempotencyConflictError("Synthetic conflict")

    async def fail(request, **_kwargs):
        errors = {
            "provider-failed": AnalysisInferenceError,
            "provider-unavailable": AnalysisUnavailableError,
            "provider-timeout": AnalysisTimeoutError,
            "unexpected-error": RuntimeError,
        }
        raise errors[request.subject]("Synthetic provider detail must not escape")

    async def observed(scope, receive, send):
        if scope["type"] == "http" and scope["path"] == "/__client_contract":
            body = json.dumps({"kind": "disposable-client-contract", "token": token}).encode()
            await send({"type": "http.response.start", "status": 200,
                        "headers": [(b"content-type", b"application/json")]})
            await send({"type": "http.response.body", "body": body})
            return
        if scope["type"] == "http":
            calls.append((scope["method"], scope["path"]))
        await app(scope, receive, send)

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(observed, log_level="critical", lifespan="off"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    with patch.object(saved_create, "get_database_url", return_value="synthetic-only"), \
            patch.object(saved_create, "get_ai_config", return_value=("mock", None, None)), \
            patch.object(saved_create, "find_idempotent_saved_analysis", side_effect=existing), \
            patch.object(saved_create, "create_saved_analysis", side_effect=fail):
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() >= deadline:
                    raise RuntimeError("Loopback server did not start")
                time.sleep(0.01)
            rejected = subprocess.run([node, str(ROOT / "scripts/verify_client_errors.mjs"),
                                       f"http://127.0.0.1:{port}", "x" * 32], cwd=ROOT,
                                      capture_output=True, check=False, timeout=60)
            assert rejected.returncode != 0 and not calls, "Wrong target identity allowed a POST"
            print("Wrong loopback handshake rejected before any POST")
            subprocess.run([node, str(ROOT / "scripts/verify_client_errors.mjs"),
                            f"http://127.0.0.1:{port}", token], cwd=ROOT, check=True, timeout=60)
            assert len(calls) == 8, calls
            assert all(call == ("POST", "/api/analyses") for call in calls), calls
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
    if thread.is_alive():
        raise RuntimeError("Loopback server did not stop")
    print(json.dumps({"result": "passed", "requests": len(calls), "database": "substitute",
                      "provider": "controlled substitute", "external_writes": False}))


if __name__ == "__main__":
    main()
