"""
Test Mobile Cache Implementation

This test verifies the mobile-specific caching functionality including
connection-aware caching, offline-first caching, and user behavior tracking.
"""

import unittest
import time
import tempfile
import shutil
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Import the services we're testing
from hockey_stats_webapp.services.mobile_cache_service import (
    MobileCacheService, ConnectionType, DataPriority, 
    ConnectionProfile, UserBehaviorPattern
)
from hockey_stats_webapp.services.mobile_cache_integration import MobileCacheIntegration
from hockey_stats_webapp.services.smart_cache_manager import SmartCacheManager
from hockey_stats_webapp.services.multi_level_cache import MultiLevelCache


class TestMobileCacheImplementation(unittest.TestCase):
    """Test suite for mobile cache implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock services
        self.mock_cache_manager = Mock(spec=SmartCacheManager)
        self.mock_cache_manager.default_ttl = 3600
        self.mock_cache_manager.get_stats.return_value = {'hits': 10, 'misses': 5}
        
        self.mock_multi_level_cache = Mock(spec=MultiLevelCache)
        self.mock_multi_level_cache.get_comprehensive_stats.return_value = {
            'l1_hits': 5, 'l2_hits': 3, 'l3_hits': 2
        }
        
        self.mock_sheets_service = Mock()
        self.mock_data_service = Mock()
        
        # Create mobile cache service
        self.mobile_cache = MobileCacheService(
            cache_manager=self.mock_cache_manager,
            multi_level_cache=self.mock_multi_level_cache,
            max_offline_cache_mb=10,  # Small for testing
            behavior_tracking_days=7
        )
        
        # Create integration service
        self.integration = MobileCacheIntegration(
            sheets_service=self.mock_sheets_service,
            data_service=self.mock_data_service,
            cache_manager=self.mock_cache_manager,
            multi_level_cache=self.mock_multi_level_cache
        )
    
    def test_connection_aware_caching_strategies(self):
        """Test connection-aware caching strategies."""
        # Test WiFi connection
        self.mobile_cache.update_connection_profile(
            ConnectionType.WIFI, 50000, 20, False, False
        )
        self.assertEqual(self.mobile_cache.current_connection.connection_type, ConnectionType.WIFI)
        self.assertTrue(self.mobile_cache.current_connection.is_fast_connection)
        
        # Test slow connection adaptation
        self.mobile_cache.update_connection_profile(
            ConnectionType.CELLULAR_2G, 100, 500, True, True
        )
        self.assertEqual(self.mobile_cache.current_connection.connection_type, ConnectionType.CELLULAR_2G)
        self.assertTrue(self.mobile_cache.current_connection.is_slow_connection)
        self.assertTrue(self.mobile_cache.current_connection.data_saver_mode)
        
        # Verify cache TTL adjustment
        self.assertEqual(self.mock_cache_manager.default_ttl, 7200)  # 2 hours for slow connection
        
        # Test offline mode
        self.mobile_cache.update_connection_profile(
            ConnectionType.OFFLINE, 0, 0, False, False
        )
        self.assertEqual(self.mobile_cache.current_connection.connection_type, ConnectionType.OFFLINE)
        self.assertEqual(self.mock_cache_manager.default_ttl, 86400)  # 24 hours for offline
    
    def test_offline_first_caching_critical_data(self):
        """Test offline-first caching for critical data."""
        # Mock multi-level cache to return data
        test_data = {'players': [{'id': 1, 'name': 'Test Player'}]}
        self.mock_multi_level_cache.get.return_value = test_data
        
        # Cache critical data
        success = self.mobile_cache.cache_with_mobile_strategy(
            'players_team1', test_data, DataPriority.CRITICAL
        )
        self.assertTrue(success)
        
        # Verify data is in offline cache
        self.assertIn('players_team1', self.mobile_cache.offline_cache)
        entry = self.mobile_cache.offline_cache['players_team1']
        self.assertEqual(entry.priority, DataPriority.CRITICAL)
        self.assertTrue(entry.is_critical)
        
        # Test offline retrieval
        self.mobile_cache.update_connection_profile(ConnectionType.OFFLINE, 0, 0, False, False)
        retrieved_data = self.mobile_cache.get_with_mobile_strategy('players_team1')
        self.assertEqual(retrieved_data, test_data)
    
    def test_cache_preloading_user_behavior(self):
        """Test cache preloading based on user behavior patterns."""
        # Track user behavior
        self.mobile_cache.track_user_behavior(
            user_id='user1',
            team_id='team1',
            page='player_stats',
            data_types={'players', 'statistics'}
        )
        
        # Verify behavior is tracked
        behavior_key = 'user1_team1'
        self.assertIn(behavior_key, self.mobile_cache.user_behaviors)
        behavior = self.mobile_cache.user_behaviors[behavior_key]
        self.assertEqual(behavior.user_id, 'user1')
        self.assertEqual(behavior.team_id, 'team1')
        self.assertIn('player_stats', behavior.frequent_pages)
        self.assertIn('players', behavior.preferred_data_types)
        
        # Test prediction
        predicted_keys = self.mobile_cache._predict_next_data_needs(behavior)
        self.assertIn('player_stats_team1', predicted_keys)
        self.assertIn('players_team1', predicted_keys)
    
    def test_connection_detection_from_headers(self):
        """Test connection detection from HTTP headers."""
        # Test mobile user agent with 4G
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
            'Downlink': '5.2',
            'RTT': '150',
            'ECT': '4g'
        }
        
        self.integration.detect_connection_from_request(headers)
        
        # Verify connection was detected
        connection = self.integration.mobile_cache.current_connection
        self.assertEqual(connection.connection_type, ConnectionType.CELLULAR_4G)
        self.assertEqual(connection.bandwidth_kbps, 5200)
        self.assertEqual(connection.latency_ms, 150)
        self.assertTrue(connection.is_metered)
    
    def test_data_saver_mode_detection(self):
        """Test data saver mode detection."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Android; Mobile) Chrome/91.0 Opera Mini',
            'Save-Data': 'on'
        }
        
        self.integration.detect_connection_from_request(headers)
        
        connection = self.integration.mobile_cache.current_connection
        self.assertTrue(connection.data_saver_mode)
    
    def test_cache_size_management(self):
        """Test cache size management and eviction."""
        # Fill cache beyond limit
        large_data = 'x' * (2 * 1024 * 1024)  # 2MB of data
        
        for i in range(10):  # Try to add 20MB total
            self.mobile_cache.cache_with_mobile_strategy(
                f'large_data_{i}', large_data, DataPriority.LOW
            )
        
        # Verify cache size is managed
        self.assertLessEqual(
            self.mobile_cache.offline_cache_size,
            self.mobile_cache.max_offline_cache_bytes
        )
    
    def test_cache_warming_strategies(self):
        """Test cache warming strategies."""
        # Mock preload strategy
        def mock_preload_strategy():
            return {'test': 'data'}
        
        self.mobile_cache.register_preload_strategy('test_key', mock_preload_strategy)
        
        # Test WiFi cache warming (aggressive)
        self.mobile_cache.update_connection_profile(
            ConnectionType.WIFI, 50000, 20, False, False
        )
        
        # Trigger cache warming
        self.mobile_cache.warm_cache_for_connection()
        
        # Give warming thread time to work
        time.sleep(0.1)
        
        # Verify strategy was registered
        self.assertIn('test_key', self.mobile_cache.preload_strategies)
    
    def test_background_sync_critical_data(self):
        """Test background synchronization of critical data."""
        # Add critical data that needs sync
        test_data = {'critical': 'data'}
        self.mobile_cache._add_to_offline_cache(
            'critical_data', test_data, DataPriority.CRITICAL
        )
        
        # Mark as needing sync
        entry = self.mobile_cache.offline_cache['critical_data']
        entry.sync_required = True
        entry.last_accessed = datetime.now()
        
        # Mock preload strategy
        def mock_sync_strategy():
            return {'critical': 'updated_data'}
        
        self.mobile_cache.register_preload_strategy('critical_data', mock_sync_strategy)
        
        # Enable background sync
        self.mobile_cache.update_connection_profile(
            ConnectionType.WIFI, 50000, 20, False, False
        )
        
        # Trigger sync
        self.mobile_cache._sync_critical_data()
        
        # Verify data was updated
        updated_entry = self.mobile_cache.offline_cache['critical_data']
        self.assertEqual(updated_entry.data, {'critical': 'updated_data'})
    
    def test_mobile_optimized_data_retrieval(self):
        """Test mobile-optimized data retrieval methods."""
        # Mock sheets service responses
        players_df = pd.DataFrame([
            {'ID': 1, 'Name': 'Player 1', 'Team': 'team1'},
            {'ID': 2, 'Name': 'Player 2', 'Team': 'team1'}
        ])
        self.mock_sheets_service.get_players.return_value = players_df
        
        # Set user session
        self.integration.set_user_session('user1', 'team1')
        
        # Test players retrieval
        result = self.integration.get_players_mobile_optimized('team1')
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        
        # Verify caching occurred
        self.mock_multi_level_cache.set.assert_called()
    
    def test_connection_adaptive_data_strategies(self):
        """Test connection-adaptive data retrieval strategies."""
        # Set up offline mode
        self.integration.mobile_cache.update_connection_profile(
            ConnectionType.OFFLINE, 0, 0, False, False
        )
        
        # Add some cached data
        cached_data = {'offline': 'data'}
        self.integration.mobile_cache.offline_cache['players_team1'] = Mock()
        self.integration.mobile_cache.offline_cache['players_team1'].data = cached_data
        self.integration.mobile_cache.offline_cache['players_team1'].expires_at = datetime.now() + timedelta(hours=1)
        
        # Mock the get method to return cached data
        self.integration.mobile_cache.get_with_mobile_strategy = Mock(return_value=cached_data)
        
        # Test offline-only data retrieval
        result = self.integration.get_connection_adaptive_data('players', 'team1')
        self.assertEqual(result, cached_data)
    
    def test_performance_statistics(self):
        """Test performance statistics collection."""
        # Generate some cache activity
        self.mobile_cache.stats['offline_cache_hits'] = 15
        self.mobile_cache.stats['offline_cache_misses'] = 5
        self.mobile_cache.stats['preload_operations'] = 8
        
        # Get statistics
        stats = self.mobile_cache.get_mobile_cache_stats()
        
        # Verify statistics
        self.assertEqual(stats['offline_hit_rate_percent'], 75.0)  # 15/(15+5) * 100
        self.assertEqual(stats['preload_operations'], 8)
        self.assertIn('connection_type', stats)
        
        # Test comprehensive statistics
        comprehensive_stats = self.integration.get_cache_statistics()
        self.assertIn('mobile_cache', comprehensive_stats)
        self.assertIn('multi_level_cache', comprehensive_stats)
        self.assertIn('smart_cache', comprehensive_stats)
    
    def test_time_based_predictions(self):
        """Test time-based data predictions."""
        # Create behavior with time patterns
        behavior = UserBehaviorPattern(
            user_id='user1',
            team_id='team1'
        )
        
        # Add access times during game hours (evening)
        current_time = datetime.now().replace(hour=19, minute=0, second=0)  # 7 PM
        behavior.access_times = [
            current_time - timedelta(days=1),
            current_time - timedelta(days=2),
            current_time - timedelta(days=3)
        ]
        
        # Test time-based predictions
        with patch('hockey_stats_webapp.services.mobile_cache_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            predictions = self.mobile_cache._predict_time_based_needs(behavior)
            
            # Should predict game-related data during game hours
            self.assertTrue(any('live_game_data' in pred for pred in predictions))
            self.assertTrue(any('game_roster' in pred for pred in predictions))
    
    def test_session_pattern_predictions(self):
        """Test session pattern-based predictions."""
        behavior = UserBehaviorPattern(
            user_id='user1',
            team_id='team1'
        )
        
        # Simulate long session pattern
        base_time = datetime.now()
        behavior.access_times = [
            base_time,
            base_time + timedelta(minutes=5),
            base_time + timedelta(minutes=15),
            base_time + timedelta(minutes=35)  # 35-minute session
        ]
        
        predictions = self.mobile_cache._predict_session_pattern_needs(behavior)
        
        # Should predict detailed data for long sessions
        self.assertTrue(any('detailed_player_stats' in pred for pred in predictions))
    
    def tearDown(self):
        """Clean up test environment."""
        # Stop any background threads
        if hasattr(self.mobile_cache, '_preload_stop_event'):
            self.mobile_cache._preload_stop_event.set()
        if hasattr(self.mobile_cache, '_sync_stop_event'):
            self.mobile_cache._sync_stop_event.set()
        if hasattr(self.mobile_cache, '_warming_stop_event'):
            self.mobile_cache._warming_stop_event.set()
        
        # Clear caches
        self.mobile_cache.clear_mobile_cache()


def run_mobile_cache_tests():
    """Run mobile cache implementation tests."""
    print("Running Mobile Cache Implementation Tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMobileCacheImplementation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == '__main__':
    run_mobile_cache_tests()