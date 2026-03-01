"""
Auth router — student login (credentials pre-created by admin via Google Form import).
Students CANNOT self-register.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from backend.core.config import settings
from backend.core.security import verify_password, create_access_token
from backend.core.database import get_student, update_last_login
from backend.core.deps import get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    full_name: str
    college: str
    team: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """
    Student login.
    Credentials must have been pre-created by admin (imported from Google Form).
    """
    # Check admin login first
    if body.username == settings.ADMIN_USERNAME and body.password == settings.ADMIN_PASSWORD:
        token = create_access_token({"sub": body.username, "is_admin": True,
                                     "full_name": "Admin", "college": "", "team": ""})
        return TokenResponse(access_token=token, username=body.username,
                             full_name="Admin", college="", team="")

    # Student login
    student = get_student(body.username)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not verify_password(body.password, student["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    update_last_login(body.username)
    token = create_access_token({
        "sub":       student["username"],
        "is_admin":  False,
        "full_name": student["full_name"],
        "college":   student["college"],
        "team":      student["team"],
    })
    return TokenResponse(
        access_token=token,
        username=student["username"],
        full_name=student["full_name"],
        college=student["college"],
        team=student["team"],
    )


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    """Return current user info from token."""
    return {
        "username":  user["sub"],
        "is_admin":  user.get("is_admin", False),
        "full_name": user.get("full_name", ""),
        "college":   user.get("college", ""),
        "team":      user.get("team", ""),
    }
