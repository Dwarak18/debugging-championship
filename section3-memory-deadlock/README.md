# ⚡ SECTION 3: Memory & Deadlock Simulation

## 🚨 REAL-TIME SYSTEM FAILURE: MEMORY EXHAUSTION & DEADLOCKS

### 🎯 Scenario
Your company's **real-time monitoring system** has been experiencing intermittent crashes for the past 48 hours. The system tracks sensor data from 10,000+ IoT devices and processes events in real-time. Three critical subsystems are failing:

1. **Memory Tracker** - Leaking memory on every allocation cycle
2. **Thread Manager** - Deadlocking under concurrent access
3. **Resource Scheduler** - Starving low-priority tasks

The system will run out of memory in **50 minutes** at current leak rate. Fix it before the entire infrastructure goes down.

---

## 📋 Your Mission

Fix **10 critical bugs** across 3 modules:
- `memory_tracker.py` - Memory allocation/free tracking (4 bugs)
- `thread_manager.py` - Thread lock management (3 bugs)
- `resource_scheduler.py` - Resource scheduling (3 bugs)

---

## 🚨 Known Issues

From the monitoring dashboard:

1. **Memory leak** - Allocations not tracked correctly
2. **Double free** - System crashes on freeing already-freed memory
3. **Deadlock** - Two threads waiting for each other's locks
4. **Starvation** - Low-priority tasks never execute
5. **Race condition** - Concurrent updates corrupting shared state

---

## 📏 Constraints

### ✅ You MAY:
- Fix tracking logic
- Add synchronization primitives
- Fix scheduling algorithms
- Add error handling

### ❌ You MAY NOT:
- Remove threading/concurrency
- Disable memory tracking
- Skip priority scheduling
- Hardcode test values

---

## 🏆 Victory Condition

```bash
pytest tests/test_memory_deadlock.py -v
```

**Expected output:**
```
tests/test_memory_deadlock.py::test_memory_allocation PASSED
tests/test_memory_deadlock.py::test_memory_free PASSED
tests/test_memory_deadlock.py::test_double_free_detection PASSED
tests/test_memory_deadlock.py::test_memory_leak_detection PASSED
tests/test_memory_deadlock.py::test_deadlock_detection PASSED
tests/test_memory_deadlock.py::test_lock_ordering PASSED
tests/test_memory_deadlock.py::test_resource_allocation PASSED
tests/test_memory_deadlock.py::test_resource_release PASSED
tests/test_memory_deadlock.py::test_priority_scheduling PASSED
tests/test_memory_deadlock.py::test_starvation_prevention PASSED

========== 10 passed in 0.XX s ==========
```

---

## 🐛 Bug Checklist

### Memory Tracker Bugs
- [ ] Fix allocation tracking (not recording allocations)
- [ ] Fix free tracking (not removing freed blocks)
- [ ] Add double-free detection
- [ ] Fix memory leak detection logic

### Thread Manager Bugs
- [ ] Fix deadlock from lock ordering
- [ ] Fix lock acquisition timeout
- [ ] Add proper lock release on failure

### Resource Scheduler Bugs
- [ ] Fix priority queue ordering
- [ ] Prevent starvation of low-priority tasks
- [ ] Fix resource release tracking

### Hidden Bugs (Bonus)
- [ ] Race condition in memory tracker
- [ ] Memory leak in thread cleanup
- [ ] Priority inversion scenario

---

## 📊 Scoring

| Category | Points |
|----------|--------|
| Fix memory allocation tracking | 10 |
| Fix memory free tracking | 10 |
| Add double-free detection | 15 |
| Fix memory leak detection | 10 |
| Fix deadlock issues | 15 |
| Fix lock ordering | 10 |
| Fix resource scheduling | 10 |
| Fix starvation prevention | 10 |
| Find hidden bugs | 10 |
| **TOTAL** | **100** |

---

## ⏱️ Time Limit

**50 minutes**

---

## 💡 Debugging Tips

1. **Trace memory operations** - Track every alloc and free
2. **Draw lock dependency graphs** - Visualize deadlocks
3. **Use timeouts** - Don't let threads wait forever
4. **Check ordering** - Priority queues need correct comparisons
5. **Test edge cases** - Double free, zero allocation, etc.
6. **Think concurrently** - Race conditions hide in shared state

---

## 📝 Hints Available

Stuck? Check `HINTS.md` for progressive hints.

⚠️ **Warning:** Using hints reduces bonus points!

---

## 🎯 Learning Objectives

After completing this section, you'll master:
- Memory allocation tracking patterns
- Double-free detection and prevention
- Deadlock detection and prevention
- Lock ordering protocols
- Resource starvation prevention
- Priority scheduling algorithms
- Thread-safe data structures
- Concurrent programming patterns

---

**The memory is leaking... tick tock! 💧⏰**
