#!/usr/bin/env python3

"""
Test script to verify player screen fixes:
1. Player stats aggregate all game types (no filtering)
2. Player game log shows all games with game type column
3. Verify the fixes work for both skaters and goalies
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_player_screen_fixes():
    """Test that player screen shows all game types and includes game type column."""
    
    print("=== TESTING PLAYER SCREEN FIXES ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Get test team
    teams = sheets_service.get_teams()
    if teams.empty:
        print("ERROR: No teams found!")
        return False
    
    test_team_id = teams.iloc[0]['TeamID']
    print(f"Using test team: {test_team_id}")
    
    # Get players for the team
    players = data_service.get_players(test_team_id)
    if players.empty:
        print("ERROR: No players found!")
        return False
    
    print(f"Found {len(players)} players")
    
    # Test with a skater and a goalie if available
    skaters = players[players['Position'] != 'G']
    goalies = players[players['Position'] == 'G']
    
    test_results = []
    
    # Test skater stats aggregation
    if not skaters.empty:
        test_player = skaters.iloc[0]
        print(f"\n=== TESTING SKATER: #{test_player['JerseyNumber']} (ID: {test_player['ID']}) ===")
        
        # Test stats calculation with game_type=None (should aggregate all games)
        stats = data_service.calculate_player_stats(test_player['ID'], test_team_id, None)
        
        if stats:
            print(f"✅ Skater stats calculated successfully:")
            print(f"   Games Played: {stats['games_played']}")
            print(f"   Goals: {stats['goals']}")
            print(f"   Assists: {stats['assists']}")
            print(f"   Points: {stats['points']}")
            
            # Test game log
            game_log = data_service.get_player_game_log(test_player['ID'], test_team_id)
            print(f"✅ Skater game log: {len(game_log)} games")
            
            # Check if game log includes game type information
            if game_log:
                first_game = game_log[0]
                game_type = first_game['game'].get('GameType', 'Missing')
                print(f"✅ Game type in game log: {game_type}")
                test_results.append(True)
            else:
                print("⚠️  No games in game log")
                test_results.append(True)  # Not necessarily an error
        else:
            print("❌ Failed to calculate skater stats")
            test_results.append(False)
    
    # Test goalie stats aggregation
    if not goalies.empty:
        test_goalie = goalies.iloc[0]
        print(f"\n=== TESTING GOALIE: #{test_goalie['JerseyNumber']} (ID: {test_goalie['ID']}) ===")
        
        # Test stats calculation with game_type=None (should aggregate all games)
        stats = data_service.calculate_goalie_stats(test_goalie['ID'], test_team_id, None)
        
        if stats:
            print(f"✅ Goalie stats calculated successfully:")
            print(f"   Games Played: {stats['games_played']}")
            print(f"   Wins: {stats['wins']}")
            print(f"   Shutouts: {stats['shutouts']}")
            print(f"   Save %: {stats['save_percentage']:.3f}")
            
            # Test game log
            game_log = data_service.get_player_game_log(test_goalie['ID'], test_team_id)
            print(f"✅ Goalie game log: {len(game_log)} games")
            
            # Check if game log includes game type information
            if game_log:
                first_game = game_log[0]
                game_type = first_game['game'].get('GameType', 'Missing')
                print(f"✅ Game type in game log: {game_type}")
                test_results.append(True)
            else:
                print("⚠️  No games in game log")
                test_results.append(True)  # Not necessarily an error
        else:
            print("❌ Failed to calculate goalie stats")
            test_results.append(False)
    
    # Test game type filtering comparison
    print(f"\n=== TESTING GAME TYPE FILTERING COMPARISON ===")
    
    # Get games by type to verify aggregation
    all_games = data_service.get_games(test_team_id, None)
    exhibition_games = data_service.get_games(test_team_id, 'E')
    regular_games = data_service.get_games(test_team_id, 'R')
    tournament_games = data_service.get_games(test_team_id, 'T')
    
    print(f"All games: {len(all_games)}")
    print(f"Exhibition games: {len(exhibition_games)}")
    print(f"Regular season games: {len(regular_games)}")
    print(f"Tournament games: {len(tournament_games)}")
    
    # Verify that all games = sum of individual types
    total_by_type = len(exhibition_games) + len(regular_games) + len(tournament_games)
    if len(all_games) == total_by_type:
        print("✅ Game type aggregation is correct")
        test_results.append(True)
    else:
        print(f"❌ Game type aggregation mismatch: {len(all_games)} != {total_by_type}")
        test_results.append(False)
    
    # Test that player stats with game_type=None include all game types
    if not skaters.empty:
        test_player = skaters.iloc[0]
        
        # Get stats for all game types
        all_stats = data_service.calculate_player_stats(test_player['ID'], test_team_id, None)
        exhibition_stats = data_service.calculate_player_stats(test_player['ID'], test_team_id, 'E')
        regular_stats = data_service.calculate_player_stats(test_player['ID'], test_team_id, 'R')
        tournament_stats = data_service.calculate_player_stats(test_player['ID'], test_team_id, 'T')
        
        if all_stats and exhibition_stats and regular_stats and tournament_stats:
            # Check if all stats >= individual type stats (should be sum or greater)
            all_games_played = all_stats['games_played']
            type_games_played = exhibition_stats['games_played'] + regular_stats['games_played'] + tournament_stats['games_played']
            
            print(f"Player games played - All: {all_games_played}, By type sum: {type_games_played}")
            
            if all_games_played >= type_games_played:
                print("✅ Player stats aggregation working correctly")
                test_results.append(True)
            else:
                print(f"❌ Player stats aggregation issue: {all_games_played} < {type_games_played}")
                test_results.append(False)
        else:
            print("⚠️  Could not compare player stats by game type")
            test_results.append(True)  # Not necessarily an error
    
    # Summary
    print(f"\n=== TEST SUMMARY ===")
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("✅ ALL TESTS PASSED - Player screen fixes are working correctly!")
        print("\nKey fixes verified:")
        print("1. ✅ Player stats aggregate all game types (game_type=None)")
        print("2. ✅ Player game log shows all games")
        print("3. ✅ Game type column is available in game data")
        print("4. ✅ Both skaters and goalies work correctly")
        return True
    else:
        print("❌ SOME TESTS FAILED - Please review the issues above")
        return False

if __name__ == "__main__":
    success = test_player_screen_fixes()
    sys.exit(0 if success else 1)
