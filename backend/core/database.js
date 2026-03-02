'use strict';
/**
 * PostgreSQL database layer using pg.Pool.
 * All queries are async/await.
 */

const { Pool }  = require('pg');
const crypto    = require('crypto');
const config    = require('./config');

const pool = new Pool({
  connectionString: config.DATABASE_URL,
  max:                    10,
  min:                    1,
  idleTimeoutMillis:      30_000,
  connectionTimeoutMillis: 5_000,
});

// Simple query helper
async function q(text, params) {
  const res = await pool.query(text, params);
  return res;
}

// ── Schema ────────────────────────────────────────────────────────────────────

async function initDb() {
  await q(`
    CREATE TABLE IF NOT EXISTS students (
      id            SERIAL PRIMARY KEY,
      username      TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      full_name     TEXT DEFAULT '',
      email         TEXT,
      college       TEXT DEFAULT '',
      team          TEXT DEFAULT '',
      github_username TEXT DEFAULT '',
      is_active     BOOLEAN DEFAULT TRUE,
      is_admin      BOOLEAN DEFAULT FALSE,
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
      team_no      TEXT DEFAULT '',
      team_name    TEXT DEFAULT '',
      commit_no    TEXT DEFAULT '',
      github_repo_link TEXT DEFAULT '',
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

    CREATE TABLE IF NOT EXISTS section_timers (
      section          INTEGER PRIMARY KEY,
      duration_minutes INTEGER NOT NULL DEFAULT 45,
      start_time       TIMESTAMPTZ,
      is_active        BOOLEAN DEFAULT FALSE,
      paused_at        TIMESTAMPTZ,
      elapsed_seconds  INTEGER DEFAULT 0
    );

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

    CREATE INDEX IF NOT EXISTS idx_acr_created_at ON anti_cheat_reports(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_acr_team_id ON anti_cheat_reports(team_id);
    CREATE INDEX IF NOT EXISTS idx_acr_submission_hash ON anti_cheat_reports(submission_hash);

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
  `);
  console.log('Database schema initialised');

  // ── Seed admin user ────────────────────────────────────────────────────────
  // Reads ADMIN_USERNAME / ADMIN_PASSWORD from env (defaults: admin / heisenberg)
  // Uses ON CONFLICT so it only updates when credentials change.
  const adminUser = process.env.ADMIN_USERNAME || 'admin';
  const adminPass = process.env.ADMIN_PASSWORD || 'heisenberg';
  const salt      = crypto.randomBytes(16).toString('hex');
  const hash      = crypto.pbkdf2Sync(adminPass, salt, 260000, 32, 'sha256').toString('hex');
  const adminHash = `pbkdf2:sha256:260000:${salt}:${hash}`;
  await q(
    `INSERT INTO students (username, password_hash, full_name, is_active, is_admin)
     VALUES ($1, $2, 'Administrator', TRUE, TRUE)
     ON CONFLICT (username) DO UPDATE
       SET password_hash = EXCLUDED.password_hash,
           is_active     = TRUE,
           is_admin      = TRUE`,
    [adminUser, adminHash]
  );
  console.log(`Admin user '${adminUser}' seeded`);

  // ── Seed default student users ─────────────────────────────────────────────
  const seedStudents = [
    { username: 'battery', password: 'govinda', full_name: 'battery' },
  ];
  for (const s of seedStudents) {
    const ss   = crypto.randomBytes(16).toString('hex');
    const sh   = crypto.pbkdf2Sync(s.password, ss, 260000, 32, 'sha256').toString('hex');
    const shash = `pbkdf2:sha256:260000:${ss}:${sh}`;
    await q(
      `INSERT INTO students (username, password_hash, full_name, is_active, is_admin)
       VALUES ($1, $2, $3, TRUE, FALSE)
       ON CONFLICT (username) DO UPDATE
         SET password_hash = EXCLUDED.password_hash,
             is_active     = TRUE`,
      [s.username, shash, s.full_name]
    );
    console.log(`Student '${s.username}' seeded`);
  }
}

// ── Students ──────────────────────────────────────────────────────────────────

async function createStudent({ username, passwordHash, fullName='', email='', college='', team='', githubUsername='', isAdmin=false }) {
  try {
    await q(
      `INSERT INTO students (username,password_hash,full_name,email,college,team,github_username,is_admin)
       VALUES ($1,$2,$3,NULLIF($4,''),$5,$6,$7,$8)`,
      [username, passwordHash, fullName, email, college, team, githubUsername, isAdmin]
    );
    return true;
  } catch (err) {
    if (err.code === '23505') return false; // unique violation
    throw err;
  }
}

async function getStudent(username) {
  const res = await q('SELECT * FROM students WHERE username=$1 AND is_active=TRUE', [username]);
  return res.rows[0] || null;
}

async function listStudents() {
  const res = await q('SELECT * FROM students ORDER BY created_at DESC');
  return res.rows;
}

async function updateLastLogin(username) {
  await q('UPDATE students SET last_login=NOW() WHERE username=$1', [username]);
}

async function updateStudent(username, { fullName, email, college, team, isActive }) {
  const fields = [], vals = [];
  if (fullName  !== undefined && fullName  !== null) { fields.push(`full_name=$${fields.length+1}`);  vals.push(fullName); }
  if (email     !== undefined && email     !== null) { fields.push(`email=$${fields.length+1}`);      vals.push(email || null); }
  if (college   !== undefined && college   !== null) { fields.push(`college=$${fields.length+1}`);    vals.push(college); }
  if (team      !== undefined && team      !== null) { fields.push(`team=$${fields.length+1}`);       vals.push(team); }
  if (isActive  !== undefined && isActive  !== null) { fields.push(`is_active=$${fields.length+1}`);  vals.push(isActive); }
  if (!fields.length) return;
  vals.push(username);
  await q(`UPDATE students SET ${fields.join(', ')} WHERE username=$${vals.length}`, vals);
}

async function resetStudentPassword(username, newHash) {
  await q('UPDATE students SET password_hash=$1 WHERE username=$2', [newHash, username]);
}

async function deactivateStudent(username) {
  await q('UPDATE students SET is_active=FALSE WHERE username=$1', [username]);
}

async function reactivateStudent(username) {
  await q('UPDATE students SET is_active=TRUE WHERE username=$1', [username]);
}

async function updateGithubUsername(username, githubUsername) {
  await q('UPDATE students SET github_username=$1 WHERE username=$2', [githubUsername, username]);
}

// ── Leaderboard ───────────────────────────────────────────────────────────────

async function upsertScore({ username, section, score, passedTests, totalTests, timeTaken,
  fullName='', college='', team='', teamNo='', teamName='', commitNo='', githubRepoLink='' }) {
  const sec = `section${section}`;
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query(
      `INSERT INTO submissions (username,section,score,passed_tests,total_tests,time_taken,
         team_no,team_name,commit_no,github_repo_link)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`,
      [username, section, score, passedTests, totalTests, timeTaken,
       teamNo, teamName, commitNo, githubRepoLink]
    );
    await client.query(`
      INSERT INTO leaderboard (username,full_name,college,team,${sec},total_score)
      VALUES ($1,$2,$3,$4,$5,$5)
      ON CONFLICT (username) DO UPDATE SET
        full_name   = EXCLUDED.full_name,
        college     = EXCLUDED.college,
        team        = EXCLUDED.team,
        ${sec}      = GREATEST(leaderboard.${sec}, EXCLUDED.${sec}),
        total_score = (
          GREATEST(leaderboard.section1, CASE WHEN $6=1 THEN EXCLUDED.${sec} ELSE leaderboard.section1 END) +
          GREATEST(leaderboard.section2, CASE WHEN $6=2 THEN EXCLUDED.${sec} ELSE leaderboard.section2 END) +
          GREATEST(leaderboard.section3, CASE WHEN $6=3 THEN EXCLUDED.${sec} ELSE leaderboard.section3 END) +
          GREATEST(leaderboard.section4, CASE WHEN $6=4 THEN EXCLUDED.${sec} ELSE leaderboard.section4 END)
        ),
        updated_at  = NOW()
    `, [username, fullName, college, team, score, section]);
    await client.query('COMMIT');
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}

async function getLeaderboard() {
  const res = await q(`
    SELECT username,full_name,college,team,
           total_score,section1,section2,section3,section4
    FROM leaderboard ORDER BY total_score DESC, updated_at ASC
  `);
  return res.rows;
}

async function getUserScores(username) {
  const res = await q('SELECT * FROM leaderboard WHERE username=$1', [username]);
  return res.rows[0] || null;
}

async function getSubmissionsLog(limit = 500) {
  const res = await q(`
    SELECT s.id, s.username, st.full_name, s.section,
           s.score, s.passed_tests, s.total_tests, s.time_taken,
           s.team_no, s.team_name, s.commit_no, s.github_repo_link,
           s.submitted_at
    FROM submissions s
    LEFT JOIN students st ON st.username = s.username
    ORDER BY s.submitted_at DESC
    LIMIT $1
  `, [Math.min(Math.max(limit, 1), 1000)]);
  return res.rows;
}

async function resetLeaderboard() {
  await q('TRUNCATE submissions, leaderboard');
}

// ── Section Timers ────────────────────────────────────────────────────────────

async function setSectionTimer(section, durationMinutes, startTime = null) {
  const st = startTime || new Date();
  await q(`
    INSERT INTO section_timers (section,duration_minutes,start_time,is_active,paused_at,elapsed_seconds)
    VALUES ($1,$2,$3,TRUE,NULL,0)
    ON CONFLICT (section) DO UPDATE SET
      duration_minutes = $2,
      start_time       = $3,
      is_active        = TRUE,
      paused_at        = NULL,
      elapsed_seconds  = 0
  `, [section, durationMinutes, st]);
}

async function pauseSectionTimer(section) {
  await q(`
    UPDATE section_timers SET paused_at=NOW()
    WHERE section=$1 AND is_active=TRUE AND paused_at IS NULL
  `, [section]);
}

async function resumeSectionTimer(section) {
  await q(`
    UPDATE section_timers
    SET elapsed_seconds = elapsed_seconds + EXTRACT(EPOCH FROM (NOW() - paused_at))::INTEGER,
        start_time      = NOW(),
        paused_at       = NULL
    WHERE section=$1 AND is_active=TRUE AND paused_at IS NOT NULL
  `, [section]);
}

async function stopSectionTimer(section) {
  await q(`UPDATE section_timers SET is_active=FALSE, paused_at=NULL WHERE section=$1`, [section]);
}

async function resetSectionTimer(section) {
  await q(`
    UPDATE section_timers
    SET is_active=FALSE, start_time=NULL, paused_at=NULL, elapsed_seconds=0
    WHERE section=$1
  `, [section]);
}

async function getSectionTimer(section) {
  const res = await q('SELECT * FROM section_timers WHERE section=$1', [section]);
  return res.rows[0] || null;
}

async function getAllSectionTimers() {
  const res = await q('SELECT * FROM section_timers ORDER BY section');
  return res.rows;
}

// ── Anti-cheat ────────────────────────────────────────────────────────────────

async function saveAntiCheatReport(report) {
  const res = await q(`
    INSERT INTO anti_cheat_reports (
      username, team_id, section, submission_hash,
      tests_collected, tests_passed, tests_failed, tests_skipped,
      runtime_seconds, cpu_usage_percent, memory_usage_mb,
      suspicious_imports, test_hash_valid, duplicate_detected,
      submission_rate_last_10min, paste_attempts, large_injection_events,
      typing_anomaly_detected, copy_risk_score, average_typing_speed_cps,
      tab_switches, window_blur_seconds,
      risk_score, risk_level, risk_flags, raw_pytest_output
    ) VALUES (
      $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,
      $12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26
    ) RETURNING id
  `, [
    report.username || '',
    report.team_id || '',
    report.section || 0,
    report.submission_hash || '',
    report.tests_collected || 0,
    report.tests_passed || 0,
    report.tests_failed || 0,
    report.tests_skipped || 0,
    report.runtime_seconds || 0,
    report.cpu_usage_percent || 0,
    report.memory_usage_mb || 0,
    JSON.stringify(report.suspicious_imports || []),
    report.test_hash_valid !== false,
    report.duplicate_detected || false,
    report.submission_rate_last_10min || 0,
    report.paste_attempts || 0,
    report.large_injection_events || 0,
    report.typing_anomaly_detected || false,
    report.copy_risk_score || 0,
    report.average_typing_speed_cps || 0,
    report.tab_switches || 0,
    report.window_blur_seconds || 0,
    report.risk_score || 0,
    report.risk_level || 'Low',
    JSON.stringify(report.risk_flags || []),
    report.raw_pytest_output || '',
  ]);
  return res.rows[0].id;
}

async function findDuplicateSubmissionHash(submissionHash, teamId) {
  const res = await q(`
    SELECT id, username, team_id, submission_hash, created_at
    FROM anti_cheat_reports
    WHERE submission_hash=$1 AND team_id<>$2
    ORDER BY created_at DESC LIMIT 1
  `, [submissionHash, teamId]);
  return res.rows[0] || null;
}

async function countRecentSubmissions(teamId, minutes = 10) {
  const res = await q(`
    SELECT COUNT(*) FROM anti_cheat_reports
    WHERE team_id=$1 AND created_at >= NOW() - ($2::text||' minutes')::interval
  `, [teamId, minutes]);
  return parseInt(res.rows[0].count, 10);
}

async function listAntiCheatReports(limit = 200, flaggedOnly = false) {
  const cond = flaggedOnly ? 'WHERE risk_score >= 60' : '';
  const res = await q(
    `SELECT * FROM anti_cheat_reports ${cond} ORDER BY created_at DESC LIMIT $1`,
    [Math.min(Math.max(limit, 1), 500)]
  );
  return res.rows;
}

async function getAntiCheatReport(id) {
  const res = await q('SELECT * FROM anti_cheat_reports WHERE id=$1', [id]);
  return res.rows[0] || null;
}

// ── Editor activity ───────────────────────────────────────────────────────────

async function logEditorActivity({ username, teamId, event, editorLengthBefore=0, editorLengthAfter=0,
  charsDelta=0, deltaMs=0, typingSpeedCps=0, metadata={} }) {
  const res = await q(`
    INSERT INTO editor_activity_logs
      (username,team_id,event,editor_length_before,editor_length_after,
       chars_delta,delta_ms,typing_speed_cps,metadata)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id
  `, [username, teamId, event,
      parseInt(editorLengthBefore) || 0, parseInt(editorLengthAfter) || 0,
      parseInt(charsDelta) || 0, parseInt(deltaMs) || 0,
      parseFloat(typingSpeedCps) || 0,
      JSON.stringify(metadata)]);
  return res.rows[0].id;
}

async function getEditorActivityMetrics(teamId, minutes = 10) {
  const res = await q(`
    SELECT
      COALESCE(SUM(CASE WHEN event='paste_attempt' THEN 1 ELSE 0 END),0) AS paste_attempts,
      COALESCE(SUM(CASE WHEN event='large_injection' THEN 1 ELSE 0 END),0) AS large_injection_events,
      COALESCE(SUM(CASE WHEN event='typing_anomaly' THEN 1 ELSE 0 END),0) AS typing_anomaly_events,
      COALESCE(AVG(CASE WHEN typing_speed_cps > 0 THEN typing_speed_cps END),0) AS average_typing_speed_cps,
      COALESCE(SUM(CASE WHEN event='tab_switch' THEN 1 ELSE 0 END),0) AS tab_switches,
      COALESCE(SUM(CASE WHEN event='window_blur'
        THEN COALESCE((metadata->'details'->>'blur_seconds')::REAL,0) ELSE 0 END),0) AS window_blur_seconds
    FROM editor_activity_logs
    WHERE team_id=$1 AND created_at >= NOW() - ($2::text||' minutes')::interval
  `, [teamId, minutes]);

  const row = res.rows[0] || {};
  const pasteAttempts      = parseInt(row.paste_attempts, 10) || 0;
  const largeInjections    = parseInt(row.large_injection_events, 10) || 0;
  const typingAnomalyEvents = parseInt(row.typing_anomaly_events, 10) || 0;
  const avgCps             = parseFloat(row.average_typing_speed_cps) || 0;

  let copyRiskScore = 0;
  if (pasteAttempts > 0) copyRiskScore += 10;
  if (largeInjections > 0) copyRiskScore += 25;
  if (pasteAttempts > 1) copyRiskScore += 15;
  if (typingAnomalyEvents > 0) copyRiskScore += 20;

  return {
    paste_attempts:           pasteAttempts,
    large_injection_events:   largeInjections,
    typing_anomaly_detected:  typingAnomalyEvents > 0,
    typing_anomaly_events:    typingAnomalyEvents,
    average_typing_speed_cps: Math.round(avgCps * 100) / 100,
    copy_risk_score:          copyRiskScore,
    tab_switches:             parseInt(row.tab_switches, 10) || 0,
    window_blur_seconds:      parseFloat(row.window_blur_seconds) || 0,
  };
}

async function listEditorActivityTimeline(teamId, limit = 200) {
  const res = await q(`
    SELECT id, username, team_id, event,
           editor_length_before, editor_length_after,
           chars_delta, delta_ms, typing_speed_cps, metadata, created_at
    FROM editor_activity_logs WHERE team_id=$1
    ORDER BY created_at DESC LIMIT $2
  `, [teamId, limit]);
  return res.rows;
}

module.exports = {
  pool, initDb,
  createStudent, getStudent, listStudents, updateLastLogin,
  updateStudent, resetStudentPassword, deactivateStudent, reactivateStudent, updateGithubUsername,
  upsertScore, getLeaderboard, getUserScores, getSubmissionsLog, resetLeaderboard,
  setSectionTimer, pauseSectionTimer, resumeSectionTimer, stopSectionTimer,
  resetSectionTimer, getSectionTimer, getAllSectionTimers,
  saveAntiCheatReport, findDuplicateSubmissionHash, countRecentSubmissions,
  listAntiCheatReports, getAntiCheatReport,
  logEditorActivity, getEditorActivityMetrics, listEditorActivityTimeline,
};
