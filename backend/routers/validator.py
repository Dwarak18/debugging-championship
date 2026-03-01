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
import resource
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional

from core.config import settings
from core.deps import get_current_user
from core.database import (
    upsert_score,
    get_section_timer,
    save_anti_cheat_report,
    find_duplicate_submission_hash,
    count_recent_submissions,
    log_editor_activity,
    get_editor_activity_metrics,
)
from anti_cheat import verify_test_integrity, scan_suspicious_imports, hash_source_tree
from risk_engine import build_risk

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


class EditorActivityRequest(BaseModel):
    event: str
    team_id: Optional[str] = None
    timestamp: Optional[str] = None
    editor_length_before: int = 0
    editor_length_after: int = 0
    chars_delta: int = 0
    delta_ms: int = 0
    typing_speed_cps: float = 0.0
    flags: List[str] = Field(default_factory=list)
    details: dict = Field(default_factory=dict)


@router.post("/editor-activity")
def track_editor_activity(body: EditorActivityRequest, user: dict = Depends(get_current_user)):
    """Receive client-side editor telemetry events (paste attempts / typing anomalies)."""
    team_id = body.team_id or user.get("team") or user.get("sub") or "unknown"
    metadata = {
        "timestamp": body.timestamp,
        "flags": body.flags,
        "details": body.details,
    }
    log_id = log_editor_activity(
        username=user.get("sub", ""),
        team_id=team_id,
        event=body.event,
        editor_length_before=body.editor_length_before,
        editor_length_after=body.editor_length_after,
        chars_delta=body.chars_delta,
        delta_ms=body.delta_ms,
        typing_speed_cps=body.typing_speed_cps,
        metadata=metadata,
    )
    return {"ok": True, "id": log_id}


def _limit_process_resources() -> None:
    """Child-process hardening: memory cap + soft CPU limit."""
    mem_limit_mb = int(os.getenv("PYTEST_MEMORY_LIMIT_MB", "512"))
    mem_bytes = mem_limit_mb * 1024 * 1024

    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    cpu_cap = max(settings.PYTEST_TIMEOUT + 5, 10)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_cap, cpu_cap))


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
    raw_stdout = ""
    raw_stderr = ""
    test_hash_valid = True
    test_hash_mismatches = []
    suspicious_imports = []
    suspicious_occurrences = 0
    submission_hash = ""
    duplicate_detected = False
    duplicate_with = None
    submission_rate_last_10min = 0
    copy_metrics = {
        "paste_attempts": 0,
        "large_injection_events": 0,
        "typing_anomaly_detected": False,
        "typing_anomaly_events": 0,
        "average_typing_speed_cps": 0.0,
        "copy_risk_score": 0,
        "tab_switches": 0,
        "window_blur_seconds": 0.0,
    }
    child_cpu_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_mem_before_kb = child_cpu_before.ru_maxrss
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

        # ── Anti-cheat pre-checks ───────────────────────────────────────────
        team_id = user.get("team") or user.get("sub") or "unknown"
        test_hash_valid, test_hash_mismatches = verify_test_integrity(settings.REPO_ROOT, tmpdir)
        suspicious_imports, suspicious_occurrences = scan_suspicious_imports(tmpdir)
        submission_hash = hash_source_tree(tmpdir)

        duplicate_row = find_duplicate_submission_hash(submission_hash, team_id)
        duplicate_detected = duplicate_row is not None
        duplicate_with = duplicate_row.get("team_id") if duplicate_row else None

        submission_rate_last_10min = count_recent_submissions(team_id=team_id, minutes=10)
        copy_metrics = get_editor_activity_metrics(team_id=team_id, minutes=10)

        # ── Run pytest ────────────────────────────────────────────────────────
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            report_path = f.name

        start_t = time.monotonic()
        run_result = subprocess.run(
            [
                "python", "-m", "pytest", test_path,
                "--json-report", f"--json-report-file={report_path}",
                "--tb=no", "-q",
                f"--timeout={settings.PYTEST_TIMEOUT}",
            ],
            capture_output=True, text=True,
            timeout=settings.PYTEST_TIMEOUT + 30,
            cwd=tmpdir,
            preexec_fn=_limit_process_resources,
        )
        duration = time.monotonic() - start_t
        raw_stdout = run_result.stdout or ""
        raw_stderr = run_result.stderr or ""

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
    skipped = summary.get("skipped", 0)
    collected = summary.get("collected", total)

    child_cpu_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_time_delta = (
        (child_cpu_after.ru_utime + child_cpu_after.ru_stime)
        - (child_cpu_before.ru_utime + child_cpu_before.ru_stime)
    )
    cpu_usage_percent = round((cpu_time_delta / duration) * 100, 2) if duration > 0 else 0.0
    mem_after_kb = child_cpu_after.ru_maxrss
    mem_delta_kb = max(mem_after_kb - child_mem_before_kb, 0)
    memory_usage_mb = round(mem_delta_kb / 1024.0, 2)

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

    # ── Anti-cheat report and risk score ──────────────────────────────────────
    risk_score, risk_flags, risk_level = build_risk(
        test_hash_valid=test_hash_valid,
        tests_collected=collected,
        tests_skipped=skipped,
        suspicious_occurrences=suspicious_occurrences,
        duplicate_detected=duplicate_detected,
        submission_rate_last_10min=submission_rate_last_10min,
        runtime_seconds=duration,
        paste_attempts=copy_metrics.get("paste_attempts", 0),
        large_injection_events=copy_metrics.get("large_injection_events", 0),
        typing_anomaly_detected=copy_metrics.get("typing_anomaly_detected", False),
        copy_risk_score=copy_metrics.get("copy_risk_score", 0),
        expected_total_tests=57,
    )

    if test_hash_mismatches:
        risk_flags.append(f"Mismatched tests: {', '.join(test_hash_mismatches)}")
    if duplicate_with:
        risk_flags.append(f"Duplicate with team: {duplicate_with}")

    team_id = user.get("team") or user.get("sub") or "unknown"
    anti_cheat_report = {
        "username": user.get("sub", ""),
        "team_id": team_id,
        "section": body.section,
        "submission_hash": submission_hash,
        "tests_collected": collected,
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_skipped": skipped,
        "runtime_seconds": round(duration, 4),
        "cpu_usage_percent": cpu_usage_percent,
        "memory_usage_mb": memory_usage_mb,
        "suspicious_imports": suspicious_imports,
        "test_hash_valid": test_hash_valid,
        "duplicate_detected": duplicate_detected,
        "submission_rate_last_10min": submission_rate_last_10min,
        "paste_attempts": copy_metrics.get("paste_attempts", 0),
        "large_injection_events": copy_metrics.get("large_injection_events", 0),
        "typing_anomaly_detected": copy_metrics.get("typing_anomaly_detected", False),
        "copy_risk_score": copy_metrics.get("copy_risk_score", 0),
        "average_typing_speed_cps": copy_metrics.get("average_typing_speed_cps", 0.0),
        "tab_switches": copy_metrics.get("tab_switches", 0),
        "window_blur_seconds": copy_metrics.get("window_blur_seconds", 0.0),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "raw_pytest_output": f"{raw_stdout}\n{raw_stderr}".strip(),
    }
    anti_cheat_report_id = save_anti_cheat_report(anti_cheat_report)

    return {
        "section":          body.section,
        "passed":           passed,
        "failed":           failed,
        "total":            total,
        "score":            score,
        "max_score":        max_pts,
        "duration_seconds": round(duration, 2),
        "results":          tests,
        "anti_cheat_report_id": anti_cheat_report_id,
        "anti_cheat": {
            "team_id": team_id,
            "submission_hash": submission_hash,
            "tests_collected": collected,
            "tests_passed": passed,
            "tests_failed": failed,
            "tests_skipped": skipped,
            "runtime_seconds": round(duration, 4),
            "cpu_usage_percent": cpu_usage_percent,
            "memory_usage_mb": memory_usage_mb,
            "suspicious_imports": suspicious_imports,
            "test_hash_valid": test_hash_valid,
            "duplicate_detected": duplicate_detected,
            "submission_rate_last_10min": submission_rate_last_10min,
            "paste_attempts": copy_metrics.get("paste_attempts", 0),
            "large_injection_events": copy_metrics.get("large_injection_events", 0),
            "typing_anomaly_detected": copy_metrics.get("typing_anomaly_detected", False),
            "copy_risk_score": copy_metrics.get("copy_risk_score", 0),
            "average_typing_speed_cps": copy_metrics.get("average_typing_speed_cps", 0.0),
            "tab_switches": copy_metrics.get("tab_switches", 0),
            "window_blur_seconds": copy_metrics.get("window_blur_seconds", 0.0),
            "risk_score": risk_score,
            "risk_flags": risk_flags,
            "risk_level": risk_level,
        },
        "note":             "Only your highest score per section is kept.",
    }
