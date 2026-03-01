"""
Anti-cheat helpers.

Keeps logic isolated from routers so existing submission flow remains unchanged.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

TARGET_TEST_FILES = [
    "section1-multifile-debug/tests/test_system.py",
    "section2-broken-recovery/tests/test_recovery.py",
    "section3-memory-deadlock/tests/test_memory_deadlock.py",
    "section4-logical-tracing/tests/test_logic_tracing.py",
]

SUSPICIOUS_PATTERNS = [
    r"\binspect\b",
    r"\bsubprocess\b",
    r"\bos\.system\b",
    r"\bpytest\.skip\b",
    r"\bmonkeypatch\b",
    r"\bimport\s+test_",
]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_test_hashes(repo_root: str) -> Dict[str, str]:
    """Return SHA256 hashes for the canonical test files."""
    hashes: Dict[str, str] = {}
    root = Path(repo_root)
    for rel in TARGET_TEST_FILES:
        fp = root / rel
        if fp.exists() and fp.is_file():
            hashes[rel] = _sha256_file(fp)
        else:
            hashes[rel] = ""
    return hashes


def verify_test_integrity(baseline_root: str, submitted_root: str) -> Tuple[bool, List[str]]:
    """
    Compare canonical test file hashes between baseline repo and submitted repo.
    Returns (is_valid, mismatched_files).
    """
    baseline = compute_test_hashes(baseline_root)
    submitted = compute_test_hashes(submitted_root)

    mismatched = [
        rel for rel in TARGET_TEST_FILES
        if baseline.get(rel, "") != submitted.get(rel, "")
    ]
    return (len(mismatched) == 0, mismatched)


def scan_suspicious_imports(repo_root: str) -> Tuple[List[str], int]:
    """
    Scan submitted python files for suspicious anti-test patterns.

    Returns:
      - list of unique matched patterns (human labels)
      - total occurrences
    """
    root = Path(repo_root)
    labels = {
        r"\binspect\b": "inspect",
        r"\bsubprocess\b": "subprocess",
        r"\bos\.system\b": "os.system",
        r"\bpytest\.skip\b": "pytest.skip",
        r"\bmonkeypatch\b": "monkeypatch",
        r"\bimport\s+test_": "import test_",
    }

    unique_hits = set()
    total_occurrences = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            file_path = Path(dirpath) / name
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern in SUSPICIOUS_PATTERNS:
                found = re.findall(pattern, text, flags=re.IGNORECASE)
                if found:
                    unique_hits.add(labels[pattern])
                    total_occurrences += len(found)

    return sorted(unique_hits), total_occurrences


def hash_source_tree(repo_root: str) -> str:
    """Stable hash of submitted source tree for duplicate detection."""
    root = Path(repo_root)
    h = hashlib.sha256()

    include_suffixes = {".py", ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini"}

    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}]
        for n in filenames:
            p = Path(dirpath) / n
            if p.suffix.lower() in include_suffixes:
                paths.append(p)

    for p in sorted(paths):
        rel = str(p.relative_to(root)).replace("\\", "/")
        h.update(rel.encode("utf-8", errors="ignore"))
        try:
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
        except Exception:
            # Keep hash deterministic even if read fails
            h.update(b"<unreadable>")

    return h.hexdigest()
