'use strict';
const router   = require('express').Router();
const path     = require('path');
const fs       = require('fs');
const archiver = require('archiver');
const config   = require('../core/config');
const { verifyToken } = require('../middleware/auth');

const SECTION_DIRS = {
  1: 'section1-multifile-debug',
  2: 'section2-broken-recovery',
  3: 'section3-memory-deadlock',
  4: 'section4-logical-tracing',
};

const EXCLUDE_FILES = new Set(['hints.md', 'hints.txt', 'solutions.py', 'summary.md', 'solutions.md']);
const EXCLUDE_DIRS  = new Set(['__pycache__', '.pytest_cache']);

// Pre-built zips live at backend/downloads/  (bundled with the backend deployment)
const PREBUILT_DIR = path.join(__dirname, '..', 'downloads');

// GET /api/download/section/:id?token=...
router.get('/section/:id', (req, res) => {
  const token = req.query.token;
  if (!token) return res.status(401).json({ detail: 'Missing token' });
  const payload = verifyToken(token);
  if (!payload) return res.status(401).json({ detail: 'Invalid or expired token' });

  const sectionId = parseInt(req.params.id, 10);
  if (!SECTION_DIRS[sectionId]) return res.status(404).json({ detail: 'Section not found' });

  const dirName = SECTION_DIRS[sectionId];
  const zipName = `${dirName}.zip`;

  // ── 1. Serve pre-built zip if present (always available, deployed with backend)
  const prebuiltPath = path.join(PREBUILT_DIR, zipName);
  if (fs.existsSync(prebuiltPath)) {
    console.log(`[download] serving pre-built zip: ${prebuiltPath}`);
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename="${zipName}"`);
    res.setHeader('Cache-Control', 'no-store');
    return fs.createReadStream(prebuiltPath).pipe(res);
  }

  // ── 2. Fall back: build on the fly from repo (when REPO_ROOT is available)
  const sectionDir = path.join(config.REPO_ROOT, dirName);
  if (!fs.existsSync(sectionDir)) {
    console.error(`[download] neither pre-built zip nor section dir found.`);
    console.error(`  pre-built: ${prebuiltPath}`);
    console.error(`  on-the-fly: ${sectionDir} (REPO_ROOT=${config.REPO_ROOT})`);
    return res.status(500).json({ detail: 'Section files not found on server. Please contact the administrator.' });
  }

  res.setHeader('Content-Type', 'application/zip');
  res.setHeader('Content-Disposition', `attachment; filename="${zipName}"`);
  res.setHeader('Cache-Control', 'no-store');

  const archive = archiver('zip', { zlib: { level: 6 } });
  archive.on('error', err => { console.error('[download] archiver error', err); res.destroy(); });
  archive.pipe(res);

  function addDir(dir, baseInZip) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (EXCLUDE_DIRS.has(entry.name)) continue;
      const full = path.join(dir, entry.name);
      const rel  = path.join(baseInZip, entry.name);
      if (entry.isDirectory()) { addDir(full, rel); }
      else {
        if (EXCLUDE_FILES.has(entry.name.toLowerCase())) continue;
        if (entry.name.endsWith('.pyc')) continue;
        archive.file(full, { name: rel });
      }
    }
  }
  addDir(sectionDir, dirName);
  archive.finalize();
});

module.exports = router;
