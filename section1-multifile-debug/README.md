# 🔧 SECTION 1: Multi-File Debugging Lab

## ⚠️ SYSTEM NODE FAILURE – CAPACITY ENGINE COLLAPSE

### 🎯 Scenario
Your company's internal **User Allocation System** has crashed during a live onboarding event for 500+ new employees. Multiple modules are throwing import errors, state is corrupted, and the capacity checker is rejecting valid users while accepting over-limit requests.

The CTO is in panic mode. The system auto-locks in **45 minutes** if not restored.

---

## 📋 Your Mission

Fix **10 critical bugs** across 6 interconnected Python modules:
- `main.py` - Entry point (Integration bug)
- `config.py` - Configuration (Type mismatch)
- `state.py` - Shared state manager (Corruption)
- `utils.py` - Helper functions (Off-by-one, hidden bug)
- `module_a.py` - User manager (Import error)
- `module_b.py` - Analytics (Circular dependency)

---

## 🚨 Known Issues

From the incident report:

1. **"ModuleNotFoundError: No module named 'configurations'"** - Someone renamed a file
2. **"TypeError: '>' not supported between 'int' and 'str'"** - Config type issue
3. **Users with ID 5 accepted when MAX=5** - Off-by-one error
4. **State counter not incrementing** - Shared state corruption
5. **Circular import crash** - module_a ↔ module_b dependency hell
6. **System accepts 6 users when MAX=5** - Capacity logic bug

---

## 📏 Constraints

### ✅ You MAY:
- Fix import statements
- Correct logical errors
- Fix type issues
- Refactor functions (keep names)

### ❌ You MAY NOT:
- Delete any file
- Hardcode test results
- Remove function definitions
- Change test files

---

## 🏆 Victory Condition

```bash
pytest tests/test_system.py -v
```

**Expected output:**
```
tests/test_system.py::test_import_config PASSED
tests/test_system.py::test_capacity_limit PASSED
tests/test_system.py::test_within_capacity PASSED
tests/test_system.py::test_state_increment PASSED
tests/test_system.py::test_state_isolation PASSED
tests/test_system.py::test_module_chain PASSED
tests/test_system.py::test_config_type PASSED
tests/test_system.py::test_full_system PASSED

========== 8 passed in 0.XX s ==========
```

---

## 🐛 Bug Checklist

- [ ] Fix phantom import (config.py reference)
- [ ] Fix off-by-one in capacity check
- [ ] Fix shared state corruption
- [ ] Resolve circular dependency
- [ ] Fix config type mismatch
- [ ] Fix module_a import error
- [ ] Fix state increment bug
- [ ] Integration test passes

### 🎁 Hidden Bugs (Bonus)
- [ ] Division by zero in utils.py
- [ ] Unused import causing overhead
- [ ] String constant should be int

---

## 📊 Scoring

| Category | Points |
|----------|--------|
| Fix import errors | 10 |
| Fix off-by-one error | 10 |
| Fix shared state bug | 15 |
| Resolve circular dependency | 20 |
| Fix config type mismatch | 10 |
| Pass all 8 tests | 20 |
| Find hidden bugs | 15 |
| **TOTAL** | **100** |

---

## ⏱️ Time Limit

**45 minutes**

---

## 💡 Debugging Tips

1. **Start with imports** - Fix ModuleNotFoundError first
2. **Read error messages carefully** - They tell you exactly what's wrong
3. **Check type mismatches** - Python is dynamically typed but not type-ignorant
4. **Draw dependency graph** - Visualize circular imports
5. **Use print debugging** - Add prints to track state
6. **Test incrementally** - Fix one test at a time

---

## 🔍 Running Tests

```bash
# Run all tests
pytest tests/test_system.py -v

# Run specific test
pytest tests/test_system.py::test_capacity_limit -v

# Show print statements
pytest tests/test_system.py -v -s

# Stop on first failure
pytest tests/test_system.py -x
```

---

## 📝 Hints Available

Stuck? Check `HINTS.md` for progressive hints.

⚠️ **Warning:** Using hints reduces bonus points!

---

## 🎯 Learning Objectives

After completing this section, you'll master:
- Python import system and module resolution
- Circular dependency detection and resolution
- Shared state management patterns
- Type safety in configuration
- Boundary condition testing
- Integration debugging strategies

---

**Good luck! The clock is ticking... ⏰**
