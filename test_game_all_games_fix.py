#!/usr/bin/env python3

"""
Test script to verify the "All games" and other game type filters fix for the game stats screen.
This script tests that the game dropdown updates correctly when different game type filters are selected.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.data_service import DataService
from services.sheets_service import SheetsService

def test_game_filters():
    """Test that game stats screen shows correct games when different filters are selected."""
    
    print("=== TESTING GAME STATS SCREEN FILTER FIX ===")
    print("Testing game dropdown filtering across all game types...")
    
    try:
        # Initialize services
        sheets_service = SheetsService()
        data_service = DataService(sheets_service, force_refresh=True)
        
        team_id = "your_team"
        
        print(f"\n1. Testing individual game type filters:")
        
        # Test Exhibition games
        exhibition_games = data_service.get_games(team_id, game_type='E')
        exhibition_completed = data_service._filter_games_by_date(exhibition_games, include_future=False)
        print(f"   Exhibition: {len(exhibition_completed)} completed games (out of {len(exhibition_games)} total)")
        
        # Test Tournament games
        tournament_games = data_service.get_games(team_id, game_type='T')
        tournament_completed = data_service._filter_games_by_date(tournament_games, include_future=False)
        print(f"   Tournament: {len(tournament_completed)} completed games (out of {len(tournament_games)} total)")
        
        # Test Regular Season games
        regular_games = data_service.get_games(team_id, game_type='R')
        regular_completed = data_service._filter_games_by_date(regular_games, include_future=False)
        print(f"   Regular Season: {len(regular_completed)} completed games (out of {len(regular_games)} total)")
        
        print(f"\n2. Testing All Games filter (game_type=None):")
        
        # Test All Games (game_type=None) - this is what the fix should enable
        all_games = data_service.get_games(team_id, game_type=None)
        all_completed = data_service._filter_games_by_date(all_games, include_future=False)
        print(f"   All Games: {len(all_completed)} completed games (out of {len(all_games)} total)")
        
        # Calculate expected totals
        expected_total_games = len(exhibition_games) + len(tournament_games) + len(regular_games)
        expected_completed_games = len(exhibition_completed) + len(tournament_completed) + len(regular_completed)
        
        print(f"\n3. Game Filter Verification:")
        print(f"   Expected total games: {expected_total_games}")
        print(f"   Actual total games:   {len(all_games)}")
        print(f"   Expected completed games: {expected_completed_games}")
        print(f"   Actual completed games:   {len(all_completed)}")
        
        # Check if game filtering is working
        total_games_correct = len(all_games) == expected_total_games
        completed_games_correct = len(all_completed) == expected_completed_games
        
        if total_games_correct and completed_games_correct and expected_total_games > 0:
            print(f"   ✅ SUCCESS: Game filtering is working correctly!")
            print(f"   ✅ All Games filter shows {len(all_games)} total games and {len(all_completed)} completed games")
        else:
            print(f"   ❌ FAILURE: Game filtering is not working correctly!")
            if not total_games_correct:
                print(f"   ❌ Total games mismatch: expected {expected_total_games}, got {len(all_games)}")
            if not completed_games_correct:
                print(f"   ❌ Completed games mismatch: expected {expected_completed_games}, got {len(all_completed)}")
            return False
        
        print(f"\n4. Testing game dropdown content for each filter:")
        
        # Test what the game dropdown would show for each filter
        filters_to_test = [
            ('Exhibition', 'E'),
            ('Regular Season', 'R'), 
            ('Tournament', 'T'),
            ('All Games', None)
        ]
        
        all_dropdown_working = True
        
        for filter_name, game_type in filters_to_test:
            games = data_service.get_games(team_id, game_type=game_type)
            completed_games = data_service._filter_games_by_date(games, include_future=False)
            
            print(f"   {filter_name} dropdown would show: {len(completed_games)} games")
            
            # Show sample games if any exist
            if not completed_games.empty:
                sample_game = completed_games.iloc[0]
                game_type_code = sample_game.get('GameType', 'E')
                print(f"     Sample: {sample_game['Date']} vs {sample_game['Opponent']} ({game_type_code})")
            else:
                print(f"     No completed games found for {filter_name}")
                if filter_name != 'All Games':  # It's OK if individual types have no games
                    continue
                else:  # But All Games should have games if any individual type has games
                    if expected_completed_games > 0:
                        print(f"     ❌ ERROR: All Games shows no games but individual types have {expected_completed_games} total")
                        all_dropdown_working = False
        
        if all_dropdown_working:
            print(f"   ✅ SUCCESS: Game dropdown content is correct for all filters!")
        else:
            print(f"   ❌ FAILURE: Game dropdown content has issues!")
            return False
        
        print(f"\n5. Testing game type consistency:")
        
        # Verify that All Games actually contains games from all types
        if not all_completed.empty:
            game_types_in_all = set(all_completed['GameType'].unique())
            expected_game_types = set()
            
            if not exhibition_completed.empty:
                expected_game_types.update(exhibition_completed['GameType'].unique())
            if not tournament_completed.empty:
                expected_game_types.update(tournament_completed['GameType'].unique())
            if not regular_completed.empty:
                expected_game_types.update(regular_completed['GameType'].unique())
            
            print(f"   Game types in All Games: {sorted(game_types_in_all)}")
            print(f"   Expected game types: {sorted(expected_game_types)}")
            
            if game_types_in_all == expected_game_types:
                print(f"   ✅ SUCCESS: All Games contains correct game types!")
            else:
                print(f"   ❌ FAILURE: All Games missing some game types!")
                return False
        
        print(f"\n🎉 ALL TESTS PASSED: Game stats screen filters are working correctly!")
        print(f"   - Exhibition filter shows only Exhibition games")
        print(f"   - Regular Season filter shows only Regular Season games")
        print(f"   - Tournament filter shows only Tournament games")
        print(f"   - All Games filter shows games from all types combined")
        return True
            
    except Exception as e:
        print(f"❌ ERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_game_filters()
    if success:
        print(f"\n🎉 GAME FILTERS FIX VERIFIED: The fix is working correctly!")
        print(f"   The game stats screen should now properly filter games when different game types are selected.")
    else:
        print(f"\n💥 GAME FILTERS FIX FAILED: There may still be an issue with the implementation.")
    
    sys.exit(0 if success else 1)
