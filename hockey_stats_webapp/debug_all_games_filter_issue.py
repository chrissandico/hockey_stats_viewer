#!/usr/bin/env python3

"""
Debug script to investigate why the "All Games" filter is not working correctly.
The user reported that "All Games" should show 7 games (1E + 4T + 2R = 7) but it's only showing 2.
"""

from services.data_service import DataService
from services.sheets_service import SheetsService
from services.auth_service import AuthService

def debug_all_games_filter():
    """Debug the All Games filter issue."""
    
    print("=== DEBUGGING ALL GAMES FILTER ISSUE ===")
    
    # Initialize services
    sheets_service = SheetsService()
    auth_service = AuthService(sheets_service)
    data_service = DataService(sheets_service, auth_service)
    
    # Data is already refreshed during initialization
    print("\n1. Data service initialized and refreshed...")
    
    # Test authentication for the specific team
    print("\n2. Testing authentication for cwaxersu12aa...")
    auth_result = auth_service.verify_password("cwaxersu12aa")
    print(f"Authentication result: {auth_result}")
    
    if not auth_result:
        print("ERROR: Authentication failed!")
        return
    
    team_id = auth_result['team_id']
    print(f"Team ID: {team_id}")
    
    # Test different game type filters
    print(f"\n3. Testing game type filters for team {team_id}...")
    
    # Test All Games (game_type=None)
    print("\n--- Testing All Games (game_type=None) ---")
    all_games = data_service.get_games(team_id, game_type=None)
    print(f"All Games count: {len(all_games)}")
    if len(all_games) > 0:
        print("Game types in All Games:")
        game_type_counts = all_games['GameType'].value_counts()
        print(game_type_counts)
        print("\nFirst few games:")
        print(all_games[['Date', 'Opponent', 'GameType', 'Result']].head(10))
    
    # Test Regular Season
    print("\n--- Testing Regular Season (game_type='R') ---")
    regular_games = data_service.get_games(team_id, game_type='R')
    print(f"Regular Season count: {len(regular_games)}")
    
    # Test Exhibition
    print("\n--- Testing Exhibition (game_type='E') ---")
    exhibition_games = data_service.get_games(team_id, game_type='E')
    print(f"Exhibition count: {len(exhibition_games)}")
    
    # Test Tournament
    print("\n--- Testing Tournament (game_type='T') ---")
    tournament_games = data_service.get_games(team_id, game_type='T')
    print(f"Tournament count: {len(tournament_games)}")
    
    # Calculate expected total
    expected_total = len(regular_games) + len(exhibition_games) + len(tournament_games)
    print(f"\nExpected total (R + E + T): {expected_total}")
    print(f"Actual All Games total: {len(all_games)}")
    
    if expected_total != len(all_games):
        print("❌ MISMATCH DETECTED! All Games filter is not working correctly.")
    else:
        print("✅ All Games filter is working correctly.")
    
    # Test team stats calculation
    print(f"\n4. Testing team stats calculation for team {team_id}...")
    
    # Test All Games team stats
    print("\n--- Testing All Games team stats ---")
    all_stats = data_service.calculate_team_stats(team_id, game_type=None)
    print(f"All Games team stats: {all_stats}")
    
    # Test Regular Season team stats
    print("\n--- Testing Regular Season team stats ---")
    regular_stats = data_service.calculate_team_stats(team_id, game_type='R')
    print(f"Regular Season team stats: {regular_stats}")
    
    # Check if the issue is in the callback logic
    print(f"\n5. Testing callback logic simulation...")
    
    # Simulate the callback logic from team_layout.py
    def simulate_callback_logic(game_type_data):
        """Simulate the callback logic to see what's happening."""
        print(f"Input game_type_data: {game_type_data}")
        
        # Get game type from callback parameter
        game_type = game_type_data if isinstance(game_type_data, str) else None
        if game_type_data and isinstance(game_type_data, dict):
            game_type = game_type_data.get('game_type')
        print(f"After initial processing: {game_type}")
        
        # Handle "All Games" selection - when active_tab is "all", game_type should be None
        if game_type == "all":
            game_type = None
            print(f"After 'all' conversion: {game_type}")
        
        # Only default to Regular Season if game_type is explicitly undefined, not when it's None (All Games)
        # None means "All Games", empty string or False means no selection made
        if game_type == "" or game_type is False:
            game_type = 'R'
            print(f"After default fallback: {game_type}")
        
        return game_type
    
    # Test different callback scenarios
    test_cases = [
        "all",  # Should become None
        None,   # Should stay None
        "",     # Should become 'R'
        False,  # Should become 'R'
        "R",    # Should stay 'R'
        "E",    # Should stay 'E'
        "T",    # Should stay 'T'
    ]
    
    for test_case in test_cases:
        print(f"\nTesting callback with input: {test_case}")
        result = simulate_callback_logic(test_case)
        print(f"Final result: {result}")
        
        # Test the actual data service call
        games = data_service.get_games(team_id, game_type=result)
        print(f"Games returned: {len(games)}")

if __name__ == "__main__":
    debug_all_games_filter()
