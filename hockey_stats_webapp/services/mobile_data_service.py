"""
Mobile Data Service Integration

This service integrates data compression and optimization with the existing data service
to provide mobile-optimized data delivery.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from datetime import datetime

from .mobile_compression import MobileCompressionService
from .image_optimization import ImageOptimizationService

logger = logging.getLogger(__name__)

class MobileDataService:
    """
    Service that integrates mobile optimizations with data delivery.
    Provides compressed, lightweight data formats for mobile clients.
    """
    
    def __init__(self, data_service=None):
        """
        Initialize the mobile data service.
        
        Args:
            data_service: The main data service instance
        """
        self.data_service = data_service
        self.compression_service = MobileCompressionService()
        self.image_service = ImageOptimizationService()
        
        # Mobile optimization settings
        self.mobile_mode = False
        self.connection_type = 'wifi'  # 'wifi', '4g', '3g', 'slow'
        self.data_saver_mode = False
        
        # Performance tracking
        self.request_stats = {
            'total_requests': 0,
            'compressed_responses': 0,
            'bandwidth_saved': 0,
            'average_compression_ratio': 0
        }
    
    def set_mobile_mode(self, enabled: bool, connection_type: str = 'wifi', 
                       data_saver: bool = False):
        """
        Configure mobile optimization settings.
        
        Args:
            enabled: Whether to enable mobile optimizations
            connection_type: Type of connection ('wifi', '4g', '3g', 'slow')
            data_saver: Whether data saver mode is enabled
        """
        self.mobile_mode = enabled
        self.connection_type = connection_type
        self.data_saver_mode = data_saver
        
        # Configure compression service
        self.compression_service.enable_lightweight_mode(enabled or data_saver)
        
        logger.info(f"Mobile mode: {enabled}, Connection: {connection_type}, "
                   f"Data saver: {data_saver}")
    
    def get_optimized_players(self, team_context: Dict[str, Any] = None, 
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Get optimized player data for mobile clients.
        
        Args:
            team_context: Team context information
            page: Page number for pagination
            page_size: Number of players per page
            
        Returns:
            Optimized player data response
        """
        try:
            if not self.data_service:
                raise ValueError("Data service not available")
            
            # Get original player data
            players_df = self.data_service.get_players()
            
            # Apply team filtering if provided
            if team_context and 'team_id' in team_context:
                team_id = team_context['team_id']
                if 'Team' in players_df.columns:
                    players_df = players_df[players_df['Team'] == team_id]
            
            # Create lightweight version if mobile mode is enabled
            if self.mobile_mode or self.data_saver_mode:
                players_df = self.compression_service.create_lightweight_dataframe(
                    players_df, 'players'
                )
            
            # Convert to list of dictionaries
            players_list = players_df.to_dict('records')
            
            # Apply pagination
            paginated_response = self.compression_service.create_paginated_response(
                players_list, page, page_size
            )
            
            # Compress response if beneficial
            compressed_response = self.compression_service.compress_response(
                paginated_response
            )
            
            # Update stats
            self._update_request_stats(compressed_response)
            
            return {
                'success': True,
                'data': compressed_response,
                'mobile_optimized': self.mobile_mode,
                'connection_type': self.connection_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting optimized players: {e}")
            return {
                'success': False,
                'error': str(e),
                'mobile_optimized': self.mobile_mode
            }
    
    def get_optimized_player_stats(self, player_id: int, 
                                 team_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get optimized player statistics for mobile clients.
        
        Args:
            player_id: Player ID
            team_context: Team context information
            
        Returns:
            Optimized player statistics response
        """
        try:
            if not self.data_service:
                raise ValueError("Data service not available")
            
            # Get original player stats
            player_stats = self.data_service.calculate_player_stats(player_id)
            
            if not player_stats:
                return {
                    'success': False,
                    'error': 'Player not found or no stats available'
                }
            
            # Optimize stats for mobile
            optimized_stats = self.compression_service.optimize_player_stats(player_stats)
            
            # Add mobile-specific enhancements
            if self.mobile_mode:
                # Add formatted display values
                optimized_stats['display'] = self._create_mobile_display_stats(optimized_stats)
                
                # Add performance indicators
                optimized_stats['performance_indicators'] = self._get_performance_indicators(optimized_stats)
            
            # Compress response
            compressed_response = self.compression_service.compress_response(optimized_stats)
            
            # Update stats
            self._update_request_stats(compressed_response)
            
            return {
                'success': True,
                'data': compressed_response,
                'player_id': player_id,
                'mobile_optimized': self.mobile_mode,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting optimized player stats for {player_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'player_id': player_id
            }
    
    def get_optimized_games(self, team_context: Dict[str, Any] = None,
                          game_type: str = None, page: int = 1, 
                          page_size: int = 10) -> Dict[str, Any]:
        """
        Get optimized game data for mobile clients.
        
        Args:
            team_context: Team context information
            game_type: Filter by game type
            page: Page number for pagination
            page_size: Number of games per page
            
        Returns:
            Optimized game data response
        """
        try:
            if not self.data_service:
                raise ValueError("Data service not available")
            
            # Get original game data
            games_df = self.data_service.get_games()
            
            # Apply filters
            if game_type:
                games_df = games_df[games_df['GameType'] == game_type]
            
            # Create lightweight version if mobile mode is enabled
            if self.mobile_mode or self.data_saver_mode:
                games_df = self.compression_service.create_lightweight_dataframe(
                    games_df, 'games'
                )
            
            # Sort by date (most recent first)
            if 'Date' in games_df.columns:
                games_df = games_df.sort_values('Date', ascending=False)
            
            # Convert to list of dictionaries
            games_list = games_df.to_dict('records')
            
            # Apply pagination
            paginated_response = self.compression_service.create_paginated_response(
                games_list, page, page_size
            )
            
            # Compress response
            compressed_response = self.compression_service.compress_response(
                paginated_response
            )
            
            # Update stats
            self._update_request_stats(compressed_response)
            
            return {
                'success': True,
                'data': compressed_response,
                'filters': {
                    'game_type': game_type,
                    'team_context': team_context is not None
                },
                'mobile_optimized': self.mobile_mode,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting optimized games: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_optimized_team_stats(self, team_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get optimized team statistics for mobile clients.
        
        Args:
            team_context: Team context information
            
        Returns:
            Optimized team statistics response
        """
        try:
            if not self.data_service:
                raise ValueError("Data service not available")
            
            if not team_context or 'team_id' not in team_context:
                raise ValueError("Team context required")
            
            team_id = team_context['team_id']
            
            # Get team statistics
            team_stats = self.data_service.calculate_team_stats(team_id)
            
            if not team_stats:
                return {
                    'success': False,
                    'error': 'Team stats not available'
                }
            
            # Optimize for mobile if enabled
            if self.mobile_mode or self.data_saver_mode:
                # Keep only essential team stats
                essential_stats = {
                    'team_id': team_stats.get('team_id'),
                    'team_name': team_stats.get('team_name'),
                    'games_played': team_stats.get('games_played', 0),
                    'wins': team_stats.get('wins', 0),
                    'losses': team_stats.get('losses', 0),
                    'goals_for': team_stats.get('goals_for', 0),
                    'goals_against': team_stats.get('goals_against', 0),
                    'goal_differential': team_stats.get('goal_differential', 0)
                }
                team_stats = essential_stats
            
            # Compress response
            compressed_response = self.compression_service.compress_response(team_stats)
            
            # Update stats
            self._update_request_stats(compressed_response)
            
            return {
                'success': True,
                'data': compressed_response,
                'team_id': team_id,
                'mobile_optimized': self.mobile_mode,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting optimized team stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_mobile_display_stats(self, stats: Dict[str, Any]) -> Dict[str, str]:
        """
        Create mobile-friendly display versions of statistics.
        
        Args:
            stats: Raw statistics dictionary
            
        Returns:
            Dictionary with formatted display values
        """
        display = {}
        
        try:
            # Format common stats for mobile display
            if 'goals' in stats:
                display['goals'] = f"{stats['goals']}G"
            if 'assists' in stats:
                display['assists'] = f"{stats['assists']}A"
            if 'points' in stats:
                display['points'] = f"{stats['points']}P"
            if 'games_played' in stats:
                display['games_played'] = f"{stats['games_played']} GP"
            
            # Format percentages
            for key, value in stats.items():
                if isinstance(value, float) and 0 <= value <= 1:
                    display[f"{key}_pct"] = f"{value:.1%}"
                elif isinstance(value, float):
                    display[f"{key}_formatted"] = f"{value:.2f}"
            
        except Exception as e:
            logger.error(f"Error creating mobile display stats: {e}")
        
        return display
    
    def _get_performance_indicators(self, stats: Dict[str, Any]) -> Dict[str, str]:
        """
        Get performance indicators for mobile display.
        
        Args:
            stats: Player statistics
            
        Returns:
            Dictionary with performance indicators
        """
        indicators = {}
        
        try:
            # Points per game
            if 'points' in stats and 'games_played' in stats and stats['games_played'] > 0:
                ppg = stats['points'] / stats['games_played']
                if ppg >= 1.0:
                    indicators['scoring'] = 'excellent'
                elif ppg >= 0.5:
                    indicators['scoring'] = 'good'
                else:
                    indicators['scoring'] = 'developing'
            
            # Plus/minus indicator
            if 'plus_minus' in stats:
                pm = stats['plus_minus']
                if pm > 5:
                    indicators['plus_minus'] = 'positive'
                elif pm < -5:
                    indicators['plus_minus'] = 'negative'
                else:
                    indicators['plus_minus'] = 'neutral'
            
        except Exception as e:
            logger.error(f"Error getting performance indicators: {e}")
        
        return indicators
    
    def _update_request_stats(self, compressed_response: Dict[str, Any]):
        """
        Update request statistics for monitoring.
        
        Args:
            compressed_response: Compressed response data
        """
        try:
            self.request_stats['total_requests'] += 1
            
            if compressed_response.get('compressed', False):
                self.request_stats['compressed_responses'] += 1
                
                original_size = compressed_response.get('original_size', 0)
                compressed_size = compressed_response.get('compressed_size', 0)
                
                if original_size > compressed_size:
                    savings = original_size - compressed_size
                    self.request_stats['bandwidth_saved'] += savings
                    
                    # Update average compression ratio
                    ratio = compressed_response.get('compression_ratio', 1.0)
                    current_avg = self.request_stats['average_compression_ratio']
                    total_compressed = self.request_stats['compressed_responses']
                    
                    # Calculate running average
                    self.request_stats['average_compression_ratio'] = (
                        (current_avg * (total_compressed - 1) + ratio) / total_compressed
                    )
            
        except Exception as e:
            logger.error(f"Error updating request stats: {e}")
    
    def get_mobile_optimization_stats(self) -> Dict[str, Any]:
        """
        Get mobile optimization statistics and performance metrics.
        
        Returns:
            Dictionary with optimization statistics
        """
        try:
            compression_stats = self.compression_service.get_compression_stats()
            image_stats = self.image_service.get_image_optimization_stats()
            
            return {
                'mobile_mode': self.mobile_mode,
                'connection_type': self.connection_type,
                'data_saver_mode': self.data_saver_mode,
                'request_stats': self.request_stats,
                'compression': compression_stats,
                'image_optimization': image_stats,
                'features_enabled': {
                    'data_compression': compression_stats['compression_enabled'],
                    'lightweight_mode': compression_stats['lightweight_mode'],
                    'lazy_loading': image_stats['lazy_loading_enabled'],
                    'responsive_images': image_stats['responsive_images_enabled'],
                    'pagination': True,
                    'mobile_display_formatting': self.mobile_mode
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting mobile optimization stats: {e}")
            return {
                'error': str(e),
                'mobile_mode': self.mobile_mode
            }