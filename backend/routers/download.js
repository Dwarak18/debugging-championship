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

const EXCLUDE_FILES = new Set(['hints.md', 'hints.txt', 'solutions.py', 'summary.md']);
const EXCLUDE_DIRS  = new Set(['__pycache__', '.pytest_cache']);

// GET /api/download/section/:id?token=...
router.get('/section/:id', (req, res) => {
  const token = req.query.token;
  if (!token) return res.status(401).json({ detail: 'Missing token' });
  const payload = verifyToken(token);
  if (!payload) return res.status(401).json({ detail: 'Invalid or expired token' });

  const sectionId = parseInt(req.params.id, 10);
  if (!SECTION_DIRS[sectionId]) return res.status(404).json({ detail: 'Section not found' });

  const sectionDir = path.join(config.REPO_ROOT, SECTION_DIRS[sectionId]);
  if (!fs.existsSync(sectionDir)) {
    console.error(`[download] Section dir not found: ${sectionDir} (REPO_ROOT=${config.REPO_ROOT})`);
    return res.status(500).json({ detail: `Section directory not found on server (${sectionDir})` });
  }

  const zipName = `${SECTION_DIRS[sectionId]}.zip`;
  res.setHeader('Content-Type', 'application/zip');
  res.setHeader('Content-Disposition', `attachment; filename="${zipName}"`);
  res.setHeader('Cache-Control', 'no-store');

  const archive = archiver('zip', { zlib: { level: 6 } });
  archive.on('error', err => {
    console.error('[download] archiver error', err);
    // Headers already sent — just destroy the connection
    res.destroy();
  });
  archive.pipe(res);

  function addDir(dir, baseInZip) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (EXCLUDE_DIRS.has(entry.name)) continue;
      const full = path.join(dir, entry.name);
      const rel  = path.join(baseInZip, entry.name);
      if (entry.isDirectory()) {
        addDir(full, rel);
      } else {
        if (EXCLUDE_FILES.has(entry.name.toLowerCase())) continue;
        if (entry.name.endsWith('.pyc')) continue;
        archive.file(full, { name: rel });
      }
    }
  }

  const parentDir  = path.dirname(sectionDir);
  const folderName = path.basename(sectionDir);
  addDir(sectionDir, folderName);
  archive.finalize();
});

module.exports = router;
