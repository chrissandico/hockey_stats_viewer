"""
Background Cache Refresh System for Hockey Stats Application

This module implements background tasks for cache warming, automatic refresh
of stale data, and cache refresh scheduling based on data access patterns.
"""

import time
import threading
import schedule
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class RefreshTask:
    """Represents a cache refresh task."""
    key: str
    refresh_function: Callable
    priority: int = 1  # 1=high, 2=medium, 3=low
    last_refresh: Optional[datetime] = None
    refresh_interval: int = 300  # seconds
    access_count: int = 0
    error_count: int = 0
    max_errors: int = 3
    
    def should_refresh(self) -> bool:
        """Check if task should be refreshed."""
        if self.last_refresh is None:
            return True
        
        age = datetime.now() - self.last_refresh
        return age.total_seconds() >= self.refresh_interval
    
    def is_healthy(self) -> bool:
        """Check if task is healthy (not too many errors)."""
        return self.error_count < self.max_errors


@dataclass
class AccessPattern:
    """Tracks access patterns for intelligent refresh scheduling."""
    key: str
    access_times: List[datetime] = field(default_factory=list)
    access_frequency: float = 0.0  # accesses per hour
    peak_hours: List[int] = field(default_factory=list)
    last_calculated: Optional[datetime] = None
    
    def record_access(self):
        """Record an access to this cache key."""
        now = datetime.now()
        self.access_times.append(now)
        
        # Keep only last 24 hours of access data
        cutoff = now - timedelta(hours=24)
        self.access_times = [t for t in self.access_times if t > cutoff]
        
        # Recalculate patterns if needed
        if (self.last_calculated is None or 
            (now - self.last_calculated).total_seconds() > 3600):  # Recalculate hourly
            self._calculate_patterns()
    
    def _calculate_patterns(self):
        """Calculate access frequency and peak hours."""
        now = datetime.now()
        
        if len(self.access_times) < 2:
            self.access_frequency = 0.0
            self.peak_hours = []
            self.last_calculated = now
            return
        
        # Calculate frequency (accesses per hour)
        hours_span = (self.access_times[-1] - self.access_times[0]).total_seconds() / 3600
        if hours_span > 0:
            self.access_frequency = len(self.access_times) / hours_span
        
        # Calculate peak hours
        hour_counts = defaultdict(int)
        for access_time in self.access_times:
            hour_counts[access_time.hour] += 1
        
        if hour_counts:
            avg_count = sum(hour_counts.values()) / len(hour_counts)
            self.peak_hours = [hour for hour, count in hour_counts.items() 
                             if count > avg_count * 1.5]
        
        self.last_calculated = now
        logger.debug(f"Updated access pattern for {self.key}: "
                    f"freq={self.access_frequency:.2f}/hr, peaks={self.peak_hours}")


class BackgroundCacheRefresh:
    """
    Background cache refresh system with intelligent scheduling.
    
    Features:
    - Automatic refresh of stale cache entries
    - Priority-based refresh scheduling
    - Access pattern analysis for optimal refresh timing
    - Error handling and retry logic
    - Configurable refresh intervals
    """
    
    def __init__(self, 
                 max_workers: int = 3,
                 refresh_interval: int = 60,
                 pattern_analysis_interval: int = 3600):
        """
        Initialize background cache refresh system.
        
        Args:
            max_workers: Maximum number of concurrent refresh workers
            refresh_interval: Base refresh check interval in seconds
            pattern_analysis_interval: How often to analyze access patterns
        """
        self.max_workers = max_workers
        self.refresh_interval = refresh_interval
        self.pattern_analysis_interval = pattern_analysis_interval
        
        # Task management
        self.refresh_tasks: Dict[str, RefreshTask] = {}
        self.access_patterns: Dict[str, AccessPattern] = {}
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.refresh_thread = None
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        
        # Statistics
        self.stats = {
            'total_refreshes': 0,
            'successful_refreshes': 0,
            'failed_refreshes': 0,
            'cache_hits_prevented': 0,
            'background_errors': 0
        }
        
        logger.info(f"BackgroundCacheRefresh initialized with {max_workers} workers")
    
    def register_refresh_task(self, 
                            key: str, 
                            refresh_function: Callable,
                            priority: int = 1,
                            refresh_interval: int = 300) -> bool:
        """
        Register a cache refresh task.
        
        Args:
            key: Cache key to refresh
            refresh_function: Function that returns fresh data
            priority: Task priority (1=high, 2=medium, 3=low)
            refresh_interval: Refresh interval in seconds
            
        Returns:
            True if task registered successfully
        """
        try:
            task = RefreshTask(
                key=key,
                refresh_function=refresh_function,
                priority=priority,
                refresh_interval=refresh_interval
            )
            
            self.refresh_tasks[key] = task
            
            # Initialize access pattern tracking
            if key not in self.access_patterns:
                self.access_patterns[key] = AccessPattern(key=key)
            
            logger.info(f"Registered refresh task: {key} (priority={priority}, interval={refresh_interval}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error registering refresh task {key}: {e}")
            return False
    
    def unregister_refresh_task(self, key: str):
        """Unregister a cache refresh task."""
        if key in self.refresh_tasks:
            del self.refresh_tasks[key]
            logger.info(f"Unregistered refresh task: {key}")
    
    def record_cache_access(self, key: str):
        """
        Record cache access for pattern analysis.
        
        Args:
            key: Cache key that was accessed
        """
        if key in self.access_patterns:
            self.access_patterns[key].record_access()
        elif key in self.refresh_tasks:
            # Create access pattern for registered tasks
            pattern = AccessPattern(key=key)
            pattern.record_access()
            self.access_patterns[key] = pattern
    
    def start_background_refresh(self):
        """Start background refresh threads."""
        if self.refresh_thread and self.refresh_thread.is_alive():
            logger.warning("Background refresh already running")
            return
        
        self.stop_event.clear()
        
        # Start main refresh worker
        self.refresh_thread = threading.Thread(
            target=self._refresh_worker, 
            daemon=True,
            name="CacheRefreshWorker"
        )
        self.refresh_thread.start()
        
        # Start scheduler for pattern-based refresh
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_worker,
            daemon=True,
            name="CacheSchedulerWorker"
        )
        self.scheduler_thread.start()
        
        logger.info("Started background cache refresh")
    
    def stop_background_refresh(self):
        """Stop background refresh threads."""
        self.stop_event.set()
        
        if self.refresh_thread:
            self.refresh_thread.join(timeout=5)
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Stopped background cache refresh")
    
    def _refresh_worker(self):
        """Main refresh worker thread."""
        logger.info(f"Cache refresh worker started (interval: {self.refresh_interval}s)")
        
        while not self.stop_event.wait(self.refresh_interval):
            try:
                self._process_refresh_tasks()
            except Exception as e:
                logger.error(f"Error in refresh worker: {e}")
                self.stats['background_errors'] += 1
    
    def _scheduler_worker(self):
        """Scheduler worker for pattern-based refresh."""
        logger.info(f"Cache scheduler worker started (interval: {self.pattern_analysis_interval}s)")
        
        while not self.stop_event.wait(self.pattern_analysis_interval):
            try:
                self._optimize_refresh_schedules()
                self._cleanup_old_patterns()
            except Exception as e:
                logger.error(f"Error in scheduler worker: {e}")
                self.stats['background_errors'] += 1
    
    def _process_refresh_tasks(self):
        """Process all refresh tasks based on priority and schedule."""
        
        # Get tasks that need refresh, sorted by priority
        tasks_to_refresh = []
        
        for key, task in self.refresh_tasks.items():
            if task.is_healthy() and task.should_refresh():
                tasks_to_refresh.append((key, task))
        
        if not tasks_to_refresh:
            return
        
        # Sort by priority (1=highest) and last refresh time
        tasks_to_refresh.sort(key=lambda x: (
            x[1].priority, 
            x[1].last_refresh or datetime.min
        ))
        
        logger.debug(f"Processing {len(tasks_to_refresh)} refresh tasks")
        
        # Submit tasks to thread pool
        future_to_task = {}
        
        for key, task in tasks_to_refresh:
            future = self.executor.submit(self._refresh_single_task, key, task)
            future_to_task[future] = (key, task)
        
        # Process completed tasks
        for future in as_completed(future_to_task, timeout=30):
            key, task = future_to_task[future]
            try:
                success = future.result()
                if success:
                    task.last_refresh = datetime.now()
                    task.error_count = 0
                    self.stats['successful_refreshes'] += 1
                else:
                    task.error_count += 1
                    self.stats['failed_refreshes'] += 1
                
                self.stats['total_refreshes'] += 1
                
            except Exception as e:
                logger.error(f"Error refreshing {key}: {e}")
                task.error_count += 1
                self.stats['failed_refreshes'] += 1
                self.stats['total_refreshes'] += 1
    
    def _refresh_single_task(self, key: str, task: RefreshTask) -> bool:
        """
        Refresh a single cache task.
        
        Args:
            key: Cache key
            task: Refresh task
            
        Returns:
            True if refresh was successful
        """
        try:
            logger.debug(f"Refreshing cache: {key}")
            
            # Call the refresh function
            fresh_data = task.refresh_function()
            
            if fresh_data is not None:
                logger.debug(f"Successfully refreshed cache: {key}")
                return True
            else:
                logger.warning(f"Refresh function returned None for: {key}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing cache {key}: {e}")
            return False
    
    def _optimize_refresh_schedules(self):
        """Optimize refresh schedules based on access patterns."""
        
        current_hour = datetime.now().hour
        
        for key, pattern in self.access_patterns.items():
            if key not in self.refresh_tasks:
                continue
            
            task = self.refresh_tasks[key]
            
            # Adjust refresh interval based on access frequency
            if pattern.access_frequency > 10:  # High frequency (>10 accesses/hour)
                new_interval = min(task.refresh_interval, 180)  # Refresh every 3 minutes
            elif pattern.access_frequency > 2:  # Medium frequency (2-10 accesses/hour)
                new_interval = min(task.refresh_interval, 300)  # Refresh every 5 minutes
            else:  # Low frequency (<2 accesses/hour)
                new_interval = max(task.refresh_interval, 600)  # Refresh every 10 minutes
            
            # Adjust for peak hours
            if current_hour in pattern.peak_hours:
                new_interval = int(new_interval * 0.7)  # More frequent during peak hours
            
            # Update interval if significantly different
            if abs(task.refresh_interval - new_interval) > 60:
                old_interval = task.refresh_interval
                task.refresh_interval = new_interval
                logger.debug(f"Adjusted refresh interval for {key}: {old_interval}s -> {new_interval}s")
    
    def _cleanup_old_patterns(self):
        """Clean up old access patterns to prevent memory leaks."""
        cutoff = datetime.now() - timedelta(days=7)
        
        keys_to_remove = []
        for key, pattern in self.access_patterns.items():
            if (pattern.last_calculated and 
                pattern.last_calculated < cutoff and
                len(pattern.access_times) == 0):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.access_patterns[key]
            logger.debug(f"Cleaned up old access pattern: {key}")
    
    def warm_cache_for_peak_hours(self):
        """Proactively warm cache before predicted peak hours."""
        current_hour = datetime.now().hour
        next_hour = (current_hour + 1) % 24
        
        # Find caches that will be needed in the next hour
        keys_to_warm = []
        
        for key, pattern in self.access_patterns.items():
            if next_hour in pattern.peak_hours and key in self.refresh_tasks:
                keys_to_warm.append(key)
        
        if keys_to_warm:
            logger.info(f"Warming {len(keys_to_warm)} caches for upcoming peak hour {next_hour}")
            
            for key in keys_to_warm:
                task = self.refresh_tasks[key]
                try:
                    self._refresh_single_task(key, task)
                    self.stats['cache_hits_prevented'] += 1
                except Exception as e:
                    logger.error(f"Error warming cache {key}: {e}")
    
    def force_refresh_all(self):
        """Force refresh of all registered tasks."""
        logger.info("Force refreshing all cache tasks")
        
        for key, task in self.refresh_tasks.items():
            if task.is_healthy():
                try:
                    success = self._refresh_single_task(key, task)
                    if success:
                        task.last_refresh = datetime.now()
                        task.error_count = 0
                    else:
                        task.error_count += 1
                except Exception as e:
                    logger.error(f"Error force refreshing {key}: {e}")
                    task.error_count += 1
    
    def get_refresh_stats(self) -> Dict[str, Any]:
        """Get comprehensive refresh statistics."""
        
        healthy_tasks = sum(1 for task in self.refresh_tasks.values() if task.is_healthy())
        total_tasks = len(self.refresh_tasks)
        
        success_rate = 0
        if self.stats['total_refreshes'] > 0:
            success_rate = (self.stats['successful_refreshes'] / 
                          self.stats['total_refreshes'] * 100)
        
        # Get access pattern summary
        high_frequency_keys = []
        for key, pattern in self.access_patterns.items():
            if pattern.access_frequency > 5:
                high_frequency_keys.append({
                    'key': key,
                    'frequency': pattern.access_frequency,
                    'peak_hours': pattern.peak_hours
                })
        
        return {
            'tasks': {
                'total': total_tasks,
                'healthy': healthy_tasks,
                'unhealthy': total_tasks - healthy_tasks
            },
            'refreshes': {
                'total': self.stats['total_refreshes'],
                'successful': self.stats['successful_refreshes'],
                'failed': self.stats['failed_refreshes'],
                'success_rate_percent': success_rate
            },
            'performance': {
                'cache_hits_prevented': self.stats['cache_hits_prevented'],
                'background_errors': self.stats['background_errors']
            },
            'access_patterns': {
                'tracked_keys': len(self.access_patterns),
                'high_frequency_keys': high_frequency_keys
            }
        }
    
    def __del__(self):
        """Cleanup when refresh manager is destroyed."""
        self.stop_background_refresh()