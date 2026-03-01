'use strict';
/** Risk scoring — ported from risk_engine.py */

function riskLevel(score) {
  if (score >= 60) return 'High';
  if (score >= 30) return 'Medium';
  return 'Low';
}

function buildRisk({
  testHashValid,
  testsCollected,
  testsSkipped,
  suspiciousOccurrences,
  duplicateDetected,
  submissionRateLast10min,
  runtimeSeconds,
  pasteAttempts,
  largeInjectionEvents,
  typingAnomalyDetected,
  copyRiskScore,
  expectedTotalTests = 57,
}) {
  let score = 0;
  const flags = [];

  if (!testHashValid) {
    score += 50; flags.push('Test file modified');
  }
  if (testsCollected !== expectedTotalTests) {
    score += 30; flags.push(`Unexpected test count: ${testsCollected} (expected ${expectedTotalTests})`);
  }
  if (testsSkipped > 0) {
    score += 30; flags.push(`Skipped tests detected: ${testsSkipped}`);
  }
  if (suspiciousOccurrences > 0) {
    score += 15 * suspiciousOccurrences;
    flags.push(`Suspicious imports/patterns found: ${suspiciousOccurrences}`);
  }
  if (duplicateDetected) {
    score += 40; flags.push('Duplicate submission hash detected');
  }
  if (submissionRateLast10min > 10) {
    score += 10; flags.push('High submission frequency');
  }
  if (runtimeSeconds < 0.05) {
    score += 20; flags.push('Unusually fast execution');
  }
  if (pasteAttempts > 0) flags.push(`Paste attempts detected: ${pasteAttempts}`);
  if (largeInjectionEvents > 0) flags.push(`Large code injection events: ${largeInjectionEvents}`);
  if (typingAnomalyDetected) flags.push('Unnatural typing pattern');

  score += copyRiskScore || 0;

  const escalatedHigh = copyRiskScore > 0 && (duplicateDetected || !testHashValid);
  if (escalatedHigh) flags.push('Escalated to HIGH: copy-risk combined with duplicate/tampering');

  let level = riskLevel(score);
  if (escalatedHigh && level !== 'High') level = 'High';

  return { score, flags, level };
}

module.exports = { buildRisk };
