#!/usr/bin/env python3

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def debug_game_summary_issue():
    """Debug the game summary issue for starsu11a team."""
    
    print("=== DEBUGGING GAME SUMMARY ISSUE ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    team_id = "starsu11a"
    game_id = 32  # The game that was showing incorrect scores
    
    print(f"\n1. Testing get_games method for team {team_id}:")
    games = data_service.get_games(team_id)
    game_from_games = games[games['ID'] == game_id]
    if not game_from_games.empty:
        game_row = game_from_games.iloc[0]
        print(f"   Game {game_id} from get_games:")
        print(f"   - GoalsFor: {game_row.get('GoalsFor', 'N/A')}")
        print(f"   - GoalsAgainst: {game_row.get('GoalsAgainst', 'N/A')}")
        print(f"   - Result: {game_row.get('Result', 'N/A')}")
    else:
        print(f"   Game {game_id} not found in get_games results")
    
    print(f"\n2. Testing get_game_by_id method:")
    game_by_id = data_service.get_game_by_id(game_id, team_id)
    if game_by_id is not None:
        print(f"   Game {game_id} from get_game_by_id:")
        print(f"   - GoalsFor: {game_by_id.get('GoalsFor', 'N/A')}")
        print(f"   - GoalsAgainst: {game_by_id.get('GoalsAgainst', 'N/A')}")
        print(f"   - Result: {game_by_id.get('Result', 'N/A')}")
    else:
        print(f"   Game {game_id} not found by get_game_by_id")
    
    print(f"\n3. Testing get_game_summary method:")
    game_summary = data_service.get_game_summary(game_id, team_id)
    if game_summary is not None:
        game_obj = game_summary['game']
        print(f"   Game {game_id} from get_game_summary:")
        print(f"   - GoalsFor: {game_obj.get('GoalsFor', 'N/A')}")
        print(f"   - GoalsAgainst: {game_obj.get('GoalsAgainst', 'N/A')}")
        print(f"   - Result: {game_obj.get('Result', 'N/A')}")
    else:
        print(f"   Game summary for {game_id} not found")
    
    print(f"\n4. Checking raw events for game {game_id}:")
    events = data_service.get_events()
    game_events = events[events['GameID'] == game_id]
    
    # Count goals by team
    goal_events = game_events[game_events['IsGoal'] == True]
    print(f"   Total goal events: {len(goal_events)}")
    
    if not goal_events.empty:
        team_counts = goal_events['Team'].value_counts()
        print(f"   Goals by team: {team_counts.to_dict()}")
        
        # Check what team identifier is being used
        team_identifier = data_service._get_team_identifier_for_events(team_id)
        print(f"   Team identifier for {team_id}: '{team_identifier}'")
        
        starsu11a_goals = len(goal_events[goal_events['Team'] == 'starsu11a'])
        opponent_goals = len(goal_events[goal_events['Team'] == 'opponent'])
        your_team_goals = len(goal_events[goal_events['Team'] == 'your_team'])
        
        print(f"   Goals for 'starsu11a': {starsu11a_goals}")
        print(f"   Goals for 'opponent': {opponent_goals}")
        print(f"   Goals for 'your_team': {your_team_goals}")
    
    print(f"\n5. Checking cache status:")
    if hasattr(data_service, '_games_calculated_cache'):
        cache_keys = list(data_service._games_calculated_cache.keys())
        print(f"   Cached game data keys: {cache_keys}")
        
        # Check if the cached data has the correct values
        for key in cache_keys:
            if team_id in key:
                cached_games = data_service._games_calculated_cache[key]
                cached_game = cached_games[cached_games['ID'] == game_id]
                if not cached_game.empty:
                    cached_row = cached_game.iloc[0]
                    print(f"   Cached game {game_id} in {key}:")
                    print(f"   - GoalsFor: {cached_row.get('GoalsFor', 'N/A')}")
                    print(f"   - GoalsAgainst: {cached_row.get('GoalsAgainst', 'N/A')}")
    else:
        print("   No game cache found")

if __name__ == "__main__":
    debug_game_summary_issue()
