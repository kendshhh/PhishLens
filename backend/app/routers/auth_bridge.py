"""HTTPS browser context for Managed Neon Auth, embedded by the fixed extension."""

import os
import re
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from backend.app.auth import auth_mode
from backend.core.config import PROJECT_ROOT

router = APIRouter(prefix="/auth/bridge", include_in_schema=False)
EXTENSION_ORIGIN = "chrome-extension://ceneonaedddlkdocdapimkfggbjcchlb"
BRIDGE_SCRIPT = Path(__file__).resolve().parents[2] / "static" / "auth-bridge.js"


def bridge_settings(request: Request):
    if auth_mode() != "neon":
        raise HTTPException(503, "Account connection is unavailable")
    base = os.getenv("NEON_AUTH_BASE_URL", "").rstrip("/")
    try:
        parsed = urlsplit(base)
        valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
                 and not parsed.query and not parsed.fragment and parsed.port is None
                 and parsed.netloc == parsed.hostname
                 and re.fullmatch(r"[a-z0-9.-]+", parsed.netloc)
                 and re.fullmatch(r"/[A-Za-z0-9_-]{1,63}/auth", parsed.path))
    except ValueError:
        valid = False
    if not valid:
        raise HTTPException(503, "Account connection configuration is unavailable")
    # Render provides RENDER_EXTERNAL_URL. An explicit origin also supports a
    # custom API hostname and isolated local browser tests.
    origin = os.getenv("AUTH_BRIDGE_ORIGIN", os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")
    try:
        public = urlsplit(origin)
        valid = (public.scheme == "https" and public.hostname and not public.username and not public.password
                 and not public.path and not public.query and not public.fragment
                 and public.port in (None, 443) and str(request.base_url).rstrip("/") == origin)
    except ValueError:
        valid = False
    if not valid:
        raise HTTPException(503, "Account connection configuration is unavailable")
    headers = {
        "Cache-Control": "no-store",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": (
            "default-src 'none'; script-src 'self'; "
            f"connect-src https://{parsed.netloc}; "
            f"frame-ancestors {EXTENSION_ORIGIN}; base-uri 'none'; form-action 'none'"
        ),
    }
    return base, headers


@router.get("")
def bridge(request: Request):
    base, headers = bridge_settings(request)
    body = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<title>PhishLens account connection</title></head>'
        f'<body data-auth-url="{escape(base, quote=True)}" '
        f'data-extension-origin="{EXTENSION_ORIGIN}">'
        '<script type="module" src="/auth/bridge/client.js"></script></body></html>'
    )
    return HTMLResponse(body, headers=headers)


@router.get("/client.js")
def bridge_script(request: Request):
    _, headers = bridge_settings(request)
    return FileResponse(BRIDGE_SCRIPT, media_type="text/javascript", headers=headers)


@router.get("/sdk.mjs")
def bridge_sdk(request: Request):
    _, headers = bridge_settings(request)
    return FileResponse(PROJECT_ROOT / "extension/vendor/neon/sdk.mjs", media_type="text/javascript", headers=headers)
