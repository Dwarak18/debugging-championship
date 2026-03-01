"""
Validator router — clone a participant's GitHub repo and run section tests against it.

Rules:
  - Each section has a separate time window set by admin.
  - After the window expires, validation is rejected.
  - Multiple submissions allowed; only the highest score is kept (DB GREATEST logic).
"""

import subprocess
import json
import os
import time
import tempfile
import shutil
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from webapp.core.config import settings
from webapp.core.deps import get_current_user
from webapp.core.database import upsert_score, get_section_timer

router = APIRouter()

# Points per section (max)
SECTION_POINTS = {1: 100, 2: 100, 3: 100, 4: 120}

# Relative paths to test directories inside the cloned repo
SECTION_TESTS = {
    1: "section1-multifile-debug/tests",
    2: "section2-broken-recovery/tests",
    3: "section3-memory-deadlock/tests",
    4: "section4-logical-tracing/tests",
}


class ValidateRequest(BaseModel):
    section: int
    github_url: str


@router.post("/section")
def validate_section(body: ValidateRequest, user: dict = Depends(get_current_user)):
    """
    Clone participant's GitHub repo and run pytest for the requested section.
    Returns pass/fail breakdown and updates the leaderboard (highest score kept).
    """
    if body.section not in SECTION_TESTS:
        raise HTTPException(status_code=422, detail="section must be 1–4")

    # ── Timer check ───────────────────────────────────────────────────────────
    timer = get_section_timer(body.section)
    if timer and timer.get("is_active") and timer.get("start_time"):
        start    = timer["start_time"]
        elapsed  = timer.get("elapsed_seconds") or 0
        paused_at = timer.get("paused_at")

        def _tz(dt):
            if dt and hasattr(dt, "utcoffset") and dt.utcoffset() is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        start     = _tz(start)
        paused_at = _tz(paused_at)
        total_secs = timer["duration_minutes"] * 60
        now = datetime.now(timezone.utc)

        if paused_at:
            # Timer is paused — remaining = total - elapsed_at_pause
            remaining = total_secs - elapsed
        else:
            # Timer is running
            running_secs = int((now - start).total_seconds())
            remaining = total_secs - elapsed - running_secs

        if remaining <= 0:
            raise HTTPException(
                status_code=403,
                detail=f"Section {body.section} time has expired. No more submissions accepted."
            )

    # ── Clone repo ────────────────────────────────────────────────────────────
    tmpdir = tempfile.mkdtemp(prefix="dc_validate_")
    report_path = None
    try:
        # Disable all credential helpers so git never hangs waiting for
        # a username/password prompt — only works with public repos.
        clone_env = {
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "echo",
        }
        clone = subprocess.run(
            [
                "git", "clone",
                "-c", "credential.helper=",
                "--depth=1", "--no-tags",
                body.github_url, tmpdir,
            ],
            capture_output=True, text=True, timeout=90,
            env=clone_env,
        )
        if clone.returncode != 0:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to clone repository: {clone.stderr[:400].strip()}"
            )

        # ── Verify tests exist ────────────────────────────────────────────────
        test_path = os.path.join(tmpdir, SECTION_TESTS[body.section])
        if not os.path.isdir(test_path):
            raise HTTPException(
                status_code=422,
                detail=f"Tests for section {body.section} not found in repo. "
                       f"Expected: {SECTION_TESTS[body.section]}"
            )

        # ── Run pytest ────────────────────────────────────────────────────────
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            report_path = f.name

        start_t = time.monotonic()
        subprocess.run(
            [
                "python", "-m", "pytest", test_path,
                "--json-report", f"--json-report-file={report_path}",
                "--tb=no", "-q",
                f"--timeout={settings.PYTEST_TIMEOUT}",
            ],
            capture_output=True, text=True,
            timeout=settings.PYTEST_TIMEOUT + 30,
            cwd=tmpdir,
        )
        duration = time.monotonic() - start_t

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # ── Parse report ──────────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
        os.unlink(report_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Could not parse pytest report")

    summary = report.get("summary", {})
    passed  = summary.get("passed", 0)
    failed  = summary.get("failed", 0) + summary.get("error", 0)
    total   = summary.get("total", passed + failed)

    max_pts = SECTION_POINTS[body.section]
    score   = round((passed / total * max_pts) if total else 0, 2)

    # Parse results
    def _get_test_error(t):
        for phase in ("call", "setup", "teardown"):
            pd = t.get(phase) or {}
            if pd.get("outcome") in ("failed", "error"):
                lr = pd.get("longrepr", "")
                if isinstance(lr, dict):
                    lr = lr.get("repr", "")
                return str(lr).strip()
        return ""

    tests = [
        {
            "name":     t.get("nodeid", "").split("::")[-1],
            "outcome":  t.get("outcome"),
            "duration": round(t.get("duration", 0), 3),
            "error":    _get_test_error(t) if t.get("outcome") != "passed" else "",
        }
        for t in report.get("tests", [])
    ]

    # ── Update leaderboard (GREATEST keeps highest score) ─────────────────────
    upsert_score(
        username=user["sub"],
        section=body.section,
        score=score,
        passed_tests=passed,
        total_tests=total,
        time_taken=round(duration, 2),
        full_name=user.get("full_name", ""),
        college=user.get("college", ""),
        team=user.get("team", ""),
    )

    return {
        "section":          body.section,
        "passed":           passed,
        "failed":           failed,
        "total":            total,
        "score":            score,
        "max_score":        max_pts,
        "duration_seconds": round(duration, 2),
        "results":          tests,
        "note":             "Only your highest score per section is kept.",
    }
