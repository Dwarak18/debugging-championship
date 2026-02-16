"""
Memory Tracker Module
Tracks memory allocations and frees for leak detection.

Contains 4 intentional bugs for the debugging championship.
"""

import threading


class MemoryTracker:
    """Tracks memory allocations and detects leaks."""
    
    def __init__(self):
        self._allocations = {}  # block_id -> size
        self._freed = set()     # set of freed block IDs
        self._total_allocated = 0
        self._total_freed = 0
        self._lock = threading.Lock()
    
    def allocate(self, block_id, size):
        """
        Allocate a memory block.
        
        BUG 1: Does NOT actually track the allocation in _allocations dict.
        The allocation is "lost" - never recorded.
        """
        if size <= 0:
            raise ValueError("Allocation size must be positive")
        
        if block_id in self._allocations:
            raise ValueError(f"Block {block_id} already allocated")
        
        # BUG: Missing the actual tracking!
        # Should be: self._allocations[block_id] = size
        # Instead, we only update the total (but forget the block)
        self._total_allocated += size
        
        return block_id
    
    def free(self, block_id):
        """
        Free a memory block.
        
        BUG 2: Does NOT remove from _allocations or add to _freed.
        BUG 3: Does NOT detect double-free (freeing already freed block).
        """
        # BUG: No double-free detection!
        # Missing: if block_id in self._freed: raise ValueError("Double free!")
        
        # BUG: Doesn't check if block was actually allocated
        # Missing: if block_id not in self._allocations: raise ValueError("Invalid free")
        
        # BUG: Doesn't actually track the free operation
        # Should remove from _allocations and add to _freed
        # Missing: size = self._allocations.pop(block_id)
        # Missing: self._freed.add(block_id)
        # Missing: self._total_freed += size
        
        # Currently does nothing useful!
        pass
    
    def get_allocated_blocks(self):
        """Return dict of currently allocated blocks."""
        return dict(self._allocations)
    
    def get_freed_blocks(self):
        """Return set of freed block IDs."""
        return set(self._freed)
    
    def detect_leaks(self):
        """
        Detect memory leaks (allocated but never freed).
        
        BUG 4: Returns wrong result - always returns empty dict
        because allocations are never properly tracked.
        """
        # This WOULD work if allocations were tracked correctly
        leaks = {}
        for block_id, size in self._allocations.items():
            if block_id not in self._freed:
                leaks[block_id] = size
        return leaks
    
    def get_stats(self):
        """Return memory statistics."""
        return {
            "total_allocated": self._total_allocated,
            "total_freed": self._total_freed,
            "current_blocks": len(self._allocations),
            "freed_blocks": len(self._freed),
            "leaked_bytes": self._total_allocated - self._total_freed
        }
    
    def reset(self):
        """Reset all tracking state."""
        self._allocations.clear()
        self._freed.clear()
        self._total_allocated = 0
        self._total_freed = 0
