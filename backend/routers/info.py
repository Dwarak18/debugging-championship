"""
Info / health router.
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta

from core.database import get_all_section_timers, _conn
from core.deps import get_current_user

router = APIRouter()


EVENT = {
    "name": "Debugging Championship 2026",
    "total_points": 420,
    "duration_minutes": 170,
    "sections": [
        {"id": 1, "title": "Multi-File Debugging Lab",       "duration": 45,  "points": 100, "difficulty": "⭐⭐⭐"},
        {"id": 2, "title": "Broken Project Recovery",        "duration": 40,  "points": 100, "difficulty": "⭐⭐⭐⭐"},
        {"id": 3, "title": "Memory & Deadlock Simulation",   "duration": 50,  "points": 100, "difficulty": "⭐⭐⭐⭐⭐"},
        {"id": 4, "title": "Logical Tracing — Code Detective","duration": 35, "points": 120, "difficulty": "⭐⭐⭐⭐"},
    ],
}


@router.get("/health")
def health():
    """Liveness probe — used by Docker / load balancer."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/info")
def info():
    """Return event metadata."""
    return EVENT


@router.get("/ready")
def ready():
    """Readiness probe — lightweight DB ping (does NOT re-run migrations)."""
    from fastapi import HTTPException
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/timers/status")
def timers_status(_: dict = Depends(get_current_user)):
    """Return all section timer statuses with remaining-seconds for each."""
    rows = get_all_section_timers()
    now  = datetime.now(timezone.utc)
    result = []
    for row in rows:
        start     = row.get("start_time")
        paused_at = row.get("paused_at")
        elapsed   = row.get("elapsed_seconds") or 0
        is_active = row.get("is_active", False)

        def _tz(dt):
            if dt and hasattr(dt, "utcoffset") and dt.utcoffset() is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        start     = _tz(start)
        paused_at = _tz(paused_at)
        is_paused = is_active and paused_at is not None

        remaining = None
        if is_active and start:
            total_secs = row["duration_minutes"] * 60
            if is_paused:
                # Clock frozen — remaining = total - elapsed so far
                remaining = max(0, total_secs - elapsed)
            else:
                # Clock running — account for elapsed before last resume
                running_secs = int((now - start).total_seconds())
                remaining = max(0, total_secs - elapsed - running_secs)

        result.append({
            "section":           row["section"],
            "duration_minutes":  row["duration_minutes"],
            "start_time":        start.isoformat() if start else None,
            "paused_at":         paused_at.isoformat() if paused_at else None,
            "elapsed_seconds":   elapsed,
            "is_active":         is_active,
            "is_paused":         is_paused,
            "download_unlocked": is_active,   # download available when section is open
            "remaining_seconds": remaining,
        })
    return {"timers": result}
