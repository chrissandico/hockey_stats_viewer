#!/usr/bin/env python3
"""
Debug script to analyze game stats calculation issues.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def debug_game_stats():
    """Debug game statistics calculations."""
    print("=== DEBUGGING GAME STATS ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Get raw data
    print("\n1. RAW DATA ANALYSIS:")
    teams = sheets_service.get_teams()
    games = sheets_service.get_games()
    events = sheets_service.get_events()
    
    print(f"Teams: {len(teams)} records")
    if not teams.empty:
        print(f"Team columns: {teams.columns.tolist()}")
        print(f"Teams data:\n{teams}")
    
    print(f"\nGames: {len(games)} records")
    if not games.empty:
        print(f"Game columns: {games.columns.tolist()}")
        print(f"Sample game:\n{games.iloc[0] if len(games) > 0 else 'No games'}")
    
    print(f"\nEvents: {len(events)} records")
    if not events.empty:
        print(f"Event columns: {events.columns.tolist()}")
        print(f"Unique teams in events: {events['Team'].unique() if 'Team' in events.columns else 'No Team column'}")
        print(f"Sample event:\n{events.iloc[0] if len(events) > 0 else 'No events'}")
    
    # Test team identification
    print("\n2. TEAM IDENTIFICATION TEST:")
    if not teams.empty:
        first_team_id = teams.iloc[0]['TeamID']
        first_team_name = teams.iloc[0]['TeamName']
        print(f"First team: ID='{first_team_id}', Name='{first_team_name}'")
        
        # Check if this team appears in events
        if not events.empty and 'Team' in events.columns:
            team_in_events_by_id = events['Team'].str.contains(first_team_id, na=False).any()
            team_in_events_by_name = events['Team'].str.contains(first_team_name, na=False).any()
            print(f"Team ID '{first_team_id}' found in events: {team_in_events_by_id}")
            print(f"Team Name '{first_team_name}' found in events: {team_in_events_by_name}")
    
    # Test game calculations
    print("\n3. GAME CALCULATION TEST:")
    if not games.empty:
        # Get processed games
        processed_games = data_service.get_games()
        print(f"Processed games: {len(processed_games)} records")
        
        if not processed_games.empty:
            sample_game = processed_games.iloc[0]
            print(f"Sample processed game:")
            print(f"  ID: {sample_game['ID']}")
            print(f"  Date: {sample_game['Date']}")
            print(f"  Opponent: {sample_game['Opponent']}")
            print(f"  GoalsFor: {sample_game.get('GoalsFor', 'Missing')}")
            print(f"  GoalsAgainst: {sample_game.get('GoalsAgainst', 'Missing')}")
            print(f"  Result: {sample_game.get('Result', 'Missing')}")
            
            # Test game summary
            game_id = sample_game['ID']
            print(f"\n4. GAME SUMMARY TEST for game {game_id}:")
            summary = data_service.get_game_summary(game_id)
            if summary:
                print(f"  Your team shots: {summary['your_team_shots']}")
                print(f"  Opponent shots: {summary['opponent_shots']}")
                print(f"  Your team goals: {summary['game']['GoalsFor']}")
                print(f"  Opponent goals: {summary['game']['GoalsAgainst']}")
            else:
                print("  No summary available")
    
    # Test event filtering
    print("\n5. EVENT FILTERING TEST:")
    if not events.empty and not games.empty:
        sample_game_id = games.iloc[0]['ID']
        game_events = events[events['GameID'] == sample_game_id]
        print(f"Events for game {sample_game_id}: {len(game_events)}")
        
        if not game_events.empty:
            print(f"Event types: {game_events['EventType'].value_counts().to_dict()}")
            if 'IsGoal' in game_events.columns:
                print(f"IsGoal values: {game_events['IsGoal'].value_counts().to_dict()}")
            if 'Team' in game_events.columns:
                print(f"Teams in events: {game_events['Team'].value_counts().to_dict()}")

if __name__ == "__main__":
    debug_game_stats()
