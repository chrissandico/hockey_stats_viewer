"""
Multi-Level Cache Architecture for Hockey Stats Application

This module implements a hierarchical cache system with L1 (memory), L2 (session), 
and L3 (persistent) cache layers with automatic promotion/demotion and LRU eviction.
"""

import time
import pickle
import os
import tempfile
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import logging
from collections import OrderedDict

from .smart_cache_manager import CacheEntry, SmartCacheManager

logger = logging.getLogger(__name__)


@dataclass
class CacheLevel:
    """Configuration for a cache level."""
    name: str
    max_size_mb: int
    default_ttl: int
    promotion_threshold: int  # Access count to promote to higher level
    demotion_age: int  # Age in seconds to demote to lower level


class LRUCache:
    """
    LRU (Least Recently Used) cache implementation with size limits.
    """
    
    def __init__(self, max_size_mb: int):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size = 0
        self.cache = OrderedDict()
        self.lock = threading.RLock()
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate memory size of data."""
        try:
            import sys
            return sys.getsizeof(data)
        except Exception:
            return len(str(data)) * 2
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get item from cache and move to end (most recently used)."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                entry.update_access()
                return entry
            return None
    
    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set item in cache with LRU eviction."""
        with self.lock:
            entry_size = self._estimate_size(entry.data)
            
            # Remove existing entry if present
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_size -= self._estimate_size(old_entry.data)
                del self.cache[key]
            
            # Evict LRU items if necessary
            while (self.current_size + entry_size > self.max_size_bytes and 
                   len(self.cache) > 0):
                lru_key, lru_entry = self.cache.popitem(last=False)
                self.current_size -= self._estimate_size(lru_entry.data)
                logger.debug(f"LRU evicted: {lru_key}")
            
            # Check if we can fit the new entry
            if entry_size > self.max_size_bytes:
                logger.warning(f"Entry {key} too large for cache level")
                return False
            
            # Add new entry
            entry.size_bytes = entry_size
            self.cache[key] = entry
            self.current_size += entry_size
            return True
    
    def remove(self, key: str) -> bool:
        """Remove item from cache."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.current_size -= self._estimate_size(entry.data)
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()
            self.current_size = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                'entries': len(self.cache),
                'size_bytes': self.current_size,
                'size_mb': self.current_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'usage_percent': (self.current_size / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0
            }


class PersistentCache:
    """
    Persistent cache using file system storage.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 50):
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), 'hockey_stats_cache')
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.lock = threading.RLock()
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Persistent cache directory: {self.cache_dir}")
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key."""
        # Sanitize key for filename
        safe_key = "".join(c for c in key if c.isalnum() or c in ('-', '_', '.'))
        return os.path.join(self.cache_dir, f"{safe_key}.cache")
    
    def _cleanup_old_files(self):
        """Remove old cache files to stay within size limit."""
        try:
            files = []
            total_size = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    filepath = os.path.join(self.cache_dir, filename)
                    stat = os.stat(filepath)
                    files.append((filepath, stat.st_mtime, stat.st_size))
                    total_size += stat.st_size
            
            # Sort by modification time (oldest first)
            files.sort(key=lambda x: x[1])
            
            # Remove oldest files until under size limit
            while total_size > self.max_size_bytes and files:
                filepath, _, size = files.pop(0)
                try:
                    os.remove(filepath)
                    total_size -= size
                    logger.debug(f"Removed old cache file: {filepath}")
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"Error cleaning up cache files: {e}")
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get item from persistent cache."""
        with self.lock:
            filepath = self._get_file_path(key)
            
            try:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        entry = pickle.load(f)
                    
                    # Check if expired
                    if entry.is_expired():
                        os.remove(filepath)
                        return None
                    
                    # Update access time on file
                    os.utime(filepath, None)
                    entry.update_access()
                    return entry
                    
            except Exception as e:
                logger.error(f"Error reading persistent cache {key}: {e}")
                # Remove corrupted file
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            
            return None
    
    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set item in persistent cache."""
        with self.lock:
            try:
                # Cleanup old files first
                self._cleanup_old_files()
                
                filepath = self._get_file_path(key)
                with open(filepath, 'wb') as f:
                    pickle.dump(entry, f)
                
                logger.debug(f"Persisted cache entry: {key}")
                return True
                
            except Exception as e:
                logger.error(f"Error writing persistent cache {key}: {e}")
                return False
    
    def remove(self, key: str) -> bool:
        """Remove item from persistent cache."""
        with self.lock:
            filepath = self._get_file_path(key)
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    return True
            except OSError as e:
                logger.error(f"Error removing persistent cache {key}: {e}")
            return False
    
    def clear(self):
        """Clear all persistent cache files."""
        with self.lock:
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.cache'):
                        filepath = os.path.join(self.cache_dir, filename)
                        os.remove(filepath)
                logger.info("Cleared persistent cache")
            except Exception as e:
                logger.error(f"Error clearing persistent cache: {e}")


class MultiLevelCache:
    """
    Multi-level cache architecture with automatic promotion/demotion.
    
    L1 (Memory): Fast access, small size, short TTL
    L2 (Session): Medium access, medium size, medium TTL  
    L3 (Persistent): Slow access, large size, long TTL
    """
    
    def __init__(self, 
                 l1_size_mb: int = 20,
                 l2_size_mb: int = 50, 
                 l3_size_mb: int = 100,
                 cache_dir: Optional[str] = None):
        """
        Initialize multi-level cache.
        
        Args:
            l1_size_mb: L1 cache size in MB
            l2_size_mb: L2 cache size in MB
            l3_size_mb: L3 cache size in MB
            cache_dir: Directory for persistent cache
        """
        
        # Cache level configurations
        self.levels = {
            'L1': CacheLevel('L1', l1_size_mb, 300, 5, 600),      # 5min TTL, promote after 5 accesses
            'L2': CacheLevel('L2', l2_size_mb, 900, 10, 1800),    # 15min TTL, promote after 10 accesses  
            'L3': CacheLevel('L3', l3_size_mb, 3600, 0, 7200)     # 1hr TTL, no promotion from L3
        }
        
        # Initialize cache layers
        self.l1_cache = LRUCache(l1_size_mb)
        self.l2_cache = LRUCache(l2_size_mb)
        self.l3_cache = PersistentCache(cache_dir, l3_size_mb)
        
        # Statistics
        self.stats = {
            'l1_hits': 0, 'l1_misses': 0,
            'l2_hits': 0, 'l2_misses': 0,
            'l3_hits': 0, 'l3_misses': 0,
            'promotions': 0, 'demotions': 0
        }
        
        logger.info(f"MultiLevelCache initialized: L1={l1_size_mb}MB, L2={l2_size_mb}MB, L3={l3_size_mb}MB")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache, checking L1 -> L2 -> L3.
        Promotes frequently accessed items to higher levels.
        """
        
        # Try L1 first
        entry = self.l1_cache.get(key)
        if entry and not entry.is_expired():
            self.stats['l1_hits'] += 1
            return entry.data
        self.stats['l1_misses'] += 1
        
        # Try L2
        entry = self.l2_cache.get(key)
        if entry and not entry.is_expired():
            self.stats['l2_hits'] += 1
            
            # Consider promotion to L1
            if entry.access_count >= self.levels['L1'].promotion_threshold:
                self._promote_to_l1(key, entry)
            
            return entry.data
        self.stats['l2_misses'] += 1
        
        # Try L3
        entry = self.l3_cache.get(key)
        if entry and not entry.is_expired():
            self.stats['l3_hits'] += 1
            
            # Consider promotion to L2
            if entry.access_count >= self.levels['L2'].promotion_threshold:
                self._promote_to_l2(key, entry)
            
            return entry.data
        self.stats['l3_misses'] += 1
        
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None, priority: int = 1) -> bool:
        """
        Set item in appropriate cache level based on priority and size.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds
            priority: 1=L1, 2=L2, 3=L3
        """
        
        # Determine target level based on priority
        if priority == 1:
            target_level = 'L1'
            cache = self.l1_cache
        elif priority == 2:
            target_level = 'L2'
            cache = self.l2_cache
        else:
            target_level = 'L3'
            cache = self.l3_cache
        
        # Use level-specific TTL if not provided
        if ttl is None:
            ttl = self.levels[target_level].default_ttl
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            data=data,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl),
            priority=priority
        )
        
        # Try to store in target level
        success = cache.set(key, entry)
        
        if not success and target_level != 'L3':
            # Fallback to L3 if higher levels are full
            success = self.l3_cache.set(key, entry)
            if success:
                logger.debug(f"Stored {key} in L3 (fallback)")
        
        return success
    
    def _promote_to_l1(self, key: str, entry: CacheEntry):
        """Promote entry from L2 to L1."""
        if self.l1_cache.set(key, entry):
            self.l2_cache.remove(key)
            self.stats['promotions'] += 1
            logger.debug(f"Promoted {key} to L1")
    
    def _promote_to_l2(self, key: str, entry: CacheEntry):
        """Promote entry from L3 to L2."""
        if self.l2_cache.set(key, entry):
            self.l3_cache.remove(key)
            self.stats['promotions'] += 1
            logger.debug(f"Promoted {key} to L2")
    
    def invalidate(self, key: str):
        """Remove item from all cache levels."""
        removed = False
        
        if self.l1_cache.remove(key):
            removed = True
        if self.l2_cache.remove(key):
            removed = True
        if self.l3_cache.remove(key):
            removed = True
        
        if removed:
            logger.debug(f"Invalidated {key} from all levels")
    
    def clear(self):
        """Clear all cache levels."""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.l3_cache.clear()
        logger.info("Cleared all cache levels")
    
    def demote_stale_entries(self):
        """
        Demote stale entries to lower cache levels.
        Called periodically to optimize cache hierarchy.
        """
        current_time = datetime.now()
        
        # Check L1 for stale entries to demote to L2
        stale_l1_keys = []
        for key, entry in self.l1_cache.cache.items():
            age = (current_time - entry.last_accessed).total_seconds()
            if age > self.levels['L1'].demotion_age:
                stale_l1_keys.append((key, entry))
        
        for key, entry in stale_l1_keys:
            if self.l2_cache.set(key, entry):
                self.l1_cache.remove(key)
                self.stats['demotions'] += 1
                logger.debug(f"Demoted {key} from L1 to L2")
        
        # Check L2 for stale entries to demote to L3
        stale_l2_keys = []
        for key, entry in self.l2_cache.cache.items():
            age = (current_time - entry.last_accessed).total_seconds()
            if age > self.levels['L2'].demotion_age:
                stale_l2_keys.append((key, entry))
        
        for key, entry in stale_l2_keys:
            if self.l3_cache.set(key, entry):
                self.l2_cache.remove(key)
                self.stats['demotions'] += 1
                logger.debug(f"Demoted {key} from L2 to L3")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all cache levels."""
        l1_stats = self.l1_cache.get_stats()
        l2_stats = self.l2_cache.get_stats()
        
        total_requests = sum([
            self.stats['l1_hits'], self.stats['l1_misses'],
            self.stats['l2_hits'], self.stats['l2_misses'],
            self.stats['l3_hits'], self.stats['l3_misses']
        ])
        
        total_hits = self.stats['l1_hits'] + self.stats['l2_hits'] + self.stats['l3_hits']
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'overall': {
                'total_requests': total_requests,
                'total_hits': total_hits,
                'hit_rate_percent': overall_hit_rate,
                'promotions': self.stats['promotions'],
                'demotions': self.stats['demotions']
            },
            'l1': {
                **l1_stats,
                'hits': self.stats['l1_hits'],
                'misses': self.stats['l1_misses'],
                'hit_rate_percent': (self.stats['l1_hits'] / (self.stats['l1_hits'] + self.stats['l1_misses']) * 100) 
                                   if (self.stats['l1_hits'] + self.stats['l1_misses']) > 0 else 0
            },
            'l2': {
                **l2_stats,
                'hits': self.stats['l2_hits'],
                'misses': self.stats['l2_misses'],
                'hit_rate_percent': (self.stats['l2_hits'] / (self.stats['l2_hits'] + self.stats['l2_misses']) * 100)
                                   if (self.stats['l2_hits'] + self.stats['l2_misses']) > 0 else 0
            },
            'l3': {
                'hits': self.stats['l3_hits'],
                'misses': self.stats['l3_misses'],
                'hit_rate_percent': (self.stats['l3_hits'] / (self.stats['l3_hits'] + self.stats['l3_misses']) * 100)
                                   if (self.stats['l3_hits'] + self.stats['l3_misses']) > 0 else 0
            }
        }