'use strict';
/**
 * Anti-cheat helpers — ported from anti_cheat.py.
 * All I/O is sync (runs inside a temporary cloned repo).
 */

const crypto = require('crypto');
const fs     = require('fs');
const path   = require('path');

const TARGET_TEST_FILES = [
  'section1-multifile-debug/tests/test_system.py',
  'section2-broken-recovery/tests/test_recovery.py',
  'section3-memory-deadlock/tests/test_memory_deadlock.py',
  'section4-logical-tracing/tests/test_logic_tracing.py',
];

const SUSPICIOUS_PATTERNS = [
  { re: /\binspect\b/i,       label: 'inspect' },
  { re: /\bsubprocess\b/i,    label: 'subprocess' },
  { re: /\bos\.system\b/i,    label: 'os.system' },
  { re: /\bpytest\.skip\b/i,  label: 'pytest.skip' },
  { re: /\bmonkeypatch\b/i,   label: 'monkeypatch' },
  { re: /\bimport\s+test_/i,  label: 'import test_' },
];

const PRUNE_DIRS = new Set(['.git', '__pycache__', '.pytest_cache', '.venv', 'venv', 'node_modules']);

function sha256File(filePath) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

function computeTestHashes(repoRoot) {
  const hashes = {};
  for (const rel of TARGET_TEST_FILES) {
    const fp = path.join(repoRoot, rel.replace(/\//g, path.sep));
    hashes[rel] = fs.existsSync(fp) ? sha256File(fp) : '';
  }
  return hashes;
}

function verifyTestIntegrity(baselineRoot, submittedRoot) {
  const baseline  = computeTestHashes(baselineRoot);
  const submitted = computeTestHashes(submittedRoot);
  const mismatched = TARGET_TEST_FILES.filter(rel => baseline[rel] !== submitted[rel]);
  return { valid: mismatched.length === 0, mismatched };
}

function walkDir(dir, cb) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (PRUNE_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walkDir(full, cb);
    else cb(full);
  }
}

function scanSuspiciousImports(repoRoot) {
  const uniqueHits = new Set();
  let totalOccurrences = 0;

  walkDir(repoRoot, fp => {
    if (!fp.endsWith('.py')) return;
    let text;
    try { text = fs.readFileSync(fp, 'utf8'); } catch { return; }
    for (const { re, label } of SUSPICIOUS_PATTERNS) {
      const matches = text.match(new RegExp(re, 'gi')) || [];
      if (matches.length) { uniqueHits.add(label); totalOccurrences += matches.length; }
    }
  });

  return { imports: [...uniqueHits].sort(), occurrences: totalOccurrences };
}

function hashSourceTree(repoRoot) {
  const INCLUDE_EXTS = new Set(['.py', '.json', '.md', '.txt', '.yml', '.yaml', '.toml', '.ini']);
  const paths = [];
  walkDir(repoRoot, fp => { if (INCLUDE_EXTS.has(path.extname(fp).toLowerCase())) paths.push(fp); });
  paths.sort();

  const hash = crypto.createHash('sha256');
  for (const fp of paths) {
    const rel = path.relative(repoRoot, fp).replace(/\\/g, '/');
    hash.update(rel);
    try { hash.update(fs.readFileSync(fp)); } catch { hash.update('<unreadable>'); }
  }
  return hash.digest('hex');
}

module.exports = { verifyTestIntegrity, scanSuspiciousImports, hashSourceTree };
