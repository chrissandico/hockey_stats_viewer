#!/usr/bin/env python3

"""
Test script to verify the fixes for team stats issues:
1. "All Games" view shows correct Summary stats
2. Forward and Defense leaderboards show zeros when no games of selected type exist
"""

import sys
import os
sys.path.insert(0, 'hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_team_stats_fixes():
    """Test that team stats fixes are working correctly."""
    
    print("=== Testing Team Stats Fixes ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Test with a known team
    team_id = 'your_team'
    
    print(f"\n1. Testing 'All Games' Summary Stats for team: {team_id}")
    
    # Test "All Games" view (game_type=None)
    print("\n--- All Games Summary ---")
    team_stats_all = data_service.calculate_team_stats(team_id, game_type=None)
    print(f"All Games Summary: {team_stats_all}")
    
    # Test Exhibition Games summary
    print("\n--- Exhibition Games Summary ---")
    team_stats_exhibition = data_service.calculate_team_stats(team_id, game_type='E')
    print(f"Exhibition Summary: {team_stats_exhibition}")
    
    # Test Regular Games summary
    print("\n--- Regular Games Summary ---")
    team_stats_regular = data_service.calculate_team_stats(team_id, game_type='R')
    print(f"Regular Summary: {team_stats_regular}")
    
    # Verify that All Games != Exhibition (should be different if there are other game types)
    if team_stats_all['games_played'] != team_stats_exhibition['games_played']:
        print("✅ All Games summary is different from Exhibition - Fix 1 working correctly")
    else:
        print("⚠️  All Games summary same as Exhibition - may be expected if only exhibition games exist")
    
    print(f"\n2. Testing Forward and Defense Leaderboards for Empty Game Types")
    
    # Test Regular Season leaderboards (should be empty if no regular games)
    print("\n--- Regular Season Forward Leaderboard ---")
    forwards_regular = data_service.get_team_leaderboard(
        stat='points', 
        position='F', 
        team_id=team_id, 
        game_type='R'
    )
    print(f"Regular Season Forwards: {len(forwards_regular)} players")
    if forwards_regular:
        for i, player_stats in enumerate(forwards_regular[:3]):
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['points']} points ({player_stats['games_played']} GP)")
    
    print("\n--- Regular Season Defense Leaderboard ---")
    defense_regular = data_service.get_team_leaderboard(
        stat='points', 
        position='D', 
        team_id=team_id, 
        game_type='R'
    )
    print(f"Regular Season Defense: {len(defense_regular)} players")
    if defense_regular:
        for i, player_stats in enumerate(defense_regular[:3]):
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['points']} points ({player_stats['games_played']} GP)")
    
    print("\n--- Regular Season Goalie Leaderboard ---")
    goalies_regular = data_service.get_team_leaderboard(
        stat='save_percentage', 
        position='G', 
        team_id=team_id, 
        game_type='R'
    )
    print(f"Regular Season Goalies: {len(goalies_regular)} players")
    if goalies_regular:
        for i, player_stats in enumerate(goalies_regular[:3]):
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['save_percentage']:.3f} SV% ({player_stats['games_played']} GP)")
    
    # Verify Fix 2: If no regular season games, leaderboards should be empty
    if team_stats_regular['games_played'] == 0:
        if len(forwards_regular) == 0 and len(defense_regular) == 0:
            print("✅ Forward and Defense leaderboards are empty when no games exist - Fix 2 working correctly")
        else:
            print("❌ Forward and Defense leaderboards show players when no games exist - Fix 2 NOT working")
        
        if len(goalies_regular) == 0:
            print("✅ Goalie leaderboard is also empty when no games exist - consistent behavior")
        else:
            print("⚠️  Goalie leaderboard shows players when no games exist - may need investigation")
    else:
        print(f"ℹ️  Regular season has {team_stats_regular['games_played']} games - cannot test empty leaderboard behavior")
    
    print(f"\n3. Verification Summary:")
    print(f"All Games GP: {team_stats_all['games_played']}")
    print(f"Exhibition GP: {team_stats_exhibition['games_played']}")
    print(f"Regular GP: {team_stats_regular['games_played']}")
    print(f"Regular Forwards: {len(forwards_regular)} players")
    print(f"Regular Defense: {len(defense_regular)} players")
    print(f"Regular Goalies: {len(goalies_regular)} players")

if __name__ == "__main__":
    test_team_stats_fixes()
