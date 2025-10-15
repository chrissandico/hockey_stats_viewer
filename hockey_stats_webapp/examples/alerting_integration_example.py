"""
Example: Integrating Performance Alerting with Existing Services

This example shows how to integrate the performance alerting system
with the existing hockey stats application services.
"""

import os
import sys
import time
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.alerting_integration import (
    initialize_alerting_integration,
    get_alerting_integration,
    monitor_performance,
    record_cache_hit,
    record_cache_miss,
    check_memory_usage,
    record_api_quota
)

class EnhancedSheetsService:
    """
    Example of how to enhance the existing sheets service with alerting
    """
    
    def __init__(self):
        # Initialize alerting integration
        initialize_alerting_integration()
        self.alerting = get_alerting_integration()
        
        # Simulate some service state
        self.cache = {}
        self.api_calls_made = 0
        self.api_quota_limit = 1000
    
    @monitor_performance("get_players")
    def get_players(self, force_refresh=False):
        """Enhanced get_players method with alerting"""
        cache_key = "players_data"
        
        # Check cache first
        if not force_refresh and cache_key in self.cache:
            record_cache_hit("players")
            print("Cache hit for players data")
            return self.cache[cache_key]
        
        # Cache miss - need to fetch from API
        record_cache_miss("players")
        print("Cache miss for players data - fetching from API")
        
        # Simulate API call
        self._simulate_api_call()
        
        # Simulate data processing time
        time.sleep(0.1)  # 100ms processing time
        
        # Store in cache
        players_data = {"players": ["Player 1", "Player 2", "Player 3"]}
        self.cache[cache_key] = players_data
        
        return players_data
    
    @monitor_performance("get_games")
    def get_games(self, team_id=None):
        """Enhanced get_games method with alerting"""
        cache_key = f"games_{team_id}" if team_id else "all_games"
        
        # Check cache
        if cache_key in self.cache:
            record_cache_hit("games")
            return self.cache[cache_key]
        
        record_cache_miss("games")
        
        # Simulate API call
        self._simulate_api_call()
        
        # Simulate longer processing for games
        time.sleep(0.2)  # 200ms processing time
        
        games_data = {"games": [f"Game {i}" for i in range(10)]}
        self.cache[cache_key] = games_data
        
        return games_data
    
    @monitor_performance("get_events")
    def get_events(self, game_id=None):
        """Enhanced get_events method with alerting"""
        # Simulate a slow operation that might trigger alerts
        if game_id == "slow_game":
            time.sleep(6)  # This should trigger a response time warning
        
        self._simulate_api_call()
        
        return {"events": [f"Event {i}" for i in range(5)]}
    
    def _simulate_api_call(self):
        """Simulate making an API call and track quota usage"""
        self.api_calls_made += 1
        
        # Record API quota usage
        record_api_quota(self.api_calls_made, self.api_quota_limit)
        
        # Simulate network delay
        time.sleep(0.05)  # 50ms network delay
    
    def simulate_error_scenario(self):
        """Simulate an error scenario to test error rate alerting"""
        @monitor_performance("error_prone_operation")
        def error_operation():
            raise Exception("Simulated error for testing")
        
        try:
            error_operation()
        except Exception as e:
            print(f"Caught expected error: {e}")
    
    def simulate_memory_pressure(self):
        """Simulate memory pressure to test memory alerting"""
        # This would normally be done by the application automatically
        check_memory_usage()
        
        # Simulate high memory usage by creating large objects
        large_data = [i for i in range(100000)]
        self.cache["large_data"] = large_data
        
        check_memory_usage()

def demonstrate_alerting_system():
    """Demonstrate the alerting system functionality"""
    print("=== Hockey Stats Performance Alerting Demo ===\n")
    
    # Create enhanced service
    service = EnhancedSheetsService()
    
    print("1. Normal operations (should not trigger alerts)")
    print("-" * 50)
    
    # Normal operations
    for i in range(3):
        service.get_players()
        service.get_games("team_1")
        time.sleep(0.1)
    
    print("\n2. Cache performance monitoring")
    print("-" * 50)
    
    # Test cache hits
    service.get_players()  # Should be cache hit
    service.get_players()  # Should be cache hit
    service.get_games("team_1")  # Should be cache hit
    
    print("\n3. Slow operations (may trigger response time alerts)")
    print("-" * 50)
    
    # This should trigger a response time warning
    service.get_events("slow_game")
    
    print("\n4. Error scenarios (will trigger error rate alerts)")
    print("-" * 50)
    
    # Generate some errors to test error rate alerting
    for i in range(3):
        service.simulate_error_scenario()
        time.sleep(0.1)
    
    print("\n5. Memory monitoring")
    print("-" * 50)
    
    service.simulate_memory_pressure()
    
    print("\n6. API quota monitoring")
    print("-" * 50)
    
    # Simulate high API usage
    for i in range(10):
        service._simulate_api_call()
    
    print("\n7. Alerting system status")
    print("-" * 50)
    
    # Get alerting system status
    status = service.alerting.get_alert_status()
    print(f"Alerting system status: {status}")
    
    print("\n8. Manual threshold check")
    print("-" * 50)
    
    # Manually trigger threshold checks
    service.alerting.trigger_manual_check()
    
    print("\nDemo completed. Check the logs for any triggered alerts.")

def test_configuration_loading():
    """Test loading alerting configuration"""
    print("\n=== Testing Configuration Loading ===")
    
    # Test with custom configuration
    config_path = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'alerting_config.json'
    )
    
    if os.path.exists(config_path):
        print(f"Loading configuration from: {config_path}")
        initialize_alerting_integration(config_path)
        print("Configuration loaded successfully")
    else:
        print("Configuration file not found, using defaults")
        initialize_alerting_integration()

if __name__ == "__main__":
    # Test configuration loading
    test_configuration_loading()
    
    # Run the demonstration
    demonstrate_alerting_system()
    
    # Keep the program running for a bit to see monitoring in action
    print("\nMonitoring for 30 seconds...")
    time.sleep(30)
    
    print("Demo finished.")