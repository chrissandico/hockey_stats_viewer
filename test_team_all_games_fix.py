#!/usr/bin/env python3

"""
Test script to verify the "All games" filter fix for the team stats screen.
This script tests that team summary, leaderboards, and game log all work correctly
when "All games" is selected (aggregating R, E, and T game types).
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.data_service import DataService
from services.sheets_service import SheetsService

def test_team_all_games_filter():
    """Test that team stats screen shows correct aggregated data when All Games is selected."""
    
    print("=== TESTING TEAM ALL GAMES FILTER FIX ===")
    print("Testing team statistics aggregation across all game types (R, E, T)...")
    
    try:
        # Initialize services
        sheets_service = SheetsService()
        data_service = DataService(sheets_service, force_refresh=True)
        
        team_id = "your_team"
        
        print(f"\n1. Testing individual game types for team stats:")
        
        # Test Exhibition games
        exhibition_stats = data_service.calculate_team_stats(team_id, game_type='E')
        if exhibition_stats:
            print(f"   Exhibition: {exhibition_stats['games_played']} GP, {exhibition_stats['wins']}W-{exhibition_stats['losses']}L-{exhibition_stats['ties']}T, {exhibition_stats['goals_for']}GF-{exhibition_stats['goals_against']}GA")
        else:
            print("   Exhibition: No stats found")
        
        # Test Tournament games
        tournament_stats = data_service.calculate_team_stats(team_id, game_type='T')
        if tournament_stats:
            print(f"   Tournament: {tournament_stats['games_played']} GP, {tournament_stats['wins']}W-{tournament_stats['losses']}L-{tournament_stats['ties']}T, {tournament_stats['goals_for']}GF-{tournament_stats['goals_against']}GA")
        else:
            print("   Tournament: No stats found")
        
        # Test Regular Season games
        regular_stats = data_service.calculate_team_stats(team_id, game_type='R')
        if regular_stats:
            print(f"   Regular Season: {regular_stats['games_played']} GP, {regular_stats['wins']}W-{regular_stats['losses']}L-{regular_stats['ties']}T, {regular_stats['goals_for']}GF-{regular_stats['goals_against']}GA")
        else:
            print("   Regular Season: No stats found")
        
        print(f"\n2. Testing All Games aggregation for team stats:")
        
        # Test All Games (game_type=None) - this is what the fix should enable
        all_games_stats = data_service.calculate_team_stats(team_id, game_type=None)
        if all_games_stats:
            print(f"   All Games: {all_games_stats['games_played']} GP, {all_games_stats['wins']}W-{all_games_stats['losses']}L-{all_games_stats['ties']}T, {all_games_stats['goals_for']}GF-{all_games_stats['goals_against']}GA")
            
            # Calculate expected totals
            expected_gp = 0
            expected_wins = 0
            expected_losses = 0
            expected_ties = 0
            expected_gf = 0
            expected_ga = 0
            
            for stats in [exhibition_stats, tournament_stats, regular_stats]:
                if stats:
                    expected_gp += stats['games_played']
                    expected_wins += stats['wins']
                    expected_losses += stats['losses']
                    expected_ties += stats['ties']
                    expected_gf += stats['goals_for']
                    expected_ga += stats['goals_against']
            
            print(f"\n3. Team Stats Verification:")
            print(f"   Expected totals: {expected_gp} GP, {expected_wins}W-{expected_losses}L-{expected_ties}T, {expected_gf}GF-{expected_ga}GA")
            print(f"   Actual totals:   {all_games_stats['games_played']} GP, {all_games_stats['wins']}W-{all_games_stats['losses']}L-{all_games_stats['ties']}T, {all_games_stats['goals_for']}GF-{all_games_stats['goals_against']}GA")
            
            # Check if team stats aggregation is working
            team_stats_correct = (
                all_games_stats['games_played'] == expected_gp and
                all_games_stats['wins'] == expected_wins and
                all_games_stats['losses'] == expected_losses and
                all_games_stats['ties'] == expected_ties and
                all_games_stats['goals_for'] == expected_gf and
                all_games_stats['goals_against'] == expected_ga
            )
            
            if team_stats_correct and expected_gp > 0:
                print(f"   ✅ SUCCESS: Team stats aggregation is working correctly!")
            else:
                print(f"   ❌ FAILURE: Team stats aggregation is not working correctly!")
                return False
        else:
            print("   All Games: No stats found")
            print(f"   ❌ FAILURE: All Games team stats returned None!")
            return False
        
        print(f"\n4. Testing team leaderboards for All Games:")
        
        # Test forwards leaderboard
        forwards_all = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type=None)
        forwards_e = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type='E')
        forwards_r = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type='R')
        forwards_t = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type='T')
        
        print(f"   Forwards leaderboard - All Games: {len(forwards_all)} players")
        print(f"   Forwards leaderboard - Exhibition: {len(forwards_e)} players")
        print(f"   Forwards leaderboard - Regular: {len(forwards_r)} players")
        print(f"   Forwards leaderboard - Tournament: {len(forwards_t)} players")
        
        # Test goalies leaderboard
        goalies_all = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type=None)
        goalies_e = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type='E')
        goalies_r = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type='R')
        goalies_t = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type='T')
        
        print(f"   Goalies leaderboard - All Games: {len(goalies_all)} players")
        print(f"   Goalies leaderboard - Exhibition: {len(goalies_e)} players")
        print(f"   Goalies leaderboard - Regular: {len(goalies_r)} players")
        print(f"   Goalies leaderboard - Tournament: {len(goalies_t)} players")
        
        # Verify leaderboards show aggregated stats
        if len(forwards_all) > 0 and len(goalies_all) > 0:
            print(f"   ✅ SUCCESS: Team leaderboards are populated for All Games!")
            
            # Check a sample forward's stats
            if forwards_all:
                sample_forward = forwards_all[0]
                print(f"   Sample forward #{sample_forward['player']['JerseyNumber']}: {sample_forward['games_played']} GP, {sample_forward['points']} P")
            
            # Check a sample goalie's stats
            if goalies_all:
                sample_goalie = goalies_all[0]
                print(f"   Sample goalie #{sample_goalie['player']['JerseyNumber']}: {sample_goalie['games_played']} GP, {sample_goalie['save_percentage']:.3f} SV%")
        else:
            print(f"   ❌ FAILURE: Team leaderboards are empty for All Games!")
            return False
        
        print(f"\n5. Testing team game log for All Games:")
        
        # Test game log
        games_all = data_service.get_games(team_id, game_type=None)
        games_e = data_service.get_games(team_id, game_type='E')
        games_r = data_service.get_games(team_id, game_type='R')
        games_t = data_service.get_games(team_id, game_type='T')
        
        print(f"   Game log - All Games: {len(games_all)} games")
        print(f"   Game log - Exhibition: {len(games_e)} games")
        print(f"   Game log - Regular: {len(games_r)} games")
        print(f"   Game log - Tournament: {len(games_t)} games")
        
        # Verify game log shows all games
        expected_total_games = len(games_e) + len(games_r) + len(games_t)
        if len(games_all) == expected_total_games and expected_total_games > 0:
            print(f"   ✅ SUCCESS: Team game log shows all games correctly!")
        else:
            print(f"   ❌ FAILURE: Team game log aggregation is incorrect!")
            print(f"   Expected {expected_total_games} total games, got {len(games_all)}")
            return False
        
        print(f"\n🎉 ALL TESTS PASSED: Team 'All Games' filter is working correctly!")
        print(f"   - Team summary aggregates stats across all game types")
        print(f"   - Team leaderboards show players with aggregated stats")
        print(f"   - Team game log shows all games from all game types")
        return True
            
    except Exception as e:
        print(f"❌ ERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_team_all_games_filter()
    if success:
        print(f"\n🎉 TEAM ALL GAMES FIX VERIFIED: The fix is working correctly!")
        print(f"   The team stats screen should now properly show aggregated data when 'All Games' is selected.")
    else:
        print(f"\n💥 TEAM ALL GAMES FIX FAILED: There may still be an issue with the implementation.")
    
    sys.exit(0 if success else 1)
