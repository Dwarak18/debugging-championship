# 💡 HINTS - Section 3: Memory & Deadlock Simulation

## Progressive Hint System
Use hints wisely - each hint used reduces bonus points!

---

## 🟢 Level 1 Hints (Minimal Spoilers)

### Hint 1.1 - Memory Allocation
> Look at `memory_tracker.py`'s `allocate()` method. Does it actually store the block in the tracking dictionary?

### Hint 1.2 - Memory Free
> Look at the `free()` method. Does it do... anything? Check what happens to the block after freeing.

### Hint 1.3 - Double Free
> What prevents someone from calling `free()` on the same block twice? Is there any check?

### Hint 1.4 - Deadlock
> In `thread_manager.py`, what happens when you call `acquire_lock()` with a timeout? Does the timeout actually get used?

### Hint 1.5 - Priority
> In `resource_scheduler.py`, check the `Task.__lt__` method. Which direction should the comparison go?

---

## 🟡 Level 2 Hints (Moderate Spoilers)

### Hint 2.1 - Memory Allocation Fix
> The `allocate()` method updates `_total_allocated` but never adds the block to `self._allocations`. Add: `self._allocations[block_id] = size`

### Hint 2.2 - Memory Free Fix
> The `free()` method is empty (`pass`). It needs to:
> 1. Check if block was allocated
> 2. Check for double-free
> 3. Remove from `_allocations`
> 4. Add to `_freed`
> 5. Update `_total_freed`

### Hint 2.3 - Lock Timeout
> `self._locks[lock_name].acquire()` blocks forever. Change to: `acquired = self._locks[lock_name].acquire(timeout=timeout)` and handle the False case.

### Hint 2.4 - Priority Ordering
> `Task.__lt__` returns `self.priority > other.priority` which is BACKWARDS for a min-heap. Change `>` to `<`.

### Hint 2.5 - Starvation Prevention
> When a task is re-queued because its resource is busy, increment its `wait_count`. If `wait_count` exceeds a threshold, temporarily boost its priority.

---

## 🔴 Level 3 Hints (Major Spoilers)

### Hint 3.1 - Complete Memory Allocate Fix
```python
def allocate(self, block_id, size):
    if size <= 0:
        raise ValueError("Allocation size must be positive")
    if block_id in self._allocations:
        raise ValueError(f"Block {block_id} already allocated")
    
    self._allocations[block_id] = size  # ADD THIS LINE
    self._total_allocated += size
    return block_id
```

### Hint 3.2 - Complete Memory Free Fix
```python
def free(self, block_id):
    # Double-free detection
    if block_id in self._freed:
        raise ValueError(f"Double free detected: block {block_id} already freed")
    
    # Check if block was allocated
    if block_id not in self._allocations:
        raise ValueError(f"Invalid free: block {block_id} was never allocated")
    
    # Perform the free
    size = self._allocations.pop(block_id)
    self._freed.add(block_id)
    self._total_freed += size
```

### Hint 3.3 - Complete Lock Timeout Fix
```python
def acquire_lock(self, lock_name, timeout=None):
    if lock_name not in self._locks:
        raise ValueError(f"Lock {lock_name} does not exist")
    
    thread_id = threading.current_thread().ident
    
    # Use timeout if specified
    if timeout is not None:
        acquired = self._locks[lock_name].acquire(timeout=timeout)
        if not acquired:
            return False
    else:
        self._locks[lock_name].acquire()
    
    with self._manager_lock:
        if thread_id not in self._held_locks:
            self._held_locks[thread_id] = []
        self._held_locks[thread_id].append(lock_name)
    
    return True
```

### Hint 3.4 - Complete Priority Fix
```python
class Task:
    def __lt__(self, other):
        # Lower number = higher priority = should come first
        return self.priority < other.priority  # Changed > to <
```

### Hint 3.5 - Starvation Prevention
```python
def execute_next(self):
    with self._lock:
        if not self._task_queue:
            return None
        task = heapq.heappop(self._task_queue)
    
    resource = self._resources.get(task.resource_name)
    if not resource:
        raise ValueError(f"Resource {task.resource_name} not found")
    
    if not resource.is_available():
        task.wait_count += 1
        # Starvation prevention: boost priority after too many waits
        if task.wait_count >= self._starvation_threshold:
            task.priority = 0  # Boost to highest priority
        with self._lock:
            heapq.heappush(self._task_queue, task)
        return None
    
    resource.acquire()
    task.started = True
    task.completed = True
    resource.release()
    
    with self._lock:
        self._completed.append(task)
    return task
```

---

## 🎁 Hidden Bugs Hints

### Hidden Bug 1 - Race Condition in Memory Tracker
> The `MemoryTracker` class has a `_lock` but never uses it! If two threads call `allocate()` simultaneously, both could allocate the same block_id. Wrap critical sections with `self._lock`.

### Hidden Bug 2 - Memory Leak in Thread Cleanup
> When `ThreadManager.reset()` is called, held locks are released but `_held_locks` entries for dead threads are never cleaned up.

### Hidden Bug 3 - Priority Inversion
> If a low-priority task holds a resource and a high-priority task needs it, the high-priority task waits. Meanwhile, medium-priority tasks can execute, further delaying the high-priority task.

---

## 🧠 Debugging Strategy

1. **Fix memory tracking first** - Tests 1-4 are independent
2. **Fix thread manager second** - Tests 5-6 need correct lock handling
3. **Fix scheduler last** - Tests 7-10 need correct priority ordering
4. **Hidden bugs** - Only after all 10 tests pass

---

## 🔍 Quick Verification Commands

```bash
# Test memory allocation
python -c "
from memory_tracker import MemoryTracker
t = MemoryTracker()
t.allocate('b1', 100)
print('Blocks:', t.get_allocated_blocks())
print('Expected: {\"b1\": 100}')
"

# Test memory free
python -c "
from memory_tracker import MemoryTracker
t = MemoryTracker()
t.allocate('b1', 100)
t.free('b1')
print('Blocks:', t.get_allocated_blocks())
print('Freed:', t.get_freed_blocks())
print('Expected: {} and {\"b1\"}')
"

# Test priority ordering
python -c "
from resource_scheduler import Task
t1 = Task('high', 1, 'cpu')
t2 = Task('low', 10, 'cpu')
print('t1 < t2:', t1 < t2)
print('Expected: True (high priority should be \"less than\" low priority for min-heap)')
"
```

---

**Remember: Concurrency bugs are the hardest to find. Think about what happens when two threads run simultaneously! 🧵**
