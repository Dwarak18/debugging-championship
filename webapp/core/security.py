"""
Security helpers — password hashing and JWT-like tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import hashlib
import hmac
import base64
import os

from webapp.core.config import settings


# ── Password hashing (PBKDF2-SHA256, no external deps) ───────────────────────

def hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2-SHA256."""
    salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"pbkdf2:sha256:{salt}:{h.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    try:
        _, algo, salt, expected = stored_hash.split(":", 3)
        h = hashlib.pbkdf2_hmac(algo, password.encode(), salt.encode(), 260_000)
        return hmac.compare_digest(h.hex(), expected)
    except Exception:
        return False


# ── JWT-like tokens (HS256, no PyJWT needed) ─────────────────────────────────

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(message: str) -> str:
    return _b64(
        hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    )


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """Create a signed JWT-like token (HS256)."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.API_TOKEN_EXPIRE_MINUTES
    )
    payload = {**data, "exp": expire.timestamp()}
    header  = _b64(b'{"alg":"HS256","typ":"JWT"}')
    body    = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig     = _sign(f"{header}.{body}")
    return f"{header}.{body}.{sig}"


def verify_token(token: str) -> Optional[dict]:
    """Verify token signature and expiry. Returns payload or None."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        expected = _sign(f"{header}.{body}")
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            return None
        return payload
    except Exception:
        return None
