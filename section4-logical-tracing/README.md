# 🔍 SECTION 4: Logical Tracing - Code Detective Challenge

## 🚨 CODE SABOTAGE DETECTED: LOGIC BOMBS IN PRODUCTION

### 🎯 Scenario
At 11:47 PM last night, your security team discovered that a **disgruntled ex-employee** planted subtle logic bombs in **10 critical production functions** before their access was revoked. Every function compiles and runs without errors — but each one produces **wrong output** for specific inputs.

The systems affected span your entire platform:
- **E-commerce pricing engine** — customers charged incorrect amounts
- **Authentication system** — unauthorized access possible
- **Core algorithm library** — search and sort producing wrong results
- **Financial calculations** — tax and interest computations off

Markets open in **35 minutes**. You must find and surgically fix each sabotaged function before trading begins.

---

## 📋 Your Mission

Find and fix **10 logic bugs** (+ 1 hidden bonus) in a single file:
- `logic_tracing.py` — All 10 sabotaged functions

Each function:
- ✅ Compiles successfully (no syntax errors)
- ❌ Produces wrong output for specific inputs
- 🐛 Has exactly **ONE** logic bug
- 🎯 Requires a **1–3 line fix** (surgical debugging)

---

## 🔥 Sabotaged Functions

| # | Function | Domain | Difficulty |
|---|----------|--------|------------|
| 1 | `calculate_discount` | E-commerce | ⭐ Easy |
| 2 | `authenticate_user` | Security | ⭐ Easy |
| 3 | `find_majority_element` | Algorithms | ⭐⭐ Medium |
| 4 | `calculate_compound_interest` | Finance | ⭐⭐ Medium |
| 5 | `merge_sorted_arrays` | Algorithms | ⭐ Easy |
| 6 | `validate_password` | Security | ⭐ Easy |
| 7 | `binary_search` | Algorithms | ⭐ Easy |
| 8 | `detect_cycle` | Algorithms | ⭐⭐ Medium |
| 9 | `calculate_tax_bracket` | Finance | ⭐⭐⭐ Hard |
| 10 | `graph_shortest_path` | Algorithms | ⭐⭐⭐ Hard |
| 🎁 | `calculate_fibonacci` | Bonus | 🎁 Hidden |

---

## 📏 Constraints

### ✅ You MAY:
- Fix logic errors in existing functions
- Change operators, conditions, and expressions
- Add missing lines (e.g., base cases, validations)
- Use print statements or debugger to trace execution

### ❌ You MAY NOT:
- Rewrite entire functions from scratch
- Delete or rename functions
- Hardcode expected test outputs
- Change the test file
- Use AI code generation during the event

---

## 🏆 Victory Condition

```bash
pytest tests/test_logic_tracing.py -v
```

**Expected output after fixing all bugs:**
```
tests/test_logic_tracing.py::TestCalculateDiscount::test_discount_boundaries PASSED
tests/test_logic_tracing.py::TestAuthenticateUser::test_both_fields_required PASSED
tests/test_logic_tracing.py::TestFindMajorityElement::test_no_majority PASSED
tests/test_logic_tracing.py::TestFindMajorityElement::test_has_majority PASSED
tests/test_logic_tracing.py::TestFindMajorityElement::test_empty PASSED
tests/test_logic_tracing.py::TestCompoundInterest::test_standard_calculation PASSED
tests/test_logic_tracing.py::TestCompoundInterest::test_annual_compounding PASSED
tests/test_logic_tracing.py::TestCompoundInterest::test_zero_years PASSED
tests/test_logic_tracing.py::TestMergeSortedArrays::test_basic_merge PASSED
tests/test_logic_tracing.py::TestMergeSortedArrays::test_unequal_lengths PASSED
tests/test_logic_tracing.py::TestMergeSortedArrays::test_empty_arrays PASSED
tests/test_logic_tracing.py::TestValidatePassword::test_all_conditions_required PASSED
tests/test_logic_tracing.py::TestBinarySearch::test_find_single_element PASSED
tests/test_logic_tracing.py::TestBinarySearch::test_find_last_element PASSED
tests/test_logic_tracing.py::TestBinarySearch::test_find_first_element PASSED
tests/test_logic_tracing.py::TestBinarySearch::test_not_found PASSED
tests/test_logic_tracing.py::TestBinarySearch::test_empty_list PASSED
tests/test_logic_tracing.py::TestDetectCycle::test_cycle_detection PASSED
tests/test_logic_tracing.py::TestDetectCycle::test_no_cycle PASSED
tests/test_logic_tracing.py::TestDetectCycle::test_empty_and_single PASSED
tests/test_logic_tracing.py::TestTaxBracket::test_progressive_tax PASSED
tests/test_logic_tracing.py::TestTaxBracket::test_first_bracket_only PASSED
tests/test_logic_tracing.py::TestTaxBracket::test_two_brackets PASSED
tests/test_logic_tracing.py::TestTaxBracket::test_zero_income PASSED
tests/test_logic_tracing.py::TestGraphShortestPath::test_shortest_path PASSED
tests/test_logic_tracing.py::TestGraphShortestPath::test_no_path PASSED
tests/test_logic_tracing.py::TestGraphShortestPath::test_same_node PASSED
tests/test_logic_tracing.py::TestFibonacciBonus::test_fibonacci_zero PASSED
tests/test_logic_tracing.py::TestFibonacciBonus::test_fibonacci_sequence PASSED
tests/test_logic_tracing.py::TestFibonacciBonus::test_fibonacci_negative PASSED

========== 30 passed in 0.XX s ==========
```

---

## 🐛 Bug Checklist

- [ ] Fix discount boundary condition
- [ ] Fix authentication logic
- [ ] Fix majority element verification
- [ ] Fix compound interest formula
- [ ] Fix merge leftover elements
- [ ] Fix password validation logic
- [ ] Fix binary search loop boundary
- [ ] Fix cycle detection pointer advancement
- [ ] Fix tax bracket ordering
- [ ] Fix graph path state mutation

### 🎁 Hidden Bug (Bonus)
- [ ] Fix Fibonacci base case

---

## 📊 Scoring

| Category | Points |
|----------|--------|
| Easy bugs (5 functions × 10 pts) | 50 |
| Medium bugs (3 functions × 15 pts) | 45 |
| Hard bugs (2 functions × 7.5 pts) | 15 |
| **Bonus: Hidden Fibonacci bug** | **10** |
| **Total** | **120** |

### Deductions
| Penalty | Points |
|---------|--------|
| Using Level 1 hint | −2 per hint |
| Using Level 2 hint | −4 per hint |
| Using Level 3 hint | −8 per hint |
| Rewriting function entirely | −5 per function |

---

## ⏱️ Time Limit: 35 minutes

**Recommended approach:**
1. Run the test suite to see which tests fail (2 min)
2. Start with ⭐ Easy bugs — quick wins (10 min)
3. Tackle ⭐⭐ Medium bugs — trace carefully (10 min)
4. Attempt ⭐⭐⭐ Hard bugs — think algorithmically (10 min)
5. Hunt for the 🎁 bonus if time permits (3 min)

---

## 🔗 Resources

- [HINTS.md](./HINTS.md) — Progressive hint system (3 levels)
- [Test Suite](./tests/test_logic_tracing.py) — Run to check progress

**Good luck, detective. The clock is ticking. 🕐**
