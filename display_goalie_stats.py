"""
Simple script to directly display goalie stats without going through the web interface.
This helps verify that the stats are calculated correctly.
"""

from hockey_stats_webapp.services.sheets_service import SheetsService
from hockey_stats_webapp.services.data_service import DataService
import pandas as pd
import sys
import importlib

# Force reload of modules to avoid caching issues
print("=== Forcing module reloads to avoid caching ===")
if 'hockey_stats_webapp.services.data_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.data_service'])
if 'hockey_stats_webapp.services.sheets_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.sheets_service'])

def main():
    print("\n=== Initializing services ===")
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    print("\n=== Finding goalie ===")
    players = data_service.get_players()
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
    
    print("\n=== Calculating goalie stats ===")
    goalie_stats = data_service.calculate_goalie_stats(goalie_id)
    
    if goalie_stats:
        print("\n=== GOALIE STATISTICS ===")
        print(f"Games Played: {goalie_stats['games_played']}")
        print(f"Wins: {goalie_stats['wins']}")
        print(f"Shutouts: {goalie_stats['shutouts']}")
        print(f"Goals Against: {goalie_stats['goals_against']}")
        print(f"Shots Against: {goalie_stats['shots_against']}")
        print(f"Saves: {goalie_stats['saves']}")
        print(f"Save Percentage: {goalie_stats['save_percentage']:.3f}")
        print(f"Goals Against Average: {goalie_stats['gaa']:.2f}")
        
        print("\n=== Getting game log ===")
        game_log = data_service.get_player_game_log(goalie_id)
        print(f"Game log entries: {len(game_log)}")
        
        if game_log:
            print("\n=== GAME LOG ===")
            # Create a DataFrame for better display
            game_log_data = []
            for game_stats in game_log:
                game_log_entry = {
                    'Date': game_stats['game']['Date'],
                    'Opponent': game_stats['game']['Opponent'],
                    'Result': game_stats['result'],
                    'SA': game_stats['shots_against'],
                    'SV': game_stats['saves'],
                    'GA': game_stats['goals_against'],
                    'SV%': f"{game_stats['save_percentage']:.3f}",
                    'SO': 'Yes' if game_stats['shutout'] else 'No'
                }
                game_log_data.append(game_log_entry)
            
            # Convert to DataFrame and display
            df = pd.DataFrame(game_log_data)
            print(df.to_string(index=False))
    else:
        print("ERROR: Failed to calculate goalie statistics!")

if __name__ == "__main__":
    main()
