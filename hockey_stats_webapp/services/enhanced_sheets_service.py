"""
Enhanced Sheets Service with Multi-Level Caching and Background Refresh

This module integrates the SmartCacheManager, MultiLevelCache, and BackgroundCacheRefresh
to provide a high-performance, intelligent caching layer for Google Sheets data.
"""

import os
import json
import time
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import logging
from typing import Optional, Dict, Any

from .smart_cache_manager import SmartCacheManager
from .multi_level_cache import MultiLevelCache
from .background_cache_refresh import BackgroundCacheRefresh

logger = logging.getLogger(__name__)


class EnhancedSheetsService:
    """
    Enhanced Google Sheets service with intelligent multi-level caching.
    
    Features:
    - Multi-level cache hierarchy (L1/L2/L3)
    - Smart cache invalidation based on dependencies
    - Background cache refresh and warming
    - Performance monitoring and statistics
    - Graceful error handling and recovery
    """
    
    def __init__(self, 
                 credentials_path='credentials.json', 
                 sheet_id=None,
                 cache_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Enhanced Sheets Service.
        
        Args:
            credentials_path: Path to service account credentials
            sheet_id: Google Sheets document ID
            cache_config: Cache configuration parameters
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id or '1u4olfiYFjXW0Z88U3Q1wOxI7gz04KYbg6LNn8h-rfno'
        
        # Default cache configuration
        default_config = {
            'l1_size_mb': 20,
            'l2_size_mb': 50,
            'l3_size_mb': 100,
            'smart_cache_size_mb': 30,
            'background_workers': 3,
            'enable_background_refresh': True
        }
        self.cache_config = {**default_config, **(cache_config or {})}
        
        # Initialize caching components
        self.smart_cache = SmartCacheManager(
            max_memory_mb=self.cache_config['smart_cache_size_mb']
        )
        
        self.multi_level_cache = MultiLevelCache(
            l1_size_mb=self.cache_config['l1_size_mb'],
            l2_size_mb=self.cache_config['l2_size_mb'],
            l3_size_mb=self.cache_config['l3_size_mb']
        )
        
        self.background_refresh = BackgroundCacheRefresh(
            max_workers=self.cache_config['background_workers']
        )
        
        # Google Sheets connection
        self.client = None
        self.sheet = None
        
        # Performance tracking
        self.performance_stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_requests': 0,
            'avg_response_time': 0.0
        }
        
        # Initialize connection and caching
        self._connect()
        self._setup_cache_warming()
        
        if self.cache_config['enable_background_refresh']:
            self._start_background_services()
        
        logger.info("EnhancedSheetsService initialized successfully")
    
    def _connect(self):
        """Connect to Google Sheets with enhanced error handling."""
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            # Try environment variable first, then file
            creds_json = os.environ.get('GOOGLE_CREDENTIALS')
            if creds_json:
                try:
                    creds_dict = json.loads(creds_json)
                    credentials = Credentials.from_service_account_info(
                        creds_dict, scopes=scope)
                    logger.info("Using credentials from environment variable")
                except Exception as e:
                    logger.warning(f"Error parsing environment credentials: {e}")
                    credentials = Credentials.from_service_account_file(
                        self.credentials_path, scopes=scope)
                    logger.info("Fallback to credentials file")
            else:
                credentials = Credentials.from_service_account_file(
                    self.credentials_path, scopes=scope)
                logger.info("Using credentials from file")
            
            self.client = gspread.authorize(credentials)
            
            sheet_id = os.environ.get('GOOGLE_SHEET_ID', self.sheet_id)
            self.sheet = self.client.open_by_key(sheet_id)
            
            logger.info(f"Connected to Google Sheet: {self.sheet.title}")
            
        except Exception as e:
            logger.error(f"Error connecting to Google Sheets: {e}")
            raise
    
    def _setup_cache_warming(self):
        """Setup cache warming strategies for frequently accessed data."""
        
        # Register warming strategies with the smart cache
        self.smart_cache.register_warming_strategy('players', self._fetch_players_data)
        self.smart_cache.register_warming_strategy('games', self._fetch_games_data)
        self.smart_cache.register_warming_strategy('events', self._fetch_events_data)
        self.smart_cache.register_warming_strategy('game_roster', self._fetch_game_roster_data)
        self.smart_cache.register_warming_strategy('teams', self._fetch_teams_data)
        
        # Register background refresh tasks
        self.background_refresh.register_refresh_task(
            'players', self._fetch_players_data, priority=1, refresh_interval=600
        )
        self.background_refresh.register_refresh_task(
            'games', self._fetch_games_data, priority=1, refresh_interval=300
        )
        self.background_refresh.register_refresh_task(
            'events', self._fetch_events_data, priority=1, refresh_interval=180
        )
        self.background_refresh.register_refresh_task(
            'game_roster', self._fetch_game_roster_data, priority=2, refresh_interval=600
        )
        self.background_refresh.register_refresh_task(
            'teams', self._fetch_teams_data, priority=3, refresh_interval=1800
        )
        
        logger.info("Cache warming strategies configured")
    
    def _start_background_services(self):
        """Start background cache refresh and warming services."""
        try:
            self.smart_cache.start_background_refresh(interval=300)
            self.background_refresh.start_background_refresh()
            logger.info("Background cache services started")
        except Exception as e:
            logger.error(f"Error starting background services: {e}")
    
    def _get_worksheet(self, name: str):
        """Get worksheet with connection retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.sheet.worksheet(name)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to get worksheet '{name}' after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed for worksheet '{name}': {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _fetch_players_data(self) -> Optional[pd.DataFrame]:
        """Fetch fresh players data from Google Sheets."""
        try:
            worksheet = self._get_worksheet('Players')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            self.performance_stats['api_calls'] += 1
            logger.debug("Fetched fresh players data")
            return df
        except Exception as e:
            logger.error(f"Error fetching players data: {e}")
            return None
    
    def _fetch_games_data(self) -> Optional[pd.DataFrame]:
        """Fetch fresh games data from Google Sheets."""
        try:
            worksheet = self._get_worksheet('Games')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Handle game type data processing
            if 'GameType' not in df.columns:
                df['GameType'] = 'E'
            else:
                df['GameType'] = df['GameType'].fillna('E')
                df['GameType'] = df['GameType'].replace('', 'E')
                
                # Validate game types
                from ..config import is_valid_game_type, DEFAULT_GAME_TYPE
                invalid_mask = ~df['GameType'].apply(is_valid_game_type)
                if invalid_mask.any():
                    df.loc[invalid_mask, 'GameType'] = DEFAULT_GAME_TYPE
            
            self.performance_stats['api_calls'] += 1
            logger.debug("Fetched fresh games data")
            return df
        except Exception as e:
            logger.error(f"Error fetching games data: {e}")
            return None
    
    def _fetch_events_data(self) -> Optional[pd.DataFrame]:
        """Fetch fresh events data from Google Sheets."""
        try:
            worksheet = self._get_worksheet('Events')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Convert boolean columns
            boolean_columns = ['IsGoal', 'IsPowerPlay', 'IsShortHanded']
            for col in boolean_columns:
                if col in df.columns:
                    def convert_to_bool(val):
                        if isinstance(val, bool):
                            return val
                        if isinstance(val, str):
                            val_lower = val.lower().strip()
                            if val_lower in ('true', 'yes', 'y', '1', 't'):
                                return True
                            if val_lower in ('false', 'no', 'n', '0', 'f'):
                                return False
                        if isinstance(val, (int, float)):
                            return bool(val)
                        return False
                    
                    df[col] = df[col].apply(convert_to_bool)
            
            self.performance_stats['api_calls'] += 1
            logger.debug("Fetched fresh events data")
            return df
        except Exception as e:
            logger.error(f"Error fetching events data: {e}")
            return None
    
    def _fetch_game_roster_data(self) -> Optional[pd.DataFrame]:
        """Fetch fresh game roster data from Google Sheets."""
        try:
            worksheet = self._get_worksheet('GameRoster')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            self.performance_stats['api_calls'] += 1
            logger.debug("Fetched fresh game roster data")
            return df
        except Exception as e:
            logger.error(f"Error fetching game roster data: {e}")
            return None
    
    def _fetch_teams_data(self) -> Optional[pd.DataFrame]:
        """Fetch fresh teams data from Google Sheets."""
        try:
            worksheet = self._get_worksheet('Teams')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Validate teams data
            required_columns = ['TeamID', 'TeamName', 'Password']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Teams sheet missing required columns: {missing_columns}")
            
            if df.empty:
                raise ValueError("Teams sheet is empty")
            
            # Check for duplicate passwords
            duplicate_passwords = df[df.duplicated(subset=['Password'], keep=False)]
            if not duplicate_passwords.empty:
                raise ValueError(f"Duplicate passwords found: {duplicate_passwords['Password'].tolist()}")
            
            self.performance_stats['api_calls'] += 1
            logger.debug("Fetched fresh teams data")
            return df
        except Exception as e:
            logger.error(f"Error fetching teams data: {e}")
            return None
    
    def get_players(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Get players data with intelligent caching.
        
        Args:
            force_refresh: Force refresh from Google Sheets
            
        Returns:
            DataFrame with players data
        """
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        # Record access for pattern analysis
        self.background_refresh.record_cache_access('players')
        
        cache_key = 'players'
        
        if not force_refresh:
            # Try multi-level cache first
            cached_data = self.multi_level_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self._update_response_time(start_time)
                return cached_data
            
            # Try smart cache
            cached_data = self.smart_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                # Promote to multi-level cache
                self.multi_level_cache.set(cache_key, cached_data, priority=1)
                self._update_response_time(start_time)
                return cached_data
        
        # Cache miss - fetch fresh data
        self.performance_stats['cache_misses'] += 1
        fresh_data = self._fetch_players_data()
        
        if fresh_data is not None:
            # Store in both caches
            self.smart_cache.set(cache_key, fresh_data, dependencies={'players'})
            self.multi_level_cache.set(cache_key, fresh_data, priority=1)
            
            # Invalidate dependent caches
            self.smart_cache.invalidate_by_dependency('players')
        
        self._update_response_time(start_time)
        return fresh_data if fresh_data is not None else pd.DataFrame()
    
    def get_games(self, force_refresh: bool = False) -> pd.DataFrame:
        """Get games data with intelligent caching."""
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        self.background_refresh.record_cache_access('games')
        
        cache_key = 'games'
        
        if not force_refresh:
            cached_data = self.multi_level_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self._update_response_time(start_time)
                return cached_data
            
            cached_data = self.smart_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self.multi_level_cache.set(cache_key, cached_data, priority=1)
                self._update_response_time(start_time)
                return cached_data
        
        self.performance_stats['cache_misses'] += 1
        fresh_data = self._fetch_games_data()
        
        if fresh_data is not None:
            self.smart_cache.set(cache_key, fresh_data, dependencies={'games'})
            self.multi_level_cache.set(cache_key, fresh_data, priority=1)
            self.smart_cache.invalidate_by_dependency('games')
        
        self._update_response_time(start_time)
        return fresh_data if fresh_data is not None else pd.DataFrame()
    
    def get_events(self, force_refresh: bool = False) -> pd.DataFrame:
        """Get events data with intelligent caching."""
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        self.background_refresh.record_cache_access('events')
        
        cache_key = 'events'
        
        if not force_refresh:
            cached_data = self.multi_level_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self._update_response_time(start_time)
                return cached_data
            
            cached_data = self.smart_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self.multi_level_cache.set(cache_key, cached_data, priority=1)
                self._update_response_time(start_time)
                return cached_data
        
        self.performance_stats['cache_misses'] += 1
        fresh_data = self._fetch_events_data()
        
        if fresh_data is not None:
            self.smart_cache.set(cache_key, fresh_data, dependencies={'events'})
            self.multi_level_cache.set(cache_key, fresh_data, priority=1)
            self.smart_cache.invalidate_by_dependency('events')
        
        self._update_response_time(start_time)
        return fresh_data if fresh_data is not None else pd.DataFrame()
    
    def get_game_roster(self, force_refresh: bool = False) -> pd.DataFrame:
        """Get game roster data with intelligent caching."""
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        self.background_refresh.record_cache_access('game_roster')
        
        cache_key = 'game_roster'
        
        if not force_refresh:
            cached_data = self.multi_level_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self._update_response_time(start_time)
                return cached_data
            
            cached_data = self.smart_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self.multi_level_cache.set(cache_key, cached_data, priority=2)
                self._update_response_time(start_time)
                return cached_data
        
        self.performance_stats['cache_misses'] += 1
        fresh_data = self._fetch_game_roster_data()
        
        if fresh_data is not None:
            self.smart_cache.set(cache_key, fresh_data, dependencies={'game_roster'})
            self.multi_level_cache.set(cache_key, fresh_data, priority=2)
            self.smart_cache.invalidate_by_dependency('game_roster')
        
        self._update_response_time(start_time)
        return fresh_data if fresh_data is not None else pd.DataFrame()
    
    def get_teams(self, force_refresh: bool = False) -> pd.DataFrame:
        """Get teams data with intelligent caching."""
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        self.background_refresh.record_cache_access('teams')
        
        cache_key = 'teams'
        
        if not force_refresh:
            cached_data = self.multi_level_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self._update_response_time(start_time)
                return cached_data
            
            cached_data = self.smart_cache.get(cache_key)
            if cached_data is not None:
                self.performance_stats['cache_hits'] += 1
                self.multi_level_cache.set(cache_key, cached_data, priority=3)
                self._update_response_time(start_time)
                return cached_data
        
        self.performance_stats['cache_misses'] += 1
        fresh_data = self._fetch_teams_data()
        
        if fresh_data is not None:
            self.smart_cache.set(cache_key, fresh_data, dependencies={'teams'})
            self.multi_level_cache.set(cache_key, fresh_data, priority=3)
            self.smart_cache.invalidate_by_dependency('teams')
        
        self._update_response_time(start_time)
        return fresh_data if fresh_data is not None else pd.DataFrame()
    
    def refresh_all_data(self):
        """Refresh all cached data and warm caches."""
        logger.info("Refreshing all data and warming caches")
        
        # Force refresh all data types
        self.get_teams(force_refresh=True)
        self.get_players(force_refresh=True)
        self.get_games(force_refresh=True)
        self.get_events(force_refresh=True)
        self.get_game_roster(force_refresh=True)
        
        # Warm caches for frequently accessed data
        self.smart_cache.warm_cache()
        
        logger.info("All data refreshed and caches warmed")
    
    def _update_response_time(self, start_time: float):
        """Update average response time statistics."""
        response_time = time.time() - start_time
        
        # Calculate rolling average
        if self.performance_stats['avg_response_time'] == 0:
            self.performance_stats['avg_response_time'] = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.performance_stats['avg_response_time'] = (
                alpha * response_time + 
                (1 - alpha) * self.performance_stats['avg_response_time']
            )
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance and cache statistics."""
        
        total_requests = self.performance_stats['total_requests']
        cache_hit_rate = 0
        if total_requests > 0:
            cache_hit_rate = (self.performance_stats['cache_hits'] / total_requests * 100)
        
        return {
            'performance': {
                'total_requests': total_requests,
                'cache_hits': self.performance_stats['cache_hits'],
                'cache_misses': self.performance_stats['cache_misses'],
                'cache_hit_rate_percent': cache_hit_rate,
                'api_calls': self.performance_stats['api_calls'],
                'avg_response_time_ms': self.performance_stats['avg_response_time'] * 1000
            },
            'smart_cache': self.smart_cache.get_stats(),
            'multi_level_cache': self.multi_level_cache.get_comprehensive_stats(),
            'background_refresh': self.background_refresh.get_refresh_stats()
        }
    
    def clear_all_caches(self):
        """Clear all cache levels."""
        self.smart_cache.clear()
        self.multi_level_cache.clear()
        logger.info("All caches cleared")
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        try:
            if hasattr(self, 'background_refresh'):
                self.background_refresh.stop_background_refresh()
            if hasattr(self, 'smart_cache'):
                self.smart_cache.stop_background_refresh()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")