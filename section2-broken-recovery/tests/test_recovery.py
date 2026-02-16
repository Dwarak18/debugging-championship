"""
Test suite for Section 2: Broken Project Recovery
All tests should FAIL initially - your job is to fix the bugs!
"""

import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_null_payment_object():
    """Test 1: System handles None payment gracefully"""
    from payment_gateway import validate_payment
    
    # Should raise ValueError, not crash with TypeError
    with pytest.raises(ValueError, match="[Pp]ayment.*[Nn]one|[Cc]annot be None|[Nn]ull"):
        validate_payment(None)


def test_log_parsing():
    """Test 2: Error log contains expected critical entries"""
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'error.log')
    
    with open(log_path, 'r') as f:
        log_content = f.read()
    
    # Log should contain critical error about None
    assert "NoneType" in log_content, "Log should record NoneType error"
    assert "CRITICAL" in log_content, "Log should have CRITICAL level entries"
    assert "API_TIMEOUT" in log_content, "Log should mention config issue"


def test_stack_trace_line():
    """Test 3: Stack trace points to correct error line"""
    trace_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'stack_trace.txt')
    
    with open(trace_path, 'r') as f:
        trace_content = f.read()
    
    # Stack trace should point to validate_payment
    assert "validate_payment" in trace_content, "Stack trace should mention validate_payment"
    assert "NoneType" in trace_content, "Stack trace should mention NoneType error"


def test_invalid_config():
    """Test 4: Config values are correct types"""
    from payment_gateway import load_config
    
    config = load_config()
    
    # API_TIMEOUT should be int, not string
    assert isinstance(config['API_TIMEOUT'], int), \
        f"API_TIMEOUT should be int, got {type(config['API_TIMEOUT'])}"
    
    # MAX_RETRY should be int, not string
    assert isinstance(config['MAX_RETRY'], int), \
        f"MAX_RETRY should be int, got {type(config['MAX_RETRY'])}"


def test_amount_validation():
    """Test 5: Negative amounts are rejected"""
    from payment_gateway import validate_payment
    
    negative_payment = {
        "amount": -100.00,
        "transaction_id": "TXN_NEG_001",
        "currency": "USD"
    }
    
    # Should raise ValueError for negative amount
    with pytest.raises(ValueError, match="[Aa]mount|[Nn]egative|[Pp]ositive"):
        validate_payment(negative_payment)


def test_transaction_rollback():
    """Test 6: Failed transactions return proper status"""
    from payment_gateway import execute_transaction
    
    bad_payment = {
        "amount": -500,
        "transaction_id": "TXN_ROLLBACK_001",
        "currency": "USD"
    }
    
    result = execute_transaction(bad_payment, 3)
    
    # Should indicate failure with rollback info
    assert result['status'] == "failed", "Failed transaction should have failed status"
    assert 'rollback' in result.get('reason', '').lower() or \
           'rolled_back' in result or \
           result.get('rolled_back', False) == True, \
        "Failed transaction should include rollback information"


def test_error_handling():
    """Test 7: Process payment returns useful error info"""
    from payment_gateway import process_payment
    
    # Process with None should return useful error, not crash
    result = process_payment(None)
    
    assert result['status'] in ['error', 'failed'], "Should return error status"
    assert result['reason'] != "Processing failed", \
        "Error reason should be specific, not generic 'Processing failed'"
    assert len(result['reason']) > 10, "Error reason should be descriptive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
