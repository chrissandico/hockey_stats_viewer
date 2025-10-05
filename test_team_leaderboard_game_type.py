#!/usr/bin/env python3

"""
Test script to verify that team leaderboards respect game type filtering.
"""

import sys
import os
sys.path.insert(0, 'hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_team_leaderboard_game_type():
    """Test that team leaderboards respect game type filtering."""
    
    print("=== Testing Team Leaderboard Game Type Filtering ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Test with a known team
    team_id = 'your_team'
    
    print(f"\n1. Testing Forward Leaderboard for team: {team_id}")
    
    # Test forwards leaderboard with different game types
    print("\n--- All Games ---")
    forwards_all = data_service.get_team_leaderboard(
        stat='points', 
        position='F', 
        team_id=team_id, 
        game_type=None
    )
    print(f"Forwards (All Games): {len(forwards_all)} players")
    if forwards_all:
        for i, player_stats in enumerate(forwards_all[:3]):  # Show top 3
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['points']} points ({player_stats['games_played']} GP)")
    
    print("\n--- Exhibition Games Only ---")
    forwards_exhibition = data_service.get_team_leaderboard(
        stat='points', 
        position='F', 
        team_id=team_id, 
        game_type='E'
    )
    print(f"Forwards (Exhibition): {len(forwards_exhibition)} players")
    if forwards_exhibition:
        for i, player_stats in enumerate(forwards_exhibition[:3]):  # Show top 3
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['points']} points ({player_stats['games_played']} GP)")
    
    print("\n--- Regular Games Only ---")
    forwards_regular = data_service.get_team_leaderboard(
        stat='points', 
        position='F', 
        team_id=team_id, 
        game_type='R'
    )
    print(f"Forwards (Regular): {len(forwards_regular)} players")
    if forwards_regular:
        for i, player_stats in enumerate(forwards_regular[:3]):  # Show top 3
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['points']} points ({player_stats['games_played']} GP)")
    
    print(f"\n2. Testing Defense Leaderboard for team: {team_id}")
    
    # Test defense leaderboard with different game types
    print("\n--- All Games ---")
    defense_all = data_service.get_team_leaderboard(
        stat='points', 
        position='D', 
        team_id=team_id, 
        game_type=None
    )
    print(f"Defense (All Games): {len(defense_all)} players")
    if defense_all:
        for i, player_stats in enumerate(defense_all[:3]):  # Show top 3
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['points']} points ({player_stats['games_played']} GP)")
    
    print("\n--- Exhibition Games Only ---")
    defense_exhibition = data_service.get_team_leaderboard(
        stat='points', 
        position='D', 
        team_id=team_id, 
        game_type='E'
    )
    print(f"Defense (Exhibition): {len(defense_exhibition)} players")
    if defense_exhibition:
        for i, player_stats in enumerate(defense_exhibition[:3]):  # Show top 3
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['points']} points ({player_stats['games_played']} GP)")
    
    print("\n--- Regular Games Only ---")
    defense_regular = data_service.get_team_leaderboard(
        stat='points', 
        position='D', 
        team_id=team_id, 
        game_type='R'
    )
    print(f"Defense (Regular): {len(defense_regular)} players")
    if defense_regular:
        for i, player_stats in enumerate(defense_regular[:3]):  # Show top 3
            player = player_stats['player']
            print(f"  {i+1}. #{player['JerseyNumber']} - {player_stats['points']} points ({player_stats['games_played']} GP)")
    
    # Check if the stats are actually different
    print(f"\n3. Verification:")
    
    if forwards_all and forwards_exhibition:
        all_games_points = forwards_all[0]['points'] if forwards_all else 0
        exhibition_points = forwards_exhibition[0]['points'] if forwards_exhibition else 0
        print(f"Forward leader points: All Games = {all_games_points}, Exhibition = {exhibition_points}")
        
        if all_games_points != exhibition_points:
            print("✅ Forward leaderboard IS respecting game type filter")
        else:
            print("❌ Forward leaderboard is NOT respecting game type filter")
    
    if defense_all and defense_exhibition:
        all_games_points = defense_all[0]['points'] if defense_all else 0
        exhibition_points = defense_exhibition[0]['points'] if defense_exhibition else 0
        print(f"Defense leader points: All Games = {all_games_points}, Exhibition = {exhibition_points}")
        
        if all_games_points != exhibition_points:
            print("✅ Defense leaderboard IS respecting game type filter")
        else:
            print("❌ Defense leaderboard is NOT respecting game type filter")

if __name__ == "__main__":
    test_team_leaderboard_game_type()
