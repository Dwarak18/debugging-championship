# 💥 SECTION 2: Broken Project Recovery

## 🚨 PRODUCTION DOWN: PAYMENT GATEWAY CRASH

### 🎯 Scenario
Your company's **payment gateway** crashed at 2:47 AM during peak traffic from a flash sale. Thousands of transactions failed. The error monitoring system captured logs, stack traces, and config dumps before going offline.

The VP of Engineering is demanding answers. You have **40 minutes** to:
1. Identify the root cause from logs
2. Fix critical null pointer errors
3. Repair corrupted configuration
4. Restore payment processing

**Business Impact:** $50K/minute in lost revenue

---

## 📋 Your Mission

Fix **10 critical bugs** using forensic debugging:
- `payment_gateway.py` - Core payment logic (4 bugs)
- `logs/error.log` - Production error logs (forensic analysis)
- `stack_trace.txt` - Python stack trace (line-by-line analysis)
- `config.json` - Corrupted configuration (3 bugs)

---

## 🔥 Incident Report

From the on-call engineer:

```
[02:47:13] CRITICAL - NoneType object has no attribute 'amount'
[02:47:14] ERROR - Transaction ID None rejected
[02:47:15] FATAL - Invalid config: API_TIMEOUT must be numeric
[02:47:16] ERROR - Negative transaction amount: -1500
[02:47:18] CRASH - System shutdown initiated
```

**Known Issues:**
1. Null payment objects crashing the system
2. Invalid configuration values (strings vs numbers)
3. Missing input validation (negative amounts)
4. Transaction rollback failing
5. Error handling swallowing useful information

---

## 📏 Constraints

### ✅ You MAY:
- Add null checks
- Fix config types
- Add input validation
- Improve error handling
- Add logging

### ❌ You MAY NOT:
- Skip payment validation
- Remove security checks
- Disable error logging
- Hardcode test values

---

## 🏆 Victory Condition

```bash
pytest tests/test_recovery.py -v
```

**Expected output:**
```
tests/test_recovery.py::test_null_payment_object PASSED
tests/test_recovery.py::test_log_parsing PASSED
tests/test_recovery.py::test_stack_trace_line PASSED
tests/test_recovery.py::test_invalid_config PASSED
tests/test_recovery.py::test_amount_validation PASSED
tests/test_recovery.py::test_transaction_rollback PASSED
tests/test_recovery.py::test_error_handling PASSED

========== 7 passed in 0.XX s ==========
```

---

## 🐛 Bug Checklist

### Critical Bugs
- [ ] Fix null payment object crash
- [ ] Fix config type mismatches
- [ ] Add negative amount validation
- [ ] Fix transaction ID validation
- [ ] Improve error messages

### Configuration Bugs
- [ ] API_TIMEOUT should be int, not string
- [ ] MAX_RETRY should be int, not string
- [ ] Missing required config keys

### Hidden Bugs (Bonus)
- [ ] Race condition in transaction processing
- [ ] Memory leak in error logger
- [ ] Timezone bug in timestamps

---

## 📊 Scoring

| Category | Points |
|----------|--------|
| Fix null safety | 15 |
| Fix config validation | 15 |
| Add input validation | 10 |
| Fix error handling | 10 |
| Log forensics | 10 |
| Stack trace analysis | 10 |
| Pass all 7 tests | 15 |
| Find hidden bugs | 15 |
| **TOTAL** | **100** |

---

## ⏱️ Time Limit

**40 minutes**

---

## 💡 Debugging Tips

1. **Read the logs first** - They tell you what went wrong
2. **Follow the stack trace** - Find the exact line that crashed
3. **Check config types** - JSON can be tricky with types
4. **Add null checks everywhere** - Never trust external input
5. **Validate inputs** - Negative amounts? Invalid IDs?
6. **Test error paths** - Make sure errors are handled gracefully

---

## 🔍 Forensic Analysis Tools

### Analyzing Logs
```bash
# Find all ERROR lines
grep "ERROR" logs/error.log

# Find null-related errors
grep -i "none\|null" logs/error.log

# Count error types
grep "ERROR" logs/error.log | cut -d'-' -f2 | sort | uniq -c
```

### Analyzing Stack Traces
```bash
# View stack trace
cat stack_trace.txt

# Find the triggering line
grep "File.*line" stack_trace.txt
```

### Validating Config
```bash
# Pretty print config
python -m json.tool config.json

# Check specific values
python -c "import json; print(json.load(open('config.json')))"
```

---

## 📝 Hints Available

Stuck? Check `HINTS.md` for progressive hints.

⚠️ **Warning:** Using hints reduces bonus points!

---

## 🎯 Learning Objectives

After completing this section, you'll master:
- Production log analysis
- Stack trace interpretation
- Null safety patterns
- Configuration validation
- Input sanitization
- Error handling best practices
- Transaction integrity
- Forensic debugging

---

**The clock is ticking... Every second counts! 💸⏰**
