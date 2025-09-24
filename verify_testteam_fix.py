#!/usr/bin/env python3
"""
Final verification script to confirm both testteam issues are resolved.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from services.auth_service import AuthService

def verify_testteam_fix():
    """Verify that both testteam issues are now resolved."""
    print("=== FINAL VERIFICATION: TESTTEAM FIX ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    auth_service = AuthService(sheets_service)
    
    # Test authentication
    print("\n1. Testing Authentication")
    print("-" * 30)
    auth_result = auth_service.verify_password('testteam')
    if auth_result:
        print("✅ Authentication successful!")
        team_id = auth_result['team_id']
        team_name = auth_result['team_name']
        print(f"   Team: {team_name} (ID: {team_id})")
    else:
        print("❌ Authentication failed!")
        return False
    
    # Test Issue 1: Players showing in game stats screen
    print("\n2. Testing Issue 1: Game Stats Screen - Player Performance Table")
    print("-" * 70)
    
    # Get completed games for the test team
    games = data_service.get_games(team_id)
    completed_games = data_service._filter_games_by_date(games, include_future=False)
    
    if completed_games.empty:
        print("❌ No completed games found for test team")
        return False
    
    # Test with the first completed game
    test_game = completed_games.iloc[0]
    game_id = test_game['ID']
    game_date = test_game['Date']
    opponent = test_game['Opponent']
    
    print(f"Testing with game {game_id} ({game_date} vs {opponent})")
    
    # Test get_game_player_stats (this is what the game layout uses)
    game_player_stats = data_service.get_game_player_stats(game_id, team_id=team_id)
    
    if game_player_stats:
        print(f"✅ ISSUE 1 RESOLVED: Game player stats working!")
        print(f"   Found {len(game_player_stats)} players in game {game_id}")
        print("   Top performers:")
        for i, stats in enumerate(game_player_stats[:3]):
            player = stats['player']
            print(f"     #{player['JerseyNumber']} ({player['Position']}): {stats['goals']}G, {stats['assists']}A, {stats['points']}P")
    else:
        print("❌ ISSUE 1 NOT RESOLVED: Game player stats still empty")
        return False
    
    # Test Issue 2: Player game log showing
    print("\n3. Testing Issue 2: Players Screen - Player Game Log")
    print("-" * 55)
    
    # Test with the first player
    players = data_service.get_players(team_id)
    if players.empty:
        print("❌ No players found for test team")
        return False
    
    test_player = players.iloc[0]
    player_id = test_player['ID']
    jersey = test_player['JerseyNumber']
    position = test_player['Position']
    
    print(f"Testing with player {player_id} (#{jersey} - {position})")
    
    # Test get_player_game_log (this is what the player layout uses)
    game_log = data_service.get_player_game_log(player_id, team_id)
    
    if game_log:
        print(f"✅ ISSUE 2 RESOLVED: Player game log working!")
        print(f"   Found {len(game_log)} game log entries for player #{jersey}")
        print("   Recent games:")
        for entry in game_log[:3]:
            game = entry['game']
            print(f"     {game['Date']} vs {game['Opponent']}: {entry['goals']}G, {entry['assists']}A, {entry['points']}P")
    else:
        print("❌ ISSUE 2 NOT RESOLVED: Player game log still empty")
        return False
    
    # Test with different positions
    print("\n4. Testing Different Player Positions")
    print("-" * 40)
    
    positions_tested = set()
    for _, player in players.iterrows():
        position = player['Position']
        if position not in positions_tested and len(positions_tested) < 3:
            player_id = player['ID']
            jersey = player['JerseyNumber']
            
            game_log = data_service.get_player_game_log(player_id, team_id)
            print(f"   {position} #{jersey}: {len(game_log)} game log entries")
            positions_tested.add(position)
    
    # Test goalie-specific functionality if we have goalies
    goalies = players[players['Position'] == 'G']
    if not goalies.empty:
        print("\n5. Testing Goalie-Specific Functionality")
        print("-" * 40)
        
        goalie = goalies.iloc[0]
        goalie_id = goalie['ID']
        jersey = goalie['JerseyNumber']
        
        # Test goalie stats
        goalie_stats = data_service.calculate_goalie_stats(goalie_id, team_id)
        if goalie_stats:
            print(f"✅ Goalie stats working for #{jersey}")
            print(f"   Games: {goalie_stats['games_played']}, Wins: {goalie_stats['wins']}")
            print(f"   GAA: {goalie_stats['gaa']:.2f}, Save%: {goalie_stats['save_percentage']:.3f}")
        
        # Test goalie game log
        goalie_game_log = data_service.get_player_game_log(goalie_id, team_id)
        print(f"   Goalie game log: {len(goalie_game_log)} entries")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - BOTH ISSUES RESOLVED!")
    print("="*60)
    print("\nSummary:")
    print("• Issue 1: Players now show in game stats screen player performance table")
    print("• Issue 2: Players screen now shows player game logs")
    print("• The 'testteam' login is fully functional")
    
    return True

if __name__ == "__main__":
    verify_testteam_fix()
