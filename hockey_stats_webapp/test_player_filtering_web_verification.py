#!/usr/bin/env python3
"""
Test script to verify player game type filtering works correctly.
This simulates the web interface functionality without requiring browser interaction.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from services.auth_service import AuthService

def test_player_filtering():
    """Test player game type filtering functionality."""
    
    print("=== TESTING PLAYER GAME TYPE FILTERING ===")
    
    # Initialize services
    print("1. Initializing services...")
    try:
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        auth_service = AuthService(sheets_service)
        print("   ✅ Services initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize services: {e}")
        return False
    
    # Test authentication with provided password
    print("2. Testing authentication...")
    password = "cwaxersu12aa"
    team_info = auth_service.verify_password(password)
    
    if not team_info:
        print(f"   ❌ Authentication failed for password: {password}")
        return False
    
    print(f"   ✅ Authentication successful!")
    print(f"      Team: {team_info['team_name']} (ID: {team_info['team_id']})")
    print(f"      Coach access: {team_info['is_coach']}")
    
    team_id = team_info['team_id']
    
    # Get players for this team
    print("3. Getting team players...")
    players = data_service.get_players(team_id)
    print(f"   Found {len(players)} players for team {team_info['team_name']}")
    
    if players.empty:
        print("   ❌ No players found for this team")
        return False
    
    # Test with first player
    first_player = players.iloc[0]
    player_id = data_service._get_player_id_from_series(first_player)
    jersey_number = first_player['JerseyNumber']
    position = first_player['Position']
    
    print(f"   Testing with Player #{jersey_number} (Position: {position}, ID: {player_id})")
    
    # Test different game types
    game_types = [
        ('R', 'Regular Season'),
        ('E', 'Exhibition'),
        ('T', 'Tournament')
    ]
    
    print("4. Testing game type filtering...")
    
    for game_type_code, game_type_name in game_types:
        print(f"\n   --- Testing {game_type_name} ({game_type_code}) ---")
        
        # Test season stats
        if position == 'G':
            stats = data_service.calculate_goalie_stats(player_id, team_id, game_type_code)
        else:
            stats = data_service.calculate_player_stats(player_id, team_id, game_type_code)
        
        if stats:
            print(f"      Season Stats: GP={stats['games_played']}")
            if position == 'G':
                print(f"                   Wins={stats['wins']}, GAA={stats['gaa']:.2f}, SV%={stats['save_percentage']:.3f}")
            else:
                print(f"                   Goals={stats['goals']}, Assists={stats['assists']}, Points={stats['points']}")
        else:
            print(f"      ❌ Failed to calculate season stats")
            continue
        
        # Test game log (this is the fix we implemented)
        game_log = data_service.get_player_game_log(player_id, team_id, game_type_code)
        print(f"      Game Log: {len(game_log)} games")
        
        # Verify game log games match the game type
        if game_log:
            game_types_in_log = set()
            for game_stats in game_log:
                game_type_in_log = game_stats['game'].get('GameType', 'Unknown')
                game_types_in_log.add(game_type_in_log)
            
            if len(game_types_in_log) == 1 and game_type_code in game_types_in_log:
                print(f"      ✅ Game log correctly filtered to {game_type_name} games only")
            elif len(game_types_in_log) == 0:
                print(f"      ⚠️  No games found for {game_type_name}")
            else:
                print(f"      ❌ Game log contains mixed game types: {game_types_in_log}")
                return False
        else:
            print(f"      ⚠️  No game log entries for {game_type_name}")
    
    print("\n5. Testing consistency between season stats and game log...")
    
    # Test that Regular Season stats match
    regular_season_stats = data_service.calculate_player_stats(player_id, team_id, 'R') if position != 'G' else data_service.calculate_goalie_stats(player_id, team_id, 'R')
    regular_season_log = data_service.get_player_game_log(player_id, team_id, 'R')
    
    if regular_season_stats and regular_season_log is not None:
        stats_gp = regular_season_stats['games_played']
        log_gp = len(regular_season_log)
        
        if stats_gp == log_gp:
            print(f"   ✅ Consistency check passed: Season stats GP ({stats_gp}) = Game log entries ({log_gp})")
        else:
            print(f"   ❌ Consistency check failed: Season stats GP ({stats_gp}) ≠ Game log entries ({log_gp})")
            return False
    
    print("\n=== PLAYER GAME TYPE FILTERING TEST COMPLETED SUCCESSFULLY ===")
    return True

if __name__ == "__main__":
    success = test_player_filtering()
    if success:
        print("\n🎉 All tests passed! Player game type filtering is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! There are issues with player game type filtering.")
        sys.exit(1)
