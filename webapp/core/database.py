"""
SQLite-backed database.

Student accounts are PRE-CREATED by admin (via Google Form import).
Students cannot self-register — they login with credentials issued to them.
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
            CREATE TABLE IF NOT EXISTS students (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT    UNIQUE NOT NULL,
                password_hash TEXT   NOT NULL,
                full_name    TEXT    DEFAULT '',
                email        TEXT    UNIQUE,
                college      TEXT    DEFAULT '',
                team         TEXT    DEFAULT '',
                is_active    INTEGER DEFAULT 1,
                created_at   TEXT,
                last_login   TEXT
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
                FOREIGN KEY (username) REFERENCES students(username)
            );

            CREATE TABLE IF NOT EXISTS leaderboard (
                username     TEXT PRIMARY KEY,
                full_name    TEXT DEFAULT '',
                college      TEXT DEFAULT '',
                team         TEXT DEFAULT '',
                total_score  REAL NOT NULL DEFAULT 0,
                section1     REAL DEFAULT 0,
                section2     REAL DEFAULT 0,
                section3     REAL DEFAULT 0,
                section4     REAL DEFAULT 0,
                updated_at   TEXT,
                FOREIGN KEY (username) REFERENCES students(username)
            );
        """)


# ── Student management (admin) ────────────────────────────────────────────────

def create_student(username: str, password_hash: str, full_name: str = "",
                   email: str = "", college: str = "", team: str = "") -> bool:
    """Create a pre-registered student. Returns False if username/email taken."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        with _connect() as conn:
            conn.execute(
                """INSERT INTO students
                   (username, password_hash, full_name, email, college, team, created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (username, password_hash, full_name, email or None, college, team, now),
            )
            conn.execute(
                """INSERT OR IGNORE INTO leaderboard
                   (username, full_name, college, team, updated_at)
                   VALUES (?,?,?,?,?)""",
                (username, full_name, college, team, now),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_student(username: str) -> Optional[Dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE username = ? AND is_active = 1", (username,)
        ).fetchone()
    return dict(row) if row else None


def list_students() -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, username, full_name, email, college, team, is_active, created_at, last_login "
            "FROM students ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def update_last_login(username: str):
    with _connect() as conn:
        conn.execute(
            "UPDATE students SET last_login = ? WHERE username = ?",
            (datetime.now(timezone.utc).isoformat(), username),
        )


def deactivate_student(username: str):
    with _connect() as conn:
        conn.execute("UPDATE students SET is_active = 0 WHERE username = ?", (username,))


def reset_student_password(username: str, new_hash: str):
    with _connect() as conn:
        conn.execute(
            "UPDATE students SET password_hash = ? WHERE username = ?", (new_hash, username)
        )


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
            SELECT username, full_name, college, team,
                   total_score, section1, section2, section3, section4, updated_at
            FROM leaderboard
            ORDER BY total_score DESC, updated_at ASC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_submissions(username: str) -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM submissions WHERE username = ? ORDER BY submitted_at DESC",
            (username,),
        ).fetchall()
    return [dict(r) for r in rows]
