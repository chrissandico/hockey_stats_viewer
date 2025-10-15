"""
Smart Cache Manager for Hockey Stats Application

This module provides intelligent caching with dependency tracking, cache warming,
and automatic invalidation based on data relationships.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    dependencies: Set[str] = field(default_factory=set)
    size_bytes: int = 0
    priority: int = 1  # 1=high, 2=medium, 3=low
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.now() > self.expires_at
    
    def should_refresh(self, staleness_threshold: float = 0.8) -> bool:
        """
        Determine if cache entry should be refreshed based on staleness.
        
        Args:
            staleness_threshold: Refresh when entry is this fraction of its TTL old
        """
        if self.is_expired():
            return True
        
        age = datetime.now() - self.created_at
        ttl = self.expires_at - self.created_at
        staleness = age.total_seconds() / ttl.total_seconds()
        
        return staleness >= staleness_threshold
    
    def update_access(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class SmartCacheManager:
    """
    Intelligent cache manager with dependency tracking and cache warming.
    
    Features:
    - Multi-level cache hierarchy
    - Dependency-based invalidation
    - Cache warming strategies
    - LRU eviction with priority
    - Background refresh
    """
    
    def __init__(self, 
                 max_memory_mb: int = 100,
                 default_ttl: int = 3600,
                 staleness_threshold: float = 0.8):
        """
        Initialize the Smart Cache Manager.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default time-to-live in seconds
            staleness_threshold: Refresh threshold (0.0-1.0)
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.staleness_threshold = staleness_threshold
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.current_memory_usage = 0
        
        # Dependency tracking
        self.dependencies: Dict[str, Set[str]] = {
            'players': set(),
            'games': {'events'},
            'events': {'player_stats', 'team_stats', 'game_summary'},
            'game_roster': {'player_stats'},
            'teams': set(),
            'player_stats': set(),
            'team_stats': set(),
            'game_summary': set()
        }
        
        # Reverse dependency mapping for efficient invalidation
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._build_reverse_dependencies()
        
        # Cache warming configuration
        self.warming_strategies: Dict[str, Callable] = {}
        self.warming_priorities = ['teams', 'players', 'games', 'events']
        
        # Background refresh
        self._refresh_lock = threading.Lock()
        self._refresh_thread = None
        self._stop_refresh = threading.Event()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'invalidations': 0,
            'warming_operations': 0
        }
        
        logger.info(f"SmartCacheManager initialized with {max_memory_mb}MB limit")
    
    def _build_reverse_dependencies(self):
        """Build reverse dependency mapping for efficient invalidation."""
        self.reverse_dependencies.clear()
        for key, deps in self.dependencies.items():
            for dep in deps:
                self.reverse_dependencies[dep].add(key)
    
    def _estimate_size(self, data: Any) -> int:
        """
        Estimate the memory size of data in bytes.
        
        Args:
            data: The data to estimate size for
            
        Returns:
            Estimated size in bytes
        """
        try:
            import sys
            if hasattr(data, '__sizeof__'):
                return sys.getsizeof(data)
            else:
                # Rough estimate for complex objects
                return len(str(data)) * 2
        except Exception:
            return 1024  # Default fallback
    
    def _evict_lru_entries(self, required_space: int):
        """
        Evict least recently used entries to free up space.
        
        Args:
            required_space: Minimum space needed in bytes
        """
        if not self.cache:
            return
        
        # Sort by priority (higher number = lower priority) and last access time
        sorted_entries = sorted(
            self.cache.values(),
            key=lambda x: (x.priority, x.last_accessed)
        )
        
        freed_space = 0
        evicted_keys = []
        
        for entry in sorted_entries:
            if freed_space >= required_space:
                break
            
            freed_space += entry.size_bytes
            evicted_keys.append(entry.key)
        
        # Remove evicted entries
        for key in evicted_keys:
            if key in self.cache:
                self.current_memory_usage -= self.cache[key].size_bytes
                del self.cache[key]
                self.stats['evictions'] += 1
                logger.debug(f"Evicted cache entry: {key}")
    
    def set(self, 
            key: str, 
            data: Any, 
            ttl: Optional[int] = None,
            dependencies: Optional[Set[str]] = None,
            priority: int = 1) -> bool:
        """
        Store data in cache with metadata.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds
            dependencies: Set of dependency keys
            priority: Cache priority (1=high, 2=medium, 3=low)
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            size_bytes = self._estimate_size(data)
            
            # Check if we need to evict entries
            if self.current_memory_usage + size_bytes > self.max_memory_bytes:
                self._evict_lru_entries(size_bytes)
            
            # If still not enough space, reject the cache operation
            if self.current_memory_usage + size_bytes > self.max_memory_bytes:
                logger.warning(f"Cannot cache {key}: insufficient memory")
                return False
            
            # Remove existing entry if present
            if key in self.cache:
                self.current_memory_usage -= self.cache[key].size_bytes
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl),
                dependencies=dependencies or self.dependencies.get(key, set()),
                size_bytes=size_bytes,
                priority=priority
            )
            
            self.cache[key] = entry
            self.current_memory_usage += size_bytes
            
            logger.debug(f"Cached {key} ({size_bytes} bytes, TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error caching {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if entry.is_expired():
            self.invalidate(key)
            self.stats['misses'] += 1
            return None
        
        # Update access statistics
        entry.update_access()
        self.stats['hits'] += 1
        
        return entry.data
    
    def invalidate(self, key: str, cascade: bool = True):
        """
        Invalidate cache entry and optionally cascade to dependents.
        
        Args:
            key: Cache key to invalidate
            cascade: Whether to invalidate dependent caches
        """
        if key in self.cache:
            self.current_memory_usage -= self.cache[key].size_bytes
            del self.cache[key]
            self.stats['invalidations'] += 1
            logger.debug(f"Invalidated cache entry: {key}")
        
        # Cascade invalidation to dependent caches
        if cascade and key in self.reverse_dependencies:
            for dependent_key in self.reverse_dependencies[key]:
                if dependent_key in self.cache:
                    self.invalidate(dependent_key, cascade=False)
                    logger.debug(f"Cascade invalidated: {dependent_key}")
    
    def invalidate_by_dependency(self, dependency: str):
        """
        Invalidate all caches that depend on a specific data type.
        
        Args:
            dependency: The dependency that changed
        """
        logger.info(f"Invalidating caches dependent on: {dependency}")
        
        # Find all cache entries that depend on this data type
        keys_to_invalidate = []
        for key, entry in self.cache.items():
            if dependency in entry.dependencies:
                keys_to_invalidate.append(key)
        
        # Invalidate found entries
        for key in keys_to_invalidate:
            self.invalidate(key, cascade=False)
    
    def register_warming_strategy(self, key: str, strategy: Callable):
        """
        Register a cache warming strategy for a specific key.
        
        Args:
            key: Cache key
            strategy: Function that returns data to cache
        """
        self.warming_strategies[key] = strategy
        logger.debug(f"Registered warming strategy for: {key}")
    
    def warm_cache(self, keys: Optional[List[str]] = None):
        """
        Warm cache with frequently accessed data.
        
        Args:
            keys: Specific keys to warm, or None for all registered strategies
        """
        keys_to_warm = keys or list(self.warming_strategies.keys())
        
        for key in keys_to_warm:
            if key in self.warming_strategies:
                try:
                    strategy = self.warming_strategies[key]
                    data = strategy()
                    if data is not None:
                        self.set(key, data, priority=1)  # High priority for warmed data
                        self.stats['warming_operations'] += 1
                        logger.debug(f"Warmed cache for: {key}")
                except Exception as e:
                    logger.error(f"Error warming cache for {key}: {e}")
    
    def start_background_refresh(self, interval: int = 300):
        """
        Start background thread for cache refresh.
        
        Args:
            interval: Refresh interval in seconds
        """
        if self._refresh_thread and self._refresh_thread.is_alive():
            logger.warning("Background refresh already running")
            return
        
        def refresh_worker():
            logger.info(f"Started background refresh (interval: {interval}s)")
            while not self._stop_refresh.wait(interval):
                try:
                    self._background_refresh()
                except Exception as e:
                    logger.error(f"Error in background refresh: {e}")
        
        self._refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        self._refresh_thread.start()
    
    def stop_background_refresh(self):
        """Stop background refresh thread."""
        if self._refresh_thread:
            self._stop_refresh.set()
            self._refresh_thread.join(timeout=5)
            logger.info("Stopped background refresh")
    
    def _background_refresh(self):
        """Perform background cache refresh for stale entries."""
        with self._refresh_lock:
            stale_entries = []
            
            # Find entries that should be refreshed
            for key, entry in self.cache.items():
                if entry.should_refresh(self.staleness_threshold):
                    stale_entries.append(key)
            
            # Refresh stale entries using warming strategies
            for key in stale_entries:
                if key in self.warming_strategies:
                    try:
                        strategy = self.warming_strategies[key]
                        fresh_data = strategy()
                        if fresh_data is not None:
                            self.set(key, fresh_data, priority=entry.priority)
                            logger.debug(f"Background refreshed: {key}")
                    except Exception as e:
                        logger.error(f"Error refreshing {key}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'entries': len(self.cache),
            'memory_usage_mb': self.current_memory_usage / (1024 * 1024),
            'memory_limit_mb': self.max_memory_bytes / (1024 * 1024),
            'memory_usage_percent': (self.current_memory_usage / self.max_memory_bytes * 100),
            'hit_rate_percent': hit_rate,
            'total_hits': self.stats['hits'],
            'total_misses': self.stats['misses'],
            'total_evictions': self.stats['evictions'],
            'total_invalidations': self.stats['invalidations'],
            'warming_operations': self.stats['warming_operations']
        }
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.current_memory_usage = 0
        logger.info("Cache cleared")
    
    def __del__(self):
        """Cleanup when cache manager is destroyed."""
        self.stop_background_refresh()