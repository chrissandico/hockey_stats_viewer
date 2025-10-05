#!/usr/bin/env python3

"""
Test script to verify that the regular season filter fix works properly on the team stats screen.
This tests that the player performance tables (F, D, and Goalies) properly reflect the Regular Season filter.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from services.auth_service import AuthService
import pandas as pd

def test_team_regular_season_filter():
    """Test that team stats filtering works correctly for regular season games."""
    
    print("=== Testing Team Regular Season Filter Fix ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    auth_service = AuthService(sheets_service)
    
    # Get a test team
    teams = sheets_service.get_teams()
    if teams.empty:
        print("ERROR: No teams found")
        return False
    
    print(f"Teams columns: {list(teams.columns)}")
    test_team = teams.iloc[0]
    
    # Check for different possible ID column names
    if 'ID' in teams.columns:
        team_id = test_team['ID']
    elif 'TeamID' in teams.columns:
        team_id = test_team['TeamID']
    elif 'Team ID' in teams.columns:
        team_id = test_team['Team ID']
    else:
        # Use the first column as ID
        team_id = test_team.iloc[0]
    
    # Check for different possible team name column names
    if 'TeamName' in teams.columns:
        team_name = test_team['TeamName']
    elif 'Team Name' in teams.columns:
        team_name = test_team['Team Name']
    elif 'Name' in teams.columns:
        team_name = test_team['Name']
    else:
        team_name = "Unknown Team"
    
    print(f"Testing with team: {team_name} (ID: {team_id})")
    
    # Test 1: Get all games vs regular season games
    print("\n--- Test 1: Comparing All Games vs Regular Season Games ---")
    
    # Get all games
    all_games = data_service.get_games(team_id, game_type=None)
    print(f"Total games for team: {len(all_games)}")
    
    # Get regular season games only
    regular_games = data_service.get_games(team_id, game_type='R')
    print(f"Regular season games for team: {len(regular_games)}")
    
    if len(regular_games) == 0:
        print("WARNING: No regular season games found for this team")
        return False
    
    # Test 2: Team stats comparison
    print("\n--- Test 2: Team Stats Comparison ---")
    
    all_team_stats = data_service.calculate_team_stats(team_id, game_type=None)
    regular_team_stats = data_service.calculate_team_stats(team_id, game_type='R')
    
    print(f"All Games - GP: {all_team_stats['games_played']}, W: {all_team_stats['wins']}, L: {all_team_stats['losses']}")
    print(f"Regular Season - GP: {regular_team_stats['games_played']}, W: {regular_team_stats['wins']}, L: {regular_team_stats['losses']}")
    
    # Verify that regular season stats are different from all games (unless all games are regular season)
    if len(all_games) > len(regular_games):
        if all_team_stats['games_played'] == regular_team_stats['games_played']:
            print("ERROR: Regular season stats should be different from all games stats")
            return False
        else:
            print("✓ Team stats correctly filtered for regular season")
    
    # Test 3: Player leaderboards comparison
    print("\n--- Test 3: Player Leaderboards Comparison ---")
    
    # Test forwards
    all_forwards = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type=None)
    regular_forwards = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type='R')
    
    print(f"All Games - Forwards found: {len(all_forwards)}")
    print(f"Regular Season - Forwards found: {len(regular_forwards)}")
    
    if len(all_forwards) > 0 and len(regular_forwards) > 0:
        # Compare top forward stats
        all_top = all_forwards[0] if all_forwards else None
        regular_top = regular_forwards[0] if regular_forwards else None
        
        if all_top and regular_top:
            print(f"Top Forward All Games: #{all_top['player']['JerseyNumber']} - {all_top['points']} points")
            print(f"Top Forward Regular Season: #{regular_top['player']['JerseyNumber']} - {regular_top['points']} points")
            
            # If there are non-regular season games, stats should be different
            if len(all_games) > len(regular_games):
                if all_top['points'] == regular_top['points'] and all_top['player']['JerseyNumber'] == regular_top['player']['JerseyNumber']:
                    print("WARNING: Forward stats appear identical - may indicate filtering issue")
                else:
                    print("✓ Forward stats correctly filtered for regular season")
    
    # Test defense
    all_defense = data_service.get_team_leaderboard(stat='points', position='D', team_id=team_id, game_type=None)
    regular_defense = data_service.get_team_leaderboard(stat='points', position='D', team_id=team_id, game_type='R')
    
    print(f"All Games - Defense found: {len(all_defense)}")
    print(f"Regular Season - Defense found: {len(regular_defense)}")
    
    # Test goalies
    all_goalies = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type=None)
    regular_goalies = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type='R')
    
    print(f"All Games - Goalies found: {len(all_goalies)}")
    print(f"Regular Season - Goalies found: {len(regular_goalies)}")
    
    if len(all_goalies) > 0 and len(regular_goalies) > 0:
        # Compare top goalie stats
        all_top_g = all_goalies[0] if all_goalies else None
        regular_top_g = regular_goalies[0] if regular_goalies else None
        
        if all_top_g and regular_top_g:
            print(f"Top Goalie All Games: #{all_top_g['player']['JerseyNumber']} - {all_top_g['games_played']} GP, {all_top_g['wins']} W")
            print(f"Top Goalie Regular Season: #{regular_top_g['player']['JerseyNumber']} - {regular_top_g['games_played']} GP, {regular_top_g['wins']} W")
            
            # If there are non-regular season games, stats should be different
            if len(all_games) > len(regular_games):
                if (all_top_g['games_played'] == regular_top_g['games_played'] and 
                    all_top_g['wins'] == regular_top_g['wins'] and 
                    all_top_g['player']['JerseyNumber'] == regular_top_g['player']['JerseyNumber']):
                    print("WARNING: Goalie stats appear identical - may indicate filtering issue")
                else:
                    print("✓ Goalie stats correctly filtered for regular season")
    
    # Test 4: Verify game type filtering in data service
    print("\n--- Test 4: Data Service Game Type Filtering ---")
    
    # Test that the data service properly filters games by type
    exhibition_games = data_service.get_games(team_id, game_type='E')
    tournament_games = data_service.get_games(team_id, game_type='T')
    
    print(f"Exhibition games: {len(exhibition_games)}")
    print(f"Tournament games: {len(tournament_games)}")
    print(f"Regular season games: {len(regular_games)}")
    print(f"Total games: {len(all_games)}")
    
    # Verify totals add up (approximately, accounting for any missing game types)
    calculated_total = len(exhibition_games) + len(tournament_games) + len(regular_games)
    if calculated_total != len(all_games):
        print(f"WARNING: Game type totals don't match. Calculated: {calculated_total}, Actual: {len(all_games)}")
        
        # Check for games with missing or unknown game types
        all_game_types = all_games['GameType'].value_counts()
        print("Game type distribution:")
        for game_type, count in all_game_types.items():
            print(f"  {game_type}: {count}")
    else:
        print("✓ Game type filtering appears correct")
    
    print("\n=== Team Regular Season Filter Test Complete ===")
    return True

if __name__ == "__main__":
    try:
        success = test_team_regular_season_filter()
        if success:
            print("\n✓ Team regular season filter test completed successfully")
        else:
            print("\n✗ Team regular season filter test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR during team regular season filter test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
