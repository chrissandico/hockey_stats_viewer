"""
Mobile Cache Integration Service

This service integrates mobile-specific caching with the existing hockey stats application,
providing seamless connection-aware caching and offline functionality.
"""

import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime

from .mobile_cache_service import (
    MobileCacheService, ConnectionType, DataPriority, 
    ConnectionProfile, UserBehaviorPattern
)
from .smart_cache_manager import SmartCacheManager
from .multi_level_cache import MultiLevelCache
from .sheets_service import SheetsService
from .data_service import DataService

logger = logging.getLogger(__name__)


class MobileCacheIntegration:
    """
    Integration service for mobile caching with the hockey stats application.
    """
    
    def __init__(self, 
                 sheets_service: SheetsService,
                 data_service: DataService,
                 cache_manager: SmartCacheManager,
                 multi_level_cache: MultiLevelCache):
        """
        Initialize mobile cache integration.
        
        Args:
            sheets_service: Google Sheets service
            data_service: Data processing service
            cache_manager: Smart cache manager
            multi_level_cache: Multi-level cache
        """
        self.sheets_service = sheets_service
        self.data_service = data_service
        self.cache_manager = cache_manager
        self.multi_level_cache = multi_level_cache
        
        # Initialize mobile cache service
        self.mobile_cache = MobileCacheService(
            cache_manager=cache_manager,
            multi_level_cache=multi_level_cache,
            max_offline_cache_mb=50,
            behavior_tracking_days=7
        )
        
        # Register preload strategies
        self._register_preload_strategies()
        
        # Track current session
        self.current_user_id = None
        self.current_team_id = None
        self.session_start_time = datetime.now()
        
        logger.info("MobileCacheIntegration initialized")
    
    def _register_preload_strategies(self):
        """Register preload strategies for common data types."""
        
        # Players data preload strategy
        def preload_players():
            try:
                return self.sheets_service.get_players(force_refresh=False)
            except Exception as e:
                logger.error(f"Error preloading players: {e}")
                return None
        
        # Teams data preload strategy
        def preload_teams():
            try:
                # Get unique teams from players data
                players_df = self.sheets_service.get_players(force_refresh=False)
                if players_df is not None:
                    return players_df['Team'].unique().tolist()
                return None
            except Exception as e:
                logger.error(f"Error preloading teams: {e}")
                return None
        
        # Games data preload strategy
        def preload_games():
            try:
                return self.sheets_service.get_games(force_refresh=False)
            except Exception as e:
                logger.error(f"Error preloading games: {e}")
                return None
        
        # Register strategies
        self.mobile_cache.register_preload_strategy('players', preload_players)
        self.mobile_cache.register_preload_strategy('teams', preload_teams)
        self.mobile_cache.register_preload_strategy('games', preload_games)
    
    def set_connection_profile(self,
                             connection_type: str,
                             bandwidth_kbps: int = 0,
                             latency_ms: int = 0,
                             is_metered: bool = False,
                             data_saver_mode: bool = False):
        """
        Set current connection profile for mobile optimization.
        
        Args:
            connection_type: Type of connection ('wifi', '4g', '3g', '2g', 'offline')
            bandwidth_kbps: Available bandwidth in kbps
            latency_ms: Network latency in milliseconds
            is_metered: Whether connection is metered
            data_saver_mode: Whether user has data saver enabled
        """
        try:
            conn_type = ConnectionType(connection_type.lower())
        except ValueError:
            conn_type = ConnectionType.UNKNOWN
            logger.warning(f"Unknown connection type: {connection_type}")
        
        self.mobile_cache.update_connection_profile(
            connection_type=conn_type,
            bandwidth_kbps=bandwidth_kbps,
            latency_ms=latency_ms,
            is_metered=is_metered,
            data_saver_mode=data_saver_mode
        )
        
        logger.info(f"Connection profile updated: {connection_type}")
    
    def set_user_session(self, user_id: str, team_id: str):
        """
        Set current user session for behavior tracking.
        
        Args:
            user_id: User identifier
            team_id: Team identifier
        """
        self.current_user_id = user_id
        self.current_team_id = team_id
        self.session_start_time = datetime.now()
        
        # Preload critical data for this team
        self._preload_team_critical_data(team_id)
        
        logger.info(f"User session set: {user_id} - {team_id}")
    
    def _preload_team_critical_data(self, team_id: str):
        """Preload critical data for a specific team."""
        critical_data_keys = [
            f'team_roster_{team_id}',
            f'team_games_{team_id}',
            f'team_stats_{team_id}'
        ]
        
        for key in critical_data_keys:
            try:
                if key.startswith('team_roster'):
                    data = self.data_service.get_team_roster(team_id)
                elif key.startswith('team_games'):
                    data = self.data_service.get_team_games(team_id)
                elif key.startswith('team_stats'):
                    data = self.data_service.get_team_stats(team_id)
                else:
                    continue
                
                if data is not None:
                    self.mobile_cache.cache_with_mobile_strategy(
                        key, data, DataPriority.CRITICAL
                    )
            except Exception as e:
                logger.error(f"Error preloading {key}: {e}")
    
    def get_players_mobile_optimized(self, 
                                   team_id: Optional[str] = None,
                                   force_refresh: bool = False) -> Optional[Any]:
        """
        Get players data with mobile optimization.
        
        Args:
            team_id: Optional team filter
            force_refresh: Force refresh from source
            
        Returns:
            Players data or None
        """
        cache_key = f'players_{team_id}' if team_id else 'players'
        
        # Track user behavior
        if self.current_user_id and self.current_team_id:
            self.mobile_cache.track_user_behavior(
                user_id=self.current_user_id,
                team_id=self.current_team_id,
                page='player_stats',
                data_types={'players', 'roster'}
            )
        
        # Try mobile cache first
        if not force_refresh:
            cached_data = self.mobile_cache.get_with_mobile_strategy(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Fetch from source with connection awareness
        try:
            data = self.sheets_service.get_players(force_refresh=force_refresh)
            if data is not None:
                # Filter by team if specified
                if team_id:
                    data = data[data['Team'] == team_id]
                
                # Cache with appropriate priority
                priority = DataPriority.HIGH if team_id == self.current_team_id else DataPriority.MEDIUM
                self.mobile_cache.cache_with_mobile_strategy(cache_key, data, priority)
                
                return data
        except Exception as e:
            logger.error(f"Error fetching players data: {e}")
            
            # Try to return stale cached data as fallback
            cached_data = self.mobile_cache.get_with_mobile_strategy(cache_key)
            if cached_data is not None:
                logger.info("Returning stale cached data due to fetch error")
                return cached_data
        
        return None
    
    def get_games_mobile_optimized(self,
                                 team_id: Optional[str] = None,
                                 game_type: Optional[str] = None,
                                 force_refresh: bool = False) -> Optional[Any]:
        """
        Get games data with mobile optimization.
        
        Args:
            team_id: Optional team filter
            game_type: Optional game type filter
            force_refresh: Force refresh from source
            
        Returns:
            Games data or None
        """
        cache_key = f'games_{team_id}_{game_type}' if team_id and game_type else f'games_{team_id or "all"}'
        
        # Track user behavior
        if self.current_user_id and self.current_team_id:
            self.mobile_cache.track_user_behavior(
                user_id=self.current_user_id,
                team_id=self.current_team_id,
                page='game_summary',
                data_types={'games', 'schedule'}
            )
        
        # Try mobile cache first
        if not force_refresh:
            cached_data = self.mobile_cache.get_with_mobile_strategy(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Fetch from source
        try:
            data = self.sheets_service.get_games(force_refresh=force_refresh)
            if data is not None:
                # Apply filters
                if team_id:
                    data = data[(data['HomeTeam'] == team_id) | (data['AwayTeam'] == team_id)]
                if game_type:
                    data = data[data['GameType'] == game_type]
                
                # Cache with appropriate priority
                priority = DataPriority.HIGH if team_id == self.current_team_id else DataPriority.MEDIUM
                self.mobile_cache.cache_with_mobile_strategy(cache_key, data, priority)
                
                return data
        except Exception as e:
            logger.error(f"Error fetching games data: {e}")
            
            # Try to return stale cached data as fallback
            cached_data = self.mobile_cache.get_with_mobile_strategy(cache_key)
            if cached_data is not None:
                logger.info("Returning stale cached data due to fetch error")
                return cached_data
        
        return None
    
    def get_player_stats_mobile_optimized(self,
                                        player_id: Optional[int] = None,
                                        team_id: Optional[str] = None,
                                        force_refresh: bool = False) -> Optional[Any]:
        """
        Get player statistics with mobile optimization.
        
        Args:
            player_id: Optional player filter
            team_id: Optional team filter
            force_refresh: Force refresh from source
            
        Returns:
            Player stats data or None
        """
        cache_key = f'player_stats_{player_id}_{team_id}' if player_id and team_id else f'player_stats_{team_id or "all"}'
        
        # Track user behavior
        if self.current_user_id and self.current_team_id:
            self.mobile_cache.track_user_behavior(
                user_id=self.current_user_id,
                team_id=self.current_team_id,
                page='player_stats',
                data_types={'player_stats', 'statistics'}
            )
        
        # Try mobile cache first
        if not force_refresh:
            cached_data = self.mobile_cache.get_with_mobile_strategy(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Fetch and calculate stats
        try:
            # Get required data
            players_df = self.sheets_service.get_players(force_refresh=force_refresh)
            games_df = self.sheets_service.get_games(force_refresh=force_refresh)
            events_df = self.sheets_service.get_events(force_refresh=force_refresh)
            
            if players_df is not None and games_df is not None and events_df is not None:
                # Calculate stats using data service
                stats = self.data_service.calculate_player_stats(
                    players_df, games_df, events_df, team_id, player_id
                )
                
                if stats is not None:
                    # Cache with appropriate priority
                    priority = DataPriority.HIGH if team_id == self.current_team_id else DataPriority.MEDIUM
                    self.mobile_cache.cache_with_mobile_strategy(cache_key, stats, priority)
                    
                    return stats
        except Exception as e:
            logger.error(f"Error calculating player stats: {e}")
            
            # Try to return stale cached data as fallback
            cached_data = self.mobile_cache.get_with_mobile_strategy(cache_key)
            if cached_data is not None:
                logger.info("Returning stale cached stats due to calculation error")
                return cached_data
        
        return None
    
    def detect_connection_from_request(self, request_headers: Dict[str, str]):
        """
        Detect connection type from HTTP request headers.
        
        Args:
            request_headers: HTTP request headers
        """
        # Check for mobile user agents
        user_agent = request_headers.get('User-Agent', '').lower()
        is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad'])
        
        # Check for connection hints
        connection_type = ConnectionType.UNKNOWN
        bandwidth_kbps = 0
        latency_ms = 0
        
        # Check for network information API headers (if available)
        if 'Downlink' in request_headers:
            try:
                downlink_mbps = float(request_headers['Downlink'])
                bandwidth_kbps = int(downlink_mbps * 1000)
                if downlink_mbps > 10:
                    connection_type = ConnectionType.WIFI
                elif downlink_mbps > 2:
                    connection_type = ConnectionType.CELLULAR_4G
                elif downlink_mbps > 0.5:
                    connection_type = ConnectionType.CELLULAR_3G
                else:
                    connection_type = ConnectionType.CELLULAR_2G
            except ValueError:
                pass
        
        # Check for RTT (Round Trip Time) header
        if 'RTT' in request_headers:
            try:
                latency_ms = int(request_headers['RTT'])
            except ValueError:
                pass
        
        # Check for effective connection type header
        if 'ECT' in request_headers:
            ect = request_headers['ECT'].lower()
            if ect == '4g':
                connection_type = ConnectionType.CELLULAR_4G
            elif ect == '3g':
                connection_type = ConnectionType.CELLULAR_3G
            elif ect == '2g':
                connection_type = ConnectionType.CELLULAR_2G
            elif ect == 'slow-2g':
                connection_type = ConnectionType.CELLULAR_2G
        
        # Check for data saver hints
        data_saver_mode = (
            request_headers.get('Save-Data', '').lower() == 'on' or
            'lite' in user_agent or
            'mini' in user_agent or
            'opera mini' in user_agent
        )
        
        # Update connection profile if mobile or connection info available
        if is_mobile or connection_type != ConnectionType.UNKNOWN:
            self.set_connection_profile(
                connection_type=connection_type.value,
                bandwidth_kbps=bandwidth_kbps,
                latency_ms=latency_ms,
                is_metered=is_mobile,  # Assume mobile connections are metered
                data_saver_mode=data_saver_mode
            )
            
            # Trigger cache warming for new connection
            self.mobile_cache.warm_cache_for_connection()
    
    def auto_optimize_for_request(self, request_headers: Dict[str, str], user_id: str, team_id: str):
        """
        Automatically optimize caching based on request characteristics.
        
        Args:
            request_headers: HTTP request headers
            user_id: User identifier
            team_id: Team identifier
        """
        # Detect connection from request
        self.detect_connection_from_request(request_headers)
        
        # Set user session
        self.set_user_session(user_id, team_id)
        
        # Apply mobile optimizations
        self.optimize_for_mobile_session()
        
        logger.info(f"Auto-optimized for user {user_id} on team {team_id}")
    
    def get_connection_adaptive_data(self, 
                                   data_type: str,
                                   team_id: str,
                                   **kwargs) -> Optional[Any]:
        """
        Get data with connection-adaptive caching strategy.
        
        Args:
            data_type: Type of data to retrieve
            team_id: Team identifier
            **kwargs: Additional parameters
            
        Returns:
            Data optimized for current connection
        """
        # Determine cache strategy based on connection
        connection = self.mobile_cache.current_connection
        
        if connection.connection_type == ConnectionType.OFFLINE:
            # Offline mode - only return cached data
            return self._get_offline_only_data(data_type, team_id, **kwargs)
        elif connection.is_slow_connection or connection.data_saver_mode:
            # Slow connection - prioritize cached data, minimal fresh fetches
            return self._get_cache_first_data(data_type, team_id, **kwargs)
        else:
            # Fast connection - balance fresh and cached data
            return self._get_balanced_data(data_type, team_id, **kwargs)
    
    def _get_offline_only_data(self, data_type: str, team_id: str, **kwargs) -> Optional[Any]:
        """Get data in offline-only mode."""
        cache_key = f'{data_type}_{team_id}'
        return self.mobile_cache.get_with_mobile_strategy(cache_key)
    
    def _get_cache_first_data(self, data_type: str, team_id: str, **kwargs) -> Optional[Any]:
        """Get data with cache-first strategy for slow connections."""
        cache_key = f'{data_type}_{team_id}'
        
        # Try cache first
        cached_data = self.mobile_cache.get_with_mobile_strategy(cache_key)
        if cached_data is not None:
            return cached_data
        
        # If no cache, fetch minimal data
        if data_type == 'players':
            return self.get_players_mobile_optimized(team_id, force_refresh=False)
        elif data_type == 'games':
            return self.get_games_mobile_optimized(team_id, force_refresh=False)
        elif data_type == 'player_stats':
            player_id = kwargs.get('player_id')
            return self.get_player_stats_mobile_optimized(player_id, team_id, force_refresh=False)
        
        return None
    
    def _get_balanced_data(self, data_type: str, team_id: str, **kwargs) -> Optional[Any]:
        """Get data with balanced fresh/cached strategy for fast connections."""
        # For fast connections, allow some fresh fetches but still prefer cache
        force_refresh = kwargs.get('force_refresh', False)
        
        if data_type == 'players':
            return self.get_players_mobile_optimized(team_id, force_refresh=force_refresh)
        elif data_type == 'games':
            game_type = kwargs.get('game_type')
            return self.get_games_mobile_optimized(team_id, game_type, force_refresh=force_refresh)
        elif data_type == 'player_stats':
            player_id = kwargs.get('player_id')
            return self.get_player_stats_mobile_optimized(player_id, team_id, force_refresh=force_refresh)
        
        return None
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        mobile_stats = self.mobile_cache.get_mobile_cache_stats()
        multi_level_stats = self.multi_level_cache.get_comprehensive_stats()
        smart_cache_stats = self.cache_manager.get_stats()
        
        return {
            'mobile_cache': mobile_stats,
            'multi_level_cache': multi_level_stats,
            'smart_cache': smart_cache_stats,
            'session_info': {
                'user_id': self.current_user_id,
                'team_id': self.current_team_id,
                'session_duration_minutes': (datetime.now() - self.session_start_time).total_seconds() / 60
            }
        }
    
    def clear_all_caches(self):
        """Clear all caches."""
        self.mobile_cache.clear_mobile_cache()
        self.multi_level_cache.clear()
        self.cache_manager.clear()
        logger.info("All caches cleared")
    
    def optimize_for_mobile_session(self):
        """Optimize caching for mobile session."""
        # Ensure critical data is cached
        if self.current_team_id:
            self._preload_team_critical_data(self.current_team_id)
        
        # Start intelligent preloading if on good connection
        if self.mobile_cache.current_connection.is_fast_connection:
            self.mobile_cache._start_intelligent_preloading()
        
        logger.info("Mobile session optimization applied")