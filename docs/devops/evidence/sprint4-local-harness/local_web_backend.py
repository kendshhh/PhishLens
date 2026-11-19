"""Local test key retrieval substitute; application routes/inference/DB are real."""
import os
from pathlib import Path
from types import SimpleNamespace

from cryptography.hazmat.primitives import serialization
import uvicorn

from backend.app import auth
from backend.app.main import app

key = serialization.load_pem_public_key(Path(os.environ["WEB_TEST_PUBLIC_KEY"]).read_bytes())
auth.jwks_client = lambda base: SimpleNamespace(
    get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ["WEB_TEST_API_PORT"]),
                access_log=False, loop="backend.core.event_loop:new_event_loop")
