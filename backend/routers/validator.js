'use strict';
/**
 * Validator router — clone a participant's GitHub repo and run
 * section pytest tests against it, then record score + anti-cheat report.
 */

const router  = require('express').Router();
const path    = require('path');
const fs      = require('fs');
const os      = require('os');
const { execFileSync, spawn } = require('child_process');
const config  = require('../core/config');
const db      = require('../core/database');
const { requireAuth } = require('../middleware/auth');
const { verifyTestIntegrity, scanSuspiciousImports, hashSourceTree } = require('../anti_cheat');
const { buildRisk } = require('../risk_engine');

const SECTION_POINTS = { 1: 100, 2: 100, 3: 100, 4: 120 };
const SECTION_TESTS  = {
  1: 'section1-multifile-debug/tests',
  2: 'section2-broken-recovery/tests',
  3: 'section3-memory-deadlock/tests',
  4: 'section4-logical-tracing/tests',
};

// Clone with depth=1 and a strict timeout; no interactive prompts
function gitClone(url, dest) {
  return new Promise((resolve, reject) => {
    const env = {
      ...process.env,
      GIT_TERMINAL_PROMPT: '0',
      GIT_ASKPASS: 'echo',
    };
    const proc = spawn('git', [
      'clone', '-c', 'credential.helper=',
      '--depth=1', '--no-tags', url, dest,
    ], { env });

    let stderr = '';
    proc.stderr.on('data', d => { stderr += d.toString(); });

    const timer = setTimeout(() => {
      proc.kill('SIGKILL');
      reject(Object.assign(new Error('Clone timed out after 90s'), { status: 408 }));
    }, 90_000);

    proc.on('close', code => {
      clearTimeout(timer);
      if (code === 0) resolve();
      else reject(Object.assign(new Error(`git clone failed: ${stderr.slice(0, 400).trim()}`), { status: 422 }));
    });
    proc.on('error', err => { clearTimeout(timer); reject(err); });
  });
}

function runPytest(testPath, reportPath, cwd) {
  return new Promise((resolve, reject) => {
    const timeoutMs = (config.PYTEST_TIMEOUT + 30) * 1000;
    const proc = spawn('python3', [
      '-m', 'pytest', testPath,
      '--json-report', `--json-report-file=${reportPath}`,
      '--tb=no', '-q', `--timeout=${config.PYTEST_TIMEOUT}`,
    ], { cwd });

    let killed = false;
    const timer = setTimeout(() => {
      killed = true; proc.kill('SIGKILL');
      reject(Object.assign(new Error('pytest timed out'), { status: 408 }));
    }, timeoutMs);

    proc.on('close', () => { clearTimeout(timer); if (!killed) resolve(); });
    proc.on('error', err => { clearTimeout(timer); reject(err); });
  });
}

// POST /api/validate/editor-activity
router.post('/editor-activity', requireAuth, async (req, res, next) => {
  try {
    const { event, team_id, timestamp, editor_length_before=0, editor_length_after=0,
            chars_delta=0, delta_ms=0, typing_speed_cps=0, flags=[], details={} } = req.body;
    const teamId = team_id || req.user.team || req.user.sub || 'unknown';
    const id = await db.logEditorActivity({
      username: req.user.sub || '', teamId, event,
      editorLengthBefore: editor_length_before, editorLengthAfter: editor_length_after,
      charsDelta: chars_delta, deltaMs: delta_ms, typingSpeedCps: typing_speed_cps,
      metadata: { timestamp, flags, details },
    });
    res.json({ ok: true, id });
  } catch (err) { next(err); }
});

// POST /api/validate/section
router.post('/section', requireAuth, async (req, res, next) => {
  const { section, github_url: githubUrl } = req.body;

  if (!SECTION_TESTS[section])
    return res.status(422).json({ detail: 'section must be 1–4' });
  if (!githubUrl)
    return res.status(422).json({ detail: 'github_url is required' });

  // ── Timer check ──────────────────────────────────────────────────────────
  const timer = await db.getSectionTimer(section);
  if (timer && timer.submissions_locked)
    return res.status(423).json({ detail: `Section ${section} submissions are locked by the administrator.` });
  if (timer && !timer.is_active)
    return res.status(403).json({ detail: `Section ${section} has not been started yet by the administrator.` });
  if (timer && timer.is_active && timer.start_time) {
    const start    = new Date(timer.start_time);
    const pausedAt = timer.paused_at ? new Date(timer.paused_at) : null;
    const elapsed  = timer.elapsed_seconds || 0;
    const totalSecs = timer.duration_minutes * 60;
    const now = new Date();

    let remaining;
    if (pausedAt) {
      remaining = totalSecs - elapsed;
    } else {
      const runningSecs = Math.floor((now - start) / 1000);
      remaining = totalSecs - elapsed - runningSecs;
    }
    if (remaining <= 0)
      return res.status(403).json({ detail: `Section ${section} time has expired. No more submissions accepted.` });
  }

  const teamId = req.user.team || req.user.sub || 'unknown';

  // ── GitHub username enforcement ────────────────────────────────────────────
  const student = await db.getStudent(req.user.sub);
  const regGhUser = student ? (student.github_username || '').trim().toLowerCase() : '';
  if (!regGhUser)
    return res.status(422).json({ detail: 'You must set a GitHub username on the Dashboard before validating.' });

  // Extract owner from the submitted URL: https://github.com/<owner>/<repo>
  const ghUrlMatch = githubUrl.match(/^https:\/\/github\.com\/([^\/]+)\/([^\/]+?)(\.git)?$/i);
  if (!ghUrlMatch)
    return res.status(422).json({ detail: 'Invalid GitHub URL. Use the format: https://github.com/owner/repo' });
  const repoOwner = ghUrlMatch[1].toLowerCase();
  if (repoOwner !== regGhUser)
    return res.status(403).json({
      detail: `Repository owner "${ghUrlMatch[1]}" does not match your registered GitHub username "${student.github_username}". You may only submit from your own account.`,
    });

  let tmpdir = null;
  let reportPath = null;

  try {
    tmpdir = fs.mkdtempSync(path.join(os.tmpdir(), 'dc_validate_'));

    // ── Clone ───────────────────────────────────────────────────────────────────────
    await gitClone(githubUrl, tmpdir);


    // ── Verify tests exist ─────────────────────────────────────────────────
    const testPath = path.join(tmpdir, SECTION_TESTS[section]);
    if (!fs.existsSync(testPath))
      return res.status(422).json({
        detail: `Tests for section ${section} not found in repo. Expected: ${SECTION_TESTS[section]}`,
      });

    // ── Anti-cheat pre-checks ──────────────────────────────────────────────
    const { valid: testHashValid, mismatched: testHashMismatches } =
      verifyTestIntegrity(config.REPO_ROOT, tmpdir);
    const { imports: suspiciousImports, occurrences: suspiciousOccurrences } =
      scanSuspiciousImports(tmpdir);
    const submissionHash = hashSourceTree(tmpdir);

    const duplicateRow = await db.findDuplicateSubmissionHash(submissionHash, teamId);
    const duplicateDetected = duplicateRow !== null;
    const submissionRateLast10min = await db.countRecentSubmissions(teamId, 10);
    const copyMetrics = await db.getEditorActivityMetrics(teamId, 10);

    // ── Run pytest ─────────────────────────────────────────────────────────
    reportPath = path.join(os.tmpdir(), `dc_report_${Date.now()}_${Math.random().toString(36).slice(2)}.json`);
    const startTs = Date.now();
    try {
      await runPytest(testPath, reportPath, tmpdir);
    } catch (err) {
      if (err.status === 408) return res.status(408).json({ detail: 'Test run timed out' });
      // pytest exits non-zero when tests fail — that's fine; report will still exist
    }
    const duration = (Date.now() - startTs) / 1000;

    // ── Parse report ───────────────────────────────────────────────────────
    let report;
    try {
      report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    } catch {
      return res.status(500).json({ detail: 'Could not parse pytest report' });
    }

    const summary   = report.summary || {};
    const passed    = summary.passed  || 0;
    const failed    = (summary.failed || 0) + (summary.error || 0);
    const total     = summary.total   || (passed + failed);
    const skipped   = summary.skipped || 0;
    const collected = summary.collected || total;

    const maxPts = SECTION_POINTS[section];
    const score  = total ? Math.round((passed / total) * maxPts * 100) / 100 : 0;

    const rawOutput = report.tests
      ? report.tests.map(t => `${t.nodeid}: ${t.outcome}`).join('\n')
      : '';

    // ── Risk scoring ───────────────────────────────────────────────────────
    const { score: riskScore, flags: riskFlags, level: riskLevel } = buildRisk({
      testHashValid,
      testsCollected:           collected,
      testsSkipped:             skipped,
      suspiciousOccurrences,
      duplicateDetected,
      submissionRateLast10min,
      runtimeSeconds:           duration,
      pasteAttempts:            copyMetrics.paste_attempts,
      largeInjectionEvents:     copyMetrics.large_injection_events,
      typingAnomalyDetected:    copyMetrics.typing_anomaly_detected,
      copyRiskScore:            copyMetrics.copy_risk_score,
    });

    // ── Save anti-cheat report ─────────────────────────────────────────────
    const student = await db.getStudent(req.user.sub);
    const antiCheatId = await db.saveAntiCheatReport({
      username:                  req.user.sub,
      team_id:                   teamId,
      section,
      submission_hash:           submissionHash,
      tests_collected:           collected,
      tests_passed:              passed,
      tests_failed:              failed,
      tests_skipped:             skipped,
      runtime_seconds:           duration,
      cpu_usage_percent:         0,
      memory_usage_mb:           0,
      suspicious_imports:        suspiciousImports,
      test_hash_valid:           testHashValid,
      duplicate_detected:        duplicateDetected,
      submission_rate_last_10min: submissionRateLast10min,
      paste_attempts:            copyMetrics.paste_attempts,
      large_injection_events:    copyMetrics.large_injection_events,
      typing_anomaly_detected:   copyMetrics.typing_anomaly_detected,
      copy_risk_score:           copyMetrics.copy_risk_score,
      average_typing_speed_cps:  copyMetrics.average_typing_speed_cps,
      tab_switches:              copyMetrics.tab_switches,
      window_blur_seconds:       copyMetrics.window_blur_seconds,
      risk_score:                riskScore,
      risk_level:                riskLevel,
      risk_flags:                riskFlags,
      raw_pytest_output:         rawOutput,
    });

    // ── Upsert leaderboard ─────────────────────────────────────────────────
    await db.upsertScore({
      username:       req.user.sub,
      section,
      score,
      passedTests:    passed,
      totalTests:     total,
      timeTaken:      duration,
      fullName:       req.user.full_name || '',
      college:        req.user.college   || '',
      team:           req.user.team      || '',
      teamNo:         '',
      teamName:       req.user.team || '',
      commitNo:       '',
      githubRepoLink: githubUrl,
    });

    // ── Build per-test details ─────────────────────────────────────────────
    const tests = (report.tests || []).map(t => {
      let error = '';
      for (const phase of ['call', 'setup', 'teardown']) {
        const pd = t[phase] || {};
        if (['failed', 'error'].includes(pd.outcome)) {
          error = typeof pd.longrepr === 'object' ? (pd.longrepr?.repr || '') : (pd.longrepr || '');
          break;
        }
      }
      return {
        name:     (t.nodeid || '').split('::').pop(),
        outcome:  t.outcome,
        duration: Math.round((t.duration || 0) * 1000) / 1000,
        error:    t.outcome !== 'passed' ? error.trim() : '',
      };
    });

    res.json({
      section,
      score,
      max_score:          maxPts,
      passed,
      failed,
      total,
      skipped,
      duration_seconds:   Math.round(duration * 100) / 100,
      results:            tests,
      anti_cheat_report_id: antiCheatId,
      risk_level:         riskLevel,
      risk_score:         riskScore,
      risk_flags:         riskFlags,
    });

  } catch (err) {
    if (err.status) return res.status(err.status).json({ detail: err.message });
    next(err);
  } finally {
    // Always clean up temp files
    if (reportPath && fs.existsSync(reportPath)) {
      try { fs.unlinkSync(reportPath); } catch {}
    }
    if (tmpdir && fs.existsSync(tmpdir)) {
      try { fs.rmSync(tmpdir, { recursive: true, force: true }); } catch {}
    }
  }
});

module.exports = router;
