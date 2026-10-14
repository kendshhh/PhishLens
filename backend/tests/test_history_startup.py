"""Verify startup independently of modules cached by other tests."""
import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("database_url", ["", "invalid-database-url"])
def test_startup_without_usable_database(database_url):
    script = """
from unittest.mock import patch
with patch('dotenv.load_dotenv'):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    import sys
    assert 'backend.core.database' not in sys.modules
    with TestClient(app) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/ready').status_code == 503
        response = client.get('/api/analyses')
        assert response.status_code == 503
        assert response.json() == {'detail': 'History temporarily unavailable'}
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
