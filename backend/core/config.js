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
  REPO_ROOT: process.env.REPO_ROOT || require('path').resolve(__dirname, '..', '..'),
  PYTEST_TIMEOUT:              parseInt(process.env.PYTEST_TIMEOUT     || '60', 10),

  // CORS
  ALLOWED_ORIGINS: process.env.ALLOWED_ORIGINS
    ? process.env.ALLOWED_ORIGINS.split(',').map(s => s.trim())
    : ['*'],

  ALLOWED_HOSTS: process.env.ALLOWED_HOSTS
    ? process.env.ALLOWED_HOSTS.split(',').map(s => s.trim())
    : ['*'],
};
