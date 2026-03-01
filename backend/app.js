'use strict';
require('dotenv').config();

const express    = require('express');
const cors       = require('cors');
const { initDb } = require('./core/database');

const authRouter        = require('./routers/auth');
const leaderboardRouter = require('./routers/leaderboard');
const adminRouter       = require('./routers/admin');
const infoRouter        = require('./routers/info');
const downloadRouter    = require('./routers/download');
const validatorRouter   = require('./routers/validator');
const runnerRouter      = require('./routers/runner');

const config = require('./core/config');

async function createApp() {
  // ── Init DB schema (idempotent CREATE TABLE IF NOT EXISTS) ─────────────────
  await initDb();

  const app = express();

  // ── Middleware ────────────────────────────────────────────────────────────
  app.use(cors({
    origin: config.ALLOWED_ORIGINS.includes('*') ? '*' : config.ALLOWED_ORIGINS,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['*'],
  }));
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true }));

  // ── Routers ───────────────────────────────────────────────────────────────
  app.use('/api/auth',        authRouter);
  app.use('/api/leaderboard', leaderboardRouter);
  app.use('/api/admin',       adminRouter);
  app.use('/api',             infoRouter);
  app.use('/api/download',    downloadRouter);
  app.use('/api/validate',    validatorRouter);
  app.use('/api/run',         runnerRouter);

  // ── Global error handler ─────────────────────────────────────────────────
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    const status = err.status || err.statusCode || 500;
    console.error(err);
    res.status(status).json({ detail: err.message || 'Internal server error' });
  });

  return app;
}

const PORT = process.env.PORT || 8000;

createApp().then(app => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Debugging Championship backend running on port ${PORT}`);
  });
}).catch(err => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
