# 🏆 SCORING RUBRIC - Debugging Championship

## Total Points: 420

---

## 📊 Section 1: Multi-File Debugging Lab (100 points)

### Test Cases (70 points)
| Test | Points | Bug Type |
|------|--------|----------|
| `test_import_config` | 10 | Incorrect module reference |
| `test_capacity_limit` | 10 | Off-by-one error |
| `test_within_capacity` | 5 | Boundary condition |
| `test_state_increment` | 15 | Shared state corruption |
| `test_state_isolation` | 10 | Global variable issue |
| `test_module_chain` | 10 | Circular dependency |
| `test_config_type` | 5 | Type mismatch |
| `test_full_system` | 5 | Integration |

### Hidden Bugs (20 points)
- Division by zero in utils.py (10 pts)
- String config value not caught (5 pts)
- Unused import causing memory issue (5 pts)

### Code Quality (10 points)
- Maintain modular structure (5 pts)
- Meaningful commit messages (5 pts)

---

## 📊 Section 2: Broken Project Recovery (100 points)

### Test Cases (70 points)
| Test | Points | Bug Type |
|------|--------|----------|
| `test_null_payment_object` | 15 | Null safety |
| `test_log_parsing` | 10 | Log forensics |
| `test_stack_trace_line` | 10 | Stack trace analysis |
| `test_invalid_config` | 15 | Config validation |
| `test_amount_validation` | 10 | Input sanitization |
| `test_transaction_rollback` | 5 | State management |
| `test_error_handling` | 5 | Exception handling |

### Hidden Bugs (20 points)
- Race condition in payment processing (10 pts)
- Memory leak in logger (5 pts)
- Timezone bug in timestamp (5 pts)

### Code Quality (10 points)
- Proper error messages (5 pts)
- Clean exception hierarchy (5 pts)

---

## 📊 Section 3: Memory & Deadlock Simulation (100 points)

### Test Cases (60 points)
| Test | Points | Bug Type |
|------|--------|----------|
| `test_memory_allocation` | 10 | Allocation tracking |
| `test_memory_free` | 10 | Free tracking |
| `test_double_free_detection` | 15 | Invalid free prevention |
| `test_deadlock_detection` | 15 | Thread lock inversion |
| `test_resource_starvation` | 10 | Scheduling fairness |

### Hidden Bugs (25 points)
- Subtle race condition in tracker (10 pts)
- Memory leak in thread cleanup (10 pts)
- Priority inversion scenario (5 pts)

### Code Quality (15 points)
- Thread-safe implementations (10 pts)
- Proper resource cleanup (5 pts)

---

## 📊 Section 4: Logical Tracing (120 points)

### Test Cases (110 points)
| Test | Points | Bug Type |
|------|--------|----------|
| `test_discount_boundaries` | 10 | Off-by-one (>= vs >) |
| `test_both_fields_required` | 10 | Boolean logic (AND vs OR) |
| `test_no_majority` / `test_has_majority` | 15 | Missing verification step |
| `test_standard_calculation` / `test_annual_compounding` | 15 | Operator precedence |
| `test_basic_merge` / `test_unequal_lengths` | 10 | Index error (i+1 vs i) |
| `test_all_conditions_required` | 10 | Boolean logic (AND vs OR) |
| `test_find_single_element` / `test_find_last_element` | 10 | Loop boundary (< vs <=) |
| `test_cycle_detection` | 15 | Pointer advancement |
| `test_progressive_tax` / `test_two_brackets` | 7.5 | Condition precedence |
| `test_shortest_path` | 7.5 | Mutable state / list copy |

### Hidden Bug — Bonus (10 points)
- Fibonacci missing base case for F(0) (10 pts)

### Deductions
- Level 1 hint used: −2 pts per hint
- Level 2 hint used: −4 pts per hint
- Level 3 hint used: −8 pts per hint
- Rewrote function entirely: −5 pts per function

---

## 🎖️ Bonus Achievements

### Speed Demon (Max +20 points)
- Complete Section 1 in < 30 min: +5
- Complete Section 2 in < 25 min: +5
- Complete Section 3 in < 35 min: +10

### Bug Hunter (Max +15 points)
- Find all hidden bugs: +15
- Find 2/3 sections' hidden bugs: +10
- Find 1/3 sections' hidden bugs: +5

### Code Artist (Max +10 points)
- Refactor without breaking tests: +5
- Add meaningful comments: +3
- Improve error messages: +2

### Documentation Master (Max +5 points)
- Create BUG_REPORT.md with root causes: +5

---

## 📈 Grade Distribution

| Score Range | Grade | Achievement |
|-------------|-------|-------------|
| 380-420+ | S | Master Debugger |
| 330-379 | A | Expert |
| 280-329 | B | Proficient |
| 230-279 | C | Competent |
| 180-229 | D | Developing |
| < 180 | F | Need More Practice |

---

## 📤 Submission Format

Create `SUBMISSION.md` in your repo:

```markdown
# Debugging Championship Submission

## Participant Info
- Name: Your Name
- GitHub: @username
- Date: YYYY-MM-DD

## Scores
- Section 1: X/100
- Section 2: X/100
- Section 3: X/100
- Section 4: X/120
- Bonus: X/50
- **Total: X/420**

## Time Taken
- Section 1: X minutes
- Section 2: X minutes
- Section 3: X minutes
- Section 4: X minutes
- Total: X minutes

## Bugs Fixed
### Section 1
1. Bug description and fix
2. ...

### Section 2
1. ...

### Section 3
1. ...

### Section 4
1. ...

## Hidden Bugs Found
1. ...

## Challenges Faced
- Describe your debugging journey

## Key Learnings
- What did you learn?
```

---

## 🔍 Auto-Grading Script

Run this to calculate your score:
```bash
python grade.py --json-report report.json --submission SUBMISSION.md
```

---

**Note:** Judges have final discretion on bonus points and code quality assessment.
