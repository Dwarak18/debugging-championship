'use strict';
const router = require('express').Router();
const db     = require('../core/database');
const { requireAuth } = require('../middleware/auth');

// GET /api/leaderboard/
router.get('/', async (req, res, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 50, 200);
    const entries = (await db.getLeaderboard()).slice(0, limit).map((row, i) => ({ ...row, rank: i + 1 }));
    res.json({ leaderboard: entries, count: entries.length });
  } catch (err) { next(err); }
});

// POST /api/leaderboard/submit
router.post('/submit', requireAuth, async (req, res, next) => {
  try {
    const { section, score, passed_tests, total_tests, time_taken = 0 } = req.body;
    if (![1,2,3,4].includes(section))
      return res.status(422).json({ detail: 'section must be 1–4' });
    if (score < 0 || score > 420)
      return res.status(422).json({ detail: 'score out of range' });

    await db.upsertScore({
      username: req.user.sub, section, score,
      passedTests: passed_tests, totalTests: total_tests, timeTaken: time_taken,
      fullName: req.user.full_name || '', college: req.user.college || '', team: req.user.team || '',
    });
    res.status(201).json({ message: 'Score recorded', section, score });
  } catch (err) { next(err); }
});

// GET /api/leaderboard/me
router.get('/me', requireAuth, async (req, res, next) => {
  try {
    const row = await db.getUserScores(req.user.sub);
    res.json({ username: req.user.sub, scores: row || {} });
  } catch (err) { next(err); }
});

module.exports = router;
