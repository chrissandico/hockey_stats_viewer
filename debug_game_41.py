#!/usr/bin/env python3
"""
Debug script to investigate game ID 41 and why goals aren't showing up correctly.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
import pandas as pd

def debug_game_41():
    """Debug game ID 41 specifically."""
    print("=== DEBUGGING GAME ID 41 ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Get raw data
    games = sheets_service.get_games()
    events = sheets_service.get_events()
    
    print(f"\n--- Raw Games Data ---")
    game_41 = games[games['ID'] == 41]
    if not game_41.empty:
        print("Game 41 found in Games sheet:")
        print(game_41.to_dict('records')[0])
    else:
        print("❌ Game 41 NOT found in Games sheet")
        return
    
    print(f"\n--- Raw Events Data for Game 41 ---")
    game_41_events = events[events['GameID'] == 41]
    print(f"Found {len(game_41_events)} events for game 41")
    
    if not game_41_events.empty:
        print("Events for game 41:")
        for _, event in game_41_events.iterrows():
            print(f"  Event {event['ID']}: {event['EventType']}, Team: {event['Team']}, IsGoal: {event['IsGoal']}")
    
    print(f"\n--- Team Identifier Mapping ---")
    team_id = game_41.iloc[0]['TeamID'] if not game_41.empty else 'test_team'
    print(f"Game 41 TeamID: {team_id}")
    
    team_identifier = data_service._get_team_identifier_for_events(team_id)
    print(f"Mapped team identifier: {team_identifier}")
    
    print(f"\n--- Goal Calculation for Game 41 ---")
    goals_for = len(game_41_events[(game_41_events['IsGoal'] == True) & 
                                  (game_41_events['Team'] == team_identifier)])
    goals_against = len(game_41_events[(game_41_events['IsGoal'] == True) & 
                                      (game_41_events['Team'] != team_identifier)])
    
    print(f"Goals FOR {team_identifier}: {goals_for}")
    print(f"Goals AGAINST {team_identifier}: {goals_against}")
    
    print(f"\n--- DataService Game Calculation ---")
    # Test the data service calculation
    test_team_games = data_service.get_games('test_team')
    game_41_from_service = test_team_games[test_team_games['ID'] == 41]
    
    if not game_41_from_service.empty:
        game_data = game_41_from_service.iloc[0]
        print(f"DataService calculated:")
        print(f"  GoalsFor: {game_data.get('GoalsFor', 'N/A')}")
        print(f"  GoalsAgainst: {game_data.get('GoalsAgainst', 'N/A')}")
        print(f"  Result: {game_data.get('Result', 'N/A')}")
    else:
        print("❌ Game 41 not found in DataService results")
    
    print(f"\n--- All Test Team Games ---")
    test_games = test_team_games[['ID', 'Date', 'Opponent', 'GoalsFor', 'GoalsAgainst', 'Result']]
    print(test_games.to_string(index=False))
    
    print(f"\n--- Events Team Distribution ---")
    team_counts = events['Team'].value_counts()
    print("All teams in events:")
    for team, count in team_counts.items():
        print(f"  {team}: {count} events")

def main():
    """Main debug function."""
    try:
        debug_game_41()
    except Exception as e:
        print(f"\n💥 Debug failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
