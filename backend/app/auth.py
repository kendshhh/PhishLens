"""Neon JWT verification and server-owned report identity."""
import os
from functools import lru_cache
from urllib.parse import urlsplit

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.core import config
from backend.models import User


def auth_mode():
    # Keep the local demo default, but never silently expose hosted saved-report
    # routes without an explicit Render service setting.
    config.load_local_settings()
    mode = os.getenv("REPORT_AUTH_MODE", "" if config.is_render() else "demo").strip().lower()
    if mode not in {"demo", "neon"}:
        raise HTTPException(503, "Authentication configuration unavailable")
    return mode


@lru_cache(maxsize=4)
def jwks_client(base_url):
    return PyJWKClient(base_url + "/.well-known/jwks.json", timeout=5, lifespan=300)


def verify_identity(token):
    base = os.getenv("NEON_AUTH_BASE_URL", "").rstrip("/")
    try:
        parsed = urlsplit(base)
        port = parsed.port
        valid_url = (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and (port is None or 1 <= port <= 65535)
        )
    except (TypeError, ValueError):
        valid_url = False
    if not valid_url:
        raise HTTPException(503, "Authentication configuration unavailable")
    origin = f"https://{parsed.netloc}"
    try:
        key = jwks_client(base).get_signing_key_from_jwt(token)
        claims = jwt.decode(token, key.key, algorithms=["EdDSA"], issuer=origin, audience=origin,
                            options={"require": ["exp", "iat", "sub", "iss", "aud"]})
    except PyJWKClientConnectionError:
        raise HTTPException(503, "Authentication temporarily unavailable") from None
    except (PyJWTError, ValueError, TypeError):
        raise HTTPException(401, "Sign in to access saved reports", headers={"WWW-Authenticate": "Bearer"}) from None
    subject, email = claims.get("sub"), claims.get("email")
    if not isinstance(subject, str) or not 1 <= len(subject) <= 255:
        raise HTTPException(401, "Sign in to access saved reports", headers={"WWW-Authenticate": "Bearer"})
    # Require an explicit active value so missing or malformed status claims
    # cannot silently pass verification.
    if claims.get("emailVerified") is not True or claims.get("banned") is not False:
        raise HTTPException(403, "A verified, active account is required")
    if not isinstance(email, str) or not 3 <= len(email) <= 320 or "@" not in email:
        raise HTTPException(401, "Sign in to access saved reports", headers={"WWW-Authenticate": "Bearer"})
    return subject, email


def resolve_user(subject, email):
    # Never claim a legacy/demo account by matching its email.
    try:
        from backend.core.database import SessionLocal
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.neon_auth_subject == subject))
            if user is not None:
                return user.id
            user = User(neon_auth_subject=subject, email=email)
            db.add(user)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                winner = db.scalar(select(User).where(User.neon_auth_subject == subject))
                if winner is not None:
                    return winner.id
                raise HTTPException(409, "Account requires administrator review") from None
            return user.id
    except (SQLAlchemyError, RuntimeError, ValueError):
        raise HTTPException(503, "Account storage temporarily unavailable") from None


def report_owner(authorization: str | None = Header(default=None)):
    if auth_mode() == "demo":
        return None
    parts = (authorization or "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or len(parts[1]) > 16384:
        raise HTTPException(401, "Sign in to access saved reports", headers={"WWW-Authenticate": "Bearer"})
    return resolve_user(*verify_identity(parts[1]))
