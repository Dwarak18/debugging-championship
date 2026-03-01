"""
Download router — zip and serve section source code.

Excludes hints, solutions and pycache so participants only get the
problem files (code they need to debug / fix).
"""

import os
import zipfile
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.core.config import settings
from backend.core.security import verify_token

router = APIRouter()

SECTION_DIRS = {
    1: "section1-multifile-debug",
    2: "section2-broken-recovery",
    3: "section3-memory-deadlock",
    4: "section4-logical-tracing",
}

# Files / directories never included in the download
EXCLUDE_FILES = {"hints.md", "hints.txt", "solutions.py", "summary.md"}
EXCLUDE_DIRS  = {"__pycache__", ".pytest_cache"}


@router.get("/section/{section_id}")
def download_section(
    section_id: int,
    token: str = Query(..., description="Bearer token passed as query param for browser downloads"),
):
    """
    Download a zip of the section's source files.
    Hints, solution files and __pycache__ are excluded.
    Authentication is via ?token= query param (required for browser <a> downloads).
    """
    # Validate token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if section_id not in SECTION_DIRS:
        raise HTTPException(status_code=404, detail="Section not found")

    section_dir = os.path.join(settings.REPO_ROOT, SECTION_DIRS[section_id])
    if not os.path.isdir(section_dir):
        raise HTTPException(status_code=500, detail="Section directory not found on server")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(section_dir):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for filename in sorted(files):
                if filename.lower() in EXCLUDE_FILES:
                    continue
                if filename.endswith(".pyc"):
                    continue
                filepath = os.path.join(root, filename)
                # Use path relative to parent of section dir so zip contains section folder
                arcname = os.path.relpath(filepath, os.path.dirname(section_dir))
                zf.write(filepath, arcname)
    buf.seek(0)

    zipname = f"{SECTION_DIRS[section_id]}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zipname}"'},
    )
