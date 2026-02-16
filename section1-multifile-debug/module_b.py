"""
Analytics module
"""

# BUG 10: Circular dependency - module_a imports module_b, module_b imports module_a
from module_a import get_user_list

analytics_log = []


def log_analytics(event_type, user_id):
    """Log analytics event"""
    entry = {
        "event": event_type,
        "user_id": user_id,
        "timestamp": "2026-02-16T14:26:00"
    }
    analytics_log.append(entry)


def get_analytics_summary():
    """Get summary of analytics"""
    # This will crash due to circular import
    total_users = len(get_user_list())
    total_events = len(analytics_log)
    
    return {
        "total_users": total_users,
        "total_events": total_events
    }


def clear_analytics():
    """Clear analytics log"""
    global analytics_log
    analytics_log = []
