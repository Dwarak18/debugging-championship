"""
Test suite for Section 1: Multi-File Debugging Lab
All tests should FAIL initially - your job is to fix the bugs!
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import_config():
    """Test 1: Config module can be imported correctly"""
    try:
        from config import MAX_USERS, SYSTEM_NAME
        assert MAX_USERS is not None
        assert SYSTEM_NAME is not None
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_capacity_limit():
    """Test 2: Capacity check correctly rejects when at limit"""
    from utils import calculate_capacity
    # When current (5) equals maximum (5), should return False (no capacity)
    assert calculate_capacity(5, 5) == False, "Should reject when at capacity limit"


def test_within_capacity():
    """Test 3: Capacity check correctly accepts when below limit"""
    from utils import calculate_capacity
    # When current (4) is less than maximum (5), should return True (has capacity)
    assert calculate_capacity(4, 5) == True, "Should accept when below capacity"


def test_state_increment():
    """Test 4: State increments correctly when adding users"""
    from state import reset_state, get_user_count, increment_count
    
    reset_state()
    assert get_user_count() == 0, "Initial count should be 0"
    
    increment_count()
    assert get_user_count() == 1, "Count should increment to 1"
    
    increment_count()
    assert get_user_count() == 2, "Count should increment to 2"


def test_state_isolation():
    """Test 5: State changes are reflected globally"""
    from state import reset_state, increment_count, get_user_count
    
    reset_state()
    increment_count()
    
    # Import in different context - should still see the change
    from state import get_user_count as get_count_2
    assert get_count_2() == 1, "State should be shared globally"


def test_module_chain():
    """Test 6: Module A can work without circular dependency crash"""
    from state import reset_state
    
    reset_state()
    
    # This will fail if circular dependency exists
    try:
        from module_a import add_user
        # Don't actually call it yet - just test import works
        assert add_user is not None
    except ImportError as e:
        pytest.fail(f"Circular dependency detected: {e}")


def test_config_type():
    """Test 7: Config values are correct types"""
    from config import MAX_USERS
    
    assert isinstance(MAX_USERS, int), f"MAX_USERS should be int, got {type(MAX_USERS)}"
    assert MAX_USERS > 0, "MAX_USERS should be positive"


def test_full_system():
    """Test 8: Full integration test"""
    from state import reset_state, get_user_count
    from config import MAX_USERS
    from utils import calculate_capacity
    
    reset_state()
    
    # Test capacity logic with actual config
    assert calculate_capacity(0, MAX_USERS) == True, "Empty system should have capacity"
    assert calculate_capacity(MAX_USERS - 1, MAX_USERS) == True, "One below max should have capacity"
    assert calculate_capacity(MAX_USERS, MAX_USERS) == False, "At max should have no capacity"
    assert calculate_capacity(MAX_USERS + 1, MAX_USERS) == False, "Over max should have no capacity"


# BONUS TEST - Hidden bugs (not counted in main score)
def test_hidden_bugs():
    """Bonus Test: Check for hidden bugs"""
    from utils import hidden_bonus_calculator
    
    # This should not crash for valid input
    # If it crashes, there's a hidden bug to fix!
    try:
        result = hidden_bonus_calculator(10)
        assert result != float('inf'), "Function should return valid result"
    except ZeroDivisionError:
        pytest.fail("Hidden bug found: Division by zero in hidden_bonus_calculator!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
