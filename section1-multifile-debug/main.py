#!/usr/bin/env python3
"""
Main entry point for User Allocation System
"""

from configurations import MAX_USERS, SYSTEM_NAME  # BUG 1: Wrong module name
from state import get_user_count, reset_state
from utils import calculate_capacity
from module_a import add_user, get_user_list


def main():
    """Main system function"""
    print(f"Starting {SYSTEM_NAME}...")
    reset_state()
    
    # Simulate onboarding
    for i in range(3):
        if calculate_capacity(get_user_count(), MAX_USERS):
            add_user()
            print(f"User {i+1} added. Total: {get_user_count()}")
        else:
            print(f"Capacity reached. Cannot add user {i+1}")
    
    print(f"\nFinal user count: {get_user_count()}")
    print(f"Users: {get_user_list()}")


if __name__ == "__main__":
    main()
