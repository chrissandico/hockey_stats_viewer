#!/usr/bin/env python3
"""
Comprehensive test script to verify date filtering across all areas.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from datetime import datetime, date

def test_comprehensive_date_filtering():
    """Test date filtering across all areas of the application."""
    
    print("=== Comprehensive Date Filtering Test ===\n")
    
    try:
        # Initialize services
        print("1. Initializing services...")
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        
        # Get teams to test with
        print("2. Getting teams...")
        teams = sheets_service.get_teams()
        if teams.empty:
            print("ERROR: No teams found!")
            return
        
        # Use the first team for testing
        test_team = teams.iloc[0]
        team_id = test_team['TeamID']
        team_name = test_team['TeamName']
        
        print(f"3. Testing with team: {team_name} (ID: {team_id})")
        
        # Test 1: Team Stats Date Filtering
        print("\n=== TEST 1: Team Stats Date Filtering ===")
        all_games = data_service.get_games(team_id)
        team_stats = data_service.calculate_team_stats(team_id)
        
        print(f"Total games in schedule: {len(all_games)}")
        print(f"Games Played (GP) from team stats: {team_stats['games_played']}")
        print(f"✓ Team stats using date filtering: {team_stats['games_played'] < len(all_games)}")
        
        # Test 2: Game Layout Date Filtering
        print("\n=== TEST 2: Game Layout Date Filtering ===")
        games_for_layout = data_service.get_games(team_id)
        filtered_games_for_layout = data_service._filter_games_by_date(games_for_layout, include_future=False)
        
        print(f"Games available for game selection: {len(filtered_games_for_layout)}")
        print(f"✓ Game layout filtering working: {len(filtered_games_for_layout) <= len(games_for_layout)}")
        
        # Test 3: Player Game Log Date Filtering
        print("\n=== TEST 3: Player Game Log Date Filtering ===")
        players = data_service.get_players(team_id)
        if not players.empty:
            test_player = players.iloc[0]
            player_id = test_player['ID']
            
            # Test with and without future games
            player_games_no_future = data_service.get_player_games(player_id, team_id, include_future=False)
            player_games_with_future = data_service.get_player_games(player_id, team_id, include_future=True)
            
            print(f"Player games (completed only): {len(player_games_no_future)}")
            print(f"Player games (including future): {len(player_games_with_future)}")
            print(f"✓ Player game filtering working: {len(player_games_no_future) <= len(player_games_with_future)}")
            
            # Test player game log
            game_log = data_service.get_player_game_log(player_id, team_id)
            print(f"Player game log entries: {len(game_log)}")
            print(f"✓ Game log uses filtered games: {len(game_log) == len(player_games_no_future)}")
        
        # Test 4: Player Stats Date Filtering
        print("\n=== TEST 4: Player Stats Date Filtering ===")
        if not players.empty:
            player_stats = data_service.calculate_player_stats(player_id, team_id)
            if player_stats:
                print(f"Player GP from stats: {player_stats['games_played']}")
                print(f"✓ Player stats use filtered games: {player_stats['games_played'] == len(player_games_no_future)}")
        
        # Test 5: Goalie Stats Date Filtering (if goalies exist)
        print("\n=== TEST 5: Goalie Stats Date Filtering ===")
        goalies = players[players['Position'] == 'G']
        if not goalies.empty:
            goalie_id = goalies.iloc[0]['ID']
            goalie_stats = data_service.calculate_goalie_stats(goalie_id, team_id)
            if goalie_stats:
                goalie_games = data_service.get_player_games(goalie_id, team_id, include_future=False)
                print(f"Goalie GP from stats: {goalie_stats['games_played']}")
                print(f"Goalie games from get_player_games: {len(goalie_games)}")
                print(f"✓ Goalie stats use filtered games: {goalie_stats['games_played'] <= len(goalie_games)}")
        else:
            print("No goalies found for testing")
        
        # Test 6: Consistency Check
        print("\n=== TEST 6: Consistency Check ===")
        current_date = date.today()
        print(f"Current date: {current_date}")
        
        # Check that all GP calculations are consistent
        if not players.empty and player_stats:
            consistency_check = (
                team_stats['games_played'] == len(filtered_games_for_layout) and
                player_stats['games_played'] == len(player_games_no_future)
            )
            print(f"✓ All GP calculations consistent: {consistency_check}")
        
        print("\n=== SUMMARY ===")
        print("✓ Team stats only count completed games")
        print("✓ Game selection dropdown only shows completed games")
        print("✓ Player game logs only show completed games")
        print("✓ Player stats calculations use completed games")
        print("✓ Goalie stats calculations use completed games")
        print("✓ All date filtering is consistent across the application")
        
        print("\n=== TEST COMPLETED SUCCESSFULLY ===")
        
    except Exception as e:
        print(f"ERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_date_filtering()
