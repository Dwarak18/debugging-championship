# 📋 SUMMARY — Section 4: Logical Tracing (Instructor Guide)

## Overview

| Property | Value |
|----------|-------|
| **Title** | Logical Tracing — Code Detective Challenge |
| **Duration** | 35 minutes |
| **Total Points** | 120 (110 base + 10 bonus) |
| **Functions** | 10 buggy + 1 hidden bonus |
| **File to fix** | `logic_tracing.py` |
| **Test suite** | `tests/test_logic_tracing.py` (30 test cases) |
| **Prerequisites** | Python 3.8+, pytest |

---

## 🐛 Bug Inventory

| # | Function | Bug Type | Fix | Difficulty | Points |
|---|----------|----------|-----|------------|--------|
| 1 | `calculate_discount` | `>` → `>=` | Change 2 comparisons | ⭐ Easy | 10 |
| 2 | `authenticate_user` | `or` → `and` | Change 1 operator | ⭐ Easy | 10 |
| 3 | `find_majority_element` | Missing verification | Add 3 lines | ⭐⭐ Medium | 15 |
| 4 | `calculate_compound_interest` | Missing parentheses | Add `()` around exponent | ⭐⭐ Medium | 15 |
| 5 | `merge_sorted_arrays` | `i+1` → `i` | Change 2 indices | ⭐ Easy | 10 |
| 6 | `validate_password` | `or` → `and` | Change 2 operators | ⭐ Easy | 10 |
| 7 | `binary_search` | `<` → `<=` | Change 1 operator | ⭐ Easy | 10 |
| 8 | `detect_cycle` | `.next` → `.next.next` | Change 1 line | ⭐⭐ Medium | 15 |
| 9 | `calculate_tax_bracket` | Bracket order swapped | Swap 2 if-blocks | ⭐⭐⭐ Hard | 7.5 |
| 10 | `graph_shortest_path` | `path` → `list(path)` | Change 1 assignment | ⭐⭐⭐ Hard | 7.5 |
| 🎁 | `calculate_fibonacci` | `n == 1` → `n <= 1` | Change 1 condition | 🎁 Bonus | 10 |

---

## ⏱️ Expected Solve Times

| Skill Level | Bugs Fixed | Points | Time |
|-------------|-----------|--------|------|
| Beginner | 4–6 | 40–65 | 35+ min (hints used) |
| Intermediate | 7–8 | 70–85 | 25–35 min |
| Advanced | 9–10 | 90–110 | 18–25 min |
| Expert | 10 + bonus | 110–120 | 15–20 min |

---

## 🎯 Common Mistakes Students Make

### Easy Bugs
1. **Discount/Password**: Students often spot one `or`/`>` but miss the second occurrence in the same function.
2. **Binary search**: Students may change `<` to `<=` but also incorrectly modify the `mid` calculation.
3. **Merge arrays**: Students sometimes fix by adding `- 1` elsewhere instead of removing the `+ 1`.

### Medium Bugs
4. **Majority element**: Students may add a count check but use `>=` instead of `>` for the n/2 threshold.
5. **Compound interest**: Students sometimes add parentheses in the wrong place, e.g., around `(rate / compounds_per_year * years)`.
6. **Cycle detection**: Students may change `slow` instead of `fast`, or add `fast.next.next` without the safety check (the `while fast and fast.next` already handles it).

### Hard Bugs
7. **Tax brackets**: Students often try to rewrite as `if/elif` chain instead of recognizing the simple swap.
8. **Graph path**: Students may try deep-copying the entire graph instead of just copying the path list.

### Bonus
9. **Fibonacci**: Students may add `if n == 0: return 0` as a separate line, which works but `if n <= 1: return n` is more elegant.

---

## 📊 Scoring Rubric

### Automated Scoring (pytest)
```bash
pytest tests/test_logic_tracing.py -v --tb=short 2>&1 | tail -5
```

Each test class corresponds to one function. Count passing test classes:

| Tests Passing | Approximate Score |
|---------------|-------------------|
| 30/30 (all) | 120 pts (with bonus) |
| 27/30 (no bonus) | 110 pts |
| 20–26 | 70–100 pts |
| 10–19 | 40–65 pts |
| < 10 | < 40 pts |

### Manual Deductions
- **Rewrote function entirely** (instead of surgical fix): −5 pts per function
- **Hardcoded test values**: −10 pts per function (and flag for review)
- **Changed test file**: Disqualified for that function

### Hint Penalties
- Level 1 hint used: −2 pts
- Level 2 hint used: −4 pts
- Level 3 hint used: −8 pts

---

## 🧪 Quick Verification Commands

```bash
# Verify all tests FAIL on buggy code (before event)
pytest tests/test_logic_tracing.py -v --tb=line
# Expected: 10 failed, some errors

# Verify all tests PASS on solution (instructor check)
cp SOLUTIONS.py logic_tracing.py
pytest tests/test_logic_tracing.py -v
# Expected: 30 passed

# Restore buggy version (after verification)
git checkout logic_tracing.py

# Generate JSON report for leaderboard
pytest tests/test_logic_tracing.py --json-report --json-report-file=results.json
```

---

## 🏗️ Integration with Other Sections

This section is designed to complement the existing three sections:

| Section | Cognitive Skill Tested |
|---------|----------------------|
| 1. Multi-File Debug | System thinking, dependency tracking |
| 2. Broken Recovery | Forensic analysis, log reading |
| 3. Memory & Deadlock | Concurrency reasoning, resource modeling |
| **4. Logical Tracing** | **Execution tracing, algorithmic precision** |

### Complete Level 3 Structure
```
🟡 LEVEL 3 – SYSTEM COLLAPSE (170 minutes)
├── Section 1: Multi-File Debugging    (45 min) — 100 pts
├── Section 2: Broken Recovery         (40 min) — 100 pts
├── Section 3: Memory & Deadlock       (50 min) — 100 pts
└── Section 4: Logical Tracing         (35 min) — 120 pts
    
Total: 420 points across 170 minutes
```

---

## 📝 Pre-Event Checklist

- [ ] Run `pytest tests/test_logic_tracing.py -v` and confirm all tests fail
- [ ] Run `cp SOLUTIONS.py logic_tracing.py && pytest tests/test_logic_tracing.py -v` and confirm 30 pass
- [ ] Restore buggy version: `git checkout logic_tracing.py`
- [ ] Ensure SOLUTIONS.py and SUMMARY.md are NOT in participant-visible folders
- [ ] Print HINTS.md for physical distribution (or keep digital with access tracking)
- [ ] Test timing: have a TA attempt the section to validate 35-min estimate
- [ ] Prepare leaderboard scoring script for JSON report parsing
