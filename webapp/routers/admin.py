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
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

from webapp.core.security import hash_password
from webapp.core.database import (
    create_student, list_students, deactivate_student,
    reset_student_password, get_leaderboard, reset_leaderboard as _db_reset_lb,
    set_section_timer, reset_section_timer, get_all_section_timers,
    update_github_username,
    pause_section_timer, resume_section_timer, stop_section_timer,
    list_anti_cheat_reports, get_anti_cheat_report,
    list_editor_activity_timeline,
)
from webapp.core.deps import require_admin

router = APIRouter()
web_router = APIRouter()


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


class GithubUsernameRequest(BaseModel):
    github_username: str


@router.put("/students/{username}/github", dependencies=[Depends(require_admin)])
def set_github_username(username: str, body: GithubUsernameRequest):
    """Set or update a student's GitHub username."""
    update_github_username(username, body.github_username.strip())
    return {"message": f"GitHub username set for {username}", "github_username": body.github_username.strip()}


@router.delete("/leaderboard", dependencies=[Depends(require_admin)])
def reset_leaderboard():
    """Wipe all scores (keeps student accounts)."""
    _db_reset_lb()
    return {"message": "Leaderboard reset"}


# ── Timer Management ─────────────────────────────────────────────────────────

class TimerRequest(BaseModel):
    section:          int
    duration_minutes: int  = 45
    start_now:        bool = True


@router.get("/timers", dependencies=[Depends(require_admin)])
def list_timers():
    """Return all section timer configurations."""
    return {"timers": get_all_section_timers()}


@router.post("/timers", dependencies=[Depends(require_admin)])
def set_timer(body: TimerRequest):
    """Start (or restart) the countdown timer for a section."""
    if body.section not in (1, 2, 3, 4):
        raise HTTPException(status_code=422, detail="section must be 1–4")
    set_section_timer(
        section=body.section,
        duration_minutes=body.duration_minutes,
        start_time=None if body.start_now else None,  # always NOW for now
    )
    return {"message": f"Timer started for section {body.section}",
            "duration_minutes": body.duration_minutes}


@router.delete("/timers/{section}", dependencies=[Depends(require_admin)])
def clear_timer(section: int):
    """Full reset — close section and lock downloads."""
    if section not in (1, 2, 3, 4):
        raise HTTPException(status_code=422, detail="section must be 1–4")
    reset_section_timer(section)
    return {"message": f"Timer reset for section {section}"}


@router.patch("/timers/{section}/pause", dependencies=[Depends(require_admin)])
def pause_timer(section: int):
    """Freeze the countdown without closing the section."""
    if section not in (1, 2, 3, 4):
        raise HTTPException(status_code=422, detail="section must be 1–4")
    pause_section_timer(section)
    return {"message": f"Timer paused for section {section}"}


@router.patch("/timers/{section}/resume", dependencies=[Depends(require_admin)])
def resume_timer(section: int):
    """Resume a paused timer from where it left off."""
    if section not in (1, 2, 3, 4):
        raise HTTPException(status_code=422, detail="section must be 1–4")
    resume_section_timer(section)
    return {"message": f"Timer resumed for section {section}"}


@router.patch("/timers/{section}/stop", dependencies=[Depends(require_admin)])
def stop_timer(section: int):
    """Close submissions for a section (download still allowed)."""
    if section not in (1, 2, 3, 4):
        raise HTTPException(status_code=422, detail="section must be 1–4")
    stop_section_timer(section)
    return {"message": f"Section {section} stopped — submissions closed"}


# ── Anti-cheat activity monitor ──────────────────────────────────────────────

@router.get("/activity-monitor", dependencies=[Depends(require_admin)])
def activity_monitor_data(limit: int = 200):
    """All submissions with anti-cheat fields for dashboard table."""
    rows = list_anti_cheat_reports(limit=min(max(limit, 1), 500), flagged_only=False)
    return {
        "submissions": [
            {
                "id": r["id"],
                "team": r.get("team_id", ""),
                "username": r.get("username", ""),
                "passed": r.get("tests_passed", 0),
                "total": 57,
                "runtime_seconds": r.get("runtime_seconds", 0),
                "risk_score": r.get("risk_score", 0),
                "risk_level": r.get("risk_level", "Low"),
                "duplicate_detected": r.get("duplicate_detected", False),
                "test_hash_valid": r.get("test_hash_valid", True),
                "suspicious_imports_count": len(r.get("suspicious_imports", []) or []),
                "paste_attempts": r.get("paste_attempts", 0),
                "large_injection_events": r.get("large_injection_events", 0),
                "typing_speed_cps": r.get("average_typing_speed_cps", 0),
                "copy_risk_score": r.get("copy_risk_score", 0),
                "tab_switches": r.get("tab_switches", 0),
                "window_blur_seconds": r.get("window_blur_seconds", 0),
                "last_submission_time": r.get("created_at"),
            }
            for r in rows
        ],
        "count": len(rows),
    }


@router.get("/activity-monitor/flagged", dependencies=[Depends(require_admin)])
def activity_monitor_flagged(limit: int = 200):
    """High-risk submissions only with full flag breakdown."""
    rows = list_anti_cheat_reports(limit=min(max(limit, 1), 500), flagged_only=True)
    return {
        "flagged": [
            {
                "id": r["id"],
                "team": r.get("team_id", ""),
                "username": r.get("username", ""),
                "risk_score": r.get("risk_score", 0),
                "risk_level": r.get("risk_level", "Low"),
                "risk_flags": r.get("risk_flags", []),
                "duplicate_detected": r.get("duplicate_detected", False),
                "duplicate_pair_hash": r.get("submission_hash", ""),
                "test_hash_valid": r.get("test_hash_valid", True),
                "suspicious_imports": r.get("suspicious_imports", []),
                "paste_attempts": r.get("paste_attempts", 0),
                "large_injection_events": r.get("large_injection_events", 0),
                "typing_speed_cps": r.get("average_typing_speed_cps", 0),
                "copy_risk_score": r.get("copy_risk_score", 0),
                "created_at": r.get("created_at"),
            }
            for r in rows
        ],
        "count": len(rows),
    }


@router.get("/activity-monitor/{report_id}", dependencies=[Depends(require_admin)])
def activity_monitor_detail(report_id: int):
    """Submission detail view with raw pytest output and risk explanation."""
    row = get_anti_cheat_report(report_id)
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    timeline_rows = list_editor_activity_timeline(team_id=row.get("team_id", ""), limit=150)

    return {
        "id": row["id"],
        "team_id": row.get("team_id", ""),
        "username": row.get("username", ""),
        "section": row.get("section"),
        "submission_hash": row.get("submission_hash", ""),
        "tests_collected": row.get("tests_collected", 0),
        "tests_passed": row.get("tests_passed", 0),
        "tests_failed": row.get("tests_failed", 0),
        "tests_skipped": row.get("tests_skipped", 0),
        "runtime_seconds": row.get("runtime_seconds", 0),
        "cpu_usage_percent": row.get("cpu_usage_percent", 0),
        "memory_usage_mb": row.get("memory_usage_mb", 0),
        "suspicious_imports": row.get("suspicious_imports", []),
        "test_hash_valid": row.get("test_hash_valid", True),
        "duplicate_detected": row.get("duplicate_detected", False),
        "submission_rate_last_10min": row.get("submission_rate_last_10min", 0),
        "paste_attempts": row.get("paste_attempts", 0),
        "large_injection_events": row.get("large_injection_events", 0),
        "typing_anomaly_detected": row.get("typing_anomaly_detected", False),
        "copy_risk_score": row.get("copy_risk_score", 0),
        "average_typing_speed_cps": row.get("average_typing_speed_cps", 0),
        "tab_switches": row.get("tab_switches", 0),
        "window_blur_seconds": row.get("window_blur_seconds", 0),
        "risk_score": row.get("risk_score", 0),
        "risk_level": row.get("risk_level", "Low"),
        "risk_flags": row.get("risk_flags", []),
        "risk_explanation": " ; ".join(row.get("risk_flags", [])) or "No risk flags",
        "raw_pytest_output": row.get("raw_pytest_output", ""),
        "timeline": list(reversed(timeline_rows)),
        "created_at": row.get("created_at"),
    }


@web_router.get("/admin/activity-monitor")
def activity_monitor_page():
    """Simple admin monitor page (template example)."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "static",
        "admin_activity.html",
    )
    if not os.path.isfile(template_path):
        raise HTTPException(status_code=404, detail="Template not found")
    return FileResponse(template_path)
