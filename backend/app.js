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

const PORT = process.env.PORT || 8000;

// Track DB readiness so /api/health can answer immediately even before DB is up
let dbReady = false;
let dbError = null;

const app = express();

// ── /api/health MUST be registered BEFORE any async DB work ──────────────────
// Railway probes this path; it must respond as soon as the process is up.
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', db: dbReady ? 'ready' : 'initialising', timestamp: new Date().toISOString() });
});

// ── Middleware ────────────────────────────────────────────────────────────────
app.use(cors({
  origin: config.ALLOWED_ORIGINS.includes('*') ? '*' : config.ALLOWED_ORIGINS,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['*'],
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// ── Routers ───────────────────────────────────────────────────────────────────
app.use('/api/auth',        authRouter);
app.use('/api/leaderboard', leaderboardRouter);
app.use('/api/admin',       adminRouter);
app.use('/api',             infoRouter);   // contains /api/ready, /api/info, /api/timers/status
app.use('/api/download',    downloadRouter);
app.use('/api/validate',    validatorRouter);
app.use('/api/run',         runnerRouter);

// ── 404 catch-all (must return JSON, not HTML) ───────────────────────────────
app.use((req, res, _next) => {
  res.status(404).json({ detail: `${req.method} ${req.path} not found` });
});

// ── Global error handler ──────────────────────────────────────────────────────
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  const status = err.status || err.statusCode || 500;
  console.error(err);
  res.status(status).json({ detail: err.message || 'Internal server error' });
});

// ── Start: listen first, then init DB ────────────────────────────────────────
// Listening before initDb means Railway's healthcheck at /api/health gets a 200
// immediately. DB init happens in the background; it retries on failure.
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Debugging Championship backend listening on port ${PORT}`);

  // Init DB schema after server is already accepting connections
  initDb()
    .then(() => {
      dbReady = true;
      console.log('Database ready');
    })
    .catch(err => {
      dbError = err;
      console.error('Database init failed (will retry on next request):', err.message);
      // Don't exit — Railway will keep the container alive;
      // individual requests will fail until the DB becomes reachable.
    });
});
