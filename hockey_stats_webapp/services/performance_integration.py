"""
Performance Monitoring Integration

Provides easy integration of performance monitoring into existing services
without requiring major code changes.
"""

import functools
from typing import Any, Dict, Optional
from .performance_metrics import performance_metrics
from .performance_decorators import track_performance, track_api_calls, PerformanceContext
from .alerting_integration import get_alerting_integration, record_cache_hit, record_cache_miss, check_memory_usage


class PerformanceMonitoringMixin:
    """
    Mixin class to add performance monitoring capabilities to existing services.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._performance_enabled = True
    
    def enable_performance_monitoring(self):
        """Enable performance monitoring for this service"""
        self._performance_enabled = True
    
    def disable_performance_monitoring(self):
        """Disable performance monitoring for this service"""
        self._performance_enabled = False
    
    def track_operation(self, operation_name: str, user_session: str = ""):
        """
        Context manager for tracking operation performance
        
        Usage:
            with self.track_operation("get_player_stats"):
                # Your code here
                pass
        """
        if not self._performance_enabled:
            return PerformanceContext("disabled")
        
        endpoint_name = f"{self.__class__.__name__}.{operation_name}"
        return PerformanceContext(endpoint_name, user_session)
    
    def record_cache_operation(self, cache_key: str, hit: bool, user_session: str = ""):
        """Record a cache hit or miss"""
        if self._performance_enabled:
            performance_metrics.record_cache_hit(cache_key, hit, user_session)
            # Also record for alerting system
            if hit:
                record_cache_hit(cache_key)
            else:
                record_cache_miss(cache_key)
    
    def record_api_operation(self, api_type: str = 'google_sheets', user_session: str = ""):
        """Record an API call"""
        if self._performance_enabled:
            performance_metrics.record_api_call(api_type, user_session)


def integrate_performance_monitoring(service_class, methods_to_track: Optional[list] = None):
    """
    Class decorator to automatically add performance monitoring to service methods.
    
    Args:
        service_class: The service class to enhance
        methods_to_track: List of method names to track (if None, tracks all public methods)
    
    Returns:
        Enhanced service class with performance monitoring
    """
    
    # Get methods to track
    if methods_to_track is None:
        methods_to_track = [
            method for method in dir(service_class)
            if not method.startswith('_') and callable(getattr(service_class, method))
        ]
    
    # Add performance tracking to specified methods
    for method_name in methods_to_track:
        if hasattr(service_class, method_name):
            original_method = getattr(service_class, method_name)
            if callable(original_method):
                # Create tracked version of the method
                tracked_method = track_performance(
                    endpoint_name=f"{service_class.__name__}.{method_name}",
                    track_errors=True
                )(original_method)
                
                # Replace the original method
                setattr(service_class, method_name, tracked_method)
    
    return service_class


class SheetsServicePerformanceWrapper:
    """
    Wrapper for SheetsService to add performance monitoring without modifying the original class.
    """
    
    def __init__(self, sheets_service):
        self._sheets_service = sheets_service
        self._wrap_methods()
    
    def _wrap_methods(self):
        """Wrap all public methods with performance monitoring"""
        methods_to_wrap = [
            'get_players', 'get_games', 'get_events', 'get_game_roster',
            'update_player', 'update_game', 'add_event'
        ]
        
        for method_name in methods_to_wrap:
            if hasattr(self._sheets_service, method_name):
                original_method = getattr(self._sheets_service, method_name)
                wrapped_method = self._create_wrapped_method(method_name, original_method)
                setattr(self, method_name, wrapped_method)
    
    def _create_wrapped_method(self, method_name: str, original_method):
        """Create a performance-monitored version of a method"""
        
        @functools.wraps(original_method)
        def wrapped_method(*args, **kwargs):
            endpoint_name = f"SheetsService.{method_name}"
            
            with PerformanceContext(endpoint_name):
                # Record API call for Google Sheets operations
                performance_metrics.record_api_call('google_sheets')
                
                # Execute original method
                result = original_method(*args, **kwargs)
                
                return result
        
        return wrapped_method
    
    def __getattr__(self, name):
        """Delegate attribute access to the wrapped service"""
        return getattr(self._sheets_service, name)


class DataServicePerformanceWrapper:
    """
    Wrapper for DataService to add performance monitoring.
    """
    
    def __init__(self, data_service):
        self._data_service = data_service
        self._wrap_methods()
    
    def _wrap_methods(self):
        """Wrap all public methods with performance monitoring"""
        methods_to_wrap = [
            'get_player_stats', 'get_team_stats', 'get_game_summary',
            'get_player_game_log', 'get_goalie_stats', 'calculate_team_standings'
        ]
        
        for method_name in methods_to_wrap:
            if hasattr(self._data_service, method_name):
                original_method = getattr(self._data_service, method_name)
                wrapped_method = self._create_wrapped_method(method_name, original_method)
                setattr(self, method_name, wrapped_method)
    
    def _create_wrapped_method(self, method_name: str, original_method):
        """Create a performance-monitored version of a method"""
        
        @functools.wraps(original_method)
        def wrapped_method(*args, **kwargs):
            endpoint_name = f"DataService.{method_name}"
            
            with PerformanceContext(endpoint_name):
                # Execute original method
                result = original_method(*args, **kwargs)
                
                return result
        
        return wrapped_method
    
    def __getattr__(self, name):
        """Delegate attribute access to the wrapped service"""
        return getattr(self._data_service, name)


def create_monitored_services(sheets_service, data_service):
    """
    Create performance-monitored versions of the core services.
    
    Args:
        sheets_service: Original SheetsService instance
        data_service: Original DataService instance
    
    Returns:
        Tuple of (monitored_sheets_service, monitored_data_service)
    """
    monitored_sheets = SheetsServicePerformanceWrapper(sheets_service)
    monitored_data = DataServicePerformanceWrapper(data_service)
    
    return monitored_sheets, monitored_data


# Utility functions for manual performance tracking
def track_user_action(action_name: str, user_session: str = ""):
    """
    Context manager for tracking user-initiated actions.
    
    Usage:
        with track_user_action("view_player_stats", session_id):
            # Handle user action
            pass
    """
    return PerformanceContext(f"user_action.{action_name}", user_session)


def get_performance_summary(time_window_minutes: int = 60) -> Dict[str, Any]:
    """Get current performance summary"""
    return performance_metrics.get_performance_summary(time_window_minutes)


def check_performance_alerts() -> list:
    """Check for any performance alerts"""
    alerts = performance_metrics.check_performance_thresholds()
    
    # Also check memory usage for alerting
    check_memory_usage()
    
    # Trigger manual alerting check
    try:
        alerting = get_alerting_integration()
        alerting.trigger_manual_check()
    except Exception:
        pass  # Alerting system may not be initialized
    
    return alerts