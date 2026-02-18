"""
Admin router — manage students pre-created from Google Form responses.

Endpoints:
  POST /api/admin/students/import   — bulk create from Google Form CSV/JSON
  POST /api/admin/students          — create single student
  GET  /api/admin/students          — list all students
  PUT  /api/admin/students/{u}/reset-password
  DELETE /api/admin/students/{u}    — deactivate student
  DELETE /api/admin/leaderboard     — wipe scores
"""

import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List

from webapp.core.security import hash_password
from webapp.core.database import (
    create_student, list_students, deactivate_student,
    reset_student_password, get_leaderboard
)
from webapp.core.deps import require_admin

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class StudentIn(BaseModel):
    username: str
    password: str
    full_name: str  = ""
    email: str      = ""
    college: str    = ""
    team: str       = ""


class BulkImportRow(BaseModel):
    username: str
    password: str
    full_name: str  = ""
    email: str      = ""
    college: str    = ""
    team: str       = ""


class BulkImportRequest(BaseModel):
    students: List[BulkImportRow]


class ResetPasswordRequest(BaseModel):
    new_password: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/students", status_code=201, dependencies=[Depends(require_admin)])
def create_one_student(body: StudentIn):
    """Create a single student account."""
    ok = create_student(
        username=body.username.strip(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        email=body.email,
        college=body.college,
        team=body.team,
    )
    if not ok:
        raise HTTPException(status_code=409, detail=f"Username or email already exists")
    return {"message": "Student created", "username": body.username}


@router.post("/students/import", dependencies=[Depends(require_admin)])
def bulk_import_students(body: BulkImportRequest):
    """
    Bulk import students from Google Form export (JSON format).

    Google Form → Sheets → Download as CSV → Convert to JSON list.
    Each item must have: username, password, full_name, email, college, team.

    Example payload:
    {
      "students": [
        {"username":"john_doe","password":"Pass@123","full_name":"John Doe",
         "email":"john@college.edu","college":"MIT","team":"Alpha"}
      ]
    }
    """
    created, skipped = [], []
    for s in body.students:
        ok = create_student(
            username=s.username.strip(),
            password_hash=hash_password(s.password),
            full_name=s.full_name,
            email=s.email,
            college=s.college,
            team=s.team,
        )
        (created if ok else skipped).append(s.username)

    return {
        "created": len(created),
        "skipped": len(skipped),
        "created_users": created,
        "skipped_users": skipped,
    }


@router.post("/students/import-csv", dependencies=[Depends(require_admin)])
async def import_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file exported from Google Sheets.

    Required columns: username, password, full_name, email, college, team
    (column order flexible — determined by header row)
    """
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")   # handle BOM from Excel/Sheets
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    required = {"username", "password"}
    if rows and not required.issubset(set(rows[0].keys())):
        raise HTTPException(
            status_code=422,
            detail=f"CSV must have columns: {required}. Found: {list(rows[0].keys())}"
        )

    created, skipped = [], []
    for row in rows:
        username = row.get("username", "").strip()
        password = row.get("password", "").strip()
        if not username or not password:
            skipped.append(username or "(empty)")
            continue
        ok = create_student(
            username=username,
            password_hash=hash_password(password),
            full_name=row.get("full_name", ""),
            email=row.get("email", ""),
            college=row.get("college", ""),
            team=row.get("team", ""),
        )
        (created if ok else skipped).append(username)

    return {
        "total_rows": len(rows),
        "created": len(created),
        "skipped": len(skipped),
        "created_users": created,
        "skipped_users": skipped,
    }


@router.get("/students", dependencies=[Depends(require_admin)])
def get_all_students():
    """List all students (active and inactive)."""
    return {"students": list_students(), "total": len(list_students())}


@router.put("/students/{username}/reset-password", dependencies=[Depends(require_admin)])
def reset_password(username: str, body: ResetPasswordRequest):
    """Reset a student's password."""
    if len(body.new_password) < 4:
        raise HTTPException(status_code=422, detail="Password too short")
    reset_student_password(username, hash_password(body.new_password))
    return {"message": f"Password reset for {username}"}


@router.delete("/students/{username}", dependencies=[Depends(require_admin)])
def deactivate(username: str):
    """Deactivate a student (they cannot login but scores are preserved)."""
    deactivate_student(username)
    return {"message": f"{username} deactivated"}


@router.delete("/leaderboard", dependencies=[Depends(require_admin)])
def reset_leaderboard():
    """Wipe all scores (keeps student accounts)."""
    import sqlite3
    from webapp.core.config import settings as cfg
    with sqlite3.connect(cfg.DB_PATH) as conn:
        conn.execute("DELETE FROM submissions")
        conn.execute(
            "UPDATE leaderboard SET total_score=0, section1=0, section2=0, section3=0, section4=0"
        )
    return {"message": "Leaderboard reset"}
