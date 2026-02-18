"""
JWT-based auth helpers.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import hashlib
import hmac
import base64

from webapp.core.config import settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(message: str) -> str:
    return _b64(
        hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    )


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """Create a simple signed JWT-like token (HS256)."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.API_TOKEN_EXPIRE_MINUTES
    )
    payload = {**data, "exp": expire.timestamp()}
    header  = _b64(b'{"alg":"HS256","typ":"JWT"}')
    body    = _b64(json.dumps(payload).encode())
    sig     = _sign(f"{header}.{body}")
    return f"{header}.{body}.{sig}"


def verify_token(token: str) -> Optional[dict]:
    """Verify token and return payload, or None if invalid/expired."""
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
