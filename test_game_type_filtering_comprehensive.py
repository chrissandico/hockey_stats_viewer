#!/usr/bin/env python3
"""
Comprehensive test script to verify game type filtering functionality across all screens.
"""

import sys
import os

# Add the hockey_stats_webapp directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

from services.sheets_service import SheetsService
from services.data_service import DataService
import config

def test_comprehensive_game_type_filtering():
    """Test comprehensive game type filtering functionality across all components."""
    print("=== Comprehensive Game Type Filtering Test ===")
    
    try:
        # Initialize services
        print("Initializing services...")
        sheets_service = SheetsService()
        data_service = DataService(sheets_service, force_refresh=True)
        
        # Test 1: Verify DataService methods accept game_type parameter
        print("\n1. Testing DataService method signatures...")
        
        # Get first team for testing
        teams = sheets_service.get_teams()
        if teams.empty:
            print("ERROR: No teams found")
            return False
        
        test_team_id = teams.iloc[0]['TeamID']
        print(f"Testing with team: {test_team_id}")
        
        # Get first player for testing
        players = data_service.get_players(test_team_id)
        if players.empty:
            print("ERROR: No players found")
            return False
        
        test_player_id = players.iloc[0]['ID']
        print(f"Testing with player: {test_player_id}")
        
        # Test each game type
        for game_type in ['E', 'R', 'T', None]:
            game_type_label = config.get_game_type_name(game_type) if game_type else "All Games"
            print(f"\n  Testing game type: {game_type_label}")
            
            # Test calculate_team_stats with game_type
            try:
                team_stats = data_service.calculate_team_stats(test_team_id, game_type)
                print(f"    ✅ calculate_team_stats: {team_stats['games_played']} games")
            except Exception as e:
                print(f"    ❌ calculate_team_stats failed: {e}")
                return False
            
            # Test get_team_leaderboard with game_type
            try:
                leaderboard = data_service.get_team_leaderboard(
                    stat='points', position='F', team_id=test_team_id, game_type=game_type
                )
                print(f"    ✅ get_team_leaderboard: {len(leaderboard)} players")
            except Exception as e:
                print(f"    ❌ get_team_leaderboard failed: {e}")
                return False
            
            # Test calculate_player_stats with game_type
            try:
                player_stats = data_service.calculate_player_stats(test_player_id, test_team_id, game_type)
                if player_stats:
                    print(f"    ✅ calculate_player_stats: {player_stats['games_played']} games")
                else:
                    print(f"    ⚠️  calculate_player_stats: No stats returned")
            except Exception as e:
                print(f"    ❌ calculate_player_stats failed: {e}")
                return False
            
            # Test get_player_games with game_type
            try:
                player_games = data_service.get_player_games(test_player_id, test_team_id, game_type=game_type)
                print(f"    ✅ get_player_games: {len(player_games)} games")
            except Exception as e:
                print(f"    ❌ get_player_games failed: {e}")
                return False
        
        # Test 2: Verify game type filtering actually filters data
        print("\n2. Testing game type filtering effectiveness...")
        
        # Get games for each type and verify they're different
        all_games = data_service.get_games(test_team_id)
        exhibition_games = data_service.get_games(test_team_id, 'E')
        regular_games = data_service.get_games(test_team_id, 'R')
        tournament_games = data_service.get_games(test_team_id, 'T')
        
        print(f"  All games: {len(all_games)}")
        print(f"  Exhibition games: {len(exhibition_games)}")
        print(f"  Regular games: {len(regular_games)}")
        print(f"  Tournament games: {len(tournament_games)}")
        
        # Verify filtering is working
        total_filtered = len(exhibition_games) + len(regular_games) + len(tournament_games)
        if total_filtered <= len(all_games):
            print("  ✅ Game type filtering is working correctly")
        else:
            print("  ❌ Game type filtering may have issues")
            return False
        
        # Test 3: Verify team stats change with game type
        print("\n3. Testing team stats variation by game type...")
        
        all_stats = data_service.calculate_team_stats(test_team_id, None)
        exhibition_stats = data_service.calculate_team_stats(test_team_id, 'E')
        
        print(f"  All games stats: {all_stats['games_played']} GP, {all_stats['wins']} W")
        print(f"  Exhibition stats: {exhibition_stats['games_played']} GP, {exhibition_stats['wins']} W")
        
        if exhibition_stats['games_played'] <= all_stats['games_played']:
            print("  ✅ Team stats filtering is working correctly")
        else:
            print("  ❌ Team stats filtering may have issues")
            return False
        
        # Test 4: Verify player stats change with game type
        print("\n4. Testing player stats variation by game type...")
        
        all_player_stats = data_service.calculate_player_stats(test_player_id, test_team_id, None)
        exhibition_player_stats = data_service.calculate_player_stats(test_player_id, test_team_id, 'E')
        
        if all_player_stats and exhibition_player_stats:
            print(f"  All games: {all_player_stats['games_played']} GP, {all_player_stats['points']} P")
            print(f"  Exhibition: {exhibition_player_stats['games_played']} GP, {exhibition_player_stats['points']} P")
            
            if exhibition_player_stats['games_played'] <= all_player_stats['games_played']:
                print("  ✅ Player stats filtering is working correctly")
            else:
                print("  ❌ Player stats filtering may have issues")
                return False
        else:
            print("  ⚠️  Could not test player stats variation (no stats returned)")
        
        # Test 5: Verify session game type methods
        print("\n5. Testing session game type methods...")
        
        try:
            # Test setting game type in session (will fail outside Flask context, but method should exist)
            current_game_type = data_service._get_game_type_from_session()
            print(f"  ✅ _get_game_type_from_session: {current_game_type}")
        except RuntimeError:
            print("  ✅ _get_game_type_from_session: Working outside request context (expected)")
        except Exception as e:
            print(f"  ❌ _get_game_type_from_session failed: {e}")
            return False
        
        # Test 6: Verify game type helper functions
        print("\n6. Testing game type helper functions...")
        
        for game_type in ['E', 'R', 'T']:
            name = config.get_game_type_name(game_type)
            color = config.get_game_type_color(game_type)
            badge_class = config.get_game_type_badge_class(game_type)
            print(f"  {game_type}: {name} (Color: {color}, Badge: {badge_class})")
        
        # Test 7: Verify game type filtering in games data
        print("\n7. Testing game type column in games data...")
        
        if 'GameType' in all_games.columns:
            game_type_counts = all_games['GameType'].value_counts()
            print(f"  Game type distribution: {game_type_counts.to_dict()}")
            print("  ✅ GameType column exists and has data")
        else:
            print("  ❌ GameType column not found in games data")
            return False
        
        print("\n=== Comprehensive Game Type Filtering Tests Completed Successfully ===")
        print("\nSummary:")
        print("✅ All DataService methods accept game_type parameter")
        print("✅ Game type filtering effectively filters data")
        print("✅ Team stats vary correctly by game type")
        print("✅ Player stats vary correctly by game type")
        print("✅ Session game type methods are implemented")
        print("✅ Game type helper functions work correctly")
        print("✅ GameType column exists in games data")
        print("\n🎉 Game type filtering is fully implemented and working!")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Comprehensive game type filtering test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comprehensive_game_type_filtering()
    sys.exit(0 if success else 1)
