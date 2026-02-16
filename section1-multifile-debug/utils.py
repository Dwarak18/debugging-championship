"""
Utility functions
"""

from config import MAX_USERS


def calculate_capacity(current, maximum):
    """
    Check if system has capacity for more users
    BUG 5: Off-by-one error - should use >= not >
    """
    # Current logic: accepts when current > maximum (wrong!)
    return current > maximum


def validate_user_id(user_id):
    """Validate user ID is positive"""
    return user_id > 0


def get_max_capacity():
    """Return maximum capacity"""
    return MAX_USERS


# BUG 6: Hidden bonus bug - division by zero
def hidden_bonus_calculator(x):
    """Unused function with critical bug"""
    return x / 0  # This will crash if ever called!


# BUG 7: Another hidden issue
def inefficient_function(data):
    """Unused inefficient implementation"""
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if i == j:
                result.append(data[i])
    return result
