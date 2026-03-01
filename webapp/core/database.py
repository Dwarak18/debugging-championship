"""
PostgreSQL-backed database with connection pooling.

Handles 400+ concurrent users without bottlenecking via
psycopg2.pool.ThreadedConnectionPool (min=4, max=40 connections).

Student accounts are PRE-CREATED by admin (imported from Google Form).
"""

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from typing import List, Dict, Optional

from webapp.core.config import settings

# ── Connection pool ───────────────────────────────────────────────────────────
_pool: Optional[ThreadedConnectionPool] = None


def _get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(minconn=4, maxconn=40, dsn=settings.DATABASE_URL)
    return _pool


@contextmanager
def _conn():
    pool = _get_pool()
    conn = pool.getconn()
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def _row(cur) -> Optional[Dict]:
    r = cur.fetchone()
    return dict(r) if r else None

def _rows(cur) -> List[Dict]:
    return [dict(r) for r in cur.fetchall()]

RD = psycopg2.extras.RealDictCursor


# ── Schema ────────────────────────────────────────────────────────────────────

def init_db():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id            SERIAL PRIMARY KEY,
                    username      TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name     TEXT DEFAULT '',
                    email         TEXT,
                    college       TEXT DEFAULT '',
                    team          TEXT DEFAULT '',
                    is_active     BOOLEAN DEFAULT TRUE,
                    created_at    TIMESTAMPTZ DEFAULT NOW(),
                    last_login    TIMESTAMPTZ
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    id           SERIAL PRIMARY KEY,
                    username     TEXT NOT NULL,
                    section      INTEGER NOT NULL,
                    score        REAL NOT NULL,
                    passed_tests INTEGER NOT NULL,
                    total_tests  INTEGER NOT NULL,
                    time_taken   REAL,
                    submitted_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS leaderboard (
                    username    TEXT PRIMARY KEY,
                    full_name   TEXT DEFAULT '',
                    college     TEXT DEFAULT '',
                    team        TEXT DEFAULT '',
                    total_score REAL NOT NULL DEFAULT 0,
                    section1    REAL DEFAULT 0,
                    section2    REAL DEFAULT 0,
                    section3    REAL DEFAULT 0,
                    section4    REAL DEFAULT 0,
                    updated_at  TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_lb_total ON leaderboard(total_score DESC);

                -- Migration: add github_username if the column doesn't exist yet
                ALTER TABLE students ADD COLUMN IF NOT EXISTS github_username TEXT DEFAULT '';

                -- Migration: add pause/resume support to timers
                ALTER TABLE section_timers ADD COLUMN IF NOT EXISTS paused_at       TIMESTAMPTZ;
                ALTER TABLE section_timers ADD COLUMN IF NOT EXISTS elapsed_seconds INTEGER DEFAULT 0;

                CREATE TABLE IF NOT EXISTS section_timers (
                    section          INTEGER PRIMARY KEY,
                    duration_minutes INTEGER NOT NULL DEFAULT 45,
                    start_time       TIMESTAMPTZ,
                    is_active        BOOLEAN DEFAULT FALSE
                );
                INSERT INTO section_timers (section, duration_minutes)
                VALUES (1,45),(2,40),(3,50),(4,35)
                ON CONFLICT (section) DO NOTHING;
            """)


# ── Student management ────────────────────────────────────────────────────────

def create_student(username, password_hash, full_name="", email="", college="", team="", github_username="") -> bool:
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO students (username,password_hash,full_name,email,college,team,github_username)
                       VALUES (%s,%s,%s,NULLIF(%s,''),  %s,%s,%s)""",
                    (username, password_hash, full_name, email, college, team, github_username)
                )
        return True
    except psycopg2.errors.UniqueViolation:
        return False


def get_student(username) -> Optional[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute("SELECT * FROM students WHERE username=%s AND is_active=TRUE", (username,))
            return _row(cur)


def list_students() -> List[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute("SELECT * FROM students ORDER BY created_at DESC")
            return _rows(cur)


def update_last_login(username):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET last_login=NOW() WHERE username=%s", (username,))


def deactivate_student(username):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET is_active=FALSE WHERE username=%s", (username,))


def reset_student_password(username, new_hash):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET password_hash=%s WHERE username=%s", (new_hash, username))


def update_github_username(username, github_username):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET github_username=%s WHERE username=%s",
                        (github_username, username))


# ── Leaderboard ───────────────────────────────────────────────────────────────

def upsert_score(username, section, score, passed_tests, total_tests, time_taken,
                 full_name="", college="", team=""):
    sec = f"section{section}"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO submissions (username,section,score,passed_tests,total_tests,time_taken) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (username, section, score, passed_tests, total_tests, time_taken)
            )
            cur.execute(f"""
                INSERT INTO leaderboard (username,full_name,college,team,{sec},total_score)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (username) DO UPDATE SET
                  full_name   = EXCLUDED.full_name,
                  college     = EXCLUDED.college,
                  team        = EXCLUDED.team,
                  {sec}       = GREATEST(leaderboard.{sec}, EXCLUDED.{sec}),
                  total_score = (
                    GREATEST(leaderboard.section1, CASE WHEN %s=1 THEN EXCLUDED.{sec} ELSE leaderboard.section1 END) +
                    GREATEST(leaderboard.section2, CASE WHEN %s=2 THEN EXCLUDED.{sec} ELSE leaderboard.section2 END) +
                    GREATEST(leaderboard.section3, CASE WHEN %s=3 THEN EXCLUDED.{sec} ELSE leaderboard.section3 END) +
                    GREATEST(leaderboard.section4, CASE WHEN %s=4 THEN EXCLUDED.{sec} ELSE leaderboard.section4 END)
                  ),
                  updated_at  = NOW()
            """, (username, full_name, college, team, score, score,
                  section, section, section, section))


def get_leaderboard() -> List[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute("""
                SELECT username,full_name,college,team,
                       total_score,section1,section2,section3,section4
                FROM leaderboard ORDER BY total_score DESC, updated_at ASC
            """)
            return _rows(cur)


def get_user_scores(username) -> Optional[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute("SELECT * FROM leaderboard WHERE username=%s", (username,))
            return _row(cur)


def reset_leaderboard():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE submissions, leaderboard")


# ── Section Timers ────────────────────────────────────────────────────────────

def set_section_timer(section: int, duration_minutes: int, start_time=None) -> None:
    """Start (or restart) a section timer from zero."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO section_timers
                    (section, duration_minutes, start_time, is_active, paused_at, elapsed_seconds)
                VALUES (%s, %s, COALESCE(%s, NOW()), TRUE, NULL, 0)
                ON CONFLICT (section) DO UPDATE SET
                    duration_minutes = EXCLUDED.duration_minutes,
                    start_time       = COALESCE(%s, NOW()),
                    is_active        = TRUE,
                    paused_at        = NULL,
                    elapsed_seconds  = 0
            """, (section, duration_minutes, start_time, start_time))


def pause_section_timer(section: int) -> None:
    """Freeze the countdown clock (section stays open for download/validation)."""
    with _conn() as conn:
        with conn.cursor() as cur:
            # Only pause if running (not already paused, is_active=TRUE)
            cur.execute("""
                UPDATE section_timers
                SET paused_at = NOW()
                WHERE section=%s AND is_active=TRUE AND paused_at IS NULL
            """, (section,))


def resume_section_timer(section: int) -> None:
    """Resume a paused timer; absorb the paused gap into elapsed_seconds."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE section_timers
                SET elapsed_seconds = elapsed_seconds +
                        EXTRACT(EPOCH FROM (NOW() - paused_at))::INTEGER,
                    start_time      = NOW(),
                    paused_at       = NULL
                WHERE section=%s AND is_active=TRUE AND paused_at IS NOT NULL
            """, (section,))


def stop_section_timer(section: int) -> None:
    """Stop accepting submissions but keep section open for download."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE section_timers
                SET is_active=FALSE,
                    paused_at=NULL
                WHERE section=%s
            """, (section,))


def reset_section_timer(section: int) -> None:
    """Full reset — close section, lock download, clear all timer state."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE section_timers
                SET is_active=FALSE, start_time=NULL,
                    paused_at=NULL, elapsed_seconds=0
                WHERE section=%s
            """, (section,))


def get_section_timer(section: int) -> Optional[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute("SELECT * FROM section_timers WHERE section=%s", (section,))
            return _row(cur)


def get_all_section_timers() -> List[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute("SELECT * FROM section_timers ORDER BY section")
            return _rows(cur)
