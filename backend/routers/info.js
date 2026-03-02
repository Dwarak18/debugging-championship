'use strict';
const router  = require('express').Router();
const { getAllSectionTimers } = require('../core/database');
const { requireAuth } = require('../middleware/auth');

const EVENT = {
  name: 'Debugging Championship 2026',
  total_points: 420,
  duration_minutes: 170,
  sections: [
    { id: 1, title: 'Multi-File Debugging Lab',        duration: 45,  points: 100, difficulty: '⭐⭐⭐' },
    { id: 2, title: 'Broken Project Recovery',         duration: 40,  points: 100, difficulty: '⭐⭐⭐⭐' },
    { id: 3, title: 'Memory & Deadlock Simulation',    duration: 50,  points: 100, difficulty: '⭐⭐⭐⭐⭐' },
    { id: 4, title: 'Logical Tracing — Code Detective',duration: 35,  points: 120, difficulty: '⭐⭐⭐⭐' },
  ],
};

// GET /api/info
router.get('/info', (_req, res) => res.json(EVENT));

// GET /api/ready  — readiness probe (lightweight DB ping)
router.get('/ready', async (_req, res, next) => {
  try {
    const { pool } = require('../core/database');
    await pool.query('SELECT 1');
    res.json({ status: 'ready' });
  } catch (err) {
    res.status(503).json({ detail: err.message });
  }
});

// GET /api/timers/status
router.get('/timers/status', requireAuth, async (_req, res, next) => {
  try {
    const rows = await getAllSectionTimers();
    const now  = new Date();
    const result = rows.map(row => {
      let start    = row.start_time ? new Date(row.start_time) : null;
      let pausedAt = row.paused_at  ? new Date(row.paused_at)  : null;
      const elapsed   = row.elapsed_seconds || 0;
      const isActive  = row.is_active || false;
      const isPaused  = isActive && pausedAt !== null;
      const totalSecs = row.duration_minutes * 60;

      let remaining = null;
      if (isActive && start) {
        if (isPaused) {
          remaining = Math.max(0, totalSecs - elapsed);
        } else {
          const runningSecs = Math.floor((now - start) / 1000);
          remaining = Math.max(0, totalSecs - elapsed - runningSecs);
        }
      }

      return {
        section:            row.section,
        duration_minutes:   row.duration_minutes,
        start_time:         start ? start.toISOString() : null,
        paused_at:          pausedAt ? pausedAt.toISOString() : null,
        elapsed_seconds:    elapsed,
        is_active:          isActive,
        is_paused:          isPaused,
        download_unlocked:  isActive,
        submissions_locked: row.submissions_locked || false,
        remaining_seconds:  remaining,
      };
    });
    res.json({ timers: result });
  } catch (err) { next(err); }
});

module.exports = router;
