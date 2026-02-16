"""
Payment Gateway Module
PRODUCTION CODE - Handle with care!
"""

import json
import os
from datetime import datetime


def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)


def validate_payment(payment):
    """
    Validate payment object
    BUG 1: No null check - crashes if payment is None
    """
    # Missing: if payment is None: raise ValueError("Payment cannot be None")
    
    # BUG 2: No validation for negative amounts
    amount = payment['amount']
    # Missing: if amount <= 0: raise ValueError("Amount must be positive")
    
    # BUG 3: No transaction_id validation
    transaction_id = payment.get('transaction_id')
    # Missing: if not transaction_id: raise ValueError("Transaction ID required")
    
    return True


def process_payment(payment):
    """
    Process a payment transaction
    BUG 4: Doesn't handle None gracefully
    """
    config = load_config()
    
    # BUG 5: Config values are strings but used as ints
    timeout = config['API_TIMEOUT']  # This is "30" (string) not 30 (int)
    max_retry = config['MAX_RETRY']  # This is "3" (string) not 3 (int)
    
    # This will crash if payment is None
    if not validate_payment(payment):
        return {"status": "failed", "reason": "Invalid payment"}
    
    # Simulate API call
    try:
        # BUG 6: Type error - can't compare string timeout with int
        if timeout > 10:  # Crashes: '30' > 10 (str vs int)
            print(f"Using extended timeout: {timeout}")
        
        # Process transaction
        result = execute_transaction(payment, max_retry)
        return result
        
    except Exception as e:
        # BUG 7: Swallows useful error information
        return {"status": "error", "reason": "Processing failed"}


def execute_transaction(payment, max_retry):
    """
    Execute the actual transaction
    BUG 8: No rollback on failure
    """
    amount = payment['amount']
    transaction_id = payment['transaction_id']
    
    # Simulate transaction
    print(f"Processing transaction {transaction_id} for ${amount}")
    
    # BUG 9: No proper error handling for transaction failure
    if amount < 0:
        # Should rollback, but doesn't
        return {"status": "failed", "reason": "Negative amount"}
    
    return {
        "status": "success",
        "transaction_id": transaction_id,
        "amount": amount,
        "timestamp": datetime.now().isoformat()
    }


def get_transaction_status(transaction_id):
    """Get status of a transaction"""
    # BUG 10: Hidden bonus - no validation of transaction_id
    if not transaction_id:
        return None
    
    # Simulate database lookup
    return {
        "transaction_id": transaction_id,
        "status": "pending"
    }


# BONUS BUG: Memory leak simulation
_error_cache = []

def log_error(error_message):
    """Log error message"""
    # BUG: Never clears the cache - memory leak!
    _error_cache.append({
        "message": error_message,
        "timestamp": datetime.now().isoformat()
    })
    print(f"ERROR: {error_message}")


if __name__ == "__main__":
    # Test case that should work
    payment = {
        "amount": 100.00,
        "transaction_id": "TXN_001",
        "currency": "USD"
    }
    
    result = process_payment(payment)
    print(f"Result: {result}")
