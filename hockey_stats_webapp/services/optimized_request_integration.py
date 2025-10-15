"""
Optimized Request Integration Module

This module integrates the batch request manager and request coalescing
with the existing sheets service to provide optimized API call patterns.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Future
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import logging

from .batch_request_manager import (
    BatchRequestManager, RequestPriority as BatchPriority, 
    SheetsServiceIntegration, get_batch_manager
)
from .request_coalescing import (
    RequestCoalescer, RequestPriority as CoalescePriority, 
    RequestType, get_request_coalescer
)


class OptimizedSheetsService:
    """
    Optimized wrapper for SheetsService that uses batch processing and request coalescing.
    
    This service provides the same interface as the original SheetsService but with
    significant performance improvements through intelligent request optimization.
    """
    
    def __init__(self, original_sheets_service):
        """
        Initialize with the original sheets service.
        
        Args:
            original_sheets_service: The original SheetsService instance
        """
        self.original_service = original_sheets_service
        
        # Initialize optimization components
        self.batch_manager = get_batch_manager()
        self.coalescer = get_request_coalescer()
        
        # Setup integration
        self.sheets_integration = SheetsServiceIntegration(
            original_sheets_service, self.batch_manager
        )
        
        # Performance tracking
        self.performance_metrics = {
            'total_requests': 0,
            'optimized_requests': 0,
            'cache_hits': 0,
            'api_calls_saved': 0,
            'average_response_time': 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Request routing configuration
        self.optimization_config = {
            'enable_batching': True,
            'enable_coalescing': True,
            'batch_size_threshold': 3,  # Use batching when 3+ similar requests
            'coalescing_window': 1.0,   # 1 second coalescing window
            'high_priority_methods': {'get_live_game_data', 'get_current_roster'},
            'batch_preferred_methods': {'get_players', 'get_games', 'get_events'},
            'coalesce_preferred_methods': {'get_player_stats', 'get_team_stats'}
        }
    
    def get_players(self, force_refresh: bool = False, **kwargs) -> pd.DataFrame:
        """
        Get players data with optimization.
        
        Args:
            force_refresh (bool): Force refresh from API
            **kwargs: Additional parameters
            
        Returns:
            pd.DataFrame: Players data
        """
        return self._execute_optimized_request(
            method='get_players',
            kwargs={'force_refresh': force_refresh, **kwargs},
            priority=self._determine_priority('get_players', kwargs),
            request_type=RequestType.READ,
            fallback=lambda: self.original_service.get_players(force_refresh, **kwargs)
        )
    
    def get_games(self, force_refresh: bool = False, **kwargs) -> pd.DataFrame:
        """
        Get games data with optimization.
        
        Args:
            force_refresh (bool): Force refresh from API
            **kwargs: Additional parameters
            
        Returns:
            pd.DataFrame: Games data
        """
        return self._execute_optimized_request(
            method='get_games',
            kwargs={'force_refresh': force_refresh, **kwargs},
            priority=self._determine_priority('get_games', kwargs),
            request_type=RequestType.READ,
            fallback=lambda: self.original_service.get_games(force_refresh, **kwargs)
        )
    
    def get_events(self, force_refresh: bool = False, **kwargs) -> pd.DataFrame:
        """
        Get events data with optimization.
        
        Args:
            force_refresh (bool): Force refresh from API
            **kwargs: Additional parameters
            
Returns:
            pd.DataFrame: Events data
        """
        return self._execute_optimized_request(
            method='get_events',
            kwargs={'force_refresh': force_refresh, **kwargs},
            priority=self._determine_priority('get_events', kwargs),
            request_type=RequestType.READ,
            fallback=lambda: self.original_service.get_events(force_refresh, **kwargs)
        )
    
    def get_game_roster(self, force_refresh: bool = False, **kwargs) -> pd.DataFrame:
        """
        Get game roster data with optimization.
        
        Args:
            force_refresh (bool): Force refresh from API
            **kwargs: Additional parameters
            
        Returns:
            pd.DataFrame: Game roster data
        """
        return self._execute_optimized_request(
            method='get_game_roster',
            kwargs={'force_refresh': force_refresh, **kwargs},
            priority=self._determine_priority('get_game_roster', kwargs),
            request_type=RequestType.READ,
            fallback=lambda: self.original_service.get_game_roster(force_refresh, **kwargs)
        )
    
    def update_player(self, player_data: Dict[str, Any], **kwargs) -> bool:
        """
        Update player data with optimization.
        
        Args:
            player_data (Dict): Player data to update
            **kwargs: Additional parameters
            
        Returns:
            bool: Success status
        """
        return self._execute_optimized_request(
            method='update_player',
            kwargs={'player_data': player_data, **kwargs},
            priority=CoalescePriority.HIGH,  # Updates are high priority
            request_type=RequestType.UPDATE,
            fallback=lambda: self.original_service.update_player(player_data, **kwargs)
        )
    
    def add_event(self, event_data: Dict[str, Any], **kwargs) -> bool:
        """
        Add event data with optimization.
        
        Args:
            event_data (Dict): Event data to add
            **kwargs: Additional parameters
            
        Returns:
            bool: Success status
        """
        return self._execute_optimized_request(
            method='add_event',
            kwargs={'event_data': event_data, **kwargs},
            priority=CoalescePriority.HIGH,  # Event additions are high priority
            request_type=RequestType.WRITE,
            fallback=lambda: self.original_service.add_event(event_data, **kwargs)
        )
    
    def _execute_optimized_request(self, method: str, kwargs: Dict[str, Any],
                                 priority: CoalescePriority, request_type: RequestType,
                                 fallback: callable) -> Any:
        """
        Execute a request using the optimal strategy (batching, coalescing, or direct).
        
        Args:
            method (str): Method name
            kwargs (Dict): Method arguments
            priority (CoalescePriority): Request priority
            request_type (RequestType): Type of request
            fallback (callable): Fallback function for direct execution
            
        Returns:
            Any: Request result
        """
        start_time = time.time()
        self.performance_metrics['total_requests'] += 1
        
        try:
            # Determine optimization strategy
            strategy = self._choose_optimization_strategy(method, kwargs, priority, request_type)
            
            if strategy == 'coalescing':
                result = self._execute_with_coalescing(method, kwargs, priority, request_type)
                self.performance_metrics['optimized_requests'] += 1
                
            elif strategy == 'batching':
                result = self._execute_with_batching(method, kwargs, priority)
                self.performance_metrics['optimized_requests'] += 1
                
            else:  # direct execution
                result = fallback()
            
            # Update performance metrics
            execution_time = time.time() - start_time
            self._update_response_time_metric(execution_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in optimized request execution for {method}: {e}")
            # Fallback to direct execution on error
            return fallback()
    
    def _choose_optimization_strategy(self, method: str, kwargs: Dict[str, Any],
                                    priority: CoalescePriority, request_type: RequestType) -> str:
        """
        Choose the optimal strategy for request execution.
        
        Args:
            method (str): Method name
            kwargs (Dict): Method arguments
            priority (CoalescePriority): Request priority
            request_type (RequestType): Type of request
            
        Returns:
            str: Strategy name ('coalescing', 'batching', 'direct')
        """
        # High priority requests go direct
        if priority == CoalescePriority.HIGH:
            return 'direct'
        
        # Force refresh requests go direct
        if kwargs.get('force_refresh', False):
            return 'direct'
        
        # Check if coalescing is preferred for this method
        if (self.optimization_config['enable_coalescing'] and 
            method in self.optimization_config['coalesce_preferred_methods']):
            return 'coalescing'
        
        # Check if batching is preferred for this method
        if (self.optimization_config['enable_batching'] and 
            method in self.optimization_config['batch_preferred_methods']):
            return 'batching'
        
        # Default to direct execution
        return 'direct'
    
    def _execute_with_coalescing(self, method: str, kwargs: Dict[str, Any],
                               priority: CoalescePriority, request_type: RequestType) -> Any:
        """Execute request using coalescing optimization."""
        future = self.coalescer.add_request(
            method=method,
            kwargs=kwargs,
            priority=priority,
            request_type=request_type,
            timeout=30.0
        )
        
        # Wait for result with timeout
        try:
            return future.result(timeout=35.0)
        except TimeoutError:
            self.logger.warning(f"Coalesced request timed out for {method}")
            raise
    
    def _execute_with_batching(self, method: str, kwargs: Dict[str, Any],
                             priority: CoalescePriority) -> Any:
        """Execute request using batch optimization."""
        # Convert priority
        batch_priority = self._convert_priority_to_batch(priority)
        
        future = self.batch_manager.add_request(
            method=method,
            kwargs=kwargs,
            priority=batch_priority,
            timeout=30.0
        )
        
        # Wait for result with timeout
        try:
            return future.result(timeout=35.0)
        except TimeoutError:
            self.logger.warning(f"Batched request timed out for {method}")
            raise
    
    def _determine_priority(self, method: str, kwargs: Dict[str, Any]) -> CoalescePriority:
        """Determine request priority based on method and parameters."""
        # High priority methods
        if method in self.optimization_config['high_priority_methods']:
            return CoalescePriority.HIGH
        
        # Force refresh is high priority
        if kwargs.get('force_refresh', False):
            return CoalescePriority.HIGH
        
        # Live/real-time data requests are high priority
        if kwargs.get('live_data', False) or kwargs.get('real_time', False):
            return CoalescePriority.HIGH
        
        # Default to medium priority
        return CoalescePriority.MEDIUM
    
    def _convert_priority_to_batch(self, coalesce_priority: CoalescePriority) -> BatchPriority:
        """Convert coalescing priority to batch priority."""
        mapping = {
            CoalescePriority.HIGH: BatchPriority.HIGH,
            CoalescePriority.MEDIUM: BatchPriority.MEDIUM,
            CoalescePriority.LOW: BatchPriority.LOW
        }
        return mapping.get(coalesce_priority, BatchPriority.MEDIUM)
    
    def _update_response_time_metric(self, execution_time: float):
        """Update average response time metric."""
        current_avg = self.performance_metrics['average_response_time']
        total_requests = self.performance_metrics['total_requests']
        
        # Calculate new average
        new_avg = ((current_avg * (total_requests - 1)) + execution_time) / total_requests
        self.performance_metrics['average_response_time'] = new_avg
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get comprehensive optimization metrics."""
        batch_metrics = self.batch_manager.get_queue_status()
        coalescing_metrics = self.coalescer.get_metrics()
        
        return {
            'service_metrics': self.performance_metrics.copy(),
            'batch_metrics': batch_metrics,
            'coalescing_metrics': coalescing_metrics,
            'optimization_ratio': (
                self.performance_metrics['optimized_requests'] / 
                max(self.performance_metrics['total_requests'], 1)
            )
        }
    
    def configure_optimization(self, **config_updates):
        """Update optimization configuration."""
        self.optimization_config.update(config_updates)
        self.logger.info(f"Optimization configuration updated: {config_updates}")
    
    def clear_caches(self):
        """Clear all optimization caches."""
        self.batch_manager.clear_cache()
        self.batch_manager.cleanup_expired_cache()
        self.logger.info("Optimization caches cleared")
    
    def shutdown(self):
        """Shutdown optimization services."""
        self.batch_manager.stop()
        self.coalescer.stop()
        self.logger.info("Optimized sheets service shutdown complete")
    
    # Delegate other methods to original service
    def __getattr__(self, name):
        """Delegate unknown methods to the original service."""
        return getattr(self.original_service, name)


class OptimizedServiceFactory:
    """Factory for creating optimized service instances."""
    
    @staticmethod
    def create_optimized_sheets_service(original_service) -> OptimizedSheetsService:
        """
        Create an optimized sheets service wrapper.
        
        Args:
            original_service: The original SheetsService instance
            
        Returns:
            OptimizedSheetsService: Optimized service wrapper
        """
        return OptimizedSheetsService(original_service)
    
    @staticmethod
    def create_with_custom_config(original_service, config: Dict[str, Any]) -> OptimizedSheetsService:
        """
        Create an optimized service with custom configuration.
        
        Args:
            original_service: The original SheetsService instance
            config (Dict): Custom optimization configuration
            
        Returns:
            OptimizedSheetsService: Optimized service wrapper with custom config
        """
        optimized_service = OptimizedSheetsService(original_service)
        optimized_service.configure_optimization(**config)
        return optimized_service


# Integration helper functions
def wrap_sheets_service_with_optimization(sheets_service):
    """
    Convenience function to wrap an existing sheets service with optimization.
    
    Args:
        sheets_service: Existing SheetsService instance
        
    Returns:
        OptimizedSheetsService: Optimized wrapper
    """
    return OptimizedServiceFactory.create_optimized_sheets_service(sheets_service)


def create_high_performance_config() -> Dict[str, Any]:
    """
    Create a high-performance optimization configuration.
    
    Returns:
        Dict: High-performance configuration
    """
    return {
        'enable_batching': True,
        'enable_coalescing': True,
        'batch_size_threshold': 2,  # More aggressive batching
        'coalescing_window': 0.5,   # Shorter coalescing window for faster response
        'high_priority_methods': {
            'get_live_game_data', 'get_current_roster', 'add_event', 'update_player'
        },
        'batch_preferred_methods': {
            'get_players', 'get_games', 'get_events', 'get_game_roster'
        },
        'coalesce_preferred_methods': {
            'get_player_stats', 'get_team_stats', 'get_season_summary'
        }
    }


def create_conservative_config() -> Dict[str, Any]:
    """
    Create a conservative optimization configuration for stability.
    
    Returns:
        Dict: Conservative configuration
    """
    return {
        'enable_batching': True,
        'enable_coalescing': False,  # Disable coalescing for simplicity
        'batch_size_threshold': 5,   # Higher threshold for batching
        'coalescing_window': 2.0,    # Longer window if coalescing is enabled
        'high_priority_methods': {
            'add_event', 'update_player', 'update_game'
        },
        'batch_preferred_methods': {
            'get_players', 'get_games'
        },
        'coalesce_preferred_methods': set()  # Empty set
    }