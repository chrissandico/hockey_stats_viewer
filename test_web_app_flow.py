"""
Test script that mimics the exact flow of the web app when selecting a goalie.
This helps diagnose why goalie stats might be showing zeros in the web interface.
"""

import sys
import importlib
import pandas as pd

# Force reload of modules to avoid caching issues
print("=== TEST: Forcing module reloads to avoid caching ===")
if 'hockey_stats_webapp.services.data_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.data_service'])
if 'hockey_stats_webapp.services.sheets_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.sheets_service'])

# Import services
from hockey_stats_webapp.services.sheets_service import SheetsService
from hockey_stats_webapp.services.data_service import DataService

def main():
    print("\n=== TEST: Initializing services (exactly as web app does) ===")
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    print("\n=== TEST: Simulating player dropdown initialization ===")
    # Get all players for the dropdown (as done in create_player_layout)
    players = data_service.get_players()
    print(f"Total players: {len(players)}")
    
    # Find goalies
    goalies = players[players['Position'] == 'G']
    print(f"Found {len(goalies)} goalies in player data")
    
    if goalies.empty:
        print("ERROR: No goalies found in player data!")
        return
    
    # Get the first goalie
    goalie = goalies.iloc[0]
    goalie_id = goalie['ID']
    jersey_number = goalie.get('JerseyNumber', 'Unknown')
    print(f"Using goalie: ID={goalie_id}, Jersey={jersey_number}")
    
    print("\n=== TEST: Simulating player selection callback ===")
    # Simulate the callback when a player is selected
    print(f"Getting player with jersey number: {jersey_number}")
    player = data_service.get_player_by_jersey(jersey_number)
    if player is None:
        print(f"ERROR: Player with jersey number {jersey_number} not found!")
        return
    
    print(f"Found player: ID={player['ID']}, Position={player['Position']}")
    
    # Check if player is a goalie and calculate appropriate stats
    is_goalie = player['Position'] == 'G'
    print(f"Player position: {player['Position']}, Is goalie: {is_goalie}")
    
    if is_goalie:
        print(f"=== TEST: Calculating goalie stats for player ID: {player['ID']} ===")
        
        # Debug: Check game roster for goalie
        print("Getting game roster...")
        game_roster = data_service.get_game_roster()
        goalie_roster = game_roster[game_roster['PlayerID'] == player['ID']]
        print(f"DEBUG: Goalie roster entries: {len(goalie_roster)}")
        
        # Debug: Check games for goalie
        print("Getting player games...")
        goalie_games = data_service.get_player_games(player['ID'])
        print(f"DEBUG: Goalie games count: {len(goalie_games)}")
        if not goalie_games.empty:
            print(f"DEBUG: First game data: {goalie_games.iloc[0].to_dict()}")
        else:
            print("WARNING: No games found for goalie!")
        
        # Calculate goalie stats
        print("Calculating goalie stats...")
        try:
            stats = data_service.calculate_goalie_stats(player['ID'])
            print(f"DEBUG: Goalie stats calculated: {stats}")
            
            # Verify stats values
            if stats:
                print(f"Goalie stats verification:")
                print(f"  Games Played: {stats['games_played']}")
                print(f"  Wins: {stats['wins']}")
                print(f"  Shutouts: {stats['shutouts']}")
                print(f"  Goals Against: {stats['goals_against']}")
                print(f"  Shots Against: {stats['shots_against']}")
                print(f"  Saves: {stats['saves']}")
                print(f"  Save Percentage: {stats['save_percentage']:.3f}")
            else:
                print("ERROR: calculate_goalie_stats returned None!")
        except Exception as e:
            print(f"EXCEPTION in calculate_goalie_stats: {str(e)}")
            import traceback
            traceback.print_exc()
            stats = None
        
        # Debug: Check game log for goalie
        print("Getting player game log...")
        game_log = data_service.get_player_game_log(player['ID'])
        print(f"DEBUG: Goalie game log entries: {len(game_log)}")
        if game_log:
            print(f"DEBUG: First game log entry: {game_log[0]}")
    else:
        print(f"Calculating player stats for player ID: {player['ID']}")
        stats = data_service.calculate_player_stats(player['ID'])
    
    print("\n=== TEST: Completed web app flow simulation ===")
    if stats:
        print("SUCCESS: Stats were calculated correctly")
    else:
        print("ERROR: Failed to calculate stats")

if __name__ == "__main__":
    main()
