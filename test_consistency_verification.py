#!/usr/bin/env python3
"""
Test script to verify plus-minus consistency across different calculation methods.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_plus_minus_consistency():
    """Test that plus-minus is consistent across different calculation methods."""
    print("=== TESTING PLUS-MINUS CONSISTENCY ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Test with a specific player
    player_id = "player_4"  # This player had -5 plus/minus in the test
    team_id = "your_team"
    game_id = "2"
    
    print(f"\nTesting consistency for player {player_id}")
    
    # Method 1: Season stats (calculate_player_stats)
    season_stats = data_service.calculate_player_stats(player_id, team_id)
    season_plus_minus = season_stats['plus_minus'] if season_stats else 0
    print(f"Season stats plus/minus: {season_plus_minus}")
    
    # Method 2: Game stats (calculate_player_game_stats)
    game_stats = data_service.calculate_player_game_stats(player_id, game_id)
    game_plus_minus = game_stats['plus_minus'] if game_stats else 0
    print(f"Game stats plus/minus: {game_plus_minus}")
    
    # Method 3: Team leaderboard (get_team_leaderboard)
    leaderboard = data_service.get_team_leaderboard(stat='plus_minus', team_id=team_id)
    leaderboard_plus_minus = None
    for player_stats in leaderboard:
        if player_stats['player']['ID'] == player_id:
            leaderboard_plus_minus = player_stats['plus_minus']
            break
    
    print(f"Leaderboard plus/minus: {leaderboard_plus_minus}")
    
    # Verify consistency
    print(f"\n=== CONSISTENCY CHECK ===")
    if season_plus_minus == game_plus_minus == leaderboard_plus_minus:
        print(f"✅ SUCCESS: All methods return the same plus/minus value: {season_plus_minus}")
        return True
    else:
        print(f"❌ INCONSISTENCY DETECTED:")
        print(f"  Season stats: {season_plus_minus}")
        print(f"  Game stats: {game_plus_minus}")
        print(f"  Leaderboard: {leaderboard_plus_minus}")
        return False

if __name__ == "__main__":
    success = test_plus_minus_consistency()
    if success:
        print("\n🎉 Plus/minus calculation is now consistent across all screens!")
    else:
        print("\n⚠️  There are still inconsistencies that need to be addressed.")
