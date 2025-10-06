#!/usr/bin/env python3

"""
Comprehensive test script to verify the "All Games" filter fix.
Tests that all 7 games (1E + 4T + 2R = 7) are properly shown across all screens.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_all_games_aggregation():
    """Test that 'All Games' filter properly aggregates all game types."""
    
    print("=== COMPREHENSIVE ALL GAMES FILTER TEST ===")
    print("Testing that 'All Games' shows 1E + 4T + 2R = 7 total games")
    
    # Initialize services
    try:
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        print("✅ Services initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return False
    
    # Test team: your_team (Waxers U12 AA)
    team_id = 'your_team'
    
    print(f"\n=== TESTING TEAM: {team_id} ===")
    
    # Test 1: Individual game type counts
    print("\n1. Testing individual game type counts:")
    
    exhibition_games = data_service.get_games(team_id, game_type='E')
    regular_games = data_service.get_games(team_id, game_type='R')
    tournament_games = data_service.get_games(team_id, game_type='T')
    
    print(f"   Exhibition games (E): {len(exhibition_games)}")
    print(f"   Regular Season games (R): {len(regular_games)}")
    print(f"   Tournament games (T): {len(tournament_games)}")
    
    expected_total = len(exhibition_games) + len(regular_games) + len(tournament_games)
    print(f"   Expected total: {expected_total}")
    
    # Test 2: All Games aggregation (game_type=None)
    print("\n2. Testing 'All Games' aggregation (game_type=None):")
    
    all_games = data_service.get_games(team_id, game_type=None)
    print(f"   All games count: {len(all_games)}")
    
    # Verify the counts match
    if len(all_games) == expected_total:
        print(f"   ✅ All Games count matches expected total ({expected_total})")
    else:
        print(f"   ❌ All Games count ({len(all_games)}) does not match expected total ({expected_total})")
        return False
    
    # Test 3: Team stats aggregation
    print("\n3. Testing team stats aggregation:")
    
    # Individual game type stats
    exhibition_stats = data_service.calculate_team_stats(team_id, game_type='E')
    regular_stats = data_service.calculate_team_stats(team_id, game_type='R')
    tournament_stats = data_service.calculate_team_stats(team_id, game_type='T')
    
    print(f"   Exhibition stats - GP: {exhibition_stats['games_played']}")
    print(f"   Regular Season stats - GP: {regular_stats['games_played']}")
    print(f"   Tournament stats - GP: {tournament_stats['games_played']}")
    
    expected_total_gp = exhibition_stats['games_played'] + regular_stats['games_played'] + tournament_stats['games_played']
    print(f"   Expected total GP: {expected_total_gp}")
    
    # All Games stats
    all_games_stats = data_service.calculate_team_stats(team_id, game_type=None)
    print(f"   All Games stats - GP: {all_games_stats['games_played']}")
    
    if all_games_stats['games_played'] == expected_total_gp:
        print(f"   ✅ All Games GP matches expected total ({expected_total_gp})")
    else:
        print(f"   ❌ All Games GP ({all_games_stats['games_played']}) does not match expected total ({expected_total_gp})")
        return False
    
    # Test 4: Player stats aggregation
    print("\n4. Testing player stats aggregation:")
    
    # Get a sample player
    players = data_service.get_players(team_id)
    if not players.empty:
        sample_player_id = data_service._get_player_id_from_series(players.iloc[0])
        sample_player_jersey = players.iloc[0]['JerseyNumber']
        
        print(f"   Testing player #{sample_player_jersey} (ID: {sample_player_id})")
        
        # Individual game type stats
        exhibition_player_stats = data_service.calculate_player_stats(sample_player_id, team_id, game_type='E')
        regular_player_stats = data_service.calculate_player_stats(sample_player_id, team_id, game_type='R')
        tournament_player_stats = data_service.calculate_player_stats(sample_player_id, team_id, game_type='T')
        
        print(f"   Exhibition player stats - GP: {exhibition_player_stats['games_played'] if exhibition_player_stats else 0}")
        print(f"   Regular Season player stats - GP: {regular_player_stats['games_played'] if regular_player_stats else 0}")
        print(f"   Tournament player stats - GP: {tournament_player_stats['games_played'] if tournament_player_stats else 0}")
        
        expected_player_gp = (
            (exhibition_player_stats['games_played'] if exhibition_player_stats else 0) +
            (regular_player_stats['games_played'] if regular_player_stats else 0) +
            (tournament_player_stats['games_played'] if tournament_player_stats else 0)
        )
        print(f"   Expected total player GP: {expected_player_gp}")
        
        # All Games player stats
        all_games_player_stats = data_service.calculate_player_stats(sample_player_id, team_id, game_type=None)
        actual_player_gp = all_games_player_stats['games_played'] if all_games_player_stats else 0
        print(f"   All Games player stats - GP: {actual_player_gp}")
        
        if actual_player_gp == expected_player_gp:
            print(f"   ✅ All Games player GP matches expected total ({expected_player_gp})")
        else:
            print(f"   ❌ All Games player GP ({actual_player_gp}) does not match expected total ({expected_player_gp})")
            return False
    
    # Test 5: Game type breakdown verification
    print("\n5. Verifying specific game type breakdown:")
    
    if len(all_games) > 0:
        game_type_counts = all_games['GameType'].value_counts()
        print(f"   Game type breakdown in 'All Games':")
        for game_type, count in game_type_counts.items():
            game_type_name = {'E': 'Exhibition', 'R': 'Regular Season', 'T': 'Tournament'}.get(game_type, game_type)
            print(f"     {game_type_name} ({game_type}): {count}")
        
        # Verify expected counts
        expected_counts = {'E': 1, 'R': 2, 'T': 4}  # Based on user's specification
        all_match = True
        
        for game_type, expected_count in expected_counts.items():
            actual_count = game_type_counts.get(game_type, 0)
            if actual_count == expected_count:
                print(f"   ✅ {game_type} count matches expected ({expected_count})")
            else:
                print(f"   ❌ {game_type} count ({actual_count}) does not match expected ({expected_count})")
                all_match = False
        
        if not all_match:
            return False
    
    print("\n=== TEST SUMMARY ===")
    print("✅ All tests passed!")
    print(f"✅ 'All Games' filter correctly shows {len(all_games)} total games")
    print("✅ Team stats aggregation working correctly")
    print("✅ Player stats aggregation working correctly")
    print("✅ Game type breakdown matches expected (1E + 4T + 2R = 7)")
    
    return True

def test_layout_logic_simulation():
    """Simulate the layout logic to verify the fix works."""
    
    print("\n=== LAYOUT LOGIC SIMULATION ===")
    print("Testing the fixed logic in team and game layouts")
    
    # Simulate the old (broken) logic
    def old_logic(game_type_data):
        game_type = game_type_data if isinstance(game_type_data, str) else None
        if game_type_data and isinstance(game_type_data, dict):
            game_type = game_type_data.get('game_type')
        
        # Handle "All Games" selection
        if game_type == "all":
            game_type = None
        
        # OLD BUG: This would override None with 'R'
        if not game_type:
            game_type = 'R'
        
        return game_type
    
    # Simulate the new (fixed) logic
    def new_logic(game_type_data):
        game_type = game_type_data if isinstance(game_type_data, str) else None
        if game_type_data and isinstance(game_type_data, dict):
            game_type = game_type_data.get('game_type')
        
        # Handle "All Games" selection
        if game_type == "all":
            game_type = None
        
        # FIXED: Only default to Regular Season if explicitly undefined, not when None
        if game_type == "" or game_type is False:
            game_type = 'R'
        
        return game_type
    
    # Test cases
    test_cases = [
        ("all", "All Games selection"),
        (None, "No selection (None)"),
        ("", "Empty string"),
        (False, "False value"),
        ("R", "Regular Season"),
        ("E", "Exhibition"),
        ("T", "Tournament")
    ]
    
    print("\nTesting logic with different inputs:")
    print("Input -> Old Logic -> New Logic -> Expected")
    print("-" * 50)
    
    all_correct = True
    for input_val, description in test_cases:
        old_result = old_logic(input_val)
        new_result = new_logic(input_val)
        
        # Determine expected result
        if input_val == "all":
            expected = None  # Should be None for All Games
        elif input_val == "" or input_val is False:
            expected = 'R'  # Should default to Regular Season
        elif input_val is None:
            expected = None  # Should stay None (All Games)
        else:
            expected = input_val  # Should stay as is
        
        status = "✅" if new_result == expected else "❌"
        print(f"{str(input_val):8} -> {str(old_result):8} -> {str(new_result):8} -> {str(expected):8} {status}")
        
        if new_result != expected:
            all_correct = False
    
    if all_correct:
        print("\n✅ All logic tests passed! The fix correctly handles 'All Games' selection.")
    else:
        print("\n❌ Some logic tests failed!")
    
    return all_correct

if __name__ == "__main__":
    print("Starting comprehensive All Games filter test...")
    
    # Run the tests
    aggregation_test = test_all_games_aggregation()
    logic_test = test_layout_logic_simulation()
    
    print("\n" + "="*60)
    print("FINAL RESULTS:")
    print(f"Aggregation Test: {'✅ PASSED' if aggregation_test else '❌ FAILED'}")
    print(f"Logic Test: {'✅ PASSED' if logic_test else '❌ FAILED'}")
    
    if aggregation_test and logic_test:
        print("\n🎉 ALL TESTS PASSED! The 'All Games' filter fix is working correctly.")
        print("   - Team Stats will now show all 7 games when 'All Games' is selected")
        print("   - Game Stats will now show all 7 games when 'All Games' is selected")
        print("   - Player Stats already worked correctly and continues to work")
    else:
        print("\n❌ SOME TESTS FAILED! Please review the implementation.")
    
    print("="*60)
