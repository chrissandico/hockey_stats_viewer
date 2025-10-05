#!/usr/bin/env python3

"""
Test script to verify that player stats and game log properly filter by game type.
This addresses the user's question about whether player stats show up according to the game filter.
"""

import sys
import os
import traceback

# Add the hockey_stats_webapp directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def test_player_game_type_filtering():
    """Test that player stats and game log properly respect game type filtering."""
    
    print("=== TESTING PLAYER GAME TYPE FILTERING ===")
    
    try:
        # Import required modules
        from services.sheets_service import SheetsService
        from services.data_service import DataService
        
        print("1. Initializing services...")
        
        try:
            sheets_service = SheetsService()
            data_service = DataService(sheets_service)
            print("   ✓ Services initialized successfully")
        except Exception as e:
            print(f"   ⚠ Services failed to initialize (expected): {e}")
            print("   This test requires credentials.json to run properly")
            return
        
        print("\n2. Testing game type filtering for player stats...")
        
        # Get a test player
        players = data_service.get_players()
        if players.empty:
            print("   ⚠ No players found")
            return
        
        # Find a skater (non-goalie) for testing
        skaters = players[players['Position'] != 'G']
        if skaters.empty:
            print("   ⚠ No skaters found")
            return
        
        test_player = skaters.iloc[0]
        player_id = data_service._get_player_id_from_series(test_player)
        jersey_number = test_player['JerseyNumber']
        
        print(f"   Testing with player #{jersey_number} (ID: {player_id})")
        
        # Test different game types
        game_types = ['R', 'E', 'T']  # Regular Season, Exhibition, Tournament
        game_type_names = {'R': 'Regular Season', 'E': 'Exhibition', 'T': 'Tournament'}
        
        for game_type in game_types:
            print(f"\n   Testing game type: {game_type_names[game_type]} ({game_type})")
            
            # Test season stats with game type filter
            try:
                stats = data_service.calculate_player_stats(player_id, game_type=game_type)
                if stats:
                    print(f"     Season Stats: {stats['games_played']} GP, {stats['goals']}G, {stats['assists']}A, {stats['points']}P")
                else:
                    print(f"     Season Stats: No stats calculated")
            except Exception as e:
                print(f"     ❌ Error calculating season stats: {e}")
            
            # Test game log with game type filter - THIS IS THE POTENTIAL ISSUE
            try:
                game_log = data_service.get_player_game_log(player_id)
                print(f"     Game Log (NO filter): {len(game_log)} games")
                
                # Check if game log respects game type by examining game types in the log
                if game_log:
                    game_types_in_log = set()
                    for game_stats in game_log:
                        game_type_in_log = game_stats['game'].get('GameType', 'Unknown')
                        game_types_in_log.add(game_type_in_log)
                    
                    print(f"     Game types in log: {list(game_types_in_log)}")
                    
                    # Count games by type
                    type_counts = {}
                    for game_stats in game_log:
                        gt = game_stats['game'].get('GameType', 'Unknown')
                        type_counts[gt] = type_counts.get(gt, 0) + 1
                    
                    print(f"     Game type breakdown: {type_counts}")
                
            except Exception as e:
                print(f"     ❌ Error getting game log: {e}")
        
        print("\n3. Testing the issue: Game log should filter by game type but doesn't...")
        
        # Get all games for comparison
        all_games = data_service.get_player_games(player_id)
        regular_season_games = data_service.get_player_games(player_id, game_type='R')
        
        print(f"   All games for player: {len(all_games)}")
        print(f"   Regular season games only: {len(regular_season_games)}")
        
        # Get game log (which should be filtered but isn't)
        game_log = data_service.get_player_game_log(player_id)
        print(f"   Game log entries: {len(game_log)}")
        
        if len(game_log) == len(all_games) and len(regular_season_games) < len(all_games):
            print("   ❌ ISSUE CONFIRMED: Game log shows ALL games, not filtered by game type!")
            print("   The get_player_game_log method needs to accept and use game_type parameter")
        elif len(game_log) == len(regular_season_games):
            print("   ✓ Game log appears to be filtered correctly")
        else:
            print("   ⚠ Unclear filtering behavior - needs investigation")
        
        print("\n4. Testing goalie game type filtering...")
        
        # Find a goalie for testing
        goalies = players[players['Position'] == 'G']
        if not goalies.empty:
            test_goalie = goalies.iloc[0]
            goalie_id = data_service._get_player_id_from_series(test_goalie)
            goalie_jersey = test_goalie['JerseyNumber']
            
            print(f"   Testing with goalie #{goalie_jersey} (ID: {goalie_id})")
            
            # Test goalie stats with different game types
            for game_type in game_types:
                try:
                    goalie_stats = data_service.calculate_goalie_stats(goalie_id, game_type=game_type)
                    if goalie_stats:
                        print(f"     {game_type_names[game_type]}: {goalie_stats['games_played']} GP, {goalie_stats['wins']} W, {goalie_stats['save_percentage']:.3f} SV%")
                    else:
                        print(f"     {game_type_names[game_type]}: No stats calculated")
                except Exception as e:
                    print(f"     ❌ Error calculating goalie stats for {game_type}: {e}")
        
        print("\n=== GAME TYPE FILTERING TEST COMPLETE ===")
        
    except Exception as e:
        print(f"CRITICAL ERROR in test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_player_game_type_filtering()
