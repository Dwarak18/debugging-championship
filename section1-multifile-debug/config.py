"""
System configuration
"""

# BUG 2: String instead of int (causes type comparison issues)
MAX_USERS = "5"

SYSTEM_NAME = "User Allocation System v2.0"

# System limits
MIN_USERS = 0
DEFAULT_CAPACITY = 100

# BUG 3: Unused config that might cause issues
DEBUG_MODE = True
