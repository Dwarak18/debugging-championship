"""
Test Suite for Section 4: Logical Tracing - Code Detective Challenge

Each test targets exactly ONE buggy function.
All 11 tests should FAIL on the original code.
After fixing all bugs, all 11 tests should PASS.

Run with:
    pytest tests/test_logic_tracing.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic_tracing import (
    calculate_discount,
    authenticate_user,
    find_majority_element,
    calculate_compound_interest,
    merge_sorted_arrays,
    validate_password,
    binary_search,
    detect_cycle,
    ListNode,
    calculate_tax_bracket,
    graph_shortest_path,
    calculate_fibonacci,
)


# ------------------------------------------------------------------
# Test 1: calculate_discount — off-by-one on boundary values
# ------------------------------------------------------------------
class TestCalculateDiscount:
    def test_discount_boundaries(self):
        """Orders of exactly $100 and $50 should receive discounts."""
        # Exactly $100 → 10% discount
        assert calculate_discount(100) == 0.10, \
            "Order of exactly $100 should get 10% discount"
        # Exactly $50 → 5% discount
        assert calculate_discount(50) == 0.05, \
            "Order of exactly $50 should get 5% discount"
        # Above thresholds
        assert calculate_discount(150) == 0.10
        assert calculate_discount(75) == 0.05
        # Below threshold
        assert calculate_discount(30) == 0.0


# ------------------------------------------------------------------
# Test 2: authenticate_user — boolean logic (AND vs OR)
# ------------------------------------------------------------------
class TestAuthenticateUser:
    def test_both_fields_required(self):
        """Authentication should fail if either field is empty."""
        # Both provided → True
        assert authenticate_user("admin", "pass123") is True
        # Missing password → False
        assert authenticate_user("admin", "") is False, \
            "Should reject when password is empty"
        # Missing username → False
        assert authenticate_user("", "pass123") is False, \
            "Should reject when username is empty"
        # Both empty → False
        assert authenticate_user("", "") is False


# ------------------------------------------------------------------
# Test 3: find_majority_element — missing verification step
# ------------------------------------------------------------------
class TestFindMajorityElement:
    def test_no_majority(self):
        """Should return None when no element has > n/2 occurrences."""
        assert find_majority_element([1, 2, 3, 4, 5]) is None, \
            "No element appears > n/2 times; should return None"

    def test_has_majority(self):
        """Should correctly identify a majority element."""
        assert find_majority_element([3, 3, 3, 2, 1]) == 3
        assert find_majority_element([1, 1, 1, 1, 2, 3]) == 1

    def test_empty(self):
        assert find_majority_element([]) is None


# ------------------------------------------------------------------
# Test 4: calculate_compound_interest — operator precedence
# ------------------------------------------------------------------
class TestCompoundInterest:
    def test_standard_calculation(self):
        """$1000 at 5% compounded quarterly for 2 years → $1104.49."""
        result = calculate_compound_interest(1000, 0.05, 4, 2)
        assert result == 1104.49, \
            f"Expected $1104.49, got ${result}. Check operator precedence in formula."

    def test_annual_compounding(self):
        """$5000 at 10% compounded annually for 3 years → $6655.0."""
        result = calculate_compound_interest(5000, 0.10, 1, 3)
        assert result == 6655.0, \
            f"Expected $6655.00, got ${result}"

    def test_zero_years(self):
        """No time elapsed means principal is returned."""
        result = calculate_compound_interest(1000, 0.05, 4, 0)
        assert result == 1000.0


# ------------------------------------------------------------------
# Test 5: merge_sorted_arrays — index error on leftover elements
# ------------------------------------------------------------------
class TestMergeSortedArrays:
    def test_basic_merge(self):
        """Merge [1,3,5] and [2,4,6] → [1,2,3,4,5,6]."""
        result = merge_sorted_arrays([1, 3, 5], [2, 4, 6])
        assert result == [1, 2, 3, 4, 5, 6], \
            f"Expected [1,2,3,4,5,6], got {result}"

    def test_unequal_lengths(self):
        """Merge arrays of different lengths."""
        result = merge_sorted_arrays([1, 2], [3, 4, 5, 6])
        assert result == [1, 2, 3, 4, 5, 6]

    def test_empty_arrays(self):
        assert merge_sorted_arrays([], [1, 2]) == [1, 2]
        assert merge_sorted_arrays([1, 2], []) == [1, 2]
        assert merge_sorted_arrays([], []) == []


# ------------------------------------------------------------------
# Test 6: validate_password — boolean logic (AND vs OR)
# ------------------------------------------------------------------
class TestValidatePassword:
    def test_all_conditions_required(self):
        """Password must satisfy ALL three conditions simultaneously."""
        # Valid: long enough, has uppercase, has digit
        assert validate_password("Secure1234") is True
        # Fails length (too short, even with upper + digit)
        assert validate_password("Ab1") is False, \
            "Short password should be rejected even with upper + digit"
        # Fails uppercase (long enough, has digit, no uppercase)
        assert validate_password("alllower1234") is False, \
            "Password without uppercase should be rejected"
        # Fails digit (long enough, has uppercase, no digit)
        assert validate_password("NoDigitsHere") is False, \
            "Password without digit should be rejected"


# ------------------------------------------------------------------
# Test 7: binary_search — loop boundary (< vs <=)
# ------------------------------------------------------------------
class TestBinarySearch:
    def test_find_single_element(self):
        """Should find an element in a single-element list."""
        assert binary_search([42], 42) == 0, \
            "Failed to find element in single-element list — check loop condition"

    def test_find_last_element(self):
        """Should find the last element in the list."""
        assert binary_search([1, 2, 3, 4, 5], 5) == 4

    def test_find_first_element(self):
        assert binary_search([1, 2, 3, 4, 5], 1) == 0

    def test_not_found(self):
        assert binary_search([1, 2, 3, 4, 5], 99) == -1

    def test_empty_list(self):
        assert binary_search([], 1) == -1


# ------------------------------------------------------------------
# Test 8: detect_cycle — pointer advancement
# ------------------------------------------------------------------
class TestDetectCycle:
    def test_cycle_detection(self):
        """Should detect a cycle in the linked list."""
        # Build: 1 → 2 → 3 → 4 → back to 2
        node1 = ListNode(1)
        node2 = ListNode(2)
        node3 = ListNode(3)
        node4 = ListNode(4)
        node1.next = node2
        node2.next = node3
        node3.next = node4
        node4.next = node2  # cycle here

        assert detect_cycle(node1) is True, \
            "Failed to detect cycle — is the fast pointer advancing by 2?"

    def test_no_cycle(self):
        """Should correctly identify a list with no cycle."""
        node1 = ListNode(1)
        node2 = ListNode(2)
        node3 = ListNode(3)
        node1.next = node2
        node2.next = node3

        assert detect_cycle(node1) is False

    def test_empty_and_single(self):
        assert detect_cycle(None) is False
        assert detect_cycle(ListNode(1)) is False


# ------------------------------------------------------------------
# Test 9: calculate_tax_bracket — condition precedence
# ------------------------------------------------------------------
class TestTaxBracket:
    def test_progressive_tax(self):
        """$90,000 income should be taxed progressively across all brackets.

        Bracket breakdown:
            $0–$10,000   → $10,000 × 10% = $1,000
            $10,001–$40k → $30,000 × 20% = $6,000
            $40,001–$85k → $45,000 × 30% = $13,500
            $85,001–$90k → $5,000  × 40% = $2,000
            Total = $22,500
        """
        result = calculate_tax_bracket(90000)
        assert result == 22500.0, \
            f"Expected $22,500.00, got ${result}. Check bracket order."

    def test_first_bracket_only(self):
        """$8,000 income → $800 tax (10% only)."""
        assert calculate_tax_bracket(8000) == 800.0

    def test_two_brackets(self):
        """$25,000 income → $1,000 + $3,000 = $4,000."""
        assert calculate_tax_bracket(25000) == 4000.0

    def test_zero_income(self):
        assert calculate_tax_bracket(0) == 0.0


# ------------------------------------------------------------------
# Test 10: graph_shortest_path — state mutation
# ------------------------------------------------------------------
class TestGraphShortestPath:
    def test_shortest_path(self):
        """Should find shortest path A→D in a simple graph."""
        graph = {
            'A': ['B', 'C'],
            'B': ['A', 'D'],
            'C': ['A', 'D'],
            'D': ['B', 'C'],
        }
        path = graph_shortest_path(graph, 'A', 'D')
        assert len(path) == 3, \
            f"Expected path length 3 (e.g. A→B→D), got {path}. Check list copy."
        assert path[0] == 'A'
        assert path[-1] == 'D'

    def test_no_path(self):
        graph = {
            'A': ['B'],
            'B': ['A'],
            'C': ['D'],
            'D': ['C'],
        }
        assert graph_shortest_path(graph, 'A', 'D') == []

    def test_same_node(self):
        graph = {'A': ['B'], 'B': ['A']}
        assert graph_shortest_path(graph, 'A', 'A') == ['A']


# ------------------------------------------------------------------
# BONUS Test 11: calculate_fibonacci — missing base case
# ------------------------------------------------------------------
class TestFibonacciBonus:
    def test_fibonacci_zero(self):
        """F(0) should return 0."""
        assert calculate_fibonacci(0) == 0, \
            "BONUS BUG: F(0) should be 0 — check base cases"

    def test_fibonacci_sequence(self):
        """Verify first several Fibonacci numbers."""
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        for i, val in enumerate(expected):
            assert calculate_fibonacci(i) == val, \
                f"F({i}) should be {val}, got {calculate_fibonacci(i)}"

    def test_fibonacci_negative(self):
        """Negative input should raise ValueError."""
        import pytest
        with pytest.raises(ValueError):
            calculate_fibonacci(-1)
