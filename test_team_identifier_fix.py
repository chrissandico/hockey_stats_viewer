#!/usr/bin/env python3
"""
Test script to verify the team identifier mapping fix works for both teams.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_team_identifier_fix():
    """Test that team identifier mapping works for both Stars U11 A and Waxers U12 AA."""
    print("=== TESTING TEAM IDENTIFIER MAPPING FIX ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Test both teams
    teams_to_test = [
        {'team_id': 'starsu11a', 'team_name': 'Stars U11 A'},
        {'team_id': 'your_team', 'team_name': 'Waxers U12 AA'}
    ]
    
    for team_info in teams_to_test:
        team_id = team_info['team_id']
        team_name = team_info['team_name']
        
        print(f"\n{'='*50}")
        print(f"TESTING TEAM: {team_name} (ID: {team_id})")
        print(f"{'='*50}")
        
        # Test 1: Team identifier mapping
        print(f"\n1. Testing team identifier mapping...")
        team_identifier = data_service._get_team_identifier_for_events(team_id)
        print(f"   Result: '{team_id}' -> '{team_identifier}'")
        
        # Test 2: Get players for this team
        print(f"\n2. Testing player retrieval...")
        players = data_service.get_players(team_id)
        print(f"   Found {len(players)} players for team {team_id}")
        if not players.empty:
            print(f"   Sample player: #{players.iloc[0]['JerseyNumber']} (ID: {players.iloc[0]['ID']})")
        
        # Test 3: Get games for this team
        print(f"\n3. Testing game retrieval...")
        games = data_service.get_games(team_id)
        print(f"   Found {len(games)} games for team {team_id}")
        if not games.empty:
            sample_game = games.iloc[0]
            print(f"   Sample game: {sample_game['Date']} vs {sample_game['Opponent']}")
            print(f"   Score: {sample_game.get('GoalsFor', 0)}-{sample_game.get('GoalsAgainst', 0)}")
        
        # Test 4: Player stats calculation
        print(f"\n4. Testing player stats calculation...")
        if not players.empty:
            test_player_id = players.iloc[0]['ID']
            test_player_jersey = players.iloc[0]['JerseyNumber']
            print(f"   Testing player #{test_player_jersey} (ID: {test_player_id})")
            
            player_stats = data_service.calculate_player_stats(test_player_id, team_id)
            if player_stats:
                print(f"   ✅ Player stats calculated successfully:")
                print(f"      Games Played: {player_stats['games_played']}")
                print(f"      Goals: {player_stats['goals']}")
                print(f"      Assists: {player_stats['assists']}")
                print(f"      Points: {player_stats['points']}")
                print(f"      Plus/Minus: {player_stats['plus_minus']}")
            else:
                print(f"   ❌ Failed to calculate player stats")
        
        # Test 5: Game log
        print(f"\n5. Testing game log...")
        if not players.empty:
            game_log = data_service.get_player_game_log(test_player_id, team_id)
            print(f"   Found {len(game_log)} games in player's game log")
            if game_log:
                sample_game_stats = game_log[0]
                print(f"   Sample game log entry:")
                print(f"      Date: {sample_game_stats['game']['Date']}")
                print(f"      Goals: {sample_game_stats['goals']}")
                print(f"      Assists: {sample_game_stats['assists']}")
                print(f"      Points: {sample_game_stats['points']}")
        
        # Test 6: Game player stats
        print(f"\n6. Testing game player stats...")
        if not games.empty:
            test_game_id = games.iloc[0]['ID']
            print(f"   Testing game {test_game_id}")
            
            game_player_stats = data_service.get_game_player_stats(test_game_id, None, team_id)
            print(f"   Found stats for {len(game_player_stats)} players in this game")
            if game_player_stats:
                sample_player_stats = game_player_stats[0]
                print(f"   Sample player game stats:")
                print(f"      Player: #{sample_player_stats['player']['JerseyNumber']}")
                print(f"      Goals: {sample_player_stats['goals']}")
                print(f"      Assists: {sample_player_stats['assists']}")
                print(f"      Points: {sample_player_stats['points']}")
        
        # Summary for this team
        success_indicators = [
            len(players) > 0,
            len(games) > 0,
            player_stats is not None if not players.empty else True,
            len(game_log) > 0 if not players.empty else True,
            len(game_player_stats) > 0 if not games.empty else True
        ]
        
        success_count = sum(success_indicators)
        total_tests = len(success_indicators)
        
        print(f"\n📊 TEAM SUMMARY: {team_name}")
        print(f"   Success Rate: {success_count}/{total_tests} tests passed")
        if success_count == total_tests:
            print(f"   ✅ All tests PASSED for {team_name}")
        else:
            print(f"   ❌ Some tests FAILED for {team_name}")
    
    print(f"\n{'='*50}")
    print("OVERALL TEST COMPLETE")
    print(f"{'='*50}")

if __name__ == "__main__":
    test_team_identifier_fix()
