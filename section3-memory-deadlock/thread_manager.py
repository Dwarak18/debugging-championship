"""
Thread Manager Module
Manages thread synchronization and detects deadlocks.

Contains 3 intentional bugs for the debugging championship.
"""

import threading
import time


class ThreadManager:
    """Manages locks and detects potential deadlocks."""
    
    def __init__(self):
        self._locks = {}          # lock_name -> threading.Lock
        self._lock_order = {}     # lock_name -> order (int)
        self._held_locks = {}     # thread_id -> [lock_names]
        self._manager_lock = threading.Lock()
        self._deadlock_detected = False
    
    def create_lock(self, lock_name, order=None):
        """
        Create a named lock with optional ordering.
        
        BUG 5: Lock ordering is not enforced - locks can be acquired
        in any order, leading to potential deadlocks.
        """
        if lock_name in self._locks:
            raise ValueError(f"Lock {lock_name} already exists")
        
        self._locks[lock_name] = threading.Lock()
        
        # BUG: Order is stored but NEVER checked during acquisition
        if order is not None:
            self._lock_order[lock_name] = order
    
    def acquire_lock(self, lock_name, timeout=None):
        """
        Acquire a named lock.
        
        BUG 6: No timeout handling - if timeout is specified,
        it's completely ignored and the thread blocks forever.
        
        BUG 7: Lock ordering not validated - doesn't prevent
        acquiring a lower-order lock while holding a higher-order one.
        """
        if lock_name not in self._locks:
            raise ValueError(f"Lock {lock_name} does not exist")
        
        thread_id = threading.current_thread().ident
        
        # BUG: Should check lock ordering before acquiring
        # If thread holds lock with order N, should not acquire lock with order < N
        # Missing: order validation logic
        
        # BUG: Timeout is completely ignored!
        # Should use: acquired = self._locks[lock_name].acquire(timeout=timeout)
        # Instead, blocks forever:
        self._locks[lock_name].acquire()  # No timeout!
        
        # Track which locks this thread holds
        with self._manager_lock:
            if thread_id not in self._held_locks:
                self._held_locks[thread_id] = []
            self._held_locks[thread_id].append(lock_name)
        
        return True
    
    def release_lock(self, lock_name):
        """Release a named lock."""
        if lock_name not in self._locks:
            raise ValueError(f"Lock {lock_name} does not exist")
        
        thread_id = threading.current_thread().ident
        
        try:
            self._locks[lock_name].release()
        except RuntimeError:
            raise ValueError(f"Lock {lock_name} is not held by current thread")
        
        # Remove from held locks tracking
        with self._manager_lock:
            if thread_id in self._held_locks:
                if lock_name in self._held_locks[thread_id]:
                    self._held_locks[thread_id].remove(lock_name)
    
    def check_lock_order(self, lock_name):
        """
        Check if acquiring this lock would violate ordering.
        Returns True if safe to acquire, False if would violate order.
        """
        thread_id = threading.current_thread().ident
        
        if lock_name not in self._lock_order:
            return True  # No ordering constraint
        
        requested_order = self._lock_order[lock_name]
        
        with self._manager_lock:
            held = self._held_locks.get(thread_id, [])
            for held_lock in held:
                if held_lock in self._lock_order:
                    held_order = self._lock_order[held_lock]
                    if held_order >= requested_order:
                        # Would violate ordering: holding higher/equal order lock
                        return False
        
        return True
    
    def detect_deadlock(self):
        """
        Check if any threads are in a potential deadlock state.
        Returns True if deadlock is detected.
        """
        return self._deadlock_detected
    
    def get_held_locks(self, thread_id=None):
        """Get locks held by a thread (or current thread)."""
        if thread_id is None:
            thread_id = threading.current_thread().ident
        
        with self._manager_lock:
            return list(self._held_locks.get(thread_id, []))
    
    def get_all_locks(self):
        """Return dict of all lock names and their states."""
        return {name: lock.locked() for name, lock in self._locks.items()}
    
    def reset(self):
        """Reset all lock state."""
        # Release any held locks
        for lock_name, lock in self._locks.items():
            try:
                lock.release()
            except RuntimeError:
                pass  # Already released
        
        self._locks.clear()
        self._lock_order.clear()
        self._held_locks.clear()
        self._deadlock_detected = False
