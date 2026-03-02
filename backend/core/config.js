'use strict';

module.exports = {
  DATABASE_URL: (process.env.DATABASE_URL || '').replace(/^postgres:\/\//, 'postgresql://'),


  // Auth
  SECRET_KEY:                  process.env.SECRET_KEY                  || 'change-me-in-production-please',
  ADMIN_USERNAME:              process.env.ADMIN_USERNAME              || 'admin',
  ADMIN_PASSWORD:              process.env.ADMIN_PASSWORD              || 'heisenberg',
  API_TOKEN_EXPIRE_MINUTES:    parseInt(process.env.API_TOKEN_EXPIRE_MINUTES || '480', 10),

  // REPO_ROOT: where the section folders live.
  // On Railway with root dir = backend/, the app runs inside /app (= backend/).
  // The section dirs are one level up at /app/.. in the cloned repo.
  // Override via REPO_ROOT env var if needed.
  ENV:       process.env.ENV || 'development',
  // REPO_ROOT resolution order:
  //  1. REPO_ROOT env var (set this on Railway if needed)
  //  2. Two levels up from this file (/app/backend/core → /app = repo root when full repo deployed)
  //  3. process.cwd() — Railway CWD is the deploy root, which may be the repo root
  REPO_ROOT: process.env.REPO_ROOT || (() => {
    const fromFile = require('path').resolve(__dirname, '..', '..');
    const fs = require('fs');
    // Verify the resolved path actually contains section directories
    const sectionCheck = require('path').join(fromFile, 'section1-multifile-debug');
    if (fs.existsSync(sectionCheck)) return fromFile;
    // Fall back to CWD (Railway sets this to repo root when using full-repo deployment)
    const fromCwd = require('path').resolve(process.cwd());
    const cwdCheck = require('path').join(fromCwd, 'section1-multifile-debug');
    if (fs.existsSync(cwdCheck)) return fromCwd;
    // Last resort: one level up from CWD (if CWD = /app/backend)
    const parentCwd = require('path').resolve(process.cwd(), '..');
    return parentCwd;
  })(),
  PYTEST_TIMEOUT:              parseInt(process.env.PYTEST_TIMEOUT     || '60', 10),

  // CORS
  // Note: REPO_ROOT env var can override the auto-detection below.
  // When deployed via repo-root railway.json, CWD = /app (repo root) and
  // __dirname = /app/backend/core, so ../.. resolves to /app correctly.
  // When only the backend/ folder is deployed, REPO_ROOT env var must be set.
  ALLOWED_ORIGINS: process.env.ALLOWED_ORIGINS
    ? process.env.ALLOWED_ORIGINS.split(',').map(s => s.trim())
    : ['*'],

  ALLOWED_HOSTS: process.env.ALLOWED_HOSTS
    ? process.env.ALLOWED_HOSTS.split(',').map(s => s.trim())
    : ['*'],
};
