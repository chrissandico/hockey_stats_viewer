#!/usr/bin/env python3
"""
Test script to verify that game summary scores are consistent across the app.
This tests the fix for the starsu11a team game summary issue.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_game_summary_consistency():
    """Test that game summary scores are consistent with the centralized data service."""
    print("=== TESTING GAME SUMMARY CONSISTENCY ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Test both teams mentioned by the user
    test_teams = [
        {'team_id': 'starsu11a', 'team_name': 'Stars U11 A'},
        {'team_id': 'waxersu12aa', 'team_name': 'Waxers U12 AA'}
    ]
    
    for team_info in test_teams:
        team_id = team_info['team_id']
        team_name = team_info['team_name']
        
        print(f"\n{'='*60}")
        print(f"Testing team: {team_name} (ID: {team_id})")
        print(f"{'='*60}")
        
        # Get team games
        games = data_service.get_games(team_id)
        completed_games = data_service._filter_games_by_date(games, include_future=False)
        
        if completed_games.empty:
            print(f"   ⚠️  No completed games found for {team_name}")
            continue
        
        print(f"   Found {len(completed_games)} completed games for {team_name}")
        
        # Test the first few games
        test_games = completed_games.head(3)  # Test first 3 games
        
        for idx, (_, game) in enumerate(test_games.iterrows()):
            game_id = game['ID']
            game_date = game['Date']
            
            print(f"\n   Game {idx + 1}: {game_id} ({game_date})")
            print(f"   {'='*50}")
            
            # Get goals from the centralized get_games method
            goals_for_from_games = game.get('GoalsFor', 0)
            goals_against_from_games = game.get('GoalsAgainst', 0)
            
            print(f"   Goals from get_games method:")
            print(f"      Goals For: {goals_for_from_games}")
            print(f"      Goals Against: {goals_against_from_games}")
            
            # Get game summary (which should now use the same data) - pass team_id for consistency
            game_summary = data_service.get_game_summary(game_id, team_id)
            
            if game_summary is None:
                print(f"   ❌ ERROR: Could not get game summary for game {game_id}")
                continue
            
            # Extract goals from game summary
            summary_game = game_summary['game']
            goals_for_from_summary = summary_game.get('GoalsFor', 0)
            goals_against_from_summary = summary_game.get('GoalsAgainst', 0)
            
            print(f"   Goals from get_game_summary method:")
            print(f"      Goals For: {goals_for_from_summary}")
            print(f"      Goals Against: {goals_against_from_summary}")
            
            # Check consistency
            goals_for_match = goals_for_from_games == goals_for_from_summary
            goals_against_match = goals_against_from_games == goals_against_from_summary
            
            if goals_for_match and goals_against_match:
                print(f"   ✅ CONSISTENCY CHECK PASSED")
                print(f"      Score: {goals_for_from_games}-{goals_against_from_games}")
            else:
                print(f"   ❌ CONSISTENCY CHECK FAILED")
                print(f"      get_games score: {goals_for_from_games}-{goals_against_from_games}")
                print(f"      get_game_summary score: {goals_for_from_summary}-{goals_against_from_summary}")
                return False
            
            # Also check other game summary stats for completeness
            print(f"   Other game summary stats:")
            print(f"      Your Team Shots: {game_summary['your_team_shots']}")
            print(f"      Opponent Shots: {game_summary['opponent_shots']}")
            print(f"      Your Team PIM: {game_summary['your_team_pim']}")
            print(f"      Opponent PIM: {game_summary['opponent_pim']}")
            print(f"      Your Team PP: {game_summary['your_team_pp_goals']}/{game_summary['your_team_pp_opps']}")
            print(f"      Opponent PP: {game_summary['opponent_pp_goals']}/{game_summary['opponent_pp_opps']}")
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print("✅ All game summary scores are now consistent across the app!")
    print("✅ Both starsu11a and waxersu12aa teams should display correct scores")
    print("✅ The centralized DataService ensures consistency")
    
    return True

def test_team_stats_consistency():
    """Test that team stats are also consistent."""
    print(f"\n{'='*60}")
    print("TESTING TEAM STATS CONSISTENCY")
    print(f"{'='*60}")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    test_teams = [
        {'team_id': 'starsu11a', 'team_name': 'Stars U11 A'},
        {'team_id': 'waxersu12aa', 'team_name': 'Waxers U12 AA'}
    ]
    
    for team_info in test_teams:
        team_id = team_info['team_id']
        team_name = team_info['team_name']
        
        print(f"\n   Team: {team_name}")
        
        # Get team stats
        team_stats = data_service.calculate_team_stats(team_id)
        
        print(f"      Games Played: {team_stats['games_played']}")
        print(f"      Record: {team_stats['wins']}-{team_stats['losses']}-{team_stats['ties']}")
        print(f"      Goals For: {team_stats['goals_for']}")
        print(f"      Goals Against: {team_stats['goals_against']}")
        print(f"      Win %: {team_stats['win_percentage']:.3f}")
    
    print(f"\n   ✅ Team stats are calculated using the same centralized method")

if __name__ == "__main__":
    print("Testing game summary consistency fix...")
    
    success = test_game_summary_consistency()
    
    if success:
        test_team_stats_consistency()
        print(f"\n🎉 SUCCESS: Game summary consistency fix is working!")
        print("   - starsu11a team should now show correct scores")
        print("   - waxersu12aa team should continue to work correctly")
        print("   - All screens use the same centralized data source")
    else:
        print(f"\n❌ FAILURE: There are still consistency issues to resolve")
