"""
Info / health router.
"""

from fastapi import APIRouter
from datetime import datetime, timezone

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
    """Readiness probe — checks DB is reachable."""
    from webapp.core.database import init_db
    try:
        init_db()
        return {"status": "ready"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=str(e))
