'use strict';
const router = require('express').Router();
const path   = require('path');
const fs     = require('fs');
const { spawn } = require('child_process');
const config = require('../core/config');
const { requireAdmin } = require('../middleware/auth');

const SECTION_POINTS = { 1: 100, 2: 100, 3: 100, 4: 120 };
const SECTION_TESTS  = {
  1: 'section1-multifile-debug/tests',
  2: 'section2-broken-recovery/tests',
  3: 'section3-memory-deadlock/tests',
  4: 'section4-logical-tracing/tests',
};

function runPytest(testPath, reportPath) {
  return new Promise((resolve, reject) => {
    const timeout = (config.PYTEST_TIMEOUT + 10) * 1000;
    const proc = spawn('python3', [
      '-m', 'pytest', testPath,
      '--json-report', `--json-report-file=${reportPath}`,
      '--tb=no', '-q',
      `--timeout=${config.PYTEST_TIMEOUT}`,
    ], { cwd: config.REPO_ROOT });

    let killed = false;
    const timer = setTimeout(() => {
      killed = true;
      proc.kill('SIGKILL');
      reject(new Error('timeout'));
    }, timeout);

    proc.on('close', () => {
      clearTimeout(timer);
      if (!killed) resolve();
    });
    proc.on('error', err => { clearTimeout(timer); reject(err); });
  });
}

// POST /api/run/section
router.post('/section', requireAdmin, async (req, res, next) => {
  try {
    const section = parseInt(req.body.section, 10);
    if (!SECTION_TESTS[section])
      return res.status(422).json({ detail: 'section must be 1–4' });

    const testPath   = path.normalize(path.join(config.REPO_ROOT, SECTION_TESTS[section]));
    if (!fs.existsSync(testPath))
      return res.status(500).json({ detail: `Test directory not found: ${testPath}` });

    const reportPath = path.join(require('os').tmpdir(), `dc_run_${Date.now()}.json`);
    const startTs    = Date.now();

    try {
      await runPytest(testPath, reportPath);
    } catch (err) {
      if (err.message === 'timeout') return res.status(408).json({ detail: 'Test run timed out' });
      return next(err);
    }
    const duration = (Date.now() - startTs) / 1000;

    let report;
    try {
      report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
      fs.unlinkSync(reportPath);
    } catch {
      return res.status(500).json({ detail: 'Could not parse pytest report' });
    }

    const summary  = report.summary || {};
    const passed   = summary.passed || 0;
    const failed   = (summary.failed || 0) + (summary.error || 0);
    const total    = summary.total  || passed + failed;
    const maxPts   = SECTION_POINTS[section];
    const score    = total ? Math.round((passed / total) * maxPts * 100) / 100 : 0;

    const tests = (report.tests || []).map(t => {
      let error = '';
      for (const phase of ['call', 'setup', 'teardown']) {
        const pd = t[phase] || {};
        if (['failed', 'error'].includes(pd.outcome)) {
          error = typeof pd.longrepr === 'object' ? (pd.longrepr.repr || '') : (pd.longrepr || '');
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

    res.json({ section, passed, failed, total, score, max_score: maxPts,
               duration_seconds: Math.round(duration * 100) / 100, results: tests });
  } catch (err) { next(err); }
});

// GET /api/run/sections
router.get('/sections', requireAdmin, (_req, res) => {
  res.json({
    sections: Object.entries(SECTION_POINTS).map(([id, pts]) => ({
      id: parseInt(id, 10), max_points: pts, tests_dir: SECTION_TESTS[parseInt(id, 10)],
    })),
  });
});

module.exports = router;
