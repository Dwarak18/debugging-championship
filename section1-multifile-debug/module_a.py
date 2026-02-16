"""
User management module
"""

# BUG 8: This creates circular dependency with module_b
from module_b import log_analytics

# BUG 9: Wrong import - should use state.increment_count()
from state import user_count  # Wrong! Should import function, not variable


users = []


def add_user():
    """Add a new user"""
    global user_count
    # BUG: Modifying local copy, not the actual state
    user_count += 1  # This doesn't work!
    
    user_id = len(users) + 1
    users.append(f"User_{user_id}")
    
    # This causes circular import issue
    log_analytics("user_added", user_id)
    
    return user_id


def get_user_list():
    """Get list of all users"""
    return users


def remove_user(user_id):
    """Remove a user"""
    if user_id <= len(users):
        users.pop(user_id - 1)
