"""
SQLite-backed leaderboard database.
"""

import sqlite3
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

from webapp.core.config import settings


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS participants (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT    UNIQUE NOT NULL,
                github    TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT NOT NULL,
                section      INTEGER NOT NULL,
                score        REAL NOT NULL,
                passed_tests INTEGER NOT NULL,
                total_tests  INTEGER NOT NULL,
                time_taken   REAL,
                submitted_at TEXT,
                FOREIGN KEY (username) REFERENCES participants(username)
            );

            CREATE TABLE IF NOT EXISTS leaderboard (
                username     TEXT PRIMARY KEY,
                total_score  REAL NOT NULL DEFAULT 0,
                section1     REAL DEFAULT 0,
                section2     REAL DEFAULT 0,
                section3     REAL DEFAULT 0,
                section4     REAL DEFAULT 0,
                updated_at   TEXT,
                FOREIGN KEY (username) REFERENCES participants(username)
            );
        """)


def register_participant(username: str, github: str = "") -> bool:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO participants (username, github, created_at) VALUES (?,?,?)",
                (username, github, datetime.now(timezone.utc).isoformat()),
            )
            conn.execute(
                "INSERT OR IGNORE INTO leaderboard (username, updated_at) VALUES (?,?)",
                (username, datetime.now(timezone.utc).isoformat()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def upsert_score(username: str, section: int, score: float,
                 passed: int, total: int, time_taken: float = 0.0):
    """Record a submission and update the leaderboard."""
    col = f"section{section}"
    with _connect() as conn:
        conn.execute(
            """INSERT INTO submissions
               (username, section, score, passed_tests, total_tests, time_taken, submitted_at)
               VALUES (?,?,?,?,?,?,?)""",
            (username, section, score, passed, total, time_taken,
             datetime.now(timezone.utc).isoformat()),
        )
        # Keep best score per section
        conn.execute(f"""
            UPDATE leaderboard
            SET {col} = MAX({col}, ?),
                total_score = (
                    COALESCE(section1,0) + COALESCE(section2,0) +
                    COALESCE(section3,0) + COALESCE(section4,0)
                ),
                updated_at = ?
            WHERE username = ?
        """, (score, datetime.now(timezone.utc).isoformat(), username))


def get_leaderboard(limit: int = 50) -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT username, total_score, section1, section2, section3, section4, updated_at
            FROM leaderboard
            ORDER BY total_score DESC, updated_at ASC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_participant(username: str) -> Optional[Dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM participants WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


def get_submissions(username: str) -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM submissions WHERE username = ? ORDER BY submitted_at DESC",
            (username,),
        ).fetchall()
    return [dict(r) for r in rows]
