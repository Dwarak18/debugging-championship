"""
Section 4: Logical Tracing - Code Detective Challenge

SCENARIO:
A disgruntled ex-employee planted subtle logic bombs in 10 critical
production functions before leaving the company. Each function compiles
and runs without errors — but produces WRONG output for specific inputs.

YOUR MISSION:
Find and fix all 10 sabotaged algorithms before market open.
Each function has exactly ONE logic bug requiring a 1-3 line fix.

MODULES AFFECTED:
- E-commerce pricing engine
- Authentication system
- Core algorithm library
- Financial calculations engine
"""


# ============================================================
# FUNCTION 1: E-Commerce Discount Calculator
# ============================================================
# Business rule:
#   - Orders >= $100 get 10% discount
#   - Orders >= $50  get 5% discount
#   - Orders < $50   get no discount
# ============================================================

def calculate_discount(order_amount):
    """Calculate discount based on order amount.

    Args:
        order_amount (float): The total order amount.

    Returns:
        float: The discount percentage (0.0, 0.05, or 0.10).
    """
    if order_amount > 100:        # BUG: should be >= 100
        return 0.10
    elif order_amount > 50:       # BUG: should be >= 50
        return 0.05
    else:
        return 0.0


# ============================================================
# FUNCTION 2: User Authentication
# ============================================================
# Rules:
#   - Username must not be empty
#   - Password must not be empty
#   - Both must be non-empty to authenticate
# ============================================================

def authenticate_user(username, password):
    """Authenticate a user with username and password.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        bool: True if authenticated, False otherwise.
    """
    if username or password:       # BUG: should be 'and' not 'or'
        return True
    return False


# ============================================================
# FUNCTION 3: Majority Element Finder
# ============================================================
# Find the element that appears more than n/2 times in the list.
# Uses Boyer-Moore Voting Algorithm.
# Returns None if no majority element exists.
# ============================================================

def find_majority_element(nums):
    """Find the majority element (appears > n/2 times).

    Args:
        nums (list): List of integers.

    Returns:
        int or None: The majority element, or None.
    """
    if not nums:
        # BUG: should return None for empty list
        raise ValueError("List is empty!")  # BUG: crashes instead of returning None

    candidate = nums[0]
    count = 1

    for i in range(1, len(nums)):
        if count == 1:              # BUG: should be count == 0
            candidate = nums[i]
            count = 1
        elif nums[i] == candidate:
            count += 1
        else:
            count -= 1

    # BUG: returns candidate without verifying it's actually a majority
    return candidate  # Should verify count > n/2 before returning


# ============================================================
# FUNCTION 4: Compound Interest Calculator
# ============================================================
# Formula: A = P * (1 + r/n)^(n*t)
#   P = principal, r = annual rate, n = compounds/year, t = years
# Returns the final amount (not the interest earned).
# ============================================================

def calculate_compound_interest(principal, rate, compounds_per_year, years):
    """Calculate compound interest.

    Args:
        principal (float): Initial investment.
        rate (float): Annual interest rate (e.g., 0.05 for 5%).
        compounds_per_year (int): Number of times interest compounds per year.
        years (int): Number of years.

    Returns:
        float: Final amount after compound interest.
    """
    # BUG: operator precedence — rate / compounds_per_year * years
    # should be rate / compounds_per_year, then ** (compounds_per_year * years)
    amount = principal * (1 + rate / compounds_per_year) ** compounds_per_year * years
    return round(amount, 2)


# ============================================================
# FUNCTION 5: Merge Two Sorted Arrays
# ============================================================
# Given two sorted lists, merge them into one sorted list.
# ============================================================

def merge_sorted_arrays(arr1, arr2):
    """Merge two sorted arrays into one sorted array.

    Args:
        arr1 (list): First sorted list.
        arr2 (list): Second sorted list.

    Returns:
        list: Merged sorted list.
    """
    result = []
    i, j = 0, 0

    while i < len(arr1) and j < len(arr2):
        if arr1[i] <= arr2[j]:
            result.append(arr1[i])
            i += 1
        else:
            result.append(arr2[j])
            j += 1

    # BUG: appends from wrong index (i+1 / j+1 instead of i / j)
    result.extend(arr1[i + 1:])
    result.extend(arr2[j + 1:])

    return result


# ============================================================
# FUNCTION 6: Password Validator
# ============================================================
# Password requirements:
#   - At least 8 characters long
#   - Contains at least one uppercase letter
#   - Contains at least one digit
# All three conditions must be met.
# ============================================================

def validate_password(password):
    """Validate password meets security requirements.

    Args:
        password (str): The password to validate.

    Returns:
        bool: True if password is valid, False otherwise.
    """
    has_length = len(password) >= 8
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)

    # BUG: uses OR instead of AND — any single condition passes
    return has_length or has_upper or has_digit


# ============================================================
# FUNCTION 7: Binary Search
# ============================================================
# Standard binary search on a sorted list.
# Returns the index of the target, or -1 if not found.
# ============================================================

def binary_search(sorted_list, target):
    """Perform binary search on a sorted list.

    Args:
        sorted_list (list): A sorted list of comparable elements.
        target: The element to search for.

    Returns:
        int: Index of target, or -1 if not found.
    """
    left, right = 1, len(sorted_list) - 1   # BUG: left should start at 0

    while left < right:            # BUG: should be left <= right
        mid = (left + right) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return len(sorted_list)        # BUG: should return -1 when not found


# ============================================================
# FUNCTION 8: Linked List Cycle Detection
# ============================================================
# Uses Floyd's Tortoise and Hare algorithm.
# ============================================================

class ListNode:
    """Simple linked list node."""
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def detect_cycle(head):
    """Detect if a linked list has a cycle.

    Args:
        head (ListNode): Head of the linked list.

    Returns:
        bool: True if cycle exists, False otherwise.
    """
    if not head or not head.next:
        return True   # BUG: should return False (no cycle if empty/single node)

    slow = head
    fast = head

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next    # correctly advances by 2
        if slow == fast:
            return False          # BUG: should return True when cycle detected

    return True   # BUG: should return False when no cycle found


# ============================================================
# FUNCTION 9: Tax Bracket Calculator
# ============================================================
# Tax brackets (progressive):
#   $0      - $10,000  → 10%
#   $10,001 - $40,000  → 20%
#   $40,001 - $85,000  → 30%
#   $85,001+           → 40%
#
# Tax is calculated progressively (each bracket only applies
# to income within that range).
# ============================================================

def calculate_tax_bracket(income):
    """Calculate progressive tax based on income brackets.

    Args:
        income (float): Annual income.

    Returns:
        float: Total tax owed.
    """
    if income < 0:             # BUG: should be income <= 0 (zero income not handled)
        return 0.0

    tax = 100.0                 # BUG: should start at 0.0 (phantom flat-fee bug)

    # BUG: Bracket conditions checked in wrong order —
    # the first condition (income > 85000) catches everything above 85k
    # but then falls through incorrectly. The elif chain is misordered.
    if income > 85000:
        tax += (income - 85000) * 0.40
        income = 85000
    if income > 10000:             # BUG: should check > 40000 here
        tax += (income - 10000) * 0.20
        income = 10000
    if income > 40000:             # BUG: should check > 10000 here
        tax += (income - 40000) * 0.30
        income = 40000
    tax += income * 0.10

    return round(tax, 2)


# ============================================================
# FUNCTION 10: Graph Shortest Path (BFS)
# ============================================================
# Find shortest path between two nodes in an unweighted graph.
# Graph is given as an adjacency list (dict of lists).
# Returns the shortest path as a list, or empty list if no path.
# ============================================================

def graph_shortest_path(graph, start, end):
    """Find shortest path in an unweighted graph using BFS.

    Args:
        graph (dict): Adjacency list. e.g. {'A': ['B','C'], 'B': ['A']}
        start: Start node.
        end: End node.

    Returns:
        list: Shortest path as list of nodes, or [] if no path.
    """
    if start == end:
        return []   # BUG: should return [start]

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
            new_path = path             # BUG: should be path.copy() or list(path)
            new_path.append(neighbor)
            if neighbor == end:
                return new_path
            queue.append(new_path)

    return [start]   # BUG: should return [] when no path found


# ============================================================
# BONUS FUNCTION: Fibonacci Calculator
# ============================================================
# Calculate the nth Fibonacci number.
# F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)
# ============================================================

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number.

    Args:
        n (int): The index (0-based) of the Fibonacci number.

    Returns:
        int: The nth Fibonacci number.

    Raises:
        ValueError: If n is negative.
    """
    if n < -1:   # BUG: should be n < 0 (misses n == -1 case)
        raise ValueError("n must be non-negative")

    # BUG: missing base case for n == 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
