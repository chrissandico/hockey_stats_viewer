#!/usr/bin/env python3
"""
Debug script to investigate game ID 38 and verify the goals are showing up correctly.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
import pandas as pd

def debug_game_38():
    """Debug game ID 38 specifically."""
    print("=== DEBUGGING GAME ID 38 ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Get raw data
    games = sheets_service.get_games()
    events = sheets_service.get_events()
    
    print(f"\n--- Raw Games Data ---")
    game_38 = games[games['ID'] == 38]
    if not game_38.empty:
        print("Game 38 found in Games sheet:")
        print(game_38.to_dict('records')[0])
    else:
        print("❌ Game 38 NOT found in Games sheet")
        return
    
    print(f"\n--- Raw Events Data for Game 38 ---")
    game_38_events = events[events['GameID'] == 38]
    print(f"Found {len(game_38_events)} events for game 38")
    
    if not game_38_events.empty:
        print("Events for game 38:")
        goals_for_test_team = 0
        goals_against_test_team = 0
        
        for _, event in game_38_events.iterrows():
            is_goal = event['IsGoal']
            team = event['Team']
            event_type = event['EventType']
            
            if is_goal:
                if team == 'test_team':
                    goals_for_test_team += 1
                else:
                    goals_against_test_team += 1
            
            print(f"  Event {event['ID']}: {event_type}, Team: {team}, IsGoal: {is_goal}")
        
        print(f"\nGoal Summary:")
        print(f"  Goals FOR test_team: {goals_for_test_team}")
        print(f"  Goals AGAINST test_team: {goals_against_test_team}")
    
    print(f"\n--- Team Identifier Mapping ---")
    team_id = game_38.iloc[0]['TeamID'] if not game_38.empty else 'test_team'
    print(f"Game 38 TeamID: {team_id}")
    
    team_identifier = data_service._get_team_identifier_for_events(team_id)
    print(f"Mapped team identifier: {team_identifier}")
    
    print(f"\n--- DataService Game Calculation ---")
    # Test the data service calculation
    test_team_games = data_service.get_games('test_team')
    game_38_from_service = test_team_games[test_team_games['ID'] == 38]
    
    if not game_38_from_service.empty:
        game_data = game_38_from_service.iloc[0]
        print(f"DataService calculated:")
        print(f"  GoalsFor: {game_data.get('GoalsFor', 'N/A')}")
        print(f"  GoalsAgainst: {game_data.get('GoalsAgainst', 'N/A')}")
        print(f"  Result: {game_data.get('Result', 'N/A')}")
    else:
        print("❌ Game 38 not found in DataService results")
    
    print(f"\n--- Team Stats Calculation ---")
    team_stats = data_service.calculate_team_stats('test_team')
    print(f"Team Stats:")
    print(f"  Games Played: {team_stats['games_played']}")
    print(f"  Wins: {team_stats['wins']}")
    print(f"  Losses: {team_stats['losses']}")
    print(f"  Ties: {team_stats['ties']}")
    print(f"  Goals For: {team_stats['goals_for']}")
    print(f"  Goals Against: {team_stats['goals_against']}")
    
    print(f"\n--- All Test Team Games ---")
    test_games = test_team_games[['ID', 'Date', 'Opponent', 'GoalsFor', 'GoalsAgainst', 'Result']]
    print(test_games.to_string(index=False))

def main():
    """Main debug function."""
    try:
        debug_game_38()
    except Exception as e:
        print(f"\n💥 Debug failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
