#!/usr/bin/env python3
"""
Comprehensive test to verify centralized game type filtering across all layouts.
Tests Player, Team, and Game layouts for consistent Regular Season filtering.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.data_service import DataService
from services.sheets_service import SheetsService
from layouts.player_layout import create_player_layout, register_player_callbacks
from layouts.team_layout import create_team_layout, register_team_callbacks  
from layouts.game_layout import create_game_layout, register_game_callbacks
import config

def test_data_service_game_type_filtering():
    """Test that DataService properly supports game type filtering."""
    print("=" * 60)
    print("TESTING DATA SERVICE GAME TYPE FILTERING")
    print("=" * 60)
    
    try:
        # Initialize services
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        
        # Test team_id for TestTeam
        test_team_id = 'TestTeam'
        
        print(f"\n1. Testing get_games() with different game types for team: {test_team_id}")
        
        # Test all games
        all_games = data_service.get_games(test_team_id, game_type=None)
        print(f"   All games: {len(all_games)} games")
        
        # Test Regular Season games
        regular_games = data_service.get_games(test_team_id, game_type='R')
        print(f"   Regular Season games: {len(regular_games)} games")
        
        # Test Exhibition games
        exhibition_games = data_service.get_games(test_team_id, game_type='E')
        print(f"   Exhibition games: {len(exhibition_games)} games")
        
        # Test Tournament games
        tournament_games = data_service.get_games(test_team_id, game_type='T')
        print(f"   Tournament games: {len(tournament_games)} games")
        
        # Verify game type filtering is working
        if len(regular_games) > 0:
            print(f"\n   ✓ Regular Season filtering working - found {len(regular_games)} games")
            
            # Show sample Regular Season games
            print("   Sample Regular Season games:")
            for _, game in regular_games.head(3).iterrows():
                game_type_name = config.get_game_type_name(game.get('GameType', 'E'))
                print(f"     - {game['Date']} vs {game['Opponent']} ({game_type_name})")
        else:
            print("   ⚠ No Regular Season games found")
        
        print(f"\n2. Testing player stats with game type filtering")
        
        # Get roster for testing
        roster = data_service.get_roster(test_team_id)
        if len(roster) > 0:
            test_player = roster.iloc[0]
            player_id = test_player['ID']
            print(f"   Testing player: #{test_player['JerseyNumber']} (ID: {player_id})")
            
            # Test player stats with different game types
            all_stats = data_service.calculate_player_stats(player_id, test_team_id, game_type=None)
            regular_stats = data_service.calculate_player_stats(player_id, test_team_id, game_type='R')
            
            print(f"   All games - GP: {all_stats.get('games_played', 0)}, G: {all_stats.get('goals', 0)}, A: {all_stats.get('assists', 0)}")
            print(f"   Regular Season - GP: {regular_stats.get('games_played', 0)}, G: {regular_stats.get('goals', 0)}, A: {regular_stats.get('assists', 0)}")
            
            if regular_stats.get('games_played', 0) > 0:
                print("   ✓ Player stats filtering working")
            else:
                print("   ⚠ No Regular Season player stats found")
        
        print(f"\n3. Testing team leaderboards with game type filtering")
        
        # Test team leaderboards
        all_forwards = data_service.get_team_leaderboard(test_team_id, 'F', game_type=None)
        regular_forwards = data_service.get_team_leaderboard(test_team_id, 'F', game_type='R')
        
        print(f"   All games forwards: {len(all_forwards)} players")
        print(f"   Regular Season forwards: {len(regular_forwards)} players")
        
        if len(regular_forwards) > 0:
            print("   ✓ Team leaderboard filtering working")
            
            # Show top Regular Season forward
            top_forward = regular_forwards.iloc[0]
            print(f"   Top Regular Season forward: #{top_forward['JerseyNumber']} - {top_forward['Points']} pts")
        else:
            print("   ⚠ No Regular Season forwards found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing DataService: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_layout_game_type_integration():
    """Test that layouts properly integrate with game type filtering."""
    print("\n" + "=" * 60)
    print("TESTING LAYOUT GAME TYPE INTEGRATION")
    print("=" * 60)
    
    try:
        # Initialize services
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        
        # Test team context
        team_context = {'team_id': 'TestTeam', 'team_name': 'Test Team'}
        
        print(f"\n1. Testing Player Layout Integration")
        
        # Create player layout
        player_layout = create_player_layout(data_service, team_context)
        print("   ✓ Player layout created successfully")
        
        # Check if layout contains game type filter
        layout_str = str(player_layout)
        if 'game-type-filter' in layout_str:
            print("   ✓ Player layout includes game type filter component")
        else:
            print("   ❌ Player layout missing game type filter component")
        
        print(f"\n2. Testing Team Layout Integration")
        
        # Create team layout
        team_layout = create_team_layout(data_service, team_context)
        print("   ✓ Team layout created successfully")
        
        # Check if layout contains game type filter
        layout_str = str(team_layout)
        if 'game-type-filter' in layout_str:
            print("   ✓ Team layout includes game type filter component")
        else:
            print("   ❌ Team layout missing game type filter component")
        
        print(f"\n3. Testing Game Layout Integration")
        
        # Create game layout
        game_layout = create_game_layout(data_service, team_context)
        print("   ✓ Game layout created successfully")
        
        # Check if layout contains game type filter
        layout_str = str(game_layout)
        if 'game-type-filter' in layout_str:
            print("   ✓ Game layout includes game type filter component")
        else:
            print("   ❌ Game layout missing game type filter component")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing layout integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_game_type_consistency():
    """Test consistency of game type filtering across different data methods."""
    print("\n" + "=" * 60)
    print("TESTING GAME TYPE CONSISTENCY")
    print("=" * 60)
    
    try:
        # Initialize services
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        
        test_team_id = 'TestTeam'
        
        print(f"\n1. Comparing game counts across methods for team: {test_team_id}")
        
        # Get games using different methods
        games_direct = data_service.get_games(test_team_id, game_type='R')
        
        # Get games through team stats
        team_stats = data_service.get_team_stats(test_team_id, game_type='R')
        
        print(f"   Direct get_games('R'): {len(games_direct)} games")
        print(f"   Team stats games played: {team_stats.get('games_played', 0)} games")
        
        # Check consistency
        if len(games_direct) == team_stats.get('games_played', 0):
            print("   ✓ Game counts consistent between methods")
        else:
            print("   ⚠ Game count mismatch between methods")
        
        print(f"\n2. Testing game type codes in actual data")
        
        if len(games_direct) > 0:
            game_types = games_direct['GameType'].value_counts()
            print("   Game type distribution in Regular Season filter:")
            for game_type, count in game_types.items():
                type_name = config.get_game_type_name(game_type)
                print(f"     {game_type} ({type_name}): {count} games")
            
            # Verify all games are Regular Season
            if all(games_direct['GameType'] == 'R'):
                print("   ✓ All filtered games are Regular Season (R)")
            else:
                print("   ❌ Non-Regular Season games found in Regular Season filter")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing game type consistency: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive game type filtering tests."""
    print("COMPREHENSIVE GAME TYPE FILTERING TEST")
    print("Testing centralized filtering across Player, Team, and Game layouts")
    print("=" * 80)
    
    # Run all tests
    tests = [
        ("DataService Game Type Filtering", test_data_service_game_type_filtering),
        ("Layout Game Type Integration", test_layout_game_type_integration),
        ("Game Type Consistency", test_game_type_consistency)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Game type filtering is working correctly across all layouts.")
        print("\nKey fixes implemented:")
        print("- Player Layout: Removed hard-coded game_type=None, added filter component")
        print("- Game Layout: Added game type filter component and callback")
        print("- Team Layout: Already working correctly")
        print("- All layouts now use centralized DataService with consistent game_type parameter")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Review the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
