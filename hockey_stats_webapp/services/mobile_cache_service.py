"""
Mobile-Specific Caching Service

This service provides connection-aware caching strategies, offline-first caching,
and cache preloading based on user behavior patterns for mobile clients.
"""

import json
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque

try:
    from .smart_cache_manager import SmartCacheManager
    from .multi_level_cache import MultiLevelCache
except ImportError:
    # Fallback for direct execution
    from smart_cache_manager import SmartCacheManager
    from multi_level_cache import MultiLevelCache

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Network connection types for mobile optimization."""
    WIFI = "wifi"
    CELLULAR_4G = "4g"
    CELLULAR_3G = "3g"
    CELLULAR_2G = "2g"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class DataPriority(Enum):
    """Data priority levels for mobile caching."""
    CRITICAL = 1    # Essential for app functionality
    HIGH = 2        # Important for user experience
    MEDIUM = 3      # Nice to have
    LOW = 4         # Background/prefetch data


@dataclass
class ConnectionProfile:
    """Network connection profile for mobile optimization."""
    connection_type: ConnectionType
    bandwidth_kbps: int
    latency_ms: int
    is_metered: bool
    data_saver_mode: bool = False
    
    @property
    def is_fast_connection(self) -> bool:
        """Check if connection is fast enough for full functionality."""
        return self.connection_type in [ConnectionType.WIFI, ConnectionType.CELLULAR_4G]
    
    @property
    def is_slow_connection(self) -> bool:
        """Check if connection requires optimization."""
        return self.connection_type in [ConnectionType.CELLULAR_2G, ConnectionType.CELLULAR_3G]


@dataclass
class UserBehaviorPattern:
    """User behavior pattern for predictive caching."""
    user_id: str
    team_id: str
    frequent_pages: List[str] = field(default_factory=list)
    access_times: List[datetime] = field(default_factory=list)
    session_duration_avg: float = 0.0
    preferred_data_types: Set[str] = field(default_factory=set)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class OfflineCacheEntry:
    """Offline cache entry with mobile-specific metadata."""
    key: str
    data: Any
    priority: DataPriority
    size_bytes: int
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
    access_count: int = 0
    is_critical: bool = False
    sync_required: bool = False


class MobileCacheService:
    """
    Mobile-specific caching service with connection-aware strategies,
    offline-first caching, and predictive preloading.
    """
    
    def __init__(self,
                 cache_manager: SmartCacheManager,
                 multi_level_cache: MultiLevelCache,
                 max_offline_cache_mb: int = 50,
                 behavior_tracking_days: int = 7):
        """
        Initialize mobile cache service.
        
        Args:
            cache_manager: Smart cache manager instance
            multi_level_cache: Multi-level cache instance
            max_offline_cache_mb: Maximum offline cache size in MB
            behavior_tracking_days: Days to track user behavior
        """
        self.cache_manager = cache_manager
        self.multi_level_cache = multi_level_cache
        self.max_offline_cache_bytes = max_offline_cache_mb * 1024 * 1024
        self.behavior_tracking_days = behavior_tracking_days
        
        # Connection awareness
        self.current_connection = ConnectionProfile(
            ConnectionType.UNKNOWN, 0, 0, False
        )
        self.connection_history: deque = deque(maxlen=100)
        
        # Offline-first cache
        self.offline_cache: Dict[str, OfflineCacheEntry] = {}
        self.offline_cache_size = 0
        self.critical_data_keys = {
            'teams', 'players', 'current_season_games',
            'player_stats_summary', 'team_standings'
        }
        
        # User behavior tracking
        self.user_behaviors: Dict[str, UserBehaviorPattern] = {}
        self.page_access_log: deque = deque(maxlen=1000)
        
        # Preloading strategies
        self.preload_strategies: Dict[str, Callable] = {}
        self.preload_queue: deque = deque()
        self.preload_lock = threading.Lock()
        
        # Mobile-specific cache policies
        self.connection_policies = {
            ConnectionType.WIFI: {
                'cache_aggressively': True,
                'preload_enabled': True,
                'max_request_size_mb': 10,
                'background_sync': True
            },
            ConnectionType.CELLULAR_4G: {
                'cache_aggressively': True,
                'preload_enabled': True,
                'max_request_size_mb': 5,
                'background_sync': True
            },
            ConnectionType.CELLULAR_3G: {
                'cache_aggressively': True,
                'preload_enabled': False,
                'max_request_size_mb': 2,
                'background_sync': False
            },
            ConnectionType.CELLULAR_2G: {
                'cache_aggressively': True,
                'preload_enabled': False,
                'max_request_size_mb': 1,
                'background_sync': False
            },
            ConnectionType.OFFLINE: {
                'cache_aggressively': False,
                'preload_enabled': False,
                'max_request_size_mb': 0,
                'background_sync': False
            }
        }
        
        # Statistics
        self.stats = {
            'offline_cache_hits': 0,
            'offline_cache_misses': 0,
            'preload_operations': 0,
            'connection_adaptations': 0,
            'data_saved_mb': 0.0
        }
        
        logger.info("MobileCacheService initialized")
    
    def update_connection_profile(self, 
                                connection_type: ConnectionType,
                                bandwidth_kbps: int = 0,
                                latency_ms: int = 0,
                                is_metered: bool = False,
                                data_saver_mode: bool = False):
        """
        Update current connection profile and adapt caching strategy.
        
        Args:
            connection_type: Type of network connection
            bandwidth_kbps: Available bandwidth in kbps
            latency_ms: Network latency in milliseconds
            is_metered: Whether connection is metered
            data_saver_mode: Whether user has data saver enabled
        """
        old_connection = self.current_connection.connection_type
        
        self.current_connection = ConnectionProfile(
            connection_type=connection_type,
            bandwidth_kbps=bandwidth_kbps,
            latency_ms=latency_ms,
            is_metered=is_metered,
            data_saver_mode=data_saver_mode
        )
        
        # Log connection change
        self.connection_history.append({
            'timestamp': datetime.now(),
            'connection_type': connection_type,
            'bandwidth_kbps': bandwidth_kbps,
            'latency_ms': latency_ms
        })
        
        if old_connection != connection_type:
            self.stats['connection_adaptations'] += 1
            self._adapt_to_connection_change()
            logger.info(f"Connection changed: {old_connection} -> {connection_type}")
    
    def _adapt_to_connection_change(self):
        """Adapt caching strategy based on connection change."""
        policy = self.connection_policies[self.current_connection.connection_type]
        
        # Adjust cache behavior based on connection
        if self.current_connection.connection_type == ConnectionType.OFFLINE:
            # Switch to offline-only mode
            self._enable_offline_mode()
        elif self.current_connection.is_slow_connection:
            # Optimize for slow connection
            self._optimize_for_slow_connection()
        elif self.current_connection.is_fast_connection:
            # Enable full functionality
            self._enable_full_functionality()
        
        # Update cache TTL based on connection quality
        self._adjust_cache_ttl_for_connection()
        
        # Update preloading based on connection
        if policy['preload_enabled'] and not self.current_connection.data_saver_mode:
            self._start_intelligent_preloading()
        else:
            self._stop_preloading()
        
        # Adjust cache size limits based on connection
        self._adjust_cache_limits_for_connection()
    
    def _enable_offline_mode(self):
        """Enable offline-only mode using cached data."""
        logger.info("Enabling offline mode")
        # Prioritize critical data in offline cache
        self._ensure_critical_data_cached()
    
    def _optimize_for_slow_connection(self):
        """Optimize caching for slow connections."""
        logger.info("Optimizing for slow connection")
        
        # Increase cache TTL to reduce requests
        self.cache_manager.default_ttl = 7200  # 2 hours
        
        # Prioritize essential data
        self._cache_essential_data_only()
        
        # Enable aggressive compression
        self._enable_data_compression()
    
    def _enable_full_functionality(self):
        """Enable full caching functionality for fast connections."""
        logger.info("Enabling full functionality")
        
        # Reset normal cache TTL
        self.cache_manager.default_ttl = 3600  # 1 hour
        
        # Enable background sync
        self._enable_background_sync()
    
    def cache_with_mobile_strategy(self,
                                 key: str,
                                 data: Any,
                                 priority: DataPriority = DataPriority.MEDIUM,
                                 ttl: Optional[int] = None) -> bool:
        """
        Cache data using mobile-optimized strategy.
        
        Args:
            key: Cache key
            data: Data to cache
            priority: Data priority level
            ttl: Time-to-live in seconds
            
        Returns:
            True if successfully cached
        """
        # Determine caching strategy based on connection and priority
        policy = self.connection_policies[self.current_connection.connection_type]
        
        # Skip caching if offline or data saver mode for non-critical data
        if (self.current_connection.connection_type == ConnectionType.OFFLINE or
            (self.current_connection.data_saver_mode and priority.value > DataPriority.HIGH.value)):
            return False
        
        # Estimate data size
        data_size = self._estimate_data_size(data)
        max_size_bytes = policy['max_request_size_mb'] * 1024 * 1024
        
        if data_size > max_size_bytes:
            logger.warning(f"Data too large for current connection: {data_size} bytes")
            return False
        
        # Cache in appropriate level based on priority and connection
        cache_level = self._determine_cache_level(priority)
        success = self.multi_level_cache.set(key, data, ttl, cache_level)
        
        # Also cache in offline cache if critical
        if success and priority in [DataPriority.CRITICAL, DataPriority.HIGH]:
            self._add_to_offline_cache(key, data, priority, ttl)
        
        return success
    
    def get_with_mobile_strategy(self, key: str) -> Optional[Any]:
        """
        Get data using mobile-optimized strategy.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None
        """
        # Try multi-level cache first
        data = self.multi_level_cache.get(key)
        if data is not None:
            self._track_access(key)
            return data
        
        # Try offline cache if online cache miss
        if key in self.offline_cache:
            entry = self.offline_cache[key]
            if not self._is_offline_entry_expired(entry):
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self.stats['offline_cache_hits'] += 1
                self._track_access(key)
                return entry.data
            else:
                # Remove expired entry
                self._remove_from_offline_cache(key)
        
        self.stats['offline_cache_misses'] += 1
        return None
    
    def track_user_behavior(self,
                          user_id: str,
                          team_id: str,
                          page: str,
                          data_types: Set[str]):
        """
        Track user behavior for predictive caching.
        
        Args:
            user_id: User identifier
            team_id: Team identifier
            page: Page accessed
            data_types: Types of data accessed
        """
        # Get or create user behavior pattern
        behavior_key = f"{user_id}_{team_id}"
        if behavior_key not in self.user_behaviors:
            self.user_behaviors[behavior_key] = UserBehaviorPattern(
                user_id=user_id,
                team_id=team_id
            )
        
        behavior = self.user_behaviors[behavior_key]
        
        # Update behavior pattern
        behavior.access_times.append(datetime.now())
        behavior.preferred_data_types.update(data_types)
        behavior.last_updated = datetime.now()
        
        # Update frequent pages
        if page not in behavior.frequent_pages:
            behavior.frequent_pages.append(page)
        elif len(behavior.frequent_pages) > 10:
            # Keep only top 10 frequent pages
            behavior.frequent_pages = behavior.frequent_pages[-10:]
        
        # Log page access
        self.page_access_log.append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'team_id': team_id,
            'page': page,
            'data_types': data_types
        })
        
        # Trigger predictive preloading
        self._schedule_predictive_preload(behavior_key)
    
    def _schedule_predictive_preload(self, behavior_key: str):
        """Schedule predictive preloading based on user behavior."""
        if not self.connection_policies[self.current_connection.connection_type]['preload_enabled']:
            return
        
        behavior = self.user_behaviors[behavior_key]
        
        # Predict next likely pages/data based on patterns
        predicted_data = self._predict_next_data_needs(behavior)
        
        # Add to preload queue
        with self.preload_lock:
            for data_key in predicted_data:
                if data_key not in [item['key'] for item in self.preload_queue]:
                    self.preload_queue.append({
                        'key': data_key,
                        'priority': DataPriority.LOW,
                        'scheduled_at': datetime.now()
                    })
    
    def _predict_next_data_needs(self, behavior: UserBehaviorPattern) -> List[str]:
        """
        Predict next data needs based on user behavior.
        
        Args:
            behavior: User behavior pattern
            
        Returns:
            List of predicted data keys
        """
        predicted = []
        
        # Based on frequent pages, predict related data
        for page in behavior.frequent_pages[-3:]:  # Last 3 frequent pages
            if page == 'player_stats':
                predicted.extend([
                    f'player_stats_{behavior.team_id}',
                    f'player_game_log_{behavior.team_id}',
                    f'team_roster_{behavior.team_id}'
                ])
            elif page == 'team_analytics':
                predicted.extend([
                    f'team_stats_{behavior.team_id}',
                    f'team_standings_{behavior.team_id}',
                    f'team_games_{behavior.team_id}'
                ])
            elif page == 'game_summary':
                predicted.extend([
                    f'recent_games_{behavior.team_id}',
                    f'game_events_{behavior.team_id}',
                    f'game_roster_{behavior.team_id}'
                ])
        
        # Based on preferred data types
        for data_type in behavior.preferred_data_types:
            predicted.append(f'{data_type}_{behavior.team_id}')
        
        return list(set(predicted))  # Remove duplicates
    
    def register_preload_strategy(self, key: str, strategy: Callable):
        """
        Register a preloading strategy for a data key.
        
        Args:
            key: Data key
            strategy: Function that returns data to preload
        """
        self.preload_strategies[key] = strategy
        logger.debug(f"Registered preload strategy: {key}")
    
    def warm_cache_for_connection(self):
        """Warm cache based on current connection type."""
        policy = self.connection_policies[self.current_connection.connection_type]
        
        if not policy['cache_aggressively']:
            return
        
        # Determine cache warming strategy based on connection
        if self.current_connection.connection_type == ConnectionType.WIFI:
            self._aggressive_cache_warming()
        elif self.current_connection.connection_type == ConnectionType.CELLULAR_4G:
            self._moderate_cache_warming()
        elif self.current_connection.is_slow_connection:
            self._conservative_cache_warming()
    
    def _aggressive_cache_warming(self):
        """Aggressive cache warming for fast connections."""
        # Warm all critical and high priority data
        warming_keys = list(self.critical_data_keys)
        
        # Add high-priority data based on user behavior
        for behavior in self.user_behaviors.values():
            predicted_keys = self._predict_next_data_needs(behavior)
            warming_keys.extend(predicted_keys[:5])  # Top 5 predictions
        
        self._execute_cache_warming(warming_keys, max_concurrent=3)
    
    def _moderate_cache_warming(self):
        """Moderate cache warming for good connections."""
        # Warm critical data and some high priority data
        warming_keys = list(self.critical_data_keys)
        
        # Add limited predictions
        for behavior in self.user_behaviors.values():
            predicted_keys = self._predict_next_data_needs(behavior)
            warming_keys.extend(predicted_keys[:2])  # Top 2 predictions
        
        self._execute_cache_warming(warming_keys, max_concurrent=2)
    
    def _conservative_cache_warming(self):
        """Conservative cache warming for slow connections."""
        # Only warm critical data
        warming_keys = list(self.critical_data_keys)
        self._execute_cache_warming(warming_keys, max_concurrent=1)
    
    def _execute_cache_warming(self, keys: List[str], max_concurrent: int = 2):
        """Execute cache warming for specified keys."""
        if not hasattr(self, '_warming_thread') or not self._warming_thread.is_alive():
            self._warming_stop_event = threading.Event()
            self._warming_keys = keys[:max_concurrent * 3]  # Limit total keys
            self._warming_thread = threading.Thread(
                target=self._cache_warming_worker,
                args=(max_concurrent,),
                daemon=True
            )
            self._warming_thread.start()
            logger.info(f"Started cache warming with {len(self._warming_keys)} keys")
    
    def _cache_warming_worker(self, max_concurrent: int):
        """Background worker for cache warming."""
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = []
            
            for key in getattr(self, '_warming_keys', []):
                if self._warming_stop_event.is_set():
                    break
                
                future = executor.submit(self._warm_single_key, key)
                futures.append(future)
            
            # Wait for completion or stop event
            for future in concurrent.futures.as_completed(futures, timeout=30):
                if self._warming_stop_event.is_set():
                    break
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in cache warming: {e}")
    
    def _warm_single_key(self, key: str):
        """Warm cache for a single key."""
        try:
            # Check if already cached
            if self.multi_level_cache.get(key) is not None:
                return
            
            # Use preload strategy if available
            if key in self.preload_strategies:
                strategy = self.preload_strategies[key]
                data = strategy()
                if data is not None:
                    priority = DataPriority.CRITICAL if key in self.critical_data_keys else DataPriority.HIGH
                    self.cache_with_mobile_strategy(key, data, priority)
                    logger.debug(f"Cache warmed: {key}")
        except Exception as e:
            logger.error(f"Error warming cache for {key}: {e}")
    
    def _add_to_offline_cache(self,
                            key: str,
                            data: Any,
                            priority: DataPriority,
                            ttl: Optional[int] = None):
        """Add data to offline cache with size management."""
        data_size = self._estimate_data_size(data)
        
        # Check if we need to evict entries
        while (self.offline_cache_size + data_size > self.max_offline_cache_bytes and
               len(self.offline_cache) > 0):
            self._evict_offline_cache_entry()
        
        # Create offline cache entry
        ttl = ttl or (86400 if priority == DataPriority.CRITICAL else 3600)  # 24h for critical, 1h for others
        
        entry = OfflineCacheEntry(
            key=key,
            data=data,
            priority=priority,
            size_bytes=data_size,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl),
            last_accessed=datetime.now(),
            is_critical=priority == DataPriority.CRITICAL
        )
        
        # Remove existing entry if present
        if key in self.offline_cache:
            self.offline_cache_size -= self.offline_cache[key].size_bytes
        
        self.offline_cache[key] = entry
        self.offline_cache_size += data_size
        
        logger.debug(f"Added to offline cache: {key} ({data_size} bytes)")
    
    def _evict_offline_cache_entry(self):
        """Evict least important entry from offline cache."""
        if not self.offline_cache:
            return
        
        # Sort by priority (higher number = lower priority) and access time
        sorted_entries = sorted(
            self.offline_cache.items(),
            key=lambda x: (x[1].priority.value, x[1].last_accessed)
        )
        
        # Don't evict critical data unless absolutely necessary
        for key, entry in sorted_entries:
            if not entry.is_critical:
                self._remove_from_offline_cache(key)
                return
        
        # If only critical data remains, evict oldest critical entry
        if sorted_entries:
            key = sorted_entries[0][0]
            self._remove_from_offline_cache(key)
    
    def _remove_from_offline_cache(self, key: str):
        """Remove entry from offline cache."""
        if key in self.offline_cache:
            entry = self.offline_cache[key]
            self.offline_cache_size -= entry.size_bytes
            del self.offline_cache[key]
            logger.debug(f"Removed from offline cache: {key}")
    
    def _start_intelligent_preloading(self):
        """Start intelligent preloading based on connection and behavior."""
        if not hasattr(self, '_preload_thread') or not self._preload_thread.is_alive():
            self._preload_stop_event = threading.Event()
            self._preload_thread = threading.Thread(
                target=self._preload_worker,
                daemon=True
            )
            self._preload_thread.start()
            logger.info("Started intelligent preloading")
    
    def _stop_preloading(self):
        """Stop preloading operations."""
        if hasattr(self, '_preload_stop_event'):
            self._preload_stop_event.set()
        logger.info("Stopped preloading")
    
    def _preload_worker(self):
        """Background worker for preloading data."""
        while not self._preload_stop_event.wait(30):  # Check every 30 seconds
            try:
                self._process_preload_queue()
            except Exception as e:
                logger.error(f"Error in preload worker: {e}")
    
    def _process_preload_queue(self):
        """Process items in the preload queue."""
        with self.preload_lock:
            if not self.preload_queue:
                return
            
            # Process up to 3 items per cycle to avoid overwhelming
            items_to_process = []
            for _ in range(min(3, len(self.preload_queue))):
                if self.preload_queue:
                    items_to_process.append(self.preload_queue.popleft())
        
        for item in items_to_process:
            try:
                # Check if data is already cached
                if self.multi_level_cache.get(item['key']) is None:
                    # Use preload strategy if available
                    if item['key'] in self.preload_strategies:
                        strategy = self.preload_strategies[item['key']]
                        data = strategy()
                        if data is not None:
                            self.cache_with_mobile_strategy(
                                item['key'], 
                                data, 
                                item['priority']
                            )
                            self.stats['preload_operations'] += 1
                            logger.debug(f"Preloaded: {item['key']}")
            except Exception as e:
                logger.error(f"Error preloading {item['key']}: {e}")
    
    def _ensure_critical_data_cached(self):
        """Ensure critical data is available in offline cache."""
        for key in self.critical_data_keys:
            # Try to get from multi-level cache
            data = self.multi_level_cache.get(key)
            if data is not None:
                # Add to offline cache
                self._add_to_offline_cache(key, data, DataPriority.CRITICAL)
    
    def _cache_essential_data_only(self):
        """Cache only essential data for slow connections."""
        # Clear non-essential data from cache
        non_essential_keys = []
        for key in self.offline_cache:
            entry = self.offline_cache[key]
            if entry.priority.value > DataPriority.HIGH.value:
                non_essential_keys.append(key)
        
        for key in non_essential_keys:
            self._remove_from_offline_cache(key)
    
    def _enable_data_compression(self):
        """Enable data compression for slow connections."""
        # This would integrate with compression service
        logger.debug("Data compression enabled for slow connection")
    
    def _enable_background_sync(self):
        """Enable background synchronization for fast connections."""
        # This would integrate with background sync service
        logger.debug("Background sync enabled")
    
    def _adjust_cache_ttl_for_connection(self):
        """Adjust cache TTL based on connection quality."""
        if self.current_connection.connection_type == ConnectionType.WIFI:
            # Short TTL for fast connections to keep data fresh
            self.cache_manager.default_ttl = 1800  # 30 minutes
        elif self.current_connection.connection_type == ConnectionType.CELLULAR_4G:
            # Moderate TTL for good cellular
            self.cache_manager.default_ttl = 3600  # 1 hour
        elif self.current_connection.is_slow_connection:
            # Long TTL for slow connections to reduce requests
            self.cache_manager.default_ttl = 7200  # 2 hours
        elif self.current_connection.connection_type == ConnectionType.OFFLINE:
            # Very long TTL for offline mode
            self.cache_manager.default_ttl = 86400  # 24 hours
    
    def _adjust_cache_limits_for_connection(self):
        """Adjust cache size limits based on connection type."""
        if self.current_connection.connection_type == ConnectionType.WIFI:
            # Larger cache for WiFi
            self.max_offline_cache_bytes = 100 * 1024 * 1024  # 100MB
        elif self.current_connection.connection_type == ConnectionType.CELLULAR_4G:
            # Moderate cache for 4G
            self.max_offline_cache_bytes = 75 * 1024 * 1024  # 75MB
        elif self.current_connection.is_slow_connection:
            # Smaller cache for slow connections
            self.max_offline_cache_bytes = 50 * 1024 * 1024  # 50MB
        elif self.current_connection.data_saver_mode:
            # Minimal cache for data saver mode
            self.max_offline_cache_bytes = 25 * 1024 * 1024  # 25MB
    
    def _track_access(self, key: str):
        """Track data access for behavior analysis."""
        # Update access patterns for predictive caching
        pass
    
    def _determine_cache_level(self, priority: DataPriority) -> int:
        """
        Determine appropriate cache level based on priority.
        
        Args:
            priority: Data priority
            
        Returns:
            Cache level (1=L1, 2=L2, 3=L3)
        """
        if priority == DataPriority.CRITICAL:
            return 1  # L1 cache
        elif priority == DataPriority.HIGH:
            return 2  # L2 cache
        else:
            return 3  # L3 cache
    
    def _estimate_data_size(self, data: Any) -> int:
        """Estimate data size in bytes."""
        try:
            import sys
            return sys.getsizeof(data)
        except Exception:
            return len(str(data)) * 2
    
    def _is_offline_entry_expired(self, entry: OfflineCacheEntry) -> bool:
        """Check if offline cache entry is expired."""
        return datetime.now() > entry.expires_at
    
    def get_mobile_cache_stats(self) -> Dict[str, Any]:
        """Get mobile cache statistics."""
        total_offline_requests = (self.stats['offline_cache_hits'] + 
                                self.stats['offline_cache_misses'])
        offline_hit_rate = (self.stats['offline_cache_hits'] / total_offline_requests * 100 
                          if total_offline_requests > 0 else 0)
        
        return {
            'connection_type': self.current_connection.connection_type.value,
            'is_metered': self.current_connection.is_metered,
            'data_saver_mode': self.current_connection.data_saver_mode,
            'offline_cache_entries': len(self.offline_cache),
            'offline_cache_size_mb': self.offline_cache_size / (1024 * 1024),
            'offline_hit_rate_percent': offline_hit_rate,
            'preload_operations': self.stats['preload_operations'],
            'connection_adaptations': self.stats['connection_adaptations'],
            'data_saved_mb': self.stats['data_saved_mb'],
            'user_behaviors_tracked': len(self.user_behaviors)
        }
    
    def clear_mobile_cache(self):
        """Clear mobile-specific caches."""
        self.offline_cache.clear()
        self.offline_cache_size = 0
        self.preload_queue.clear()
        logger.info("Mobile cache cleared")