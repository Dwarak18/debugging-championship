"""
Test Runner router — runs pytest for a given section inside a sandbox.
Returns pass/fail counts, test names, and computed score.
"""

import subprocess
import json
import os
import time
import tempfile
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from backend.core.config import settings
from backend.core.deps import get_current_user, require_admin

router = APIRouter()

# Points per section (max)
SECTION_POINTS = {1: 100, 2: 100, 3: 100, 4: 120}

# Paths to test directories relative to repo root
SECTION_TESTS = {
    1: "section1-multifile-debug/tests",
    2: "section2-broken-recovery/tests",
    3: "section3-memory-deadlock/tests",
    4: "section4-logical-tracing/tests",
}


class RunRequest(BaseModel):
    section: int          # 1–4


class TestResult(BaseModel):
    section: int
    passed: int
    failed: int
    total: int
    score: float
    max_score: int
    duration_seconds: float
    results: list         # per-test details


@router.post("/section", response_model=TestResult)
def run_section(body: RunRequest, user: dict = Depends(require_admin)):
    """
    Run pytest for the requested section inside the repo.
    Returns pass/fail breakdown and computed score.
    """
    if body.section not in SECTION_TESTS:
        raise HTTPException(status_code=422, detail="section must be 1–4")

    test_path = os.path.normpath(
        os.path.join(settings.REPO_ROOT, SECTION_TESTS[body.section])
    )

    if not os.path.isdir(test_path):
        raise HTTPException(status_code=500, detail=f"Test directory not found: {test_path}")

    # Write JSON report to a temp file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        report_path = f.name

    try:
        start = time.monotonic()
        result = subprocess.run(
            [
                "python", "-m", "pytest", test_path,
                "--json-report", f"--json-report-file={report_path}",
                "--tb=no", "-q",
                f"--timeout={settings.PYTEST_TIMEOUT}",
            ],
            capture_output=True,
            text=True,
            timeout=settings.PYTEST_TIMEOUT + 10,
            cwd=settings.REPO_ROOT,
        )
        duration = time.monotonic() - start
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Test run timed out")
    finally:
        pass

    # Parse report
    try:
        with open(report_path) as f:
            report = json.load(f)
        os.unlink(report_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Could not parse pytest report")

    summary  = report.get("summary", {})
    passed   = summary.get("passed", 0)
    failed   = summary.get("failed", 0) + summary.get("error", 0)
    total    = summary.get("total", passed + failed)

    # Score: proportional to pass rate × max section points
    max_pts  = SECTION_POINTS[body.section]
    score    = round((passed / total * max_pts) if total else 0, 2)

    # Per-test details
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

    return TestResult(
        section=body.section,
        passed=passed,
        failed=failed,
        total=total,
        score=score,
        max_score=max_pts,
        duration_seconds=round(duration, 2),
        results=tests,
    )


@router.get("/sections")
def list_sections(_: dict = Depends(require_admin)):
    """Return available sections and their max points."""
    return {
        "sections": [
            {"id": s, "max_points": p, "tests_dir": SECTION_TESTS[s]}
            for s, p in SECTION_POINTS.items()
        ]
    }
