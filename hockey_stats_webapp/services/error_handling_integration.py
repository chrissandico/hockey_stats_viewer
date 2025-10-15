"""
Error Handling Integration

This module integrates circuit breaker, retry logic, and graceful degradation
to provide comprehensive error handling for the hockey stats application.

Requirements addressed: 2.2, 2.3, 2.4
"""

import logging
from typing import Callable, Any, Optional, Dict
from .circuit_breaker import GoogleSheetsCircuitBreaker, CircuitBreakerError
from .retry_manager import GoogleSheetsRetryManager
from .graceful_degradation import HockeyStatsGracefulDegradation

logger = logging.getLogger(__name__)


class RobustServiceManager:
    """
    Combines circuit breaker, retry logic, and graceful degradation
    for robust service calls with comprehensive error handling.
    """
    
    def __init__(self):
        self.circuit_breaker = GoogleSheetsCircuitBreaker()
        self.retry_manager = GoogleSheetsRetryManager()
        self.degradation_manager = HockeyStatsGracefulDegradation()
        
        logger.info("Robust service manager initialized with all error handling components")
    
    def call_service_robustly(self, 
                            service_name: str,
                            func: Callable,
                            fallback_key: str,
                            *args, 
                            **kwargs) -> tuple[Any, Dict[str, Any]]:
        """
        Execute a service call with full error handling pipeline.
        
        Args:
            service_name: Name of the service being called
            func: Function to execute
            fallback_key: Key for cached fallback data
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Tuple of (result, metadata) where metadata contains:
            - is_from_cache: bool
            - circuit_breaker_state: str
            - retry_attempts: int
            - service_status: str
        """
        metadata = {
            'is_from_cache': False,
            'circuit_breaker_state': self.circuit_breaker.get_state()['state'],
            'retry_attempts': 0,
            'service_status': 'unknown',
            'error_occurred': False,
            'error_message': None
        }
        
        def robust_call():
            """Inner function that combines circuit breaker and retry logic"""
            def circuit_protected_call():
                return self.circuit_breaker.call_sheets_api(func, *args, **kwargs)
            
            return self.retry_manager.retry_sheets_call(circuit_protected_call)
        
        try:
            # Execute with graceful degradation
            result, is_from_cache = self.degradation_manager.execute_with_fallback(
                service_name=service_name,
                primary_func=robust_call,
                fallback_key=fallback_key
            )
            
            metadata.update({
                'is_from_cache': is_from_cache,
                'service_status': 'available' if not is_from_cache else 'degraded',
                'circuit_breaker_state': self.circuit_breaker.get_state()['state']
            })
            
            return result, metadata
            
        except Exception as e:
            logger.error(f"Robust service call failed completely for {service_name}: {e}")
            
            metadata.update({
                'error_occurred': True,
                'error_message': str(e),
                'service_status': 'unavailable',
                'circuit_breaker_state': self.circuit_breaker.get_state()['state']
            })
            
            raise
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information"""
        return {
            'circuit_breaker': self.circuit_breaker.get_state(),
            'retry_manager': self.retry_manager.get_stats(),
            'degradation_manager': self.degradation_manager.get_service_status_summary(),
            'user_notifications': self.degradation_manager.get_user_notifications()
        }
    
    def reset_error_handling(self):
        """Reset all error handling components"""
        self.circuit_breaker.reset()
        self.degradation_manager.clear_old_errors()
        self.degradation_manager.clear_old_cache()
        logger.info("All error handling components reset")


class GoogleSheetsRobustService:
    """
    Robust wrapper for Google Sheets service calls with comprehensive error handling.
    
    This class provides a high-level interface for making Google Sheets API calls
    with built-in circuit breaker, retry logic, and graceful degradation.
    """
    
    def __init__(self, sheets_service):
        self.sheets_service = sheets_service
        self.robust_manager = RobustServiceManager()
        
        logger.info("Google Sheets robust service initialized")
    
    def get_players_robust(self, force_refresh: bool = False) -> tuple[Any, Dict[str, Any]]:
        """Get players data with robust error handling"""
        return self.robust_manager.call_service_robustly(
            service_name="google_sheets_players",
            func=lambda: self.sheets_service.get_players(force_refresh),
            fallback_key="players_data"
        )
    
    def get_games_robust(self, force_refresh: bool = False) -> tuple[Any, Dict[str, Any]]:
        """Get games data with robust error handling"""
        return self.robust_manager.call_service_robustly(
            service_name="google_sheets_games",
            func=lambda: self.sheets_service.get_games(force_refresh),
            fallback_key="games_data"
        )
    
    def get_events_robust(self, force_refresh: bool = False) -> tuple[Any, Dict[str, Any]]:
        """Get events data with robust error handling"""
        return self.robust_manager.call_service_robustly(
            service_name="google_sheets_events",
            func=lambda: self.sheets_service.get_events(force_refresh),
            fallback_key="events_data"
        )
    
    def get_game_roster_robust(self, force_refresh: bool = False) -> tuple[Any, Dict[str, Any]]:
        """Get game roster data with robust error handling"""
        return self.robust_manager.call_service_robustly(
            service_name="google_sheets_roster",
            func=lambda: self.sheets_service.get_game_roster(force_refresh),
            fallback_key="game_roster_data"
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health information"""
        return self.robust_manager.get_system_health()
    
    def get_user_notifications(self) -> list[Dict[str, Any]]:
        """Get user-friendly notifications about service issues"""
        return self.robust_manager.degradation_manager.get_user_notifications()
    
    def reset_error_handling(self):
        """Reset all error handling components"""
        self.robust_manager.reset_error_handling()


# Convenience functions for easy integration
def create_robust_sheets_service(sheets_service):
    """Create a robust wrapper for a sheets service"""
    return GoogleSheetsRobustService(sheets_service)


def with_robust_error_handling(service_name: str, fallback_key: str):
    """
    Decorator for adding robust error handling to any function.
    
    Args:
        service_name: Name of the service for monitoring
        fallback_key: Key for cached fallback data
        
    Returns:
        Decorator function
    """
    robust_manager = RobustServiceManager()
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            result, metadata = robust_manager.call_service_robustly(
                service_name=service_name,
                func=func,
                fallback_key=fallback_key,
                *args,
                **kwargs
            )
            return result
        return wrapper
    return decorator