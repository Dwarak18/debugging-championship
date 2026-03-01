"""
Risk scoring for anti-cheat reports.
"""

from typing import Dict, List, Tuple


def risk_level(score: int) -> str:
    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def build_risk(
    *,
    test_hash_valid: bool,
    tests_collected: int,
    tests_skipped: int,
    suspicious_occurrences: int,
    duplicate_detected: bool,
    submission_rate_last_10min: int,
    runtime_seconds: float,
    paste_attempts: int,
    large_injection_events: int,
    typing_anomaly_detected: bool,
    copy_risk_score: int,
    expected_total_tests: int = 57,
) -> Tuple[int, List[str], str]:
    score = 0
    flags: List[str] = []

    if not test_hash_valid:
        score += 50
        flags.append("Test file modified")

    if tests_collected != expected_total_tests:
        score += 30
        flags.append(f"Unexpected test count: {tests_collected} (expected {expected_total_tests})")

    if tests_skipped > 0:
        score += 30
        flags.append(f"Skipped tests detected: {tests_skipped}")

    if suspicious_occurrences > 0:
        score += 15 * suspicious_occurrences
        flags.append(f"Suspicious imports/patterns found: {suspicious_occurrences}")

    if duplicate_detected:
        score += 40
        flags.append("Duplicate submission hash detected")

    if submission_rate_last_10min > 10:
        score += 10
        flags.append("High submission frequency")

    if runtime_seconds < 0.05:
        score += 20
        flags.append("Unusually fast execution")

    if paste_attempts > 0:
        flags.append(f"Paste attempts detected: {paste_attempts}")
    if large_injection_events > 0:
        flags.append(f"Large code injection events: {large_injection_events}")
    if typing_anomaly_detected:
        flags.append("Unnatural typing pattern")

    score += int(copy_risk_score or 0)

    escalated_high = copy_risk_score > 0 and (duplicate_detected or not test_hash_valid)
    if escalated_high:
        flags.append("Escalated to HIGH: copy-risk combined with duplicate/tampering")

    level = risk_level(score)
    if escalated_high and level != "High":
        level = "High"
    return score, flags, level
