#!/usr/bin/env python3
"""
Test script to verify that all stats (goals, assists, points, plus/minus, shots, penalty minutes)
are now calculated using centralized functions and are consistent across all screens.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_centralized_stats():
    """Test that all stats are calculated consistently using centralized functions."""
    print("=== TESTING CENTRALIZED STATS CONSISTENCY ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Test with a few different players that have game data
    test_players = [84, 25, 13]  # Jersey numbers to test (changed 14 to 13 since 14 has no games)
    
    for jersey_number in test_players:
        print(f"\n🏒 TESTING JERSEY #{jersey_number}")
        print("=" * 50)
        
        # Find player
        players = data_service.get_players()
        target_player = players[players['JerseyNumber'] == jersey_number]
        
        if target_player.empty:
            print(f"❌ No player found with jersey number {jersey_number}")
            continue
        
        target_player = target_player.iloc[0]
        player_id = target_player['ID']
        
        print(f"✅ Found player: #{target_player['JerseyNumber']} (ID: {player_id})")
        print(f"   Position: {target_player['Position']}")
        
        # Get team information
        teams = sheets_service.get_teams()
        if not teams.empty:
            team_id = teams.iloc[0]['TeamID']
        else:
            team_id = 'your_team'
        
        # Test 1: Season Stats (calculate_player_stats)
        print(f"\n📊 SEASON STATS TEST")
        print("-" * 30)
        
        season_stats = data_service.calculate_player_stats(player_id, team_id)
        if season_stats:
            print(f"Goals: {season_stats['goals']}")
            print(f"Assists: {season_stats['assists']}")
            print(f"Points: {season_stats['points']}")
            print(f"Plus/Minus: {season_stats['plus_minus']:+d}")
            print(f"Shots: {season_stats['shots']}")
            print(f"Penalty Minutes: {season_stats['penalty_minutes']}")
            print(f"Games Played: {season_stats['games_played']}")
        else:
            print("❌ Could not retrieve season stats")
            continue
        
        # Test 2: Game Stats (calculate_player_game_stats)
        print(f"\n🎮 GAME STATS TEST")
        print("-" * 30)
        
        # Get player's games
        games = data_service.get_player_games(player_id, team_id)
        if not games.empty:
            # Test with the first game
            test_game = games.iloc[0]
            game_id = test_game['ID']
            
            print(f"Testing with Game ID: {game_id} ({test_game['Date']})")
            
            game_stats = data_service.calculate_player_game_stats(player_id, game_id)
            if game_stats:
                print(f"Goals: {game_stats['goals']}")
                print(f"Assists: {game_stats['assists']}")
                print(f"Points: {game_stats['points']}")
                print(f"Plus/Minus: {game_stats['plus_minus']:+d}")
                print(f"Shots: {game_stats['shots']}")
                print(f"Penalty Minutes: {game_stats['penalty_minutes']}")
            else:
                print("❌ Could not retrieve game stats")
        else:
            print("❌ No games found for this player")
        
        # Test 3: Team Leaderboard (get_team_leaderboard)
        print(f"\n🏆 LEADERBOARD TEST")
        print("-" * 30)
        
        # Get leaderboard for this player's position
        position = target_player['Position']
        leaderboard = data_service.get_team_leaderboard(stat='points', position=position, team_id=team_id)
        
        # Find this player in the leaderboard
        player_in_leaderboard = None
        for stats in leaderboard:
            if stats['player']['ID'] == player_id:
                player_in_leaderboard = stats
                break
        
        if player_in_leaderboard:
            print(f"Goals: {player_in_leaderboard['goals']}")
            print(f"Assists: {player_in_leaderboard['assists']}")
            print(f"Points: {player_in_leaderboard['points']}")
            print(f"Plus/Minus: {player_in_leaderboard['plus_minus']:+d}")
            print(f"Shots: {player_in_leaderboard['shots']}")
            print(f"Penalty Minutes: {player_in_leaderboard['penalty_minutes']}")
        else:
            print("❌ Player not found in leaderboard")
        
        # Test 4: Consistency Check
        print(f"\n✅ CONSISTENCY CHECK")
        print("-" * 30)
        
        if season_stats and player_in_leaderboard:
            # Compare season stats with leaderboard stats
            stats_match = True
            
            for stat in ['goals', 'assists', 'points', 'plus_minus', 'shots', 'penalty_minutes']:
                season_value = season_stats[stat]
                leaderboard_value = player_in_leaderboard[stat]
                
                if season_value != leaderboard_value:
                    print(f"❌ {stat.upper()} MISMATCH: Season={season_value}, Leaderboard={leaderboard_value}")
                    stats_match = False
                else:
                    print(f"✅ {stat.upper()}: {season_value} (consistent)")
            
            if stats_match:
                print(f"\n🎉 ALL STATS CONSISTENT for Jersey #{jersey_number}!")
            else:
                print(f"\n⚠️  INCONSISTENCIES FOUND for Jersey #{jersey_number}")
        else:
            print("❌ Could not perform consistency check")
    
    print("\n=== CENTRALIZED STATS TEST COMPLETE ===")

if __name__ == "__main__":
    test_centralized_stats()
