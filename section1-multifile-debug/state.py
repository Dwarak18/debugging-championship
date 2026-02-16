"""
Shared state manager
BUG 4: Improper state management causing corruption
"""

# BUG: Global variable but imported incorrectly in other modules
user_count = 0


def increment_count():
    """Increment user count"""
    global user_count
    user_count += 1
    return user_count


def get_user_count():
    """Get current user count"""
    return user_count


def reset_state():
    """Reset state to initial"""
    global user_count
    user_count = 0
