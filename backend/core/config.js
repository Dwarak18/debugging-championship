'use strict';

module.exports = {
  // Database — Railway Postgres plugin injects DATABASE_URL automatically.
  // Set DATABASE_URL in Railway dashboard → backend service → Variables.
  // Use ${{Postgres.DATABASE_URL}} to reference the Postgres plugin directly.
  DATABASE_URL: (process.env.DATABASE_URL || '')
    .replace(/^postgres:\/\//, 'postgresql://'),


  // Auth
  SECRET_KEY:                  process.env.SECRET_KEY                  || 'change-me-in-production-please',
  ADMIN_USERNAME:              process.env.ADMIN_USERNAME              || 'admin',
  ADMIN_PASSWORD:              process.env.ADMIN_PASSWORD              || 'heisenberg',
  API_TOKEN_EXPIRE_MINUTES:    parseInt(process.env.API_TOKEN_EXPIRE_MINUTES || '480', 10),

  // App
  ENV:                         process.env.ENV                         || 'development',
  REPO_ROOT:                   process.env.REPO_ROOT                   || '/app',
  PYTEST_TIMEOUT:              parseInt(process.env.PYTEST_TIMEOUT     || '60', 10),

  // CORS
  ALLOWED_ORIGINS: process.env.ALLOWED_ORIGINS
    ? process.env.ALLOWED_ORIGINS.split(',').map(s => s.trim())
    : ['*'],

  ALLOWED_HOSTS: process.env.ALLOWED_HOSTS
    ? process.env.ALLOWED_HOSTS.split(',').map(s => s.trim())
    : ['*'],
};
