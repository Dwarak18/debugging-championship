"""
System configuration
"""

# BUG 2: None instead of int (causes config validation to break entirely)
MAX_USERS = None  # BUG: Should be an integer like 5, not None

SYSTEM_NAME = "User Allocation System v2.0"

# System limits
MIN_USERS = 0
DEFAULT_CAPACITY = 100

# BUG 3: Unused config that might cause issues
DEBUG_MODE = True
