#!/usr/bin/env python3

"""
Test script to verify the All Games aggregation fix for Player #25.
This script tests the fix locally to ensure it works before investigating deployment issues.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.data_service import DataService
from services.sheets_service import SheetsService

def test_player_25_all_games_fix():
    """Test that Player #25 shows correct stats when All Games is selected."""
    
    print("=== TESTING ALL GAMES AGGREGATION FIX ===")
    print("Testing Player #25 statistics aggregation across all game types...")
    
    try:
        # Initialize services
        sheets_service = SheetsService()
        data_service = DataService(sheets_service, force_refresh=True)
        
        player_id = "25"
        team_id = "your_team"
        
        print(f"\n1. Testing individual game types for Player #{player_id}:")
        
        # Test Exhibition games
        exhibition_stats = data_service.calculate_player_stats(player_id, team_id, game_type='E')
        if exhibition_stats:
            print(f"   Exhibition: {exhibition_stats['games_played']} GP, {exhibition_stats['goals']}G, {exhibition_stats['assists']}A, {exhibition_stats['points']}P, {exhibition_stats['plus_minus']}+/-, {exhibition_stats['penalty_minutes']}PIM")
        else:
            print("   Exhibition: No stats found")
        
        # Test Tournament games
        tournament_stats = data_service.calculate_player_stats(player_id, team_id, game_type='T')
        if tournament_stats:
            print(f"   Tournament: {tournament_stats['games_played']} GP, {tournament_stats['goals']}G, {tournament_stats['assists']}A, {tournament_stats['points']}P, {tournament_stats['plus_minus']}+/-, {tournament_stats['penalty_minutes']}PIM")
        else:
            print("   Tournament: No stats found")
        
        # Test Regular Season games
        regular_stats = data_service.calculate_player_stats(player_id, team_id, game_type='R')
        if regular_stats:
            print(f"   Regular Season: {regular_stats['games_played']} GP, {regular_stats['goals']}G, {regular_stats['assists']}A, {regular_stats['points']}P, {regular_stats['plus_minus']}+/-, {regular_stats['penalty_minutes']}PIM")
        else:
            print("   Regular Season: No stats found")
        
        print(f"\n2. Testing All Games aggregation for Player #{player_id}:")
        
        # Test All Games (game_type=None)
        all_games_stats = data_service.calculate_player_stats(player_id, team_id, game_type=None)
        if all_games_stats:
            print(f"   All Games: {all_games_stats['games_played']} GP, {all_games_stats['goals']}G, {all_games_stats['assists']}A, {all_games_stats['points']}P, {all_games_stats['plus_minus']}+/-, {all_games_stats['penalty_minutes']}PIM")
            
            # Calculate expected totals
            expected_gp = 0
            expected_goals = 0
            expected_assists = 0
            expected_points = 0
            expected_pim = 0
            
            if exhibition_stats:
                expected_gp += exhibition_stats['games_played']
                expected_goals += exhibition_stats['goals']
                expected_assists += exhibition_stats['assists']
                expected_points += exhibition_stats['points']
                expected_pim += exhibition_stats['penalty_minutes']
            
            if tournament_stats:
                expected_gp += tournament_stats['games_played']
                expected_goals += tournament_stats['goals']
                expected_assists += tournament_stats['assists']
                expected_points += tournament_stats['points']
                expected_pim += tournament_stats['penalty_minutes']
            
            if regular_stats:
                expected_gp += regular_stats['games_played']
                expected_goals += regular_stats['goals']
                expected_assists += regular_stats['assists']
                expected_points += regular_stats['points']
                expected_pim += regular_stats['penalty_minutes']
            
            print(f"\n3. Verification:")
            print(f"   Expected totals: {expected_gp} GP, {expected_goals}G, {expected_assists}A, {expected_points}P, {expected_pim}PIM")
            print(f"   Actual totals:   {all_games_stats['games_played']} GP, {all_games_stats['goals']}G, {all_games_stats['assists']}A, {all_games_stats['points']}P, {all_games_stats['penalty_minutes']}PIM")
            
            # Check if fix is working
            if all_games_stats['games_played'] == expected_gp and all_games_stats['games_played'] > 0:
                print(f"   ✅ SUCCESS: All Games aggregation is working correctly!")
                print(f"   ✅ Player #25 shows {all_games_stats['games_played']} total games (should be 5: 1 Exhibition + 4 Tournament)")
                return True
            else:
                print(f"   ❌ FAILURE: All Games aggregation is not working correctly!")
                print(f"   ❌ Expected {expected_gp} games, got {all_games_stats['games_played']} games")
                return False
        else:
            print("   All Games: No stats found")
            print(f"   ❌ FAILURE: All Games aggregation returned None!")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_player_25_all_games_fix()
    if success:
        print(f"\n🎉 LOCAL TEST PASSED: The All Games aggregation fix is working locally!")
        print(f"   This suggests the issue may be a deployment delay or caching problem.")
    else:
        print(f"\n💥 LOCAL TEST FAILED: The All Games aggregation fix is not working locally!")
        print(f"   This suggests there may be an issue with the fix logic.")
    
    sys.exit(0 if success else 1)
