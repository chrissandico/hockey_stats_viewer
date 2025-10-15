"""
Optimized Data Fetching Performance Module

This module provides optimized algorithms for data fetching operations,
replacing O(n*m) iterative calculations with vectorized pandas operations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import time
from datetime import datetime


class OptimizedGoalCalculator:
    """
    Optimized goal calculation using pandas vectorized operations.
    Replaces the O(n*m) iterative approach with efficient bulk operations.
    """
    
    def __init__(self):
        self._calculation_cache = {}
        self._cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutes cache for calculations
    
    def calculate_goals_vectorized(self, games: pd.DataFrame, events: pd.DataFrame, 
                                 team_identifier: str) -> pd.DataFrame:
        """
        Calculate goals for and against using vectorized pandas operations.
        
        This replaces the inefficient O(n*m) loop:
        for idx, game in games.iterrows():
            game_events = events[events['GameID'] == game['ID']]
            goals_for = len(game_events[(game_events['IsGoal'] == True) & 
                                      (game_events['Team'] == team_identifier)])
        
        With efficient vectorized operations that process all games at once.
        
        Args:
            games (pd.DataFrame): Games dataframe
            events (pd.DataFrame): Events dataframe  
            team_identifier (str): Team identifier for filtering
            
        Returns:
            pd.DataFrame: Games dataframe with GoalsFor and GoalsAgainst columns
        """
        if games.empty or events.empty:
            games = games.copy()
            games['GoalsFor'] = 0
            games['GoalsAgainst'] = 0
            return games
        
        # Create cache key for this calculation
        cache_key = f"{len(games)}_{len(events)}_{team_identifier}_{hash(str(games['ID'].tolist()))}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            print(f"Using cached goal calculations for {len(games)} games")
            return self._calculation_cache[cache_key].copy()
        
        start_time = time.time()
        print(f"Starting vectorized goal calculation for {len(games)} games")
        
        # Create a copy to avoid modifying original
        games_result = games.copy()
        
        # Filter events to only goals
        goal_events = events[events['IsGoal'] == True].copy()
        
        if goal_events.empty:
            games_result['GoalsFor'] = 0
            games_result['GoalsAgainst'] = 0
        else:
            # Method 1: Use pandas groupby for bulk aggregation
            # Group goal events by GameID and Team, then count
            goal_counts = goal_events.groupby(['GameID', 'Team']).size().reset_index(name='GoalCount')
            
            # Separate goals for and against
            goals_for_df = goal_counts[goal_counts['Team'] == team_identifier][['GameID', 'GoalCount']]
            goals_against_df = goal_counts[goal_counts['Team'] != team_identifier][['GameID', 'GoalCount']]
            
            # Aggregate goals against by GameID (in case multiple opposing teams in one game)
            goals_against_agg = goals_against_df.groupby('GameID')['GoalCount'].sum().reset_index()
            goals_against_agg.columns = ['GameID', 'GoalCount']
            
            # Merge with games dataframe
            games_result = games_result.merge(
                goals_for_df.rename(columns={'GoalCount': 'GoalsFor'}), 
                left_on='ID', right_on='GameID', how='left'
            )
            games_result = games_result.merge(
                goals_against_agg.rename(columns={'GoalCount': 'GoalsAgainst'}), 
                left_on='ID', right_on='GameID', how='left'
            )
            
            # Clean up merge columns and fill NaN with 0
            games_result = games_result.drop(columns=['GameID_x', 'GameID_y'], errors='ignore')
            games_result['GoalsFor'] = games_result['GoalsFor'].fillna(0).astype(int)
            games_result['GoalsAgainst'] = games_result['GoalsAgainst'].fillna(0).astype(int)
        
        calculation_time = time.time() - start_time
        print(f"Vectorized goal calculation completed in {calculation_time:.3f}s for {len(games)} games")
        
        # Cache the result
        self._calculation_cache[cache_key] = games_result.copy()
        self._cache_timestamps[cache_key] = time.time()
        
        return games_result
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached calculation is still valid."""
        if cache_key not in self._calculation_cache:
            return False
        
        cache_age = time.time() - self._cache_timestamps.get(cache_key, 0)
        return cache_age < self.cache_ttl


class BulkEventProcessor:
    """
    Bulk event processing using pandas groupby operations.
    Optimizes event filtering and aggregation operations.
    """
    
    def __init__(self):
        self._processed_cache = {}
    
    def get_player_stats_bulk(self, events: pd.DataFrame, players: pd.DataFrame, 
                            team_identifier: str) -> pd.DataFrame:
        """
        Calculate player statistics using bulk operations instead of per-player loops.
        
        Args:
            events (pd.DataFrame): Events dataframe
            players (pd.DataFrame): Players dataframe
            team_identifier (str): Team identifier for filtering
            
        Returns:
            pd.DataFrame: Player statistics with Goals, Assists, Points, PIM
        """
        if events.empty or players.empty:
            return players.copy()
        
        start_time = time.time()
        
        # Filter events for the team
        team_events = events[events['Team'] == team_identifier].copy()
        
        if team_events.empty:
            # Return players with zero stats
            result = players.copy()
            result['Goals'] = 0
            result['Assists'] = 0
            result['Points'] = 0
            result['PIM'] = 0
            return result
        
        # Bulk calculate goals using groupby
        goals_df = team_events[team_events['IsGoal'] == True].groupby('PlayerID').size().reset_index(name='Goals')
        
        # Bulk calculate assists using groupby
        assists_df = team_events[team_events['IsAssist'] == True].groupby('PlayerID').size().reset_index(name='Assists')
        
        # Bulk calculate penalty minutes using groupby
        penalty_events = team_events[team_events['EventType'] == 'Penalty'].copy()
        if not penalty_events.empty:
            pim_df = penalty_events.groupby('PlayerID')['PenaltyMinutes'].sum().reset_index(name='PIM')
        else:
            pim_df = pd.DataFrame(columns=['PlayerID', 'PIM'])
        
        # Merge all stats with players dataframe
        result = players.copy()
        
        # Get player ID column name
        id_column = self._get_player_id_column(result)
        if id_column is None:
            return result
        
        # Merge stats
        result = result.merge(goals_df, left_on=id_column, right_on='PlayerID', how='left')
        result = result.merge(assists_df, left_on=id_column, right_on='PlayerID', how='left')
        result = result.merge(pim_df, left_on=id_column, right_on='PlayerID', how='left')
        
        # Clean up and fill NaN values
        result = result.drop(columns=['PlayerID_x', 'PlayerID_y', 'PlayerID'], errors='ignore')
        result['Goals'] = result['Goals'].fillna(0).astype(int)
        result['Assists'] = result['Assists'].fillna(0).astype(int)
        result['PIM'] = result['PIM'].fillna(0).astype(int)
        result['Points'] = result['Goals'] + result['Assists']
        
        processing_time = time.time() - start_time
        print(f"Bulk player stats calculation completed in {processing_time:.3f}s for {len(players)} players")
        
        return result
    
    def _get_player_id_column(self, players_df: pd.DataFrame) -> Optional[str]:
        """Get the correct player ID column name."""
        if players_df.empty:
            return None
        
        # Check for ID column variations in order of preference
        if 'ID' in players_df.columns:
            return 'ID'
        elif 'Unnamed: 0' in players_df.columns:
            return 'Unnamed: 0'
        elif '' in players_df.columns:
            return ''
        else:
            return None


class PreComputedAggregations:
    """
    Pre-computed aggregations for common queries to avoid repeated calculations.
    """
    
    def __init__(self):
        self.aggregations = {}
        self.last_updated = {}
        self.ttl = 600  # 10 minutes TTL for aggregations
    
    def get_team_season_stats(self, games: pd.DataFrame, events: pd.DataFrame, 
                            team_identifier: str) -> Dict:
        """
        Get pre-computed team season statistics.
        
        Args:
            games (pd.DataFrame): Games dataframe
            events (pd.DataFrame): Events dataframe
            team_identifier (str): Team identifier
            
        Returns:
            Dict: Team season statistics
        """
        cache_key = f"team_season_{team_identifier}_{len(games)}_{len(events)}"
        
        if self._is_aggregation_valid(cache_key):
            return self.aggregations[cache_key]
        
        start_time = time.time()
        
        # Calculate season totals using vectorized operations
        total_games = len(games)
        total_goals_for = games['GoalsFor'].sum() if 'GoalsFor' in games.columns else 0
        total_goals_against = games['GoalsAgainst'].sum() if 'GoalsAgainst' in games.columns else 0
        
        wins = len(games[games.get('Result', '') == 'W'])
        losses = len(games[games.get('Result', '') == 'L'])
        ties = len(games[games.get('Result', '') == 'T'])
        
        # Calculate advanced stats
        goal_differential = total_goals_for - total_goals_against
        win_percentage = wins / total_games if total_games > 0 else 0
        
        stats = {
            'total_games': total_games,
            'wins': wins,
            'losses': losses,
            'ties': ties,
            'goals_for': total_goals_for,
            'goals_against': total_goals_against,
            'goal_differential': goal_differential,
            'win_percentage': win_percentage,
            'calculated_at': datetime.now()
        }
        
        # Cache the result
        self.aggregations[cache_key] = stats
        self.last_updated[cache_key] = time.time()
        
        calculation_time = time.time() - start_time
        print(f"Team season stats calculated in {calculation_time:.3f}s")
        
        return stats
    
    def get_player_season_totals(self, events: pd.DataFrame, players: pd.DataFrame,
                               team_identifier: str) -> pd.DataFrame:
        """
        Get pre-computed player season totals.
        
        Args:
            events (pd.DataFrame): Events dataframe
            players (pd.DataFrame): Players dataframe
            team_identifier (str): Team identifier
            
        Returns:
            pd.DataFrame: Player season totals
        """
        cache_key = f"player_totals_{team_identifier}_{len(events)}_{len(players)}"
        
        if self._is_aggregation_valid(cache_key):
            return self.aggregations[cache_key].copy()
        
        # Use bulk processor for efficient calculation
        processor = BulkEventProcessor()
        result = processor.get_player_stats_bulk(events, players, team_identifier)
        
        # Cache the result
        self.aggregations[cache_key] = result.copy()
        self.last_updated[cache_key] = time.time()
        
        return result
    
    def _is_aggregation_valid(self, cache_key: str) -> bool:
        """Check if cached aggregation is still valid."""
        if cache_key not in self.aggregations:
            return False
        
        cache_age = time.time() - self.last_updated.get(cache_key, 0)
        return cache_age < self.ttl
    
    def clear_cache(self):
        """Clear all cached aggregations."""
        self.aggregations.clear()
        self.last_updated.clear()
        print("Pre-computed aggregations cache cleared")


class PerformanceMetrics:
    """
    Track performance metrics for optimization monitoring.
    """
    
    def __init__(self):
        self.metrics = []
    
    def record_calculation_time(self, operation: str, duration: float, 
                              record_count: int, method: str = 'optimized'):
        """
        Record calculation performance metrics.
        
        Args:
            operation (str): Operation name (e.g., 'goal_calculation')
            duration (float): Time taken in seconds
            record_count (int): Number of records processed
            method (str): Method used ('optimized' or 'original')
        """
        metric = {
            'operation': operation,
            'duration': duration,
            'record_count': record_count,
            'method': method,
            'records_per_second': record_count / duration if duration > 0 else 0,
            'timestamp': datetime.now()
        }
        
        self.metrics.append(metric)
        
        # Keep only last 100 metrics to prevent memory growth
        if len(self.metrics) > 100:
            self.metrics = self.metrics[-100:]
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary statistics."""
        if not self.metrics:
            return {}
        
        recent_metrics = self.metrics[-20:]  # Last 20 operations
        
        avg_duration = sum(m['duration'] for m in recent_metrics) / len(recent_metrics)
        avg_throughput = sum(m['records_per_second'] for m in recent_metrics) / len(recent_metrics)
        
        return {
            'average_duration': avg_duration,
            'average_throughput': avg_throughput,
            'total_operations': len(self.metrics),
            'recent_operations': len(recent_metrics)
        }