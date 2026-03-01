'use strict';
/**
 * Security helpers — password hashing (PBKDF2-SHA256 via built-in crypto)
 * and JWT tokens (jsonwebtoken / HS256).
 *
 * Password format: pbkdf2:sha256:{iterations}:{hex-salt}:{hex-digest}
 * Backward-compatible with the old Python 4-part format (iterations = 260000).
 */

const crypto = require('crypto');
const jwt    = require('jsonwebtoken');
const config = require('./config');

const ITERS  = 150_000;   // OWASP minimum is 120k
const KEYLEN = 32;        // bytes → 64 hex chars

// ── Password hashing ──────────────────────────────────────────────────────────

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, salt, ITERS, KEYLEN, 'sha256').toString('hex');
  return `pbkdf2:sha256:${ITERS}:${salt}:${hash}`;
}

function verifyPassword(password, storedHash) {
  try {
    const parts = storedHash.split(':');
    let algo, iters, salt, expected;

    if (parts.length === 5) {
      // New format: pbkdf2:sha256:{iters}:{salt}:{hash}
      [, algo, iters, salt, expected] = parts;
      iters = parseInt(iters, 10);
    } else if (parts.length === 4) {
      // Legacy Python format: pbkdf2:sha256:{salt}:{hash}
      [, algo, salt, expected] = parts;
      iters = 260_000;
    } else {
      return false;
    }

    const hash = crypto.pbkdf2Sync(password, salt, iters, KEYLEN, algo).toString('hex');
    // Constant-time comparison to prevent timing attacks
    return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), Buffer.from(expected, 'hex'));
  } catch {
    return false;
  }
}

// ── JWT ───────────────────────────────────────────────────────────────────────

function createAccessToken(data, expireMinutes) {
  const minutes = expireMinutes || config.API_TOKEN_EXPIRE_MINUTES;
  return jwt.sign(data, config.SECRET_KEY, { expiresIn: `${minutes}m` });
}

function verifyToken(token) {
  try {
    return jwt.verify(token, config.SECRET_KEY);
  } catch {
    return null;
  }
}

module.exports = { hashPassword, verifyPassword, createAccessToken, verifyToken };
