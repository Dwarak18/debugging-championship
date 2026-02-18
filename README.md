# 🔥 DEBUGGING CHAMPIONSHIP 2026
## Elite Multi-Section Debugging Event

### 🎯 Event Overview
Welcome to the **Debugging Championship** - a three-section coding event designed to test your debugging, problem-solving, and code forensics skills under pressure.

---

## 📋 Event Structure

| Section | Title | Duration | Max Points | Difficulty |
|---------|-------|----------|------------|------------|
| 1 | Multi-File Debugging Lab | 45 min | 100 | ⭐⭐⭐ |
| 2 | Broken Project Recovery | 40 min | 100 | ⭐⭐⭐⭐ |
| 3 | Memory & Deadlock Simulation | 50 min | 100 | ⭐⭐⭐⭐⭐ |
| 4 | Logical Tracing | 35 min | 120 | ⭐⭐⭐⭐ |

**Total Duration:** 170 minutes (2 hours 50 minutes)  
**Total Points:** 420

---

## 🚀 Quick Start

### Prerequisites
```bash
python >= 3.8
pytest >= 7.0
```

### Setup
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/debugging-championship.git
cd debugging-championship

# Install dependencies
pip install -r requirements.txt

# Verify setup
pytest section1-multifile-debug/tests/
pytest section2-broken-recovery/tests/
pytest section3-memory-deadlock/tests/
pytest section4-logical-tracing/tests/
```

**Expected Result:** All tests should FAIL initially. Your job is to fix them.

---

## 📖 Rules & Guidelines

### ✅ You MAY:
- Fix bugs in existing code
- Add minimal helper functions
- Refactor logic while preserving structure
- Use debugging tools (print, pdb, logs)
- Research error messages

### ❌ You MAY NOT:
- Delete files
- Hardcode test outputs
- Skip test cases
- Use AI code generation during the event
- Collaborate with other participants

### 🏆 Victory Condition
```bash
pytest --tb=short
# Must show: all passed across all sections
```

---

## 🎖️ Scoring System

### Base Points (70%)
- Fix all visible bugs
- Pass all test cases
- Maintain code structure

### Bonus Points (30%)
- 🐛 Find hidden bugs not tested
- ⚡ Optimize performance
- 📝 Document root causes
- 🎨 Clean code improvements

---

## 🔧 Section Breakdown

### Section 1: Multi-File Debugging Lab
**Scenario:** User allocation system crashed during live onboarding  
**Bugs:** 10 issues across 6 interconnected modules  
**Focus:** Import errors, state corruption, circular dependencies

[Enter Section 1 →](./section1-multifile-debug/)

---

### Section 2: Broken Project Recovery
**Scenario:** Payment gateway down in production  
**Bugs:** 10 critical issues from logs and stack traces  
**Focus:** Null safety, log forensics, config validation

[Enter Section 2 →](./section2-broken-recovery/)

---

### Section 3: Memory & Deadlock Simulation
**Scenario:** Real-time system with memory leaks and deadlocks  
**Bugs:** 10 concurrency and memory management issues  
**Focus:** Thread safety, memory tracking, race conditions

[Enter Section 3 →](./section3-memory-deadlock/)

---

### Section 4: Logical Tracing — Code Detective
**Scenario:** Ex-employee planted logic bombs in 10 production functions  
**Bugs:** 10 algorithmic logic errors + 1 hidden bonus  
**Focus:** Execution tracing, boolean logic, boundary conditions, algorithmic precision

[Enter Section 4 →](./section4-logical-tracing/)

---

## 📊 Leaderboard

Submit your results via GitHub Pull Request:
1. Fork this repository
2. Create branch: `submission/YOUR_NAME`
3. Fix bugs and commit with meaningful messages
4. Run `pytest --json-report` and include `report.json`
5. Submit PR with title: `[SUBMISSION] Your Name - Score`

---

## 🎓 Learning Outcomes

After completing this event, you will master:
- Multi-file dependency debugging
- Production log analysis
- Stack trace interpretation
- Memory leak detection
- Deadlock prevention
- Configuration validation
- Error handling patterns
- Test-driven debugging
- Manual code execution tracing
- Boolean logic and boundary condition analysis
- Algorithmic bug identification

---

## 📞 Support

- **Issues:** Open a GitHub issue with `[HELP]` prefix
- **Clarifications:** Check `HINTS.md` in each section
- **Setup Problems:** See `SETUP.md`

---

## 📄 License
MIT License - Feel free to use for educational purposes

---

## 🙏 Acknowledgments
Created for GitHub Education - Debugging Skills Development Program

**Good luck, and may your print statements be ever informative! 🐛🔍**