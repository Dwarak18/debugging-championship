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

from core.config import settings

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

                -- Migration: add team/commit/github fields to submissions
                ALTER TABLE submissions ADD COLUMN IF NOT EXISTS team_no          TEXT DEFAULT '';
                ALTER TABLE submissions ADD COLUMN IF NOT EXISTS team_name        TEXT DEFAULT '';
                ALTER TABLE submissions ADD COLUMN IF NOT EXISTS commit_no        TEXT DEFAULT '';
                ALTER TABLE submissions ADD COLUMN IF NOT EXISTS github_repo_link TEXT DEFAULT '';

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

                CREATE TABLE IF NOT EXISTS section_timers (
                    section          INTEGER PRIMARY KEY,
                    duration_minutes INTEGER NOT NULL DEFAULT 45,
                    start_time       TIMESTAMPTZ,
                    is_active        BOOLEAN DEFAULT FALSE
                );

                -- Migration: add pause/resume support to timers
                ALTER TABLE section_timers ADD COLUMN IF NOT EXISTS paused_at       TIMESTAMPTZ;
                ALTER TABLE section_timers ADD COLUMN IF NOT EXISTS elapsed_seconds INTEGER DEFAULT 0;
                INSERT INTO section_timers (section, duration_minutes)
                VALUES (1,45),(2,40),(3,50),(4,35)
                ON CONFLICT (section) DO NOTHING;

                CREATE TABLE IF NOT EXISTS anti_cheat_reports (
                    id                           SERIAL PRIMARY KEY,
                    username                     TEXT NOT NULL,
                    team_id                      TEXT NOT NULL DEFAULT '',
                    section                      INTEGER NOT NULL,
                    submission_hash              TEXT NOT NULL,
                    tests_collected              INTEGER NOT NULL DEFAULT 0,
                    tests_passed                 INTEGER NOT NULL DEFAULT 0,
                    tests_failed                 INTEGER NOT NULL DEFAULT 0,
                    tests_skipped                INTEGER NOT NULL DEFAULT 0,
                    runtime_seconds              REAL NOT NULL DEFAULT 0,
                    cpu_usage_percent            REAL NOT NULL DEFAULT 0,
                    memory_usage_mb              REAL NOT NULL DEFAULT 0,
                    suspicious_imports           JSONB NOT NULL DEFAULT '[]'::jsonb,
                    test_hash_valid              BOOLEAN NOT NULL DEFAULT TRUE,
                    duplicate_detected           BOOLEAN NOT NULL DEFAULT FALSE,
                    submission_rate_last_10min   INTEGER NOT NULL DEFAULT 0,
                    paste_attempts               INTEGER NOT NULL DEFAULT 0,
                    large_injection_events       INTEGER NOT NULL DEFAULT 0,
                    typing_anomaly_detected      BOOLEAN NOT NULL DEFAULT FALSE,
                    copy_risk_score              INTEGER NOT NULL DEFAULT 0,
                    average_typing_speed_cps     REAL NOT NULL DEFAULT 0,
                    tab_switches                 INTEGER NOT NULL DEFAULT 0,
                    window_blur_seconds          REAL NOT NULL DEFAULT 0,
                    risk_score                   INTEGER NOT NULL DEFAULT 0,
                    risk_level                   TEXT NOT NULL DEFAULT 'Low',
                    risk_flags                   JSONB NOT NULL DEFAULT '[]'::jsonb,
                    raw_pytest_output            TEXT NOT NULL DEFAULT '',
                    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                ALTER TABLE anti_cheat_reports ADD COLUMN IF NOT EXISTS paste_attempts           INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE anti_cheat_reports ADD COLUMN IF NOT EXISTS large_injection_events   INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE anti_cheat_reports ADD COLUMN IF NOT EXISTS typing_anomaly_detected  BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE anti_cheat_reports ADD COLUMN IF NOT EXISTS copy_risk_score          INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE anti_cheat_reports ADD COLUMN IF NOT EXISTS average_typing_speed_cps REAL NOT NULL DEFAULT 0;
                ALTER TABLE anti_cheat_reports ADD COLUMN IF NOT EXISTS tab_switches             INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE anti_cheat_reports ADD COLUMN IF NOT EXISTS window_blur_seconds      REAL NOT NULL DEFAULT 0;

                CREATE TABLE IF NOT EXISTS editor_activity_logs (
                    id                     SERIAL PRIMARY KEY,
                    username               TEXT NOT NULL,
                    team_id                TEXT NOT NULL DEFAULT '',
                    event                  TEXT NOT NULL,
                    editor_length_before   INTEGER NOT NULL DEFAULT 0,
                    editor_length_after    INTEGER NOT NULL DEFAULT 0,
                    chars_delta            INTEGER NOT NULL DEFAULT 0,
                    delta_ms               INTEGER NOT NULL DEFAULT 0,
                    typing_speed_cps       REAL NOT NULL DEFAULT 0,
                    metadata               JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_eal_team_time ON editor_activity_logs(team_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_eal_user_time ON editor_activity_logs(username, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_eal_event ON editor_activity_logs(event);

                CREATE INDEX IF NOT EXISTS idx_acr_created_at ON anti_cheat_reports(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_acr_team_id ON anti_cheat_reports(team_id);
                CREATE INDEX IF NOT EXISTS idx_acr_submission_hash ON anti_cheat_reports(submission_hash);
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


def update_student(username, full_name=None, email=None, college=None, team=None, is_active=None):
    """Update editable fields on a student record."""
    fields, vals = [], []
    if full_name  is not None: fields.append("full_name=%s");  vals.append(full_name)
    if email      is not None: fields.append("email=%s");      vals.append(email or None)
    if college    is not None: fields.append("college=%s");    vals.append(college)
    if team       is not None: fields.append("team=%s");       vals.append(team)
    if is_active  is not None: fields.append("is_active=%s");  vals.append(is_active)
    if not fields:
        return
    vals.append(username)
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE students SET {', '.join(fields)} WHERE username=%s", vals)


def reactivate_student(username):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET is_active=TRUE WHERE username=%s", (username,))



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
                 full_name="", college="", team="",
                 team_no="", team_name="", commit_no="", github_repo_link=""):
    sec = f"section{section}"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO submissions (username,section,score,passed_tests,total_tests,time_taken,"
                "team_no,team_name,commit_no,github_repo_link) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (username, section, score, passed_tests, total_tests, time_taken,
                 team_no, team_name, commit_no, github_repo_link)
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


def get_submissions_log(limit: int = 500) -> List[Dict]:
    """Return full submission log with team/commit/repo fields for admin view."""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute("""
                SELECT s.id, s.username, st.full_name, s.section,
                       s.score, s.passed_tests, s.total_tests, s.time_taken,
                       s.team_no, s.team_name, s.commit_no, s.github_repo_link,
                       s.submitted_at
                FROM submissions s
                LEFT JOIN students st ON st.username = s.username
                ORDER BY s.submitted_at DESC
                LIMIT %s
            """, (limit,))
            return _rows(cur)


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


# ── Anti-cheat reports ───────────────────────────────────────────────────────

def save_anti_cheat_report(report: Dict) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO anti_cheat_reports (
                    username, team_id, section, submission_hash,
                    tests_collected, tests_passed, tests_failed, tests_skipped,
                    runtime_seconds, cpu_usage_percent, memory_usage_mb,
                    suspicious_imports, test_hash_valid, duplicate_detected,
                    submission_rate_last_10min, paste_attempts, large_injection_events,
                    typing_anomaly_detected, copy_risk_score, average_typing_speed_cps,
                    tab_switches, window_blur_seconds,
                    risk_score, risk_level, risk_flags,
                    raw_pytest_output
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s
                )
                RETURNING id
                """,
                (
                    report.get("username", ""),
                    report.get("team_id", ""),
                    report.get("section", 0),
                    report.get("submission_hash", ""),
                    report.get("tests_collected", 0),
                    report.get("tests_passed", 0),
                    report.get("tests_failed", 0),
                    report.get("tests_skipped", 0),
                    report.get("runtime_seconds", 0.0),
                    report.get("cpu_usage_percent", 0.0),
                    report.get("memory_usage_mb", 0.0),
                    psycopg2.extras.Json(report.get("suspicious_imports", [])),
                    report.get("test_hash_valid", True),
                    report.get("duplicate_detected", False),
                    report.get("submission_rate_last_10min", 0),
                    report.get("paste_attempts", 0),
                    report.get("large_injection_events", 0),
                    report.get("typing_anomaly_detected", False),
                    report.get("copy_risk_score", 0),
                    report.get("average_typing_speed_cps", 0.0),
                    report.get("tab_switches", 0),
                    report.get("window_blur_seconds", 0.0),
                    report.get("risk_score", 0),
                    report.get("risk_level", "Low"),
                    psycopg2.extras.Json(report.get("risk_flags", [])),
                    report.get("raw_pytest_output", ""),
                ),
            )
            return int(cur.fetchone()[0])


def find_duplicate_submission_hash(submission_hash: str, team_id: str) -> Optional[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute(
                """
                SELECT id, username, team_id, submission_hash, created_at
                FROM anti_cheat_reports
                WHERE submission_hash = %s AND team_id <> %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (submission_hash, team_id),
            )
            return _row(cur)


def count_recent_submissions(team_id: str, minutes: int = 10) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM anti_cheat_reports
                WHERE team_id = %s
                  AND created_at >= NOW() - (%s::text || ' minutes')::interval
                """,
                (team_id, minutes),
            )
            return int(cur.fetchone()[0])


def list_anti_cheat_reports(limit: int = 200, flagged_only: bool = False) -> List[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            if flagged_only:
                cur.execute(
                    """
                    SELECT *
                    FROM anti_cheat_reports
                    WHERE risk_score >= 60
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            else:
                cur.execute(
                    """
                    SELECT *
                    FROM anti_cheat_reports
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            return _rows(cur)


def get_anti_cheat_report(report_id: int) -> Optional[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute("SELECT * FROM anti_cheat_reports WHERE id=%s", (report_id,))
            return _row(cur)


def log_editor_activity(
    username: str,
    team_id: str,
    event: str,
    editor_length_before: int = 0,
    editor_length_after: int = 0,
    chars_delta: int = 0,
    delta_ms: int = 0,
    typing_speed_cps: float = 0.0,
    metadata: Optional[Dict] = None,
) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO editor_activity_logs (
                    username, team_id, event,
                    editor_length_before, editor_length_after,
                    chars_delta, delta_ms, typing_speed_cps, metadata
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    username,
                    team_id,
                    event,
                    int(editor_length_before or 0),
                    int(editor_length_after or 0),
                    int(chars_delta or 0),
                    int(delta_ms or 0),
                    float(typing_speed_cps or 0.0),
                    psycopg2.extras.Json(metadata or {}),
                ),
            )
            return int(cur.fetchone()[0])


def get_editor_activity_metrics(team_id: str, minutes: int = 10) -> Dict:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN event='paste_attempt' THEN 1 ELSE 0 END),0) AS paste_attempts,
                    COALESCE(SUM(CASE WHEN event='large_injection' THEN 1 ELSE 0 END),0) AS large_injection_events,
                    COALESCE(SUM(CASE WHEN event='typing_anomaly' THEN 1 ELSE 0 END),0) AS typing_anomaly_events,
                    COALESCE(AVG(CASE WHEN typing_speed_cps > 0 THEN typing_speed_cps END),0) AS average_typing_speed_cps,
                    COALESCE(SUM(CASE WHEN event='tab_switch' THEN 1 ELSE 0 END),0) AS tab_switches,
                    COALESCE(SUM(CASE WHEN event='window_blur' THEN COALESCE((metadata->'details'->>'blur_seconds')::REAL,0) ELSE 0 END),0) AS window_blur_seconds
                FROM editor_activity_logs
                WHERE team_id=%s
                  AND created_at >= NOW() - (%s::text || ' minutes')::interval
                """,
                (team_id, minutes),
            )
            row = _row(cur) or {}

    paste_attempts = int(row.get("paste_attempts", 0) or 0)
    large_injections = int(row.get("large_injection_events", 0) or 0)
    typing_anomaly_events = int(row.get("typing_anomaly_events", 0) or 0)
    avg_cps = float(row.get("average_typing_speed_cps", 0) or 0.0)

    copy_risk_score = 0
    if paste_attempts > 0:
        copy_risk_score += 10
    if large_injections > 0:
        copy_risk_score += 25
    if paste_attempts > 1:
        copy_risk_score += 15
    if typing_anomaly_events > 0:
        copy_risk_score += 20

    return {
        "paste_attempts": paste_attempts,
        "large_injection_events": large_injections,
        "typing_anomaly_detected": typing_anomaly_events > 0,
        "typing_anomaly_events": typing_anomaly_events,
        "average_typing_speed_cps": round(avg_cps, 2),
        "copy_risk_score": copy_risk_score,
        "tab_switches": int(row.get("tab_switches", 0) or 0),
        "window_blur_seconds": float(row.get("window_blur_seconds", 0) or 0.0),
    }


def list_editor_activity_timeline(team_id: str, limit: int = 200) -> List[Dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=RD) as cur:
            cur.execute(
                """
                SELECT id, username, team_id, event,
                       editor_length_before, editor_length_after,
                       chars_delta, delta_ms, typing_speed_cps,
                       metadata, created_at
                FROM editor_activity_logs
                WHERE team_id=%s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (team_id, limit),
            )
            return _rows(cur)
