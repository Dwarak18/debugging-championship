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

from core.config import settings


# ── Password hashing (PBKDF2-SHA256, no external deps) ───────────────────────

_PBKDF2_ITERS = 150_000   # OWASP minimum is 120k; 260k was unnecessarily slow for a competition


def hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2-SHA256.
    
    Format: pbkdf2:sha256:{iterations}:{salt}:{hex-digest}
    Iteration count is stored in the hash so it can be changed without
    invalidating existing passwords.
    """
    salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PBKDF2_ITERS)
    return f"pbkdf2:sha256:{_PBKDF2_ITERS}:{salt}:{h.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored hash.
    
    Supports both the legacy 4-part format (pbkdf2:sha256:salt:hash) and
    the current 5-part format (pbkdf2:sha256:iterations:salt:hash).
    """
    try:
        parts = stored_hash.split(":", 4)
        if len(parts) == 5:
            # New format: pbkdf2:sha256:{iters}:{salt}:{hash}
            _, algo, iters_str, salt, expected = parts
            iterations = int(iters_str)
        elif len(parts) == 4:
            # Legacy format: pbkdf2:sha256:{salt}:{hash}
            _, algo, salt, expected = parts
            iterations = 260_000
        else:
            return False
        h = hashlib.pbkdf2_hmac(algo, password.encode(), salt.encode(), iterations)
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
