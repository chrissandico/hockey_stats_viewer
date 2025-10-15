"""
Graceful Degradation Implementation

This module provides graceful degradation capabilities when services are unavailable,
including fallback to cached data and user-friendly error handling.

Requirements addressed: 2.3, 2.4
"""

import time
import logging
from typing import Any, Optional, Dict, Callable, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service availability status"""
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class FallbackData:
    """Container for fallback data with metadata"""
    data: Any
    timestamp: float
    source: str
    is_stale: bool = False
    
    @property
    def age_seconds(self) -> float:
        """Get age of the data in seconds"""
        return time.time() - self.timestamp
    
    @property
    def age_minutes(self) -> int:
        """Get age of the data in minutes"""
        return int(self.age_seconds / 60)


@dataclass
class ServiceError:
    """Container for service error information"""
    error_type: str
    message: str
    timestamp: float
    recovery_suggestion: str
    user_message: str


class GracefulDegradationManager:
    """
    Manages graceful degradation when services are unavailable.
    
    Provides fallback mechanisms, user-friendly error messages,
    and partial functionality when some services are down.
    """
    
    def __init__(self):
        self.service_status: Dict[str, ServiceStatus] = {}
        self.fallback_cache: Dict[str, FallbackData] = {}
        self.error_messages: Dict[str, ServiceError] = {}
        self.stale_data_threshold = 3600  # 1 hour in seconds
        
        logger.info("Graceful degradation manager initialized")
    
    def execute_with_fallback(self, 
                            service_name: str,
                            primary_func: Callable,
                            fallback_key: str,
                            *args, 
                            **kwargs) -> tuple[Any, bool]:
        """
        Execute a function with fallback to cached data if it fails.
        
        Args:
            service_name: Name of the service being called
            primary_func: Primary function to execute
            fallback_key: Key for cached fallback data
            *args: Arguments for the primary function
            **kwargs: Keyword arguments for the primary function
            
        Returns:
            Tuple of (result, is_from_cache)
        """
        try:
            # Try primary function
            result = primary_func(*args, **kwargs)
            
            # Update service status and cache the result
            self._update_service_status(service_name, ServiceStatus.AVAILABLE)
            self._cache_fallback_data(fallback_key, result, "primary_service")
            
            return result, False
            
        except Exception as e:
            logger.warning(f"Primary service {service_name} failed: {e}")
            
            # Update service status
            self._update_service_status(service_name, ServiceStatus.UNAVAILABLE)
            
            # Try to get fallback data
            fallback_data = self._get_fallback_data(fallback_key)
            
            if fallback_data:
                logger.info(f"Using fallback data for {service_name} (age: {fallback_data.age_minutes} minutes)")
                
                # Create error record for user notification
                self._record_service_error(
                    service_name, 
                    type(e).__name__, 
                    str(e),
                    self._get_recovery_suggestion(service_name, e),
                    self._get_user_friendly_message(service_name, fallback_data)
                )
                
                return fallback_data.data, True
            else:
                logger.error(f"No fallback data available for {service_name}")
                
                # Create error record without fallback
                self._record_service_error(
                    service_name,
                    type(e).__name__,
                    str(e),
                    self._get_recovery_suggestion(service_name, e),
                    self._get_no_fallback_message(service_name)
                )
                
                raise
    
    def get_partial_functionality_data(self, 
                                     service_requests: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Execute multiple service requests and return partial results.
        
        Args:
            service_requests: Dictionary of service_name -> function mappings
            
        Returns:
            Dictionary of service_name -> result mappings (None for failed services)
        """
        results = {}
        
        for service_name, func in service_requests.items():
            try:
                result = func()
                results[service_name] = result
                self._update_service_status(service_name, ServiceStatus.AVAILABLE)
                
            except Exception as e:
                logger.warning(f"Service {service_name} unavailable: {e}")
                results[service_name] = None
                self._update_service_status(service_name, ServiceStatus.UNAVAILABLE)
                
                # Try to get cached data
                cached_data = self._get_fallback_data(service_name)
                if cached_data:
                    results[service_name] = cached_data.data
                    self._update_service_status(service_name, ServiceStatus.DEGRADED)
        
        return results
    
    def _update_service_status(self, service_name: str, status: ServiceStatus):
        """Update the status of a service"""
        old_status = self.service_status.get(service_name)
        self.service_status[service_name] = status
        
        if old_status != status:
            logger.info(f"Service {service_name} status changed: {old_status} -> {status}")
    
    def _cache_fallback_data(self, key: str, data: Any, source: str):
        """Cache data for potential fallback use"""
        self.fallback_cache[key] = FallbackData(
            data=data,
            timestamp=time.time(),
            source=source
        )
        
        logger.debug(f"Cached fallback data for key: {key}")
    
    def _get_fallback_data(self, key: str) -> Optional[FallbackData]:
        """Get fallback data from cache"""
        if key not in self.fallback_cache:
            return None
        
        fallback_data = self.fallback_cache[key]
        
        # Check if data is stale
        if fallback_data.age_seconds > self.stale_data_threshold:
            fallback_data.is_stale = True
        
        return fallback_data
    
    def _record_service_error(self, 
                            service_name: str, 
                            error_type: str, 
                            message: str,
                            recovery_suggestion: str,
                            user_message: str):
        """Record service error for user notification"""
        self.error_messages[service_name] = ServiceError(
            error_type=error_type,
            message=message,
            timestamp=time.time(),
            recovery_suggestion=recovery_suggestion,
            user_message=user_message
        )
    
    def _get_recovery_suggestion(self, service_name: str, error: Exception) -> str:
        """Get recovery suggestion based on error type"""
        error_type = type(error).__name__
        
        suggestions = {
            'ConnectionError': 'Check your internet connection and try again.',
            'TimeoutError': 'The service is responding slowly. Please wait a moment and try again.',
            'HTTPError': 'There may be a temporary service issue. Please try again in a few minutes.',
            'AuthenticationError': 'Please check your credentials and try logging in again.',
            'PermissionError': 'You may not have permission to access this data. Contact your administrator.',
            'RateLimitError': 'Too many requests. Please wait a moment before trying again.',
        }
        
        return suggestions.get(error_type, 'Please try again later or contact support if the problem persists.')
    
    def _get_user_friendly_message(self, service_name: str, fallback_data: FallbackData) -> str:
        """Get user-friendly message when using fallback data"""
        age_text = self._format_age(fallback_data.age_seconds)
        
        if fallback_data.is_stale:
            return (f"We're having trouble connecting to our data service. "
                   f"Showing cached data from {age_text} ago. "
                   f"Some information may be outdated.")
        else:
            return (f"We're having trouble connecting to our data service. "
                   f"Showing recent data from {age_text} ago.")
    
    def _get_no_fallback_message(self, service_name: str) -> str:
        """Get user-friendly message when no fallback data is available"""
        return (f"We're unable to connect to our data service and don't have "
               f"recent cached data available. Please check your connection and try again.")
    
    def _format_age(self, age_seconds: float) -> str:
        """Format age in human-readable format"""
        if age_seconds < 60:
            return f"{int(age_seconds)} seconds"
        elif age_seconds < 3600:
            return f"{int(age_seconds / 60)} minutes"
        else:
            return f"{int(age_seconds / 3600)} hours"
    
    def get_service_status_summary(self) -> Dict[str, Any]:
        """Get summary of all service statuses"""
        return {
            'services': {
                name: {
                    'status': status.value,
                    'has_error': name in self.error_messages,
                    'has_fallback': any(key.startswith(name) for key in self.fallback_cache.keys())
                }
                for name, status in self.service_status.items()
            },
            'overall_health': self._calculate_overall_health(),
            'error_count': len(self.error_messages),
            'cached_data_count': len(self.fallback_cache)
        }
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        if not self.service_status:
            return "UNKNOWN"
        
        statuses = list(self.service_status.values())
        available_count = sum(1 for s in statuses if s == ServiceStatus.AVAILABLE)
        degraded_count = sum(1 for s in statuses if s == ServiceStatus.DEGRADED)
        
        total = len(statuses)
        
        if available_count == total:
            return "HEALTHY"
        elif available_count + degraded_count >= total * 0.7:
            return "DEGRADED"
        else:
            return "UNHEALTHY"
    
    def get_user_notifications(self) -> list[Dict[str, Any]]:
        """Get user-friendly notifications about service issues"""
        notifications = []
        
        for service_name, error in self.error_messages.items():
            # Only show recent errors (last 5 minutes)
            if time.time() - error.timestamp < 300:
                notifications.append({
                    'type': 'warning' if service_name in self.fallback_cache else 'error',
                    'service': service_name,
                    'message': error.user_message,
                    'recovery_suggestion': error.recovery_suggestion,
                    'timestamp': error.timestamp
                })
        
        return notifications
    
    def clear_old_errors(self, max_age_seconds: int = 300):
        """Clear old error messages"""
        current_time = time.time()
        
        old_errors = [
            service for service, error in self.error_messages.items()
            if current_time - error.timestamp > max_age_seconds
        ]
        
        for service in old_errors:
            del self.error_messages[service]
            logger.debug(f"Cleared old error for service: {service}")
    
    def clear_old_cache(self, max_age_seconds: int = 7200):  # 2 hours
        """Clear old cached data"""
        current_time = time.time()
        
        old_cache_keys = [
            key for key, data in self.fallback_cache.items()
            if current_time - data.timestamp > max_age_seconds
        ]
        
        for key in old_cache_keys:
            del self.fallback_cache[key]
            logger.debug(f"Cleared old cache for key: {key}")


class HockeyStatsGracefulDegradation(GracefulDegradationManager):
    """
    Hockey stats specific graceful degradation manager.
    
    Provides hockey-specific fallback strategies and error messages.
    """
    
    def __init__(self):
        super().__init__()
        self.stale_data_threshold = 1800  # 30 minutes for hockey stats
    
    def get_player_stats_with_fallback(self, player_id: str, sheets_func: Callable) -> tuple[Any, bool]:
        """Get player stats with fallback to cached data"""
        return self.execute_with_fallback(
            service_name="google_sheets_players",
            primary_func=sheets_func,
            fallback_key=f"player_stats_{player_id}"
        )
    
    def get_team_stats_with_fallback(self, team_id: str, sheets_func: Callable) -> tuple[Any, bool]:
        """Get team stats with fallback to cached data"""
        return self.execute_with_fallback(
            service_name="google_sheets_teams",
            primary_func=sheets_func,
            fallback_key=f"team_stats_{team_id}"
        )
    
    def get_game_data_with_fallback(self, game_id: str, sheets_func: Callable) -> tuple[Any, bool]:
        """Get game data with fallback to cached data"""
        return self.execute_with_fallback(
            service_name="google_sheets_games",
            primary_func=sheets_func,
            fallback_key=f"game_data_{game_id}"
        )
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data with partial functionality"""
        service_requests = {
            'players': lambda: self._get_players_data(),
            'teams': lambda: self._get_teams_data(),
            'games': lambda: self._get_games_data(),
            'standings': lambda: self._get_standings_data()
        }
        
        return self.get_partial_functionality_data(service_requests)
    
    def _get_players_data(self):
        """Placeholder for players data retrieval"""
        # This would be implemented to call the actual sheets service
        raise NotImplementedError("To be implemented with actual sheets service")
    
    def _get_teams_data(self):
        """Placeholder for teams data retrieval"""
        # This would be implemented to call the actual sheets service
        raise NotImplementedError("To be implemented with actual sheets service")
    
    def _get_games_data(self):
        """Placeholder for games data retrieval"""
        # This would be implemented to call the actual sheets service
        raise NotImplementedError("To be implemented with actual sheets service")
    
    def _get_standings_data(self):
        """Placeholder for standings data retrieval"""
        # This would be implemented to call the actual sheets service
        raise NotImplementedError("To be implemented with actual sheets service")