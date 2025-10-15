"""
Mobile Cache Service Usage Example

This example demonstrates how to use the mobile-specific caching service
for connection-aware caching, offline functionality, and predictive preloading.
"""

import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
from hockey_stats_webapp.services.mobile_cache_service import (
    MobileCacheService, ConnectionType, DataPriority
)
from hockey_stats_webapp.services.mobile_cache_integration import MobileCacheIntegration
from hockey_stats_webapp.services.smart_cache_manager import SmartCacheManager
from hockey_stats_webapp.services.multi_level_cache import MultiLevelCache


def demonstrate_mobile_cache_service():
    """Demonstrate mobile cache service functionality."""
    
    print("=== Mobile Cache Service Demo ===\n")
    
    # Initialize cache components
    cache_manager = SmartCacheManager(max_memory_mb=50)
    multi_level_cache = MultiLevelCache(l1_size_mb=10, l2_size_mb=20, l3_size_mb=30)
    
    # Initialize mobile cache service
    mobile_cache = MobileCacheService(
        cache_manager=cache_manager,
        multi_level_cache=multi_level_cache,
        max_offline_cache_mb=25
    )
    
    print("1. Connection Awareness Demo")
    print("-" * 30)
    
    # Simulate different connection types
    connections = [
        (ConnectionType.WIFI, 50000, 10, False, False),
        (ConnectionType.CELLULAR_4G, 20000, 50, True, False),
        (ConnectionType.CELLULAR_3G, 5000, 100, True, True),
        (ConnectionType.CELLULAR_2G, 1000, 300, True, True),
        (ConnectionType.OFFLINE, 0, 0, False, False)
    ]
    
    for conn_type, bandwidth, latency, metered, data_saver in connections:
        print(f"\nConnection: {conn_type.value}")
        print(f"  Bandwidth: {bandwidth} kbps, Latency: {latency}ms")
        print(f"  Metered: {metered}, Data Saver: {data_saver}")
        
        mobile_cache.update_connection_profile(
            connection_type=conn_type,
            bandwidth_kbps=bandwidth,
            latency_ms=latency,
            is_metered=metered,
            data_saver_mode=data_saver
        )
        
        # Test caching behavior
        test_data = {"players": [{"id": 1, "name": "Player 1"}]}
        
        # Try caching with different priorities
        for priority in [DataPriority.CRITICAL, DataPriority.HIGH, DataPriority.MEDIUM, DataPriority.LOW]:
            success = mobile_cache.cache_with_mobile_strategy(
                f"test_data_{priority.name.lower()}", 
                test_data, 
                priority
            )
            print(f"  Cache {priority.name}: {'✓' if success else '✗'}")
    
    print("\n\n2. Offline Cache Demo")
    print("-" * 20)
    
    # Set to WiFi for caching
    mobile_cache.update_connection_profile(ConnectionType.WIFI, 50000, 10, False, False)
    
    # Cache critical data
    critical_data = {
        "teams": ["Team A", "Team B", "Team C"],
        "players": [{"id": i, "name": f"Player {i}", "team": f"Team {chr(65 + i % 3)}"} for i in range(1, 11)],
        "games": [{"id": i, "home": "Team A", "away": "Team B", "date": "2024-01-01"} for i in range(1, 6)]
    }
    
    for key, data in critical_data.items():
        mobile_cache.cache_with_mobile_strategy(key, data, DataPriority.CRITICAL)
        print(f"Cached critical data: {key}")
    
    # Switch to offline mode
    mobile_cache.update_connection_profile(ConnectionType.OFFLINE, 0, 0, False, False)
    
    # Test offline access
    print("\nOffline access test:")
    for key in critical_data.keys():
        cached_data = mobile_cache.get_with_mobile_strategy(key)
        print(f"  {key}: {'✓ Available' if cached_data else '✗ Not available'}")
    
    print("\n\n3. User Behavior Tracking Demo")
    print("-" * 30)
    
    # Simulate user behavior
    user_id = "user123"
    team_id = "TeamA"
    
    # Track various page accesses
    behaviors = [
        ("player_stats", {"players", "statistics"}),
        ("team_analytics", {"teams", "analytics"}),
        ("game_summary", {"games", "events"}),
        ("player_stats", {"players", "statistics"}),  # Repeat to show pattern
        ("team_analytics", {"teams", "analytics"}),
    ]
    
    print(f"Tracking behavior for user: {user_id}, team: {team_id}")
    
    for page, data_types in behaviors:
        mobile_cache.track_user_behavior(user_id, team_id, page, data_types)
        print(f"  Accessed: {page} (data: {', '.join(data_types)})")
        time.sleep(0.1)  # Small delay to simulate real usage
    
    # Register a mock preload strategy
    def mock_preload_strategy():
        return {"mock_data": "preloaded_content", "timestamp": datetime.now().isoformat()}
    
    mobile_cache.register_preload_strategy("player_stats_TeamA", mock_preload_strategy)
    
    # Switch back to WiFi to enable preloading
    mobile_cache.update_connection_profile(ConnectionType.WIFI, 50000, 10, False, False)
    
    print("\nPreloading triggered based on behavior patterns...")
    time.sleep(2)  # Allow preloading to process
    
    print("\n\n4. Cache Statistics")
    print("-" * 18)
    
    stats = mobile_cache.get_mobile_cache_stats()
    print(f"Connection Type: {stats['connection_type']}")
    print(f"Offline Cache Entries: {stats['offline_cache_entries']}")
    print(f"Offline Cache Size: {stats['offline_cache_size_mb']:.2f} MB")
    print(f"Offline Hit Rate: {stats['offline_hit_rate_percent']:.1f}%")
    print(f"Preload Operations: {stats['preload_operations']}")
    print(f"Connection Adaptations: {stats['connection_adaptations']}")
    print(f"User Behaviors Tracked: {stats['user_behaviors_tracked']}")
    
    # Clean up
    mobile_cache.clear_mobile_cache()
    print("\nMobile cache cleared")


def demonstrate_mobile_cache_integration():
    """Demonstrate mobile cache integration with hockey stats app."""
    
    print("\n\n=== Mobile Cache Integration Demo ===\n")
    
    # Note: This would normally use real services, but we'll simulate for demo
    class MockSheetsService:
        def get_players(self, force_refresh=False):
            return [{"id": 1, "name": "Player 1", "team": "TeamA"}]
        
        def get_games(self, force_refresh=False):
            return [{"id": 1, "home": "TeamA", "away": "TeamB", "date": "2024-01-01"}]
        
        def get_events(self, force_refresh=False):
            return [{"game_id": 1, "player_id": 1, "event": "Goal", "time": "10:30"}]
    
    class MockDataService:
        def get_team_roster(self, team_id):
            return [{"player_id": 1, "name": "Player 1", "position": "Forward"}]
        
        def get_team_games(self, team_id):
            return [{"game_id": 1, "opponent": "TeamB", "result": "W 3-2"}]
        
        def get_team_stats(self, team_id):
            return {"wins": 5, "losses": 2, "goals_for": 15, "goals_against": 8}
        
        def calculate_player_stats(self, players_df, games_df, events_df, team_id=None, player_id=None):
            return {"goals": 3, "assists": 2, "points": 5, "plus_minus": 2}
    
    # Initialize services
    sheets_service = MockSheetsService()
    data_service = MockDataService()
    cache_manager = SmartCacheManager(max_memory_mb=50)
    multi_level_cache = MultiLevelCache()
    
    # Initialize integration
    integration = MobileCacheIntegration(
        sheets_service=sheets_service,
        data_service=data_service,
        cache_manager=cache_manager,
        multi_level_cache=multi_level_cache
    )
    
    print("1. Connection Detection Demo")
    print("-" * 25)
    
    # Simulate mobile request headers
    mobile_headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
        'Save-Data': 'on',
        'Downlink': '2.5'  # Mbps
    }
    
    integration.detect_connection_from_request(mobile_headers)
    print("Detected mobile connection with data saver mode")
    
    print("\n2. User Session Demo")
    print("-" * 18)
    
    # Set user session
    integration.set_user_session("user123", "TeamA")
    print("User session set: user123 - TeamA")
    print("Critical team data preloaded")
    
    print("\n3. Mobile-Optimized Data Access")
    print("-" * 30)
    
    # Test mobile-optimized data access
    players_data = integration.get_players_mobile_optimized(team_id="TeamA")
    print(f"Players data: {'✓ Retrieved' if players_data else '✗ Failed'}")
    
    games_data = integration.get_games_mobile_optimized(team_id="TeamA", game_type="Regular Season")
    print(f"Games data: {'✓ Retrieved' if games_data else '✗ Failed'}")
    
    stats_data = integration.get_player_stats_mobile_optimized(player_id=1, team_id="TeamA")
    print(f"Player stats: {'✓ Retrieved' if stats_data else '✗ Failed'}")
    
    print("\n4. Cache Statistics")
    print("-" * 18)
    
    stats = integration.get_cache_statistics()
    mobile_stats = stats['mobile_cache']
    
    print(f"Connection Type: {mobile_stats['connection_type']}")
    print(f"Data Saver Mode: {mobile_stats['data_saver_mode']}")
    print(f"Session Duration: {stats['session_info']['session_duration_minutes']:.1f} minutes")
    print(f"User Behaviors Tracked: {mobile_stats['user_behaviors_tracked']}")
    
    # Clean up
    integration.clear_all_caches()
    print("\nAll caches cleared")


if __name__ == "__main__":
    try:
        demonstrate_mobile_cache_service()
        demonstrate_mobile_cache_integration()
        print("\n=== Demo completed successfully! ===")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise