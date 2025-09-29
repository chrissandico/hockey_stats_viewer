#!/usr/bin/env python3
"""
Test script to verify game type filtering functionality in the hockey stats web app.
"""

import sys
import os

# Add the hockey_stats_webapp directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

from services.sheets_service import SheetsService
from services.data_service import DataService
import config

def test_game_type_filtering():
    """Test the game type filtering functionality."""
    print("=== Testing Game Type Filtering ===")
    
    try:
        # Initialize services
        print("Initializing services...")
        sheets_service = SheetsService()
        data_service = DataService(sheets_service, force_refresh=True)
        
        # Test 1: Verify game type constants
        print("\n1. Testing game type constants...")
        game_types = config.get_all_game_types()
        print(f"Available game types: {list(game_types.keys())}")
        
        for code, info in game_types.items():
            print(f"  {code}: {info['name']} (Color: {info['color']})")
        
        # Test 2: Check if games have game type data
        print("\n2. Testing game type data retrieval...")
        all_games = data_service.get_games()
        print(f"Total games retrieved: {len(all_games)}")
        
        if 'GameType' in all_games.columns:
            game_type_counts = all_games['GameType'].value_counts()
            print(f"Game type distribution: {game_type_counts.to_dict()}")
        else:
            print("WARNING: GameType column not found in games data")
        
        # Test 3: Test filtering by each game type
        print("\n3. Testing game type filtering...")
        for game_type in ['E', 'R', 'T']:
            filtered_games = data_service.get_games(game_type=game_type)
            game_type_name = config.get_game_type_name(game_type)
            print(f"  {game_type_name} ({game_type}): {len(filtered_games)} games")
        
        # Test 4: Test team stats with game type filtering
        print("\n4. Testing team stats with game type filtering...")
        
        # Get first team for testing
        teams = sheets_service.get_teams()
        if not teams.empty:
            test_team_id = teams.iloc[0]['TeamID']
            print(f"Testing with team: {test_team_id}")
            
            # Calculate stats for each game type
            for game_type in ['E', 'R', 'T', None]:
                stats = data_service.calculate_team_stats(test_team_id, game_type)
                game_type_label = config.get_game_type_name(game_type) if game_type else "All Games"
                print(f"  {game_type_label}: {stats['games_played']} games, {stats['wins']} wins")
        
        # Test 5: Test helper functions
        print("\n5. Testing helper functions...")
        for game_type in ['E', 'R', 'T']:
            name = config.get_game_type_name(game_type)
            color = config.get_game_type_color(game_type)
            badge_class = config.get_game_type_badge_class(game_type)
            print(f"  {game_type}: {name} (Color: {color}, Badge: {badge_class})")
        
        # Test 6: Test invalid game type handling
        print("\n6. Testing invalid game type handling...")
        invalid_name = config.get_game_type_name('X')  # Invalid code
        print(f"Invalid game type 'X' returns: {invalid_name}")
        
        print("\n=== Game Type Filtering Tests Completed Successfully ===")
        return True
        
    except Exception as e:
        print(f"\nERROR: Game type filtering test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_game_type_filtering()
    sys.exit(0 if success else 1)
