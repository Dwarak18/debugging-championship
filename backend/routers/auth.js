'use strict';
const router  = require('express').Router();
const https   = require('https');
const db      = require('../core/database');
const { verifyPassword, createAccessToken } = require('../core/security');
const { requireAuth } = require('../middleware/auth');

// Helper: verify a GitHub username exists via GitHub API (no auth required)
function verifyGithubUser(username) {
  return new Promise((resolve) => {
    const opts = {
      hostname: 'api.github.com',
      path:     `/users/${encodeURIComponent(username)}`,
      method:   'GET',
      headers:  { 'User-Agent': 'Debugging-Championship-2026', 'Accept': 'application/vnd.github+json' },
    };
    const req = https.request(opts, (res) => {
      resolve(res.statusCode === 200);
      res.resume();
    });
    req.on('error', () => resolve(false));
    req.setTimeout(8000, () => { req.destroy(); resolve(false); });
    req.end();
  });
}

// POST /api/auth/login
router.post('/login', async (req, res, next) => {
  try {
    const { username, password } = req.body;
    if (!username || !password)
      return res.status(400).json({ detail: 'username and password required' });

    const student = await db.getStudent(username);
    if (!student || !verifyPassword(password, student.password_hash))
      return res.status(401).json({ detail: 'Invalid username or password' });

    await db.updateLastLogin(username);
    const isAdmin = !!student.is_admin;
    const token = createAccessToken({
      sub: student.username, is_admin: isAdmin,
      full_name: student.full_name || (isAdmin ? 'Administrator' : ''),
      college: student.college || '', team: student.team || '',
    });
    res.json({
      access_token: token, token_type: 'bearer',
      username: student.username,
      full_name: student.full_name || (isAdmin ? 'Administrator' : ''),
      college: student.college || '', team: student.team || '',
      is_admin: isAdmin,
    });
  } catch (err) { next(err); }
});

// GET /api/auth/me
router.get('/me', requireAuth, async (req, res, next) => {
  try {
    const student = await db.getStudent(req.user.sub);
    res.json({
      username:        req.user.sub,
      is_admin:        req.user.is_admin || false,
      full_name:       req.user.full_name || '',
      college:         req.user.college || '',
      team:            req.user.team || '',
      github_username: student ? (student.github_username || '') : '',
    });
  } catch (err) { next(err); }
});

// PUT /api/auth/me/github  — student sets/updates their own GitHub username
router.put('/me/github', requireAuth, async (req, res, next) => {
  try {
    const gh = (req.body.github_username || '').trim();
    if (!gh) return res.status(422).json({ detail: 'github_username is required' });
    if (!/^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,37}[a-zA-Z0-9])?$/.test(gh))
      return res.status(422).json({ detail: 'Invalid GitHub username format' });

    // Verify the username actually exists on GitHub
    const exists = await verifyGithubUser(gh);
    if (!exists)
      return res.status(422).json({ detail: `GitHub user "${gh}" does not exist. Check your username and try again.` });

    await db.updateGithubUsername(req.user.sub, gh);
    res.json({ message: 'GitHub username saved', github_username: gh });
  } catch (err) { next(err); }
});

module.exports = router;
