"""
Performance Monitoring Decorators

Provides decorators for automatic performance tracking of functions and methods.
"""

import time
import functools
from typing import Callable, Any, Optional
from .performance_metrics import performance_metrics


def track_performance(endpoint_name: Optional[str] = None, 
                     track_errors: bool = True,
                     user_session_key: str = None):
    """
    Decorator to automatically track performance metrics for functions.
    
    Args:
        endpoint_name: Custom name for the endpoint (defaults to function name)
        track_errors: Whether to track exceptions as errors
        user_session_key: Key in kwargs to extract user session ID
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Determine endpoint name
            endpoint = endpoint_name or f"{func.__module__}.{func.__name__}"
            
            # Extract user session if specified
            user_session = ""
            if user_session_key and user_session_key in kwargs:
                user_session = str(kwargs[user_session_key])
            
            # Track performance
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Record successful response time
                duration = time.time() - start_time
                performance_metrics.record_response_time(
                    endpoint=endpoint,
                    duration=duration,
                    user_session=user_session,
                    additional_data={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                
                return result
                
            except Exception as e:
                # Record error if tracking is enabled
                if track_errors:
                    performance_metrics.record_error(
                        endpoint=endpoint,
                        error_type=type(e).__name__,
                        user_session=user_session,
                        additional_data={
                            'function': func.__name__,
                            'error_message': str(e)
                        }
                    )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator


def track_cache_performance(cache_key_func: Optional[Callable] = None):
    """
    Decorator to track cache hit/miss performance.
    
    Args:
        cache_key_func: Function to extract cache key from function arguments
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Determine cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Execute function and track cache performance
            # This assumes the function returns (result, cache_hit_boolean)
            # or has a way to determine if it was a cache hit
            result = func(*args, **kwargs)
            
            # If function returns tuple with cache hit info
            if isinstance(result, tuple) and len(result) == 2:
                actual_result, cache_hit = result
                performance_metrics.record_cache_hit(
                    cache_key=cache_key,
                    hit=cache_hit
                )
                return actual_result
            else:
                # Assume cache miss if no hit info provided
                performance_metrics.record_cache_hit(
                    cache_key=cache_key,
                    hit=False
                )
                return result
        
        return wrapper
    return decorator


def track_api_calls(api_type: str = 'google_sheets'):
    """
    Decorator to track API calls for quota monitoring.
    
    Args:
        api_type: Type of API being called
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Record API call
            performance_metrics.record_api_call(api_type=api_type)
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class PerformanceContext:
    """
    Context manager for tracking performance of code blocks.
    """
    
    def __init__(self, endpoint_name: str, user_session: str = ""):
        self.endpoint_name = endpoint_name
        self.user_session = user_session
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            performance_metrics.record_response_time(
                endpoint=self.endpoint_name,
                duration=duration,
                user_session=self.user_session
            )
        
        # Track error if exception occurred
        if exc_type:
            performance_metrics.record_error(
                endpoint=self.endpoint_name,
                error_type=exc_type.__name__,
                user_session=self.user_session,
                additional_data={'error_message': str(exc_val)}
            )
        
        # Don't suppress exceptions
        return False