# 💡 HINTS - Section 1: Multi-File Debugging Lab

## Progressive Hint System
Use hints wisely - each hint used reduces bonus points!

---

## 🟢 Level 1 Hints (Minimal Spoilers)

### Hint 1.1 - Import Error
> Look at the import statement in `main.py`. Does the module name match the actual filename?

### Hint 1.2 - Type Error
> Check `config.py`. Are all constants the correct type? Python comparison operators are type-sensitive.

### Hint 1.3 - Capacity Logic
> The function name is `calculate_capacity`. If it returns `True`, that means "has capacity". When should a system have NO capacity?

---

## 🟡 Level 2 Hints (Moderate Spoilers)

### Hint 2.1 - Import Error Solution Path
> The file is named `config.py`, not `configurations.py`. Update the import in `main.py`.

### Hint 2.2 - Type Error Solution Path
> `MAX_USERS = "5"` is a string. Change it to `MAX_USERS = 5` (integer).

### Hint 2.3 - Off-by-One Error
> Current logic: `return current > maximum` means it returns True only when OVER capacity (wrong!)
> Should be: `return current < maximum` to return True when UNDER capacity

### Hint 2.4 - Shared State Issue
> In `module_a.py`, you're importing the variable directly: `from state import user_count`
> This creates a local copy! Import the function instead: `from state import increment_count`

### Hint 2.5 - Circular Dependency
> `module_a` imports `module_b`  
> `module_b` imports `module_a`  
> This creates a circular dependency. One of them needs to change.

---

## 🔴 Level 3 Hints (Major Spoilers)

### Hint 3.1 - Complete Import Fix
```python
# main.py - Line 5
# BEFORE:
from configurations import MAX_USERS, SYSTEM_NAME

# AFTER:
from config import MAX_USERS, SYSTEM_NAME
```

### Hint 3.2 - Complete Type Fix
```python
# config.py - Line 5
# BEFORE:
MAX_USERS = "5"

# AFTER:
MAX_USERS = 5
```

### Hint 3.3 - Complete Capacity Fix
```python
# utils.py - calculate_capacity function
# BEFORE:
def calculate_capacity(current, maximum):
    return current > maximum

# AFTER:
def calculate_capacity(current, maximum):
    return current < maximum
```

### Hint 3.4 - Complete State Fix
```python
# module_a.py
# BEFORE:
from state import user_count

def add_user():
    global user_count
    user_count += 1  # Modifies local copy!

# AFTER:
from state import increment_count

def add_user():
    increment_count()  # Properly updates shared state
```

### Hint 3.5 - Circular Dependency Fix
**Option A:** Remove import from `module_b.py`
```python
# module_b.py - Remove this line:
# from module_a import get_user_list

# Modify get_analytics_summary():
def get_analytics_summary():
    # Import locally to break circular dependency
    from module_a import get_user_list
    total_users = len(get_user_list())
    total_events = len(analytics_log)
    return {"total_users": total_users, "total_events": total_events}
```

**Option B:** Remove import from `module_a.py`
```python
# module_a.py - Modify log_analytics call:
def add_user():
    from state import increment_count
    increment_count()
    
    user_id = len(users) + 1
    users.append(f"User_{user_id}")
    
    # Import locally
    from module_b import log_analytics
    log_analytics("user_added", user_id)
    
    return user_id
```

---

## 🎁 Hidden Bugs Hints

### Hidden Bug 1
> Check `utils.py` for a function that divides by zero. Fix: Change `return x / 0` to `return x / 1` or `return x`

### Hidden Bug 2
> The string config issue in MAX_USERS affects multiple places. Ensure it's an integer everywhere.

### Hidden Bug 3
> Look for unused imports or inefficient functions that could be removed or optimized.

---

## 🧠 Debugging Strategy

1. **Fix imports first** - Nothing works if modules can't load
2. **Fix types second** - Prevents runtime errors
3. **Fix logic third** - Get behavior correct
4. **Fix architecture fourth** - Break circular dependencies
5. **Find hidden bugs last** - Bonus points

---

## 🔍 Quick Verification Commands

```bash
# Test imports
python -c "from config import MAX_USERS; print(MAX_USERS, type(MAX_USERS))"

# Test capacity logic
python -c "from utils import calculate_capacity; print(calculate_capacity(4, 5), calculate_capacity(5, 5))"

# Test state management
python -c "from state import reset_state, increment_count, get_user_count; reset_state(); increment_count(); print(get_user_count())"

# Test circular dependency
python -c "from module_a import add_user; print('No circular dependency!')"
```

---

**Remember: Try to solve without hints first! Each hint reduces your bonus points. 🏆**
