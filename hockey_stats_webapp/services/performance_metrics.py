"""
Performance Metrics Collection System

This module provides comprehensive performance monitoring capabilities including:
- Response time tracking for all major operations
- Cache hit/miss ratio monitoring
- Error rate tracking
- Google Sheets API quota usage monitoring
"""

import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import statistics


@dataclass
class PerformanceMetric:
    """Individual performance metric entry"""
    metric_type: str  # 'response_time', 'cache_hit', 'error_rate', 'api_call'
    value: float
    timestamp: datetime
    endpoint: str
    user_session: str = ""
    additional_data: Dict[str, Any] = field(default_factory=dict)


class PerformanceMetrics:
    """
    Centralized performance metrics collection and analysis system.
    
    Tracks response times, cache performance, error rates, and API usage
    with configurable retention periods and aggregation capabilities.
    """
    
    def __init__(self, retention_hours: int = 24, max_entries_per_type: int = 10000):
        self.retention_hours = retention_hours
        self.max_entries_per_type = max_entries_per_type
        
        # Thread-safe storage for metrics
        self._lock = threading.RLock()
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_entries_per_type))
        
        # Cache for aggregated statistics
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        
        # API quota tracking
        self._api_quota = {
            'calls_made': 0,
            'quota_limit': 100,  # Default Google Sheets API limit per 100 seconds
            'reset_time': datetime.now() + timedelta(seconds=100)
        }
        
        # Performance thresholds
        self.thresholds = {
            'response_time_warning': 3.0,  # seconds
            'response_time_critical': 5.0,  # seconds
            'error_rate_warning': 0.05,  # 5%
            'error_rate_critical': 0.10,  # 10%
            'cache_hit_rate_warning': 0.70  # 70%
        }
    
    def record_response_time(self, endpoint: str, duration: float, 
                           user_session: str = "", additional_data: Dict = None):
        """Record response time for an endpoint"""
        metric = PerformanceMetric(
            metric_type='response_time',
            value=duration,
            timestamp=datetime.now(),
            endpoint=endpoint,
            user_session=user_session,
            additional_data=additional_data or {}
        )
        
        with self._lock:
            self._metrics['response_time'].append(metric)
            self._cleanup_old_metrics()
    
    def record_cache_hit(self, cache_key: str, hit: bool, user_session: str = ""):
        """Record cache hit or miss"""
        with self._lock:
            if hit:
                self._cache_stats['hits'] += 1
            else:
                self._cache_stats['misses'] += 1
            self._cache_stats['total_requests'] += 1
        
        metric = PerformanceMetric(
            metric_type='cache_hit' if hit else 'cache_miss',
            value=1.0,
            timestamp=datetime.now(),
            endpoint=cache_key,
            user_session=user_session,
            additional_data={'cache_key': cache_key}
        )
        
        with self._lock:
            self._metrics['cache_performance'].append(metric)
    
    def record_error(self, endpoint: str, error_type: str, user_session: str = "", 
                    additional_data: Dict = None):
        """Record an error occurrence"""
        metric = PerformanceMetric(
            metric_type='error',
            value=1.0,
            timestamp=datetime.now(),
            endpoint=endpoint,
            user_session=user_session,
            additional_data={
                'error_type': error_type,
                **(additional_data or {})
            }
        )
        
        with self._lock:
            self._metrics['errors'].append(metric)
    
    def record_api_call(self, api_type: str = 'google_sheets', user_session: str = ""):
        """Record API call for quota tracking"""
        with self._lock:
            # Reset quota counter if time window has passed
            if datetime.now() > self._api_quota['reset_time']:
                self._api_quota['calls_made'] = 0
                self._api_quota['reset_time'] = datetime.now() + timedelta(seconds=100)
            
            self._api_quota['calls_made'] += 1
        
        metric = PerformanceMetric(
            metric_type='api_call',
            value=1.0,
            timestamp=datetime.now(),
            endpoint=api_type,
            user_session=user_session,
            additional_data={'api_type': api_type}
        )
        
        with self._lock:
            self._metrics['api_calls'].append(metric)
    
    def get_response_time_stats(self, endpoint: str = None, 
                              time_window_minutes: int = 60) -> Dict[str, float]:
        """Get response time statistics for the specified time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            response_times = []
            for metric in self._metrics['response_time']:
                if metric.timestamp >= cutoff_time:
                    if endpoint is None or metric.endpoint == endpoint:
                        response_times.append(metric.value)
        
        if not response_times:
            return {
                'count': 0,
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'p95': 0.0,
                'p99': 0.0
            }
        
        return {
            'count': len(response_times),
            'avg': statistics.mean(response_times),
            'min': min(response_times),
            'max': max(response_times),
            'p95': self._percentile(response_times, 95),
            'p99': self._percentile(response_times, 99)
        }
    
    def get_cache_hit_rate(self, time_window_minutes: int = 60) -> Dict[str, float]:
        """Get cache hit rate statistics"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            hits = 0
            total = 0
            
            for metric in self._metrics['cache_performance']:
                if metric.timestamp >= cutoff_time:
                    total += 1
                    if metric.metric_type == 'cache_hit':
                        hits += 1
        
        hit_rate = hits / total if total > 0 else 0.0
        
        return {
            'hit_rate': hit_rate,
            'hits': hits,
            'misses': total - hits,
            'total': total
        }
    
    def get_error_rate(self, endpoint: str = None, 
                      time_window_minutes: int = 60) -> Dict[str, float]:
        """Get error rate statistics"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            errors = 0
            total_requests = 0
            
            # Count errors
            for metric in self._metrics['errors']:
                if metric.timestamp >= cutoff_time:
                    if endpoint is None or metric.endpoint == endpoint:
                        errors += 1
            
            # Count total requests (response times as proxy)
            for metric in self._metrics['response_time']:
                if metric.timestamp >= cutoff_time:
                    if endpoint is None or metric.endpoint == endpoint:
                        total_requests += 1
        
        error_rate = errors / total_requests if total_requests > 0 else 0.0
        
        return {
            'error_rate': error_rate,
            'errors': errors,
            'total_requests': total_requests
        }
    
    def get_api_quota_usage(self) -> Dict[str, Any]:
        """Get current API quota usage"""
        with self._lock:
            usage_percentage = (self._api_quota['calls_made'] / 
                              self._api_quota['quota_limit']) * 100
            
            return {
                'calls_made': self._api_quota['calls_made'],
                'quota_limit': self._api_quota['quota_limit'],
                'usage_percentage': usage_percentage,
                'reset_time': self._api_quota['reset_time'],
                'seconds_until_reset': max(0, (self._api_quota['reset_time'] - 
                                             datetime.now()).total_seconds())
            }
    
    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'response_times': self.get_response_time_stats(time_window_minutes=time_window_minutes),
            'cache_performance': self.get_cache_hit_rate(time_window_minutes=time_window_minutes),
            'error_rates': self.get_error_rate(time_window_minutes=time_window_minutes),
            'api_quota': self.get_api_quota_usage(),
            'timestamp': datetime.now().isoformat(),
            'time_window_minutes': time_window_minutes
        }
    
    def check_performance_thresholds(self) -> List[Dict[str, Any]]:
        """Check if any performance metrics exceed thresholds"""
        alerts = []
        
        # Check response times
        response_stats = self.get_response_time_stats(time_window_minutes=10)
        if response_stats['count'] > 0:
            if response_stats['avg'] > self.thresholds['response_time_critical']:
                alerts.append({
                    'type': 'critical',
                    'metric': 'response_time',
                    'value': response_stats['avg'],
                    'threshold': self.thresholds['response_time_critical'],
                    'message': f"Average response time ({response_stats['avg']:.2f}s) exceeds critical threshold"
                })
            elif response_stats['avg'] > self.thresholds['response_time_warning']:
                alerts.append({
                    'type': 'warning',
                    'metric': 'response_time',
                    'value': response_stats['avg'],
                    'threshold': self.thresholds['response_time_warning'],
                    'message': f"Average response time ({response_stats['avg']:.2f}s) exceeds warning threshold"
                })
        
        # Check error rates
        error_stats = self.get_error_rate(time_window_minutes=10)
        if error_stats['error_rate'] > self.thresholds['error_rate_critical']:
            alerts.append({
                'type': 'critical',
                'metric': 'error_rate',
                'value': error_stats['error_rate'],
                'threshold': self.thresholds['error_rate_critical'],
                'message': f"Error rate ({error_stats['error_rate']:.1%}) exceeds critical threshold"
            })
        elif error_stats['error_rate'] > self.thresholds['error_rate_warning']:
            alerts.append({
                'type': 'warning',
                'metric': 'error_rate',
                'value': error_stats['error_rate'],
                'threshold': self.thresholds['error_rate_warning'],
                'message': f"Error rate ({error_stats['error_rate']:.1%}) exceeds warning threshold"
            })
        
        # Check cache hit rate
        cache_stats = self.get_cache_hit_rate(time_window_minutes=10)
        if cache_stats['total'] > 0 and cache_stats['hit_rate'] < self.thresholds['cache_hit_rate_warning']:
            alerts.append({
                'type': 'warning',
                'metric': 'cache_hit_rate',
                'value': cache_stats['hit_rate'],
                'threshold': self.thresholds['cache_hit_rate_warning'],
                'message': f"Cache hit rate ({cache_stats['hit_rate']:.1%}) below warning threshold"
            })
        
        return alerts
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a dataset"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        for metric_type, metrics in self._metrics.items():
            # Remove old metrics from the front of the deque
            while metrics and metrics[0].timestamp < cutoff_time:
                metrics.popleft()


# Global performance metrics instance
performance_metrics = PerformanceMetrics()