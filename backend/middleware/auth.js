'use strict';
const { verifyToken } = require('../core/security');

function getToken(req) {
  const h = req.headers.authorization || '';
  if (h.startsWith('Bearer ')) return h.slice(7);
  return null;
}

function requireAuth(req, res, next) {
  const token = getToken(req);
  if (!token) return res.status(401).json({ detail: 'Missing token' });
  const payload = verifyToken(token);
  if (!payload) return res.status(401).json({ detail: 'Invalid or expired token' });
  req.user = payload;
  next();
}

function requireAdmin(req, res, next) {
  requireAuth(req, res, () => {
    if (!req.user.is_admin) return res.status(403).json({ detail: 'Admin only' });
    next();
  });
}

module.exports = { requireAuth, requireAdmin, verifyToken };
