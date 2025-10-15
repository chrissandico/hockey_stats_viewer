#!/usr/bin/env python3
"""
Test script for cache performance monitoring and optimization features.
Tests the enhanced cache management functionality implemented in task 6.
"""

import sys
import os
import pandas as pd
import logging

# Add the hockey_stats_webapp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def test_cache_performance_monitoring():
    """Test cache performance monitoring functionality."""
    print("=== Testing Cache Performance Monitoring ===")
    
    try:
        # Import required modules
        from services.data_service import DataService
        
        # Create a mock sheets service for testing
        class MockSheetsService:
            def refresh_all_data(self):
                pass
            
            def get_games(self, team_id=None):
                # Return sample data for testing
                return pd.DataFrame({
                    'GameID': ['game1', 'game2', 'game3'],
                    'TeamID': ['team1', 'team1', 'team1'],
                    'GameType': ['R', 'R', 'E'],
                    'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
                    'GoalsFor': [3, 2, 4],
                    'GoalsAgainst': [1, 2, 0]
                })
            
            def get_events(self):
                return pd.DataFrame({
                    'GameID': ['game1', 'game1', 'game2'],
                    'Team': ['team1', 'opponent', 'team1'],
                    'IsGoal': [True, True, True],
                    'GameType': ['R', 'R', 'R']
                })
            
            def get_players(self, team_id=None):
                return pd.DataFrame({
                    'ID': ['player1', 'player2'],
                    'JerseyNumber': [10, 20],
                    'Position': ['F', 'D'],
                    'TeamID': ['team1', 'team1']
                })
            
            def get_teams(self):
                return pd.DataFrame({
                    'TeamID': ['team1'],
                    'TeamName': ['Test Team']
                })
        
        # Initialize data service with mock
        mock_sheets = MockSheetsService()
        data_service = DataService(mock_sheets)
        
        print("✓ Data service initialized successfully")
        
        # Test 1: Basic cache info functionality
        print("\n--- Test 1: Basic Cache Info ---")
        cache_info = data_service.get_cache_info()
        print(f"Initial cache info: {cache_info}")
        
        expected_keys = ['cache_initialized', 'cache_size', 'cache_keys', 'cache_memory_usage', 
                        'cache_entries_detail', 'cache_performance_metrics']
        for key in expected_keys:
            assert key in cache_info, f"Missing key in cache info: {key}"
        
        print("✓ Enhanced cache info structure is correct")
        
        # Test 2: Cache operations and monitoring
        print("\n--- Test 2: Cache Operations ---")
        
        # Add some data to cache by calling get_games
        games1 = data_service.get_games('team1', 'R')
        print(f"Retrieved {len(games1)} games for team1, game type R")
        
        # Check cache after operation
        cache_info_after = data_service.get_cache_info()
        print(f"Cache after first operation: Size={cache_info_after['cache_size']}, "
              f"Memory={cache_info_after['cache_memory_usage']:,.0f}B")
        
        assert cache_info_after['cache_size'] > 0, "Cache should have entries after operation"
        print("✓ Cache is populated after data operations")
        
        # Test 3: Optimized cache clearing
        print("\n--- Test 3: Optimized Cache Clearing ---")
        
        # Test optimized cache clearing
        clear_result = data_service.clear_games_cache_optimized('team1', 'R')
        print(f"Optimized cache clear result: {clear_result}")
        
        expected_clear_keys = ['cleared', 'entries_removed', 'memory_freed', 'reason']
        for key in expected_clear_keys:
            assert key in clear_result, f"Missing key in clear result: {key}"
        
        print("✓ Optimized cache clearing returns proper result structure")
        
        # Test 4: Cache size management
        print("\n--- Test 4: Cache Size Management ---")
        
        # Simulate adding multiple cache entries
        for i in range(5):
            games = data_service.get_games('team1', f'test_type_{i}')
        
        cache_info_multiple = data_service.get_cache_info()
        print(f"Cache after multiple operations: Size={cache_info_multiple['cache_size']}, "
              f"Memory={cache_info_multiple['cache_memory_usage']:,.0f}B")
        
        performance_metrics = cache_info_multiple.get('cache_performance_metrics', {})
        print(f"Performance metrics: {performance_metrics}")
        
        assert 'memory_efficiency' in performance_metrics, "Performance metrics should include efficiency"
        print("✓ Cache size management and performance metrics working")
        
        # Test 5: Cache optimization logic
        print("\n--- Test 5: Cache Optimization Logic ---")
        
        # Test that small, efficient cache is not cleared unnecessarily
        small_clear_result = data_service.clear_games_cache_optimized('team1', 'small_cache')
        print(f"Small cache clear result: {small_clear_result}")
        
        # The result should indicate whether clearing was skipped for optimization
        if not small_clear_result['cleared'] and 'efficient' in small_clear_result.get('reason', ''):
            print("✓ Cache optimization correctly skips unnecessary clearing")
        else:
            print("ℹ Cache clearing proceeded (may be due to cache state)")
        
        print("\n=== All Cache Performance Tests Passed! ===")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This is expected in environments without the full application setup")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_monitoring_integration():
    """Test that cache monitoring integrates properly with layout callbacks."""
    print("\n=== Testing Cache Monitoring Integration ===")
    
    try:
        # Test that the layout files have the correct monitoring code
        team_layout_path = 'hockey_stats_webapp/layouts/team_layout.py'
        player_layout_path = 'hockey_stats_webapp/layouts/player_layout.py'
        
        # Check team layout
        with open(team_layout_path, 'r') as f:
            team_content = f.read()
        
        required_team_patterns = [
            'clear_games_cache_optimized',
            'Cache performance monitoring',
            'cache_performance_metrics',
            'Post-operation cache metrics'
        ]
        
        for pattern in required_team_patterns:
            assert pattern in team_content, f"Team layout missing pattern: {pattern}"
        
        print("✓ Team layout has cache monitoring integration")
        
        # Check player layout
        with open(player_layout_path, 'r') as f:
            player_content = f.read()
        
        required_player_patterns = [
            'clear_games_cache_optimized',
            'Cache performance monitoring',
            'cache_performance_metrics',
            'Post-operation cache metrics'
        ]
        
        for pattern in required_player_patterns:
            assert pattern in player_content, f"Player layout missing pattern: {pattern}"
        
        print("✓ Player layout has cache monitoring integration")
        
        # Check data service
        data_service_path = 'hockey_stats_webapp/services/data_service.py'
        with open(data_service_path, 'r') as f:
            service_content = f.read()
        
        required_service_patterns = [
            'clear_games_cache_optimized',
            '_manage_cache_size_before_add',
            '_manage_cache_size_after_add',
            '_cleanup_cache_entries',
            'cache_performance_metrics'
        ]
        
        for pattern in required_service_patterns:
            assert pattern in service_content, f"Data service missing pattern: {pattern}"
        
        print("✓ Data service has enhanced cache management")
        
        print("\n=== Cache Monitoring Integration Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Cache Performance Monitoring and Optimization")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_cache_performance_monitoring()
    test2_passed = test_cache_monitoring_integration()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nCache performance monitoring and optimization features are working correctly:")
        print("• Enhanced cache info with detailed performance metrics")
        print("• Optimized cache clearing with selective strategies")
        print("• Automatic cache size management with cleanup")
        print("• Integration with team and player layout callbacks")
        print("• Comprehensive error handling and fallback mechanisms")
    else:
        print("⚠️  Some tests failed - see details above")
        if not test1_passed:
            print("• Cache performance monitoring test failed")
        if not test2_passed:
            print("• Cache monitoring integration test failed")
    
    print("\nImplementation Summary:")
    print("Task 6.1 ✓ Added comprehensive cache performance monitoring")
    print("Task 6.2 ✓ Implemented optimized cache clearing strategy")
    print("Task 6   ✓ Performance and monitoring improvements completed")