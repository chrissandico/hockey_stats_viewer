"""
Alerting Integration Module

Integrates the performance alerting system with existing services
and provides easy-to-use decorators and utilities for monitoring.
"""

import functools
import time
import psutil
import os
from datetime import datetime
from typing import Optional, Any, Callable
from .performance_alerting import get_alerting_system, initialize_alerting_system
from .performance_metrics import performance_metrics

class AlertingIntegration:
    """Integration layer for performance alerting"""
    
    def __init__(self):
        self.alerting_system = None
        self.performance_metrics = None
        self._initialized = False
    
    def initialize(self, config_file: Optional[str] = None, start_monitoring: bool = True):
        """Initialize the alerting integration"""
        if self._initialized:
            return
        
        # Initialize alerting system
        config_path = config_file or os.path.join(
            os.path.dirname(__file__), '..', 'config', 'alerting_config.json'
        )
        
        self.alerting_system = initialize_alerting_system(config_path, start_monitoring)
        self.performance_metrics = performance_metrics
        self._initialized = True
    
    def monitor_response_time(self, operation_name: str):
        """Decorator to monitor response times and trigger alerts"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self._initialized:
                    return func(*args, **kwargs)
                
                start_time = time.time()
                error_occurred = False
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error_occurred = True
                    raise
                finally:
                    # Record response time
                    duration = time.time() - start_time
                    self.alerting_system.add_metric('response_time', duration)
                    
                    # Record error if occurred
                    if error_occurred:
                        self.alerting_system.add_metric('error_rate', 1.0)
                    else:
                        self.alerting_system.add_metric('error_rate', 0.0)
                    
                    # Also record in performance metrics
                    if self.performance_metrics:
                        self.performance_metrics.record_response_time(operation_name, duration)
                        if error_occurred:
                            self.performance_metrics.record_error(operation_name, str(e))
            
            return wrapper
        return decorator
    
    def monitor_cache_performance(self, cache_name: str, hit: bool):
        """Record cache hit/miss for alerting"""
        if not self._initialized:
            return
        
        # Record cache hit (1.0) or miss (0.0)
        cache_hit_value = 1.0 if hit else 0.0
        self.alerting_system.add_metric('cache_miss_rate', 1.0 - cache_hit_value)
    
    def monitor_memory_usage(self):
        """Monitor current memory usage"""
        if not self._initialized:
            return
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Convert to ratio (0.0 to 1.0)
            memory_ratio = memory_percent / 100.0
            self.alerting_system.add_metric('memory_usage', memory_ratio)
            
        except Exception as e:
            # If psutil fails, skip memory monitoring
            pass
    
    def monitor_api_quota_usage(self, used_quota: int, total_quota: int):
        """Monitor Google Sheets API quota usage"""
        if not self._initialized or total_quota <= 0:
            return
        
        quota_ratio = used_quota / total_quota
        self.alerting_system.add_metric('api_quota_usage', quota_ratio)
    
    def record_custom_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a custom metric for alerting"""
        if not self._initialized:
            return
        
        self.alerting_system.add_metric(metric_name, value, timestamp)
    
    def get_alert_status(self) -> dict:
        """Get current alerting system status"""
        if not self._initialized:
            return {'status': 'not_initialized'}
        
        return self.alerting_system.get_alert_status()
    
    def trigger_manual_check(self):
        """Manually trigger threshold checks"""
        if not self._initialized:
            return
        
        self.alerting_system.check_thresholds()
        self.alerting_system.check_performance_degradation()

# Global integration instance
_alerting_integration = AlertingIntegration()

def get_alerting_integration() -> AlertingIntegration:
    """Get the global alerting integration instance"""
    return _alerting_integration

def initialize_alerting_integration(config_file: Optional[str] = None, start_monitoring: bool = True):
    """Initialize the alerting integration"""
    _alerting_integration.initialize(config_file, start_monitoring)
    return _alerting_integration

# Convenience decorators
def monitor_performance(operation_name: str):
    """Decorator to monitor performance and trigger alerts"""
    return _alerting_integration.monitor_response_time(operation_name)

def record_cache_hit(cache_name: str):
    """Record a cache hit"""
    _alerting_integration.monitor_cache_performance(cache_name, True)

def record_cache_miss(cache_name: str):
    """Record a cache miss"""
    _alerting_integration.monitor_cache_performance(cache_name, False)

def check_memory_usage():
    """Check and record current memory usage"""
    _alerting_integration.monitor_memory_usage()

def record_api_quota(used: int, total: int):
    """Record API quota usage"""
    _alerting_integration.monitor_api_quota_usage(used, total)