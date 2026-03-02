-- =============================================================================
-- Debugging Championship 2026 — PostgreSQL Schema
-- =============================================================================
-- Usage:
--   psql -h <host> -U <user> -d <dbname> -f schema.sql
--
-- Railway:
--   Copy the DATABASE_URL from Railway → Postgres service → Variables tab, then:
--   psql "<DATABASE_URL>" -f schema.sql
-- =============================================================================

-- ── students ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    id            SERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT    NOT NULL DEFAULT '',
    email         TEXT,
    college       TEXT    NOT NULL DEFAULT '',
    team          TEXT    NOT NULL DEFAULT '',
    github_username TEXT  NOT NULL DEFAULT '',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ
);

-- ── submissions ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS submissions (
    id               SERIAL PRIMARY KEY,
    username         TEXT    NOT NULL,
    section          INTEGER NOT NULL,
    score            REAL    NOT NULL,
    passed_tests     INTEGER NOT NULL,
    total_tests      INTEGER NOT NULL,
    time_taken       REAL,
    team_no          TEXT    NOT NULL DEFAULT '',
    team_name        TEXT    NOT NULL DEFAULT '',
    commit_no        TEXT    NOT NULL DEFAULT '',
    github_repo_link TEXT    NOT NULL DEFAULT '',
    submitted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sub_username ON submissions(username);
CREATE INDEX IF NOT EXISTS idx_sub_section  ON submissions(section);

-- ── leaderboard ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leaderboard (
    username    TEXT PRIMARY KEY,
    full_name   TEXT NOT NULL DEFAULT '',
    college     TEXT NOT NULL DEFAULT '',
    team        TEXT NOT NULL DEFAULT '',
    total_score REAL NOT NULL DEFAULT 0,
    section1    REAL NOT NULL DEFAULT 0,
    section2    REAL NOT NULL DEFAULT 0,
    section3    REAL NOT NULL DEFAULT 0,
    section4    REAL NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lb_total ON leaderboard(total_score DESC);

-- ── section_timers ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS section_timers (
    section             INTEGER PRIMARY KEY,
    duration_minutes    INTEGER NOT NULL DEFAULT 45,
    start_time          TIMESTAMPTZ,
    is_active           BOOLEAN NOT NULL DEFAULT FALSE,
    paused_at           TIMESTAMPTZ,
    elapsed_seconds     INTEGER NOT NULL DEFAULT 0,
    submissions_locked  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Migration: add submissions_locked to existing deployments
ALTER TABLE section_timers ADD COLUMN IF NOT EXISTS submissions_locked BOOLEAN NOT NULL DEFAULT FALSE;

-- Seed default timers (section durations in minutes)
INSERT INTO section_timers (section, duration_minutes) VALUES
    (1, 45),
    (2, 40),
    (3, 50),
    (4, 35)
ON CONFLICT (section) DO NOTHING;

-- ── anti_cheat_reports ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS anti_cheat_reports (
    id                           SERIAL PRIMARY KEY,
    username                     TEXT    NOT NULL,
    team_id                      TEXT    NOT NULL DEFAULT '',
    section                      INTEGER NOT NULL,
    submission_hash              TEXT    NOT NULL,
    tests_collected              INTEGER NOT NULL DEFAULT 0,
    tests_passed                 INTEGER NOT NULL DEFAULT 0,
    tests_failed                 INTEGER NOT NULL DEFAULT 0,
    tests_skipped                INTEGER NOT NULL DEFAULT 0,
    runtime_seconds              REAL    NOT NULL DEFAULT 0,
    cpu_usage_percent            REAL    NOT NULL DEFAULT 0,
    memory_usage_mb              REAL    NOT NULL DEFAULT 0,
    suspicious_imports           JSONB   NOT NULL DEFAULT '[]'::jsonb,
    test_hash_valid              BOOLEAN NOT NULL DEFAULT TRUE,
    duplicate_detected           BOOLEAN NOT NULL DEFAULT FALSE,
    submission_rate_last_10min   INTEGER NOT NULL DEFAULT 0,
    paste_attempts               INTEGER NOT NULL DEFAULT 0,
    large_injection_events       INTEGER NOT NULL DEFAULT 0,
    typing_anomaly_detected      BOOLEAN NOT NULL DEFAULT FALSE,
    copy_risk_score              INTEGER NOT NULL DEFAULT 0,
    average_typing_speed_cps     REAL    NOT NULL DEFAULT 0,
    tab_switches                 INTEGER NOT NULL DEFAULT 0,
    window_blur_seconds          REAL    NOT NULL DEFAULT 0,
    risk_score                   INTEGER NOT NULL DEFAULT 0,
    risk_level                   TEXT    NOT NULL DEFAULT 'Low',
    risk_flags                   JSONB   NOT NULL DEFAULT '[]'::jsonb,
    raw_pytest_output            TEXT    NOT NULL DEFAULT '',
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_acr_created_at      ON anti_cheat_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_acr_team_id         ON anti_cheat_reports(team_id);
CREATE INDEX IF NOT EXISTS idx_acr_submission_hash ON anti_cheat_reports(submission_hash);
CREATE INDEX IF NOT EXISTS idx_acr_username        ON anti_cheat_reports(username);

-- ── editor_activity_logs ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS editor_activity_logs (
    id                   SERIAL PRIMARY KEY,
    username             TEXT    NOT NULL,
    team_id              TEXT    NOT NULL DEFAULT '',
    event                TEXT    NOT NULL,
    editor_length_before INTEGER NOT NULL DEFAULT 0,
    editor_length_after  INTEGER NOT NULL DEFAULT 0,
    chars_delta          INTEGER NOT NULL DEFAULT 0,
    delta_ms             INTEGER NOT NULL DEFAULT 0,
    typing_speed_cps     REAL    NOT NULL DEFAULT 0,
    metadata             JSONB   NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eal_team_time ON editor_activity_logs(team_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eal_user_time ON editor_activity_logs(username, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eal_event     ON editor_activity_logs(event);
