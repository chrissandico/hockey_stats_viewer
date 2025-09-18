#!/usr/bin/env python3
"""
Test script to verify the Stars U11 A team fixes are working correctly.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_starsu11a_fixes():
    """Test that Stars U11 A team stats are now working correctly."""
    print("=== TESTING STARS U11 A FIXES ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    team_id = 'starsu11a'
    team_name = 'Stars U11 A'
    
    print(f"\nTesting team: {team_name} (ID: {team_id})")
    print("="*50)
    
    # Test 1: Get team players
    print("\n1. Testing player retrieval...")
    players = data_service.get_players(team_id)
    print(f"   Found {len(players)} players for {team_name}")
    
    if players.empty:
        print("   ❌ ERROR: No players found!")
        return False
    
    # Test 2: Get team games
    print("\n2. Testing game retrieval...")
    games = data_service.get_games(team_id)
    completed_games = data_service._filter_games_by_date(games, include_future=False)
    print(f"   Found {len(games)} total games, {len(completed_games)} completed games")
    
    if completed_games.empty:
        print("   ❌ ERROR: No completed games found!")
        return False
    
    # Test 3: Player stats and game logs
    print("\n3. Testing player stats and game logs...")
    test_player = players.iloc[0]  # Test with first player
    player_id = test_player['ID']
    jersey_number = test_player['JerseyNumber']
    
    print(f"   Testing player #{jersey_number} (ID: {player_id})")
    
    # Calculate player stats
    player_stats = data_service.calculate_player_stats(player_id, team_id)
    if player_stats:
        print(f"   ✅ Player stats calculated:")
        print(f"      Games Played: {player_stats['games_played']}")
        print(f"      Goals: {player_stats['goals']}")
        print(f"      Assists: {player_stats['assists']}")
        print(f"      Points: {player_stats['points']}")
        print(f"      Plus/Minus: {player_stats['plus_minus']}")
    else:
        print("   ❌ ERROR: Could not calculate player stats!")
        return False
    
    # Get player game log
    game_log = data_service.get_player_game_log(player_id, team_id)
    print(f"   ✅ Player game log: {len(game_log)} entries")
    
    if game_log:
        for i, game_stats in enumerate(game_log):
            print(f"      Game {i+1}: {game_stats['game']['Date']} - {game_stats['goals']}G {game_stats['assists']}A {game_stats['points']}P")
    
    # Test 4: Game player stats
    print("\n4. Testing game player stats...")
    test_game = completed_games.iloc[0]  # Test with first completed game
    game_id = test_game['ID']
    game_date = test_game['Date']
    
    print(f"   Testing game {game_id} ({game_date})")
    
    # Get game player stats
    game_player_stats = data_service.get_game_player_stats(game_id, None, team_id)
    print(f"   ✅ Game player stats: {len(game_player_stats)} players")
    
    if game_player_stats:
        print("   Player performance in this game:")
        for stats in game_player_stats[:5]:  # Show first 5 players
            player = stats['player']
            print(f"      #{player['JerseyNumber']} ({player['Position']}): {stats['goals']}G {stats['assists']}A {stats['points']}P {stats['plus_minus']:+d}")
    
    # Test 5: Goalie stats (if any goalies)
    print("\n5. Testing goalie stats...")
    goalies = players[players['Position'] == 'G']
    
    if not goalies.empty:
        test_goalie = goalies.iloc[0]
        goalie_id = test_goalie['ID']
        goalie_jersey = test_goalie['JerseyNumber']
        
        print(f"   Testing goalie #{goalie_jersey} (ID: {goalie_id})")
        
        goalie_stats = data_service.calculate_goalie_stats(goalie_id, team_id)
        if goalie_stats:
            print(f"   ✅ Goalie stats calculated:")
            print(f"      Games Played: {goalie_stats['games_played']}")
            print(f"      Wins: {goalie_stats['wins']}")
            print(f"      Save Percentage: {goalie_stats['save_percentage']:.3f}")
            print(f"      Goals Against Average: {goalie_stats['gaa']:.2f}")
        else:
            print("   ⚠️  Could not calculate goalie stats (may be normal if no games played)")
    else:
        print("   ℹ️  No goalies found for this team")
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY:")
    print(f"✅ Team players: {len(players)} found")
    print(f"✅ Team games: {len(completed_games)} completed games")
    print(f"✅ Player stats: Working")
    print(f"✅ Player game logs: {len(game_log)} entries")
    print(f"✅ Game player stats: {len(game_player_stats)} players in test game")
    
    print(f"\n🎉 SUCCESS: {team_name} team stats are now working correctly!")
    return True

if __name__ == "__main__":
    success = test_starsu11a_fixes()
    if success:
        print("\n✅ All tests passed! The Stars U11 A team should now display stats correctly.")
    else:
        print("\n❌ Some tests failed. There may still be issues to resolve.")
