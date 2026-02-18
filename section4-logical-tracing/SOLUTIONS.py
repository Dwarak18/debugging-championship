"""
SOLUTIONS — Section 4: Logical Tracing (INSTRUCTOR ONLY)

This file contains all 10+1 functions with bugs FIXED.
Do NOT distribute to participants.

To verify:
    cp SOLUTIONS.py logic_tracing.py
    pytest tests/test_logic_tracing.py -v
    # Expected: 30 passed
"""


# ============================================================
# FUNCTION 1: calculate_discount — FIXED
# FIX: Changed > to >= for boundary values
# ============================================================

def calculate_discount(order_amount):
    """Calculate discount based on order amount."""
    if order_amount >= 100:       # FIX: >= instead of >
        return 0.10
    elif order_amount >= 50:      # FIX: >= instead of >
        return 0.05
    else:
        return 0.0


# ============================================================
# FUNCTION 2: authenticate_user — FIXED
# FIX: Changed 'or' to 'and' — both fields required
# ============================================================

def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    if username and password:     # FIX: 'and' instead of 'or'
        return True
    return False


# ============================================================
# FUNCTION 3: find_majority_element — FIXED
# FIX: Added verification step after Boyer-Moore candidate selection
# ============================================================

def find_majority_element(nums):
    """Find the majority element (appears > n/2 times)."""
    if not nums:
        return None

    candidate = nums[0]
    count = 1

    for i in range(1, len(nums)):
        if count == 0:
            candidate = nums[i]
            count = 1
        elif nums[i] == candidate:
            count += 1
        else:
            count -= 1

    # FIX: Verify candidate actually appears > n/2 times
    if nums.count(candidate) > len(nums) // 2:
        return candidate
    return None


# ============================================================
# FUNCTION 4: calculate_compound_interest — FIXED
# FIX: Added parentheses around (compounds_per_year * years) exponent
# ============================================================

def calculate_compound_interest(principal, rate, compounds_per_year, years):
    """Calculate compound interest."""
    # FIX: Parentheses around the exponent (compounds_per_year * years)
    amount = principal * (1 + rate / compounds_per_year) ** (compounds_per_year * years)
    return round(amount, 2)


# ============================================================
# FUNCTION 5: merge_sorted_arrays — FIXED
# FIX: Changed i+1/j+1 to i/j for remaining elements
# ============================================================

def merge_sorted_arrays(arr1, arr2):
    """Merge two sorted arrays into one sorted array."""
    result = []
    i, j = 0, 0

    while i < len(arr1) and j < len(arr2):
        if arr1[i] <= arr2[j]:
            result.append(arr1[i])
            i += 1
        else:
            result.append(arr2[j])
            j += 1

    # FIX: Extend from current index i/j, not i+1/j+1
    result.extend(arr1[i:])
    result.extend(arr2[j:])

    return result


# ============================================================
# FUNCTION 6: validate_password — FIXED
# FIX: Changed 'or' to 'and' — all conditions must be met
# ============================================================

def validate_password(password):
    """Validate password meets security requirements."""
    has_length = len(password) >= 8
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)

    # FIX: 'and' instead of 'or' — ALL conditions required
    return has_length and has_upper and has_digit


# ============================================================
# FUNCTION 7: binary_search — FIXED
# FIX: Changed < to <= in while loop condition
# ============================================================

def binary_search(sorted_list, target):
    """Perform binary search on a sorted list."""
    left, right = 0, len(sorted_list) - 1

    while left <= right:           # FIX: <= instead of <
        mid = (left + right) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1


# ============================================================
# FUNCTION 8: detect_cycle — FIXED
# FIX: Fast pointer advances by 2 nodes instead of 1
# ============================================================

class ListNode:
    """Simple linked list node."""
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def detect_cycle(head):
    """Detect if a linked list has a cycle."""
    if not head or not head.next:
        return False

    slow = head
    fast = head

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next     # FIX: advance by 2 nodes, not 1
        if slow == fast:
            return True

    return False


# ============================================================
# FUNCTION 9: calculate_tax_bracket — FIXED
# FIX: Corrected bracket order (85k → 40k → 10k)
# ============================================================

def calculate_tax_bracket(income):
    """Calculate progressive tax based on income brackets."""
    if income <= 0:
        return 0.0

    tax = 0.0

    if income > 85000:
        tax += (income - 85000) * 0.40
        income = 85000
    # FIX: Check 40000 BEFORE 10000 (was swapped)
    if income > 40000:
        tax += (income - 40000) * 0.30
        income = 40000
    if income > 10000:
        tax += (income - 10000) * 0.20
        income = 10000
    tax += income * 0.10

    return round(tax, 2)


# ============================================================
# FUNCTION 10: graph_shortest_path — FIXED
# FIX: Copy path list instead of referencing same object
# ============================================================

def graph_shortest_path(graph, start, end):
    """Find shortest path in an unweighted graph using BFS."""
    if start == end:
        return [start]

    if start not in graph:
        return []

    from collections import deque

    queue = deque()
    queue.append([start])
    visited = set()

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node in visited:
            continue
        visited.add(node)

        for neighbor in graph.get(node, []):
            new_path = list(path)   # FIX: create a copy, not a reference
            new_path.append(neighbor)
            if neighbor == end:
                return new_path
            queue.append(new_path)

    return []


# ============================================================
# BONUS: calculate_fibonacci — FIXED
# FIX: Handle n==0 base case (returns 0)
# ============================================================

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n < 0:
        raise ValueError("n must be non-negative")

    # FIX: Handle both base cases: F(0)=0 and F(1)=1
    if n <= 1:
        return n

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


# ============================================================
# VERIFICATION (run this file directly to self-test)
# ============================================================

if __name__ == "__main__":
    print("=== Solution Verification ===\n")

    # 1. Discount
    assert calculate_discount(100) == 0.10
    assert calculate_discount(50) == 0.05
    assert calculate_discount(30) == 0.0
    print("✅ 1. calculate_discount")

    # 2. Auth
    assert authenticate_user("admin", "pass") is True
    assert authenticate_user("admin", "") is False
    assert authenticate_user("", "pass") is False
    print("✅ 2. authenticate_user")

    # 3. Majority
    assert find_majority_element([1, 2, 3, 4, 5]) is None
    assert find_majority_element([3, 3, 3, 2, 1]) == 3
    print("✅ 3. find_majority_element")

    # 4. Compound interest
    assert calculate_compound_interest(1000, 0.05, 4, 2) == 1104.49
    print("✅ 4. calculate_compound_interest")

    # 5. Merge
    assert merge_sorted_arrays([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]
    print("✅ 5. merge_sorted_arrays")

    # 6. Password
    assert validate_password("Secure1234") is True
    assert validate_password("Ab1") is False
    print("✅ 6. validate_password")

    # 7. Binary search
    assert binary_search([42], 42) == 0
    assert binary_search([1, 2, 3, 4, 5], 5) == 4
    print("✅ 7. binary_search")

    # 8. Cycle detection
    n1, n2, n3 = ListNode(1), ListNode(2), ListNode(3)
    n1.next, n2.next, n3.next = n2, n3, n2
    assert detect_cycle(n1) is True
    print("✅ 8. detect_cycle")

    # 9. Tax
    assert calculate_tax_bracket(90000) == 22500.0
    assert calculate_tax_bracket(8000) == 800.0
    print("✅ 9. calculate_tax_bracket")

    # 10. Graph
    g = {'A': ['B', 'C'], 'B': ['A', 'D'], 'C': ['A', 'D'], 'D': ['B', 'C']}
    p = graph_shortest_path(g, 'A', 'D')
    assert len(p) == 3 and p[0] == 'A' and p[-1] == 'D'
    print("✅ 10. graph_shortest_path")

    # 11. Fibonacci (BONUS)
    assert calculate_fibonacci(0) == 0
    assert calculate_fibonacci(10) == 55
    print("✅ 11. calculate_fibonacci (BONUS)")

    print("\n🎉 All solutions verified!")
