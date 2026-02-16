"""
Test suite for Section 3: Memory & Deadlock Simulation
All tests should FAIL initially - your job is to fix the bugs!
"""

import pytest
import threading
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================
# Memory Tracker Tests
# =============================================

def test_memory_allocation():
    """Test 1: Memory allocations are properly tracked"""
    from memory_tracker import MemoryTracker
    
    tracker = MemoryTracker()
    tracker.allocate("block_1", 1024)
    tracker.allocate("block_2", 2048)
    
    blocks = tracker.get_allocated_blocks()
    
    assert "block_1" in blocks, "block_1 should be tracked"
    assert "block_2" in blocks, "block_2 should be tracked"
    assert blocks["block_1"] == 1024, "block_1 should be 1024 bytes"
    assert blocks["block_2"] == 2048, "block_2 should be 2048 bytes"


def test_memory_free():
    """Test 2: Memory frees are properly tracked"""
    from memory_tracker import MemoryTracker
    
    tracker = MemoryTracker()
    tracker.allocate("block_1", 1024)
    tracker.allocate("block_2", 2048)
    tracker.free("block_1")
    
    blocks = tracker.get_allocated_blocks()
    freed = tracker.get_freed_blocks()
    
    assert "block_1" not in blocks, "block_1 should be removed after free"
    assert "block_2" in blocks, "block_2 should still be allocated"
    assert "block_1" in freed, "block_1 should be in freed set"
    
    stats = tracker.get_stats()
    assert stats["total_freed"] == 1024, "Total freed should be 1024"


def test_double_free_detection():
    """Test 3: Double free should raise an error"""
    from memory_tracker import MemoryTracker
    
    tracker = MemoryTracker()
    tracker.allocate("block_1", 1024)
    tracker.free("block_1")
    
    # Second free should raise ValueError
    with pytest.raises(ValueError, match="[Dd]ouble|[Aa]lready|[Ff]reed|[Ii]nvalid"):
        tracker.free("block_1")


def test_memory_leak_detection():
    """Test 4: Leak detection finds unfreed allocations"""
    from memory_tracker import MemoryTracker
    
    tracker = MemoryTracker()
    tracker.allocate("block_1", 1024)
    tracker.allocate("block_2", 2048)
    tracker.allocate("block_3", 512)
    tracker.free("block_2")
    
    leaks = tracker.detect_leaks()
    
    assert "block_1" in leaks, "block_1 is a leak (never freed)"
    assert "block_2" not in leaks, "block_2 was freed (not a leak)"
    assert "block_3" in leaks, "block_3 is a leak (never freed)"
    assert leaks["block_1"] == 1024, "Leak should report correct size"
    assert leaks["block_3"] == 512, "Leak should report correct size"


# =============================================
# Thread Manager Tests
# =============================================

def test_deadlock_detection():
    """Test 5: Lock acquisition with timeout prevents deadlocks"""
    from thread_manager import ThreadManager
    
    manager = ThreadManager()
    manager.create_lock("lock_A", order=1)
    manager.create_lock("lock_B", order=2)
    
    # Acquire lock_A
    manager.acquire_lock("lock_A", timeout=1.0)
    
    # Acquire lock_B (higher order - should succeed)
    manager.acquire_lock("lock_B", timeout=1.0)
    
    # Both locks should be held
    held = manager.get_held_locks()
    assert "lock_A" in held, "lock_A should be held"
    assert "lock_B" in held, "lock_B should be held"
    
    # Release locks
    manager.release_lock("lock_B")
    manager.release_lock("lock_A")


def test_lock_ordering():
    """Test 6: Lock ordering prevents acquiring lower-order lock while holding higher"""
    from thread_manager import ThreadManager
    
    manager = ThreadManager()
    manager.create_lock("lock_A", order=1)
    manager.create_lock("lock_B", order=2)
    
    # Acquire lock_B (order=2) first
    manager.acquire_lock("lock_B", timeout=1.0)
    
    # Trying to acquire lock_A (order=1) should be detected as unsafe
    is_safe = manager.check_lock_order("lock_A")
    assert is_safe == False, "Acquiring lower-order lock while holding higher should be unsafe"
    
    # Clean up
    manager.release_lock("lock_B")


def test_lock_timeout():
    """Test 5b: Lock acquisition respects timeout"""
    from thread_manager import ThreadManager
    
    manager = ThreadManager()
    manager.create_lock("lock_X", order=1)
    
    # Acquire the lock in current thread
    manager.acquire_lock("lock_X", timeout=1.0)
    
    # Try to acquire same lock from another thread with timeout
    result = [None]
    
    def try_acquire():
        try:
            acquired = manager.acquire_lock("lock_X", timeout=0.5)
            result[0] = acquired
        except Exception:
            result[0] = False
    
    t = threading.Thread(target=try_acquire)
    t.start()
    t.join(timeout=2.0)
    
    # The thread should have timed out (not hung forever)
    assert not t.is_alive(), "Thread should not be stuck (timeout should work)"
    assert result[0] == False, "Lock acquisition should fail/timeout when lock is held"
    
    # Clean up
    manager.release_lock("lock_X")


# =============================================
# Resource Scheduler Tests
# =============================================

def test_resource_allocation():
    """Test 7: Resources can be allocated and tracked"""
    from resource_scheduler import ResourceScheduler, Task
    
    scheduler = ResourceScheduler()
    scheduler.add_resource("cpu", capacity=2)
    scheduler.add_resource("memory", capacity=4)
    
    status = scheduler.get_resource_status()
    assert status["cpu"]["capacity"] == 2
    assert status["cpu"]["available"] == True
    assert status["memory"]["capacity"] == 4


def test_resource_release():
    """Test 8: Resources are properly released after task completion"""
    from resource_scheduler import ResourceScheduler, Task
    
    scheduler = ResourceScheduler()
    scheduler.add_resource("cpu", capacity=1)
    
    task1 = Task("task_1", priority=1, resource_name="cpu")
    scheduler.submit_task(task1)
    
    result = scheduler.execute_next()
    assert result is not None, "Task should execute"
    assert result.completed == True, "Task should be completed"
    
    # Resource should be released after task
    status = scheduler.get_resource_status()
    assert status["cpu"]["usage"] == 0, "CPU should be released after task completion"


def test_priority_scheduling():
    """Test 9: Tasks execute in correct priority order (lower number = higher priority)"""
    from resource_scheduler import ResourceScheduler, Task
    
    scheduler = ResourceScheduler()
    scheduler.add_resource("cpu", capacity=1)
    
    # Submit tasks in random priority order
    task_low = Task("low_priority", priority=10, resource_name="cpu")
    task_high = Task("high_priority", priority=1, resource_name="cpu")
    task_med = Task("med_priority", priority=5, resource_name="cpu")
    
    scheduler.submit_task(task_low)
    scheduler.submit_task(task_high)
    scheduler.submit_task(task_med)
    
    # Execute all
    results = scheduler.execute_all()
    
    assert len(results) == 3, "All 3 tasks should complete"
    assert results[0].name == "high_priority", "Highest priority (1) should execute first"
    assert results[1].name == "med_priority", "Medium priority (5) should execute second"
    assert results[2].name == "low_priority", "Lowest priority (10) should execute last"


def test_starvation_prevention():
    """Test 10: Low-priority tasks eventually execute (starvation prevention)"""
    from resource_scheduler import ResourceScheduler, Task
    
    scheduler = ResourceScheduler()
    scheduler.add_resource("cpu", capacity=1)
    
    # Submit a low-priority task
    starving_task = Task("starving", priority=100, resource_name="cpu")
    scheduler.submit_task(starving_task)
    
    # Submit several high-priority tasks
    for i in range(3):
        scheduler.submit_task(Task(f"high_{i}", priority=1, resource_name="cpu"))
    
    # Execute all tasks
    results = scheduler.execute_all()
    
    # The starving task should eventually complete
    completed_names = [t.name for t in results]
    assert "starving" in completed_names, "Low-priority task should eventually execute"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
