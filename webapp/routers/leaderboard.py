"""
Leaderboard router — view rankings, submit scores.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from webapp.core.database import get_leaderboard, upsert_score, get_submissions
from webapp.core.deps import get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ScoreSubmission(BaseModel):
    section: int           # 1–4
    score: float
    passed_tests: int
    total_tests: int
    time_taken: Optional[float] = 0.0


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/")
def leaderboard(limit: int = 50):
    """Public leaderboard — top N participants."""
    entries = get_leaderboard(limit=min(limit, 100))
    for i, row in enumerate(entries, 1):
        row["rank"] = i
    return {"leaderboard": entries, "count": len(entries)}


@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_score(body: ScoreSubmission, user: dict = Depends(get_current_user)):
    """Submit a test-run score for the authenticated participant."""
    if body.section not in (1, 2, 3, 4):
        raise HTTPException(status_code=422, detail="section must be 1–4")
    if not (0 <= body.score <= 420):
        raise HTTPException(status_code=422, detail="score out of range")

    upsert_score(
        username=user["sub"],
        section=body.section,
        score=body.score,
        passed=body.passed_tests,
        total=body.total_tests,
        time_taken=body.time_taken,
    )
    return {"message": "Score recorded", "section": body.section, "score": body.score}


@router.get("/me")
def my_scores(user: dict = Depends(get_current_user)):
    """Return all submissions for the current user."""
    return {"username": user["sub"], "submissions": get_submissions(user["sub"])}
