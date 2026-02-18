"""
Auth router — register, login, get profile.
"""

import hashlib
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from webapp.core.config import settings
from webapp.core.security import create_access_token
from webapp.core.database import register_participant, get_participant
from webapp.core.deps import get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    github: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str   # admin only; participants login with username


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    """Register a new participant and return an access token."""
    if not body.username or len(body.username) > 50:
        raise HTTPException(status_code=422, detail="Invalid username")

    created = register_participant(body.username.strip(), body.github.strip())
    if not created:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' already taken",
        )

    token = create_access_token({"sub": body.username, "is_admin": False})
    return TokenResponse(access_token=token, username=body.username)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """Admin login — returns a privileged token."""
    if (body.username != settings.ADMIN_USERNAME
            or body.password != settings.ADMIN_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token({"sub": body.username, "is_admin": True})
    return TokenResponse(access_token=token, username=body.username)


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    """Return current user info."""
    profile = get_participant(user["sub"])
    return {
        "username":  user["sub"],
        "is_admin":  user.get("is_admin", False),
        "profile":   profile,
    }
