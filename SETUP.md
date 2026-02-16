# 🛠️ SETUP GUIDE - Debugging Championship

## System Requirements

### Minimum Requirements
- **OS:** Linux, macOS, or Windows 10+
- **Python:** 3.8 or higher
- **RAM:** 2GB minimum
- **Disk Space:** 100MB

### Recommended
- **Python:** 3.10+
- **IDE:** VS Code, PyCharm, or similar
- **Terminal:** Bash, Zsh, or PowerShell

---

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/debugging-championship.git
cd debugging-championship
```

### 2. Create Virtual Environment (Recommended)
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
pytest==7.4.3
pytest-json-report==1.5.0
pytest-timeout==2.2.0
pytest-cov==4.1.0
```

### 4. Verify Installation
```bash
pytest --version
# Should show: pytest 7.4.3

python --version
# Should show: Python 3.8+
```

---

## Running Tests

### Test Individual Sections
```bash
# Section 1
cd section1-multifile-debug
pytest tests/ -v

# Section 2
cd ../section2-broken-recovery
pytest tests/ -v

# Section 3
cd ../section3-memory-deadlock
pytest tests/ -v
```

### Test Entire Championship
```bash
# From project root
pytest -v
```

### Generate Test Report
```bash
pytest --json-report --json-report-file=report.json
```

---

## Troubleshooting

### Issue: Import Errors
```
ModuleNotFoundError: No module named 'xyz'
```

**Solution:**
```bash
# Ensure you're in virtual environment
pip install -r requirements.txt

# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

### Issue: Tests Not Found
```
ERROR: file or directory not found: tests/
```

**Solution:**
```bash
# Ensure you're in correct directory
pwd

# Check directory structure
ls -la

# Run from section directory
cd section1-multifile-debug
pytest tests/
```

---

### Issue: Permission Denied
```
PermissionError: [Errno 13] Permission denied
```

**Solution (Linux/macOS):**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

**Solution (Windows):**
Run terminal as Administrator

---

### Issue: Python Version Conflict
```
SyntaxError: invalid syntax (using Python 2.7)
```

**Solution:**
```bash
# Use Python 3 explicitly
python3 -m pytest

# Or update default Python
alias python=python3
```

---

## IDE Setup

### VS Code
1. Install Python extension
2. Open project folder
3. Select virtual environment (Ctrl+Shift+P → "Python: Select Interpreter")
4. Install recommended extensions:
   - Python Test Explorer
   - Error Lens

### PyCharm
1. Open project
2. Configure interpreter (Settings → Project → Python Interpreter)
3. Enable pytest (Settings → Tools → Python Integrated Tools → Testing)
4. Right-click `tests/` → "Run pytest"

---

## Timer Setup (Optional)

### Using CLI Timer
```bash
# Install
pip install timer-cli

# Run section with timer
timer 45m "Section 1 Complete!" & pytest section1-multifile-debug/tests/
```

### Using Python Timer
```python
import time
import subprocess

def run_with_timer(minutes, command):
    start = time.time()
    subprocess.run(command, shell=True)
    elapsed = (time.time() - start) / 60
    print(f"\n⏱️  Time: {elapsed:.2f} / {minutes} minutes")

run_with_timer(45, "pytest section1-multifile-debug/tests/")
```

---

## Pre-Event Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] All test suites can be discovered (even if failing)
- [ ] IDE/editor configured
- [ ] Timer ready (optional)
- [ ] GitHub account ready for submission
- [ ] Read all README files

---

## Getting Help

### During Setup
- Check existing GitHub issues
- Create new issue with `[SETUP]` prefix
- Include error messages and system info

### During Event
- Read `HINTS.md` in each section
- Check test output carefully
- Use `pytest -v` for verbose output
- Use `pytest --tb=long` for full tracebacks

---

## Post-Event Submission

```bash
# 1. Ensure all tests pass
pytest

# 2. Generate report
pytest --json-report --json-report-file=report.json

# 3. Create submission branch
git checkout -b submission/YOUR_NAME

# 4. Commit fixes
git add .
git commit -m "Complete debugging championship"

# 5. Push and create PR
git push origin submission/YOUR_NAME
```

---

## Additional Resources

- **pytest docs:** https://docs.pytest.org
- **Python debugging:** https://docs.python.org/3/library/pdb.html
- **Git workflow:** https://guides.github.com

---

**Ready to debug? Return to main README and begin! 🚀**
