# 💡 HINTS - Section 4: Logical Tracing

## Progressive Hint System
Use hints wisely — each level reveals more, but costs bonus points!

| Hint Level | Penalty | What It Reveals |
|------------|---------|-----------------|
| 🟢 Level 1 | −2 pts | Bug type identification |
| 🟡 Level 2 | −4 pts | Execution trace with examples |
| 🔴 Level 3 | −8 pts | Exact code fix |

---

## 🟢 Level 1 Hints (Bug Type Only)

### Hint 1.1 — calculate_discount
> Bug type: **Off-by-one error**. The boundary values ($50 and $100) aren't handled correctly.

### Hint 1.2 — authenticate_user
> Bug type: **Boolean operator error**. Think about which logical operator requires BOTH conditions to be true.

### Hint 1.3 — find_majority_element
> Bug type: **Missing verification step**. The Boyer-Moore algorithm finds a *candidate*, but doesn't confirm it.

### Hint 1.4 — calculate_compound_interest
> Bug type: **Operator precedence error**. Python's order of operations may not match the mathematical formula.

### Hint 1.5 — merge_sorted_arrays
> Bug type: **Index error**. After the main loop, the remaining elements aren't being appended from the right index.

### Hint 1.6 — validate_password
> Bug type: **Boolean operator error**. Similar to Hint 1.2 — which operator requires ALL conditions?

### Hint 1.7 — binary_search
> Bug type: **Loop boundary error**. What happens when `left == right`?

### Hint 1.8 — detect_cycle
> Bug type: **Pointer advancement error**. In Floyd's algorithm, the fast pointer must move at a different speed than the slow pointer.

### Hint 1.9 — calculate_tax_bracket
> Bug type: **Condition order error**. The middle tax brackets are being applied in the wrong order.

### Hint 1.10 — graph_shortest_path
> Bug type: **Mutable state error**. When you append to a list in Python, are you modifying the original or a copy?

### Hint 1.11 — calculate_fibonacci (BONUS)
> Bug type: **Missing base case**. What should F(0) return?

---

## 🟡 Level 2 Hints (Execution Traces)

### Hint 2.1 — calculate_discount
```
Input:  calculate_discount(100)
Trace:  100 > 100 → False (skipped!)
        100 > 50 → True → returns 0.05
Result: 0.05 (WRONG — should be 0.10)

The >= comparison is needed, not just >.
```

### Hint 2.2 — authenticate_user
```
Input:  authenticate_user("admin", "")
Trace:  "admin" or "" → "admin" (truthy)
        Returns True
Result: True (WRONG — should be False)

'or' passes if EITHER is truthy.
'and' passes only if BOTH are truthy.
```

### Hint 2.3 — find_majority_element
```
Input:  find_majority_element([1, 2, 3, 4, 5])
Trace:  After Boyer-Moore: candidate = 5, count = 1
        Returns 5 immediately
Result: 5 (WRONG — no element appears > 5/2 = 2.5 times)

The candidate must be verified by counting its actual occurrences.
```

### Hint 2.4 — calculate_compound_interest
```
Input:  calculate_compound_interest(1000, 0.05, 4, 2)
Trace:  amount = 1000 * (1 + 0.05/4) ** 4 * 2
         = 1000 * (1.0125) ** 4 * 2
         = 1000 * 1.05095... * 2
         = 2101.89 (WRONG)

Expected: 1000 * (1.0125) ** (4*2) = 1000 * (1.0125)**8 = 1104.49
Parentheses are needed around (compounds_per_year * years).
```

### Hint 2.5 — merge_sorted_arrays
```
Input:  merge_sorted_arrays([1, 3, 5], [2, 4, 6])
Trace:  After main loop with i=1, j=2: result = [1, 2, 3, 4]
        arr1[i+1:] = arr1[2:] = [5] ← SKIPS arr1[1] = 3!
        arr2[j+1:] = arr2[3:] = []

Result: [1, 2, 3, 4, 5] (WRONG — missing element)
Should extend from index i, not i+1.
```

### Hint 2.6 — validate_password
```
Input:  validate_password("Ab1")
Trace:  has_length = False (len 3 < 8)
        has_upper = True
        has_digit = True
        False or True or True → True
Result: True (WRONG — should be False because too short)
```

### Hint 2.7 — binary_search
```
Input:  binary_search([42], 42)
Trace:  left=0, right=0
        while 0 < 0 → False (loop never executes!)
        Returns -1
Result: -1 (WRONG — 42 is at index 0)

The condition should be left <= right.
```

### Hint 2.8 — detect_cycle
```
Input:  1→2→3→4→(back to 2)
Trace:  Step 1: slow=2, fast=2 → slow==fast → True? No!
        Actually: slow=2, fast=2 (fast only moved ONE step, same as slow)
        They meet too early for wrong reasons — or never properly race.

The fast pointer must advance by TWO nodes: fast = fast.next.next
```

### Hint 2.9 — calculate_tax_bracket
```
Input:  calculate_tax_bracket(90000)
Trace:  income > 85000 → tax += 5000*0.40 = 2000, income = 85000
        income > 10000 → tax += 75000*0.20 = 15000, income = 10000 ← WRONG!
        income > 40000 → False (10000 > 40000 is False, bracket skipped!)
        tax += 10000*0.10 = 1000
        Total: 18000 (WRONG — expected 22500)

The 20% and 30% brackets are swapped.
```

### Hint 2.10 — graph_shortest_path
```
Input:  graph_shortest_path({'A':['B','C'], 'B':['D'], ...}, 'A', 'D')
Trace:  path = ['A']
        new_path = path (SAME object!)
        new_path.append('B') → path is now ['A','B'] too!
        On next iteration, path.append('C') → ['A','B','C']

All paths point to the same list. Use path.copy() or list(path).
```

### Hint 2.11 — calculate_fibonacci (BONUS)
```
Input:  calculate_fibonacci(0)
Trace:  n=0, n < 0 → False
        n == 1 → False
        loop range(2, 1) → empty, never runs
        Returns b = 1
Result: 1 (WRONG — F(0) should be 0)
```

---

## 🔴 Level 3 Hints (Exact Fixes)

### Hint 3.1 — calculate_discount
```python
# BEFORE:
    if order_amount > 100:
        return 0.10
    elif order_amount > 50:
        return 0.05

# AFTER:
    if order_amount >= 100:
        return 0.10
    elif order_amount >= 50:
        return 0.05
```

### Hint 3.2 — authenticate_user
```python
# BEFORE:
    if username or password:

# AFTER:
    if username and password:
```

### Hint 3.3 — find_majority_element
```python
# BEFORE:
    return candidate

# AFTER:
    # Verify candidate is actually a majority
    if nums.count(candidate) > len(nums) // 2:
        return candidate
    return None
```

### Hint 3.4 — calculate_compound_interest
```python
# BEFORE:
    amount = principal * (1 + rate / compounds_per_year) ** compounds_per_year * years

# AFTER:
    amount = principal * (1 + rate / compounds_per_year) ** (compounds_per_year * years)
```

### Hint 3.5 — merge_sorted_arrays
```python
# BEFORE:
    result.extend(arr1[i + 1:])
    result.extend(arr2[j + 1:])

# AFTER:
    result.extend(arr1[i:])
    result.extend(arr2[j:])
```

### Hint 3.6 — validate_password
```python
# BEFORE:
    return has_length or has_upper or has_digit

# AFTER:
    return has_length and has_upper and has_digit
```

### Hint 3.7 — binary_search
```python
# BEFORE:
    while left < right:

# AFTER:
    while left <= right:
```

### Hint 3.8 — detect_cycle
```python
# BEFORE:
        fast = fast.next

# AFTER:
        fast = fast.next.next
```

### Hint 3.9 — calculate_tax_bracket
```python
# BEFORE:
    if income > 85000:
        tax += (income - 85000) * 0.40
        income = 85000
    if income > 10000:
        tax += (income - 10000) * 0.20
        income = 10000
    if income > 40000:
        tax += (income - 40000) * 0.30
        income = 40000

# AFTER:
    if income > 85000:
        tax += (income - 85000) * 0.40
        income = 85000
    if income > 40000:
        tax += (income - 40000) * 0.30
        income = 40000
    if income > 10000:
        tax += (income - 10000) * 0.20
        income = 10000
```

### Hint 3.10 — graph_shortest_path
```python
# BEFORE:
            new_path = path

# AFTER:
            new_path = list(path)
```

### Hint 3.11 — calculate_fibonacci (BONUS)
```python
# BEFORE:
    if n == 1:
        return 1

# AFTER:
    if n <= 1:
        return n
```
