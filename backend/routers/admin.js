'use strict';
const router  = require('express').Router();
const multer  = require('multer');
const { parse } = require('csv-parse/sync');
let xlsx;
try { xlsx = require('xlsx'); } catch { xlsx = null; }
const db      = require('../core/database');
const { hashPassword } = require('../core/security');
const { requireAdmin } = require('../middleware/auth');

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } });

// ── Students ──────────────────────────────────────────────────────────────────

router.post('/students', requireAdmin, async (req, res, next) => {
  try {
    const { username, password, full_name='', email='', college='', team='' } = req.body;
    if (!username || !password) return res.status(400).json({ detail: 'username and password required' });
    const ok = await db.createStudent({ username: username.trim(), passwordHash: hashPassword(password),
      fullName: full_name, email, college, team });
    if (!ok) return res.status(409).json({ detail: 'Username or email already exists' });
    res.status(201).json({ message: 'Student created', username });
  } catch (err) { next(err); }
});

router.post('/students/import', requireAdmin, async (req, res, next) => {
  try {
    const students = req.body.students || [];
    const created = [], skipped = [];
    for (const s of students) {
      const ok = await db.createStudent({ username: (s.username || '').trim(),
        passwordHash: hashPassword(s.password), fullName: s.full_name || '',
        email: s.email || '', college: s.college || '', team: s.team || '' });
      (ok ? created : skipped).push(s.username);
    }
    res.json({ created: created.length, skipped: skipped.length, created_users: created, skipped_users: skipped });
  } catch (err) { next(err); }
});

router.post('/students/import-csv', requireAdmin, upload.single('file'), async (req, res, next) => {
  try {
    if (!req.file) return res.status(400).json({ detail: 'No file uploaded' });
    let rows;
    try {
      rows = parse(req.file.buffer.toString('utf8'), { columns: true, bom: true, skip_empty_lines: true });
    } catch (e) { return res.status(400).json({ detail: `CSV parse error: ${e.message}` }); }

    if (rows.length && (!rows[0].username || rows[0].password === undefined))
      return res.status(422).json({ detail: 'CSV must have columns: username, password' });

    const created = [], skipped = [];
    for (const row of rows) {
      const username = (row.username || '').trim();
      const password = (row.password || '').trim();
      if (!username || !password) { skipped.push(username || '(empty)'); continue; }
      const ok = await db.createStudent({ username, passwordHash: hashPassword(password),
        fullName: row.full_name || '', email: row.email || '',
        college: row.college || '', team: row.team || '' });
      (ok ? created : skipped).push(username);
    }
    res.json({ total_rows: rows.length, created: created.length, skipped: skipped.length,
               created_users: created, skipped_users: skipped });
  } catch (err) { next(err); }
});

router.get('/students', requireAdmin, async (_req, res, next) => {
  try {
    const students = await db.listStudents();
    res.json({ students, total: students.length });
  } catch (err) { next(err); }
});

router.put('/students/:username/reset-password', requireAdmin, async (req, res, next) => {
  try {
    const { new_password } = req.body;
    if (!new_password || new_password.length < 4)
      return res.status(422).json({ detail: 'Password too short' });
    await db.resetStudentPassword(req.params.username, hashPassword(new_password));
    res.json({ message: `Password reset for ${req.params.username}` });
  } catch (err) { next(err); }
});

router.put('/students/:username', requireAdmin, async (req, res, next) => {
  try {
    const { full_name, email, college, team, is_active } = req.body;
    await db.updateStudent(req.params.username, { fullName: full_name, email, college, team, isActive: is_active });
    res.json({ message: `Student ${req.params.username} updated` });
  } catch (err) { next(err); }
});

router.post('/students/:username/reactivate', requireAdmin, async (req, res, next) => {
  try {
    await db.reactivateStudent(req.params.username);
    res.json({ message: `${req.params.username} reactivated` });
  } catch (err) { next(err); }
});

router.delete('/students/:username', requireAdmin, async (req, res, next) => {
  try {
    await db.deactivateStudent(req.params.username);
    res.json({ message: `${req.params.username} deactivated` });
  } catch (err) { next(err); }
});

router.put('/students/:username/github', requireAdmin, async (req, res, next) => {
  try {
    const gh = (req.body.github_username || '').trim();
    await db.updateGithubUsername(req.params.username, gh);
    res.json({ message: `GitHub username set for ${req.params.username}`, github_username: gh });
  } catch (err) { next(err); }
});

// ── Leaderboard ────────────────────────────────────────────────────────────────

router.delete('/leaderboard', requireAdmin, async (_req, res, next) => {
  try { await db.resetLeaderboard(); res.json({ message: 'Leaderboard reset' }); }
  catch (err) { next(err); }
});

// ── Submissions log ────────────────────────────────────────────────────────────

router.get('/submissions', requireAdmin, async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit, 10) || 500;
    const rows  = await db.getSubmissionsLog(limit);
    res.json({ submissions: rows, total: rows.length });
  } catch (err) { next(err); }
});

// ── Timers ────────────────────────────────────────────────────────────────────

router.post('/timers/unlock-all', requireAdmin, async (req, res, next) => {
  try {
    const mins = parseInt(req.query.duration_minutes, 10) || 45;
    for (const s of [1,2,3,4]) await db.setSectionTimer(s, mins);
    res.json({ message: 'All 4 sections unlocked', duration_minutes: mins });
  } catch (err) { next(err); }
});

router.get('/timers', requireAdmin, async (_req, res, next) => {
  try { res.json({ timers: await db.getAllSectionTimers() }); }
  catch (err) { next(err); }
});

// POST /timers (body: { section, duration_minutes })
router.post('/timers', requireAdmin, async (req, res, next) => {
  try {
    const { section, duration_minutes = 45 } = req.body;
    if (![1,2,3,4].includes(section))
      return res.status(422).json({ detail: 'section must be 1–4' });
    await db.setSectionTimer(section, duration_minutes);
    res.json({ message: `Timer started for section ${section}`, duration_minutes });
  } catch (err) { next(err); }
});

// POST /timers/:section/start  — start/restart a section timer
router.post('/timers/:section/start', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    const mins = parseInt(req.query.duration_minutes || req.body.duration_minutes, 10) || 45;
    await db.setSectionTimer(s, mins);
    res.json({ message: `Timer started for section ${s}`, duration_minutes: mins });
  } catch (err) { next(err); }
});

// POST /timers/:section/reset  — reset a section timer back to stopped
router.post('/timers/:section/reset', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.resetSectionTimer(s);
    res.json({ message: `Timer reset for section ${s}` });
  } catch (err) { next(err); }
});

router.delete('/timers/:section', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.resetSectionTimer(s);
    res.json({ message: `Timer reset for section ${s}` });
  } catch (err) { next(err); }
});

router.patch('/timers/:section/pause', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.pauseSectionTimer(s);
    res.json({ message: `Timer paused for section ${s}` });
  } catch (err) { next(err); }
});

// POST /timers/:section/pause  — also accept POST for pause (frontend uses POST for all actions)
router.post('/timers/:section/pause', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.pauseSectionTimer(s);
    res.json({ message: `Timer paused for section ${s}` });
  } catch (err) { next(err); }
});

router.patch('/timers/:section/resume', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.resumeSectionTimer(s);
    res.json({ message: `Timer resumed for section ${s}` });
  } catch (err) { next(err); }
});

// POST /timers/:section/resume
router.post('/timers/:section/resume', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.resumeSectionTimer(s);
    res.json({ message: `Timer resumed for section ${s}` });
  } catch (err) { next(err); }
});

router.patch('/timers/:section/stop', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.stopSectionTimer(s);
    res.json({ message: `Section ${s} stopped — submissions closed` });
  } catch (err) { next(err); }
});

// POST /timers/:section/stop
router.post('/timers/:section/stop', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.stopSectionTimer(s);
    res.json({ message: `Section ${s} stopped — submissions closed` });
  } catch (err) { next(err); }
});

// POST /timers/:section/set-duration — update duration without changing active state
router.post('/timers/:section/set-duration', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    const mins = parseInt(req.body.duration_minutes, 10);
    if (!mins || mins < 1 || mins > 300) return res.status(422).json({ detail: 'duration_minutes must be 1–300' });
    await db.setTimerDuration(s, mins);
    res.json({ message: `Duration updated for section ${s}`, duration_minutes: mins });
  } catch (err) { next(err); }
});

// POST /timers/:section/lock-submissions
router.post('/timers/:section/lock-submissions', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.setSubmissionsLock(s, true);
    res.json({ message: `Submissions locked for section ${s}` });
  } catch (err) { next(err); }
});

// POST /timers/:section/unlock-submissions
router.post('/timers/:section/unlock-submissions', requireAdmin, async (req, res, next) => {
  try {
    const s = parseInt(req.params.section, 10);
    if (![1,2,3,4].includes(s)) return res.status(422).json({ detail: 'section must be 1–4' });
    await db.setSubmissionsLock(s, false);
    res.json({ message: `Submissions unlocked for section ${s}` });
  } catch (err) { next(err); }
});

// ── Anti-cheat monitor ────────────────────────────────────────────────────────

router.get('/activity-monitor', requireAdmin, async (req, res, next) => {
  try {
    const limit = Math.min(Math.max(parseInt(req.query.limit,10)||200, 1), 500);
    const rows  = await db.listAntiCheatReports(limit, false);
    res.json({
      submissions: rows.map(r => ({
        id: r.id, team: r.team_id, username: r.username,
        passed: r.tests_passed, total: 57,
        runtime_seconds: r.runtime_seconds, risk_score: r.risk_score, risk_level: r.risk_level,
        duplicate_detected: r.duplicate_detected, test_hash_valid: r.test_hash_valid,
        suspicious_imports_count: (r.suspicious_imports||[]).length,
        paste_attempts: r.paste_attempts, large_injection_events: r.large_injection_events,
        typing_speed_cps: r.average_typing_speed_cps, copy_risk_score: r.copy_risk_score,
        tab_switches: r.tab_switches, window_blur_seconds: r.window_blur_seconds,
        last_submission_time: r.created_at,
      })),
      count: rows.length,
    });
  } catch (err) { next(err); }
});

router.get('/activity-monitor/flagged', requireAdmin, async (req, res, next) => {
  try {
    const limit = Math.min(Math.max(parseInt(req.query.limit,10)||200, 1), 500);
    const rows  = await db.listAntiCheatReports(limit, true);
    res.json({
      flagged: rows.map(r => ({
        id: r.id, team: r.team_id, username: r.username,
        risk_score: r.risk_score, risk_level: r.risk_level, risk_flags: r.risk_flags,
        duplicate_detected: r.duplicate_detected, duplicate_pair_hash: r.submission_hash,
        test_hash_valid: r.test_hash_valid, suspicious_imports: r.suspicious_imports,
        paste_attempts: r.paste_attempts, large_injection_events: r.large_injection_events,
        typing_speed_cps: r.average_typing_speed_cps, copy_risk_score: r.copy_risk_score,
        created_at: r.created_at,
      })),
      count: rows.length,
    });
  } catch (err) { next(err); }
});

router.get('/activity-monitor/:id', requireAdmin, async (req, res, next) => {
  try {
    const row = await db.getAntiCheatReport(parseInt(req.params.id, 10));
    if (!row) return res.status(404).json({ detail: 'Report not found' });
    const timeline = await db.listEditorActivityTimeline(row.team_id || '', 150);
    res.json({
      ...row,
      risk_explanation: (row.risk_flags || []).join(' ; ') || 'No risk flags',
      timeline: [...timeline].reverse(),
    });
  } catch (err) { next(err); }
});

// ── Teams CRUD ────────────────────────────────────────────────────────────────

// GET /teams — list all teams with live scores
router.get('/teams', requireAdmin, async (_req, res, next) => {
  try {
    const teams = await db.listTeams();
    res.json({ teams, total: teams.length });
  } catch (err) { next(err); }
});

// POST /teams — create a team
router.post('/teams', requireAdmin, async (req, res, next) => {
  try {
    const { team_id, team_name, password, college='' } = req.body;
    if (!team_id || !team_name || !password)
      return res.status(400).json({ detail: 'team_id, team_name, and password are required' });
    const ok = await db.createTeam({ teamId: team_id.trim(), teamName: team_name.trim(),
      passwordHash: hashPassword(password), college });
    if (!ok) return res.status(409).json({ detail: 'Team ID already exists' });
    res.status(201).json({ message: 'Team created', team_id });
  } catch (err) { next(err); }
});

// PUT /teams/:team_id — update name / college / password
router.put('/teams/:team_id', requireAdmin, async (req, res, next) => {
  try {
    const { team_name, college, password } = req.body;
    const passwordHash = password ? hashPassword(password) : undefined;
    await db.updateTeam(req.params.team_id, { teamName: team_name, college, passwordHash });
    res.json({ message: `Team ${req.params.team_id} updated` });
  } catch (err) { next(err); }
});

// DELETE /teams/:team_id
router.delete('/teams/:team_id', requireAdmin, async (req, res, next) => {
  try {
    await db.deleteTeam(req.params.team_id);
    res.json({ message: `Team ${req.params.team_id} deleted` });
  } catch (err) { next(err); }
});

// GET /teams/leaderboard — team aggregated scores
router.get('/teams/leaderboard', requireAdmin, async (_req, res, next) => {
  try {
    const rows = await db.getTeamLeaderboard();
    res.json({ leaderboard: rows, total: rows.length });
  } catch (err) { next(err); }
});

// POST /teams/import-json — bulk create teams from JSON array
router.post('/teams/import-json', requireAdmin, async (req, res, next) => {
  try {
    const teams = req.body.teams || req.body;
    if (!Array.isArray(teams)) return res.status(400).json({ detail: 'Body must be an array or { teams: [...] }' });
    const created = [], skipped = [], errors = [];
    for (const t of teams) {
      if (!t.team_id || !t.team_name || !t.password) { errors.push(t.team_id || '?'); continue; }
      const ok = await db.createTeam({ teamId: (t.team_id||'').trim(), teamName: (t.team_name||'').trim(),
        passwordHash: hashPassword(t.password), college: t.college||'' });
      (ok ? created : skipped).push(t.team_id);
    }
    res.json({ created: created.length, skipped: skipped.length, errors: errors.length,
               created_teams: created, skipped_teams: skipped, error_teams: errors });
  } catch (err) { next(err); }
});

// POST /teams/import-xlsx — bulk create teams from Excel file (columns: team_id, team_name, password, college?)
router.post('/teams/import-xlsx', requireAdmin, upload.single('file'), async (req, res, next) => {
  try {
    if (!req.file) return res.status(400).json({ detail: 'No file uploaded' });
    if (!xlsx) return res.status(501).json({ detail: 'xlsx package not installed on server' });

    let rows;
    try {
      const wb   = xlsx.read(req.file.buffer, { type: 'buffer' });
      const ws   = wb.Sheets[wb.SheetNames[0]];
      rows = xlsx.utils.sheet_to_json(ws, { defval: '' });
    } catch (e) { return res.status(400).json({ detail: `Excel parse error: ${e.message}` }); }

    if (!rows.length) return res.status(422).json({ detail: 'Spreadsheet is empty' });
    const first = rows[0];
    if (!first.team_id || !first.team_name || first.password === undefined)
      return res.status(422).json({ detail: 'Spreadsheet must have columns: team_id, team_name, password (and optionally college)' });

    const created = [], skipped = [], errors = [];
    for (const row of rows) {
      const tid = String(row.team_id||'').trim();
      const tname = String(row.team_name||'').trim();
      const pwd = String(row.password||'').trim();
      if (!tid || !tname || !pwd) { errors.push(tid||'(empty)'); continue; }
      const ok = await db.createTeam({ teamId: tid, teamName: tname,
        passwordHash: hashPassword(pwd), college: String(row.college||'').trim() });
      (ok ? created : skipped).push(tid);
    }
    res.json({ total_rows: rows.length, created: created.length, skipped: skipped.length, errors: errors.length,
               created_teams: created, skipped_teams: skipped, error_teams: errors });
  } catch (err) { next(err); }
});

module.exports = router;
