'use strict';
const router  = require('express').Router();
const db      = require('../core/database');
const { hashPassword, verifyPassword, createAccessToken } = require('../core/security');
const config  = require('../core/config');
const { requireAuth } = require('../middleware/auth');

// POST /api/auth/login
router.post('/login', async (req, res, next) => {
  try {
    const { username, password } = req.body;
    if (!username || !password)
      return res.status(400).json({ detail: 'username and password required' });

    // Admin shortcut
    if (username === config.ADMIN_USERNAME && password === config.ADMIN_PASSWORD) {
      const token = createAccessToken({ sub: username, is_admin: true, full_name: 'Admin', college: '', team: '' });
      return res.json({ access_token: token, token_type: 'bearer', username, full_name: 'Admin', college: '', team: '' });
    }

    const student = await db.getStudent(username);
    if (!student || !verifyPassword(password, student.password_hash))
      return res.status(401).json({ detail: 'Invalid username or password' });

    await db.updateLastLogin(username);
    const token = createAccessToken({
      sub: student.username, is_admin: false,
      full_name: student.full_name, college: student.college, team: student.team,
    });
    res.json({
      access_token: token, token_type: 'bearer',
      username: student.username, full_name: student.full_name,
      college: student.college, team: student.team,
    });
  } catch (err) { next(err); }
});

// GET /api/auth/me
router.get('/me', requireAuth, (req, res) => {
  res.json({
    username:  req.user.sub,
    is_admin:  req.user.is_admin || false,
    full_name: req.user.full_name || '',
    college:   req.user.college || '',
    team:      req.user.team || '',
  });
});

module.exports = router;
