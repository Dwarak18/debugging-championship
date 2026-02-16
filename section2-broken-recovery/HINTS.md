# 💡 HINTS - Section 2: Broken Project Recovery

## Progressive Hint System
Use hints wisely - each hint used reduces bonus points!

---

## 🟢 Level 1 Hints (Minimal Spoilers)

### Hint 1.1 - Null Safety
> What happens when you try to access a key on `None`? Check the first function that touches the payment object.

### Hint 1.2 - Config Types
> JSON stores numbers as strings when they're quoted. Look at `config.json` carefully.

### Hint 1.3 - Input Validation
> What should happen if someone passes a negative dollar amount? Should the system accept it?

### Hint 1.4 - Error Messages
> "Processing failed" tells the developer nothing useful. What information would help debug?

---

## 🟡 Level 2 Hints (Moderate Spoilers)

### Hint 2.1 - Null Check Location
> Add a check at the start of `validate_payment()`: if the payment is None, raise a ValueError.

### Hint 2.2 - Config Fix Location
> In `config.json`, change `"30"` to `30` and `"3"` to `3` (remove quotes for numeric values).

### Hint 2.3 - Amount Validation
> After checking for None, validate that `payment['amount']` is greater than 0.

### Hint 2.4 - Error Handling
> In the except block of `process_payment()`, include the actual exception message: `str(e)`.

### Hint 2.5 - Rollback Information
> When a transaction fails in `execute_transaction()`, add `"rolled_back": True` to the result.

---

## 🔴 Level 3 Hints (Major Spoilers)

### Hint 3.1 - Complete Null Check Fix
```python
# payment_gateway.py - validate_payment function
def validate_payment(payment):
    if payment is None:
        raise ValueError("Payment cannot be None")
    
    amount = payment['amount']
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    transaction_id = payment.get('transaction_id')
    if not transaction_id:
        raise ValueError("Transaction ID required")
    
    return True
```

### Hint 3.2 - Complete Config Fix
```json
{
    "API_KEY": "sk_live_abcd1234567890",
    "API_TIMEOUT": 30,
    "MAX_RETRY": 3,
    "ENABLE_LOGGING": true,
    "DATABASE_URL": "postgresql://localhost:5432/payments",
    "RATE_LIMIT": 1000,
    "CURRENCY": "USD",
    "MIN_AMOUNT": 0.01,
    "MAX_AMOUNT": 999999.99
}
```

### Hint 3.3 - Complete Error Handling Fix
```python
# payment_gateway.py - process_payment function
def process_payment(payment):
    config = load_config()
    
    timeout = config['API_TIMEOUT']
    max_retry = config['MAX_RETRY']
    
    try:
        if not validate_payment(payment):
            return {"status": "failed", "reason": "Invalid payment"}
    except ValueError as e:
        return {"status": "error", "reason": str(e)}
    
    try:
        if timeout > 10:
            print(f"Using extended timeout: {timeout}")
        
        result = execute_transaction(payment, max_retry)
        return result
        
    except Exception as e:
        return {"status": "error", "reason": f"Processing failed: {str(e)}"}
```

### Hint 3.4 - Complete Rollback Fix
```python
# payment_gateway.py - execute_transaction function
def execute_transaction(payment, max_retry):
    amount = payment['amount']
    transaction_id = payment['transaction_id']
    
    if amount < 0:
        return {
            "status": "failed",
            "reason": "Negative amount - transaction rolled back",
            "rolled_back": True,
            "transaction_id": transaction_id
        }
    
    return {
        "status": "success",
        "transaction_id": transaction_id,
        "amount": amount,
        "timestamp": datetime.now().isoformat()
    }
```

---

## 🎁 Hidden Bugs Hints

### Hidden Bug 1 - Memory Leak
> Check `_error_cache` in `payment_gateway.py`. It grows forever and never gets cleared.
> Fix: Add a max size or implement `clear_error_cache()`.

### Hidden Bug 2 - Race Condition
> If two threads call `process_payment` simultaneously, the shared `_error_cache` is not thread-safe.

### Hidden Bug 3 - Timezone
> `datetime.now()` uses local time, not UTC. Use `datetime.utcnow()` or `datetime.now(timezone.utc)` for consistency.

---

## 🧠 Forensic Analysis Strategy

1. **Read `logs/error.log`** - Understand the timeline of the crash
2. **Read `stack_trace.txt`** - Find the exact lines that crashed
3. **Check `config.json`** - Identify type mismatches
4. **Fix `payment_gateway.py`** - Apply fixes based on evidence
5. **Run tests incrementally** - Verify each fix

---

## 🔍 Quick Verification Commands

```bash
# Test null handling
python -c "from payment_gateway import validate_payment; validate_payment(None)"

# Test config types
python -c "from payment_gateway import load_config; c=load_config(); print(type(c['API_TIMEOUT']))"

# Test negative amount
python -c "from payment_gateway import validate_payment; validate_payment({'amount': -100, 'transaction_id': 'x'})"

# Run all tests
pytest tests/test_recovery.py -v
```

---

**Remember: The logs and stack trace are your best friends in forensic debugging! 🔍**
