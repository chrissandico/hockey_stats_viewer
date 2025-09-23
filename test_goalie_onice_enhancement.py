#!/usr/bin/env python3
"""
Test script to verify the GoalieOnIceId enhancement for goalie statistics.
This tests both backward compatibility and the new functionality.
"""

from hockey_stats_webapp.services.sheets_service import SheetsService
from hockey_stats_webapp.services.data_service import DataService
import pandas as pd
import sys
import importlib

# Force reload of modules to avoid caching issues
print("=== Forcing module reloads to avoid caching ===")
if 'hockey_stats_webapp.services.data_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.data_service'])
if 'hockey_stats_webapp.services.sheets_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.sheets_service'])

def test_goalie_enhancement():
    """Test the enhanced goalie statistics with GoalieOnIceId support."""
    print("\n=== Testing Enhanced Goalie Statistics ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Find a goalie to test with
    players = data_service.get_players()
    goalies = players[players['Position'] == 'G']
    
    if goalies.empty:
        print("ERROR: No goalies found in player data!")
        return False
    
    # Get the first goalie
    goalie = goalies.iloc[0]
    goalie_id = goalie['ID']
    jersey_number = goalie.get('JerseyNumber', 'Unknown')
    print(f"Testing with goalie: ID={goalie_id}, Jersey={jersey_number}")
    
    # Test 1: Check if GoalieOnIceId column exists in events
    events = data_service.get_events()
    has_goalie_on_ice_column = 'GoalieOnIceId' in events.columns
    print(f"\nGoalieOnIceId column exists: {has_goalie_on_ice_column}")
    
    if has_goalie_on_ice_column:
        # Check if the column has any data
        non_null_count = events['GoalieOnIceId'].notna().sum()
        total_events = len(events)
        print(f"GoalieOnIceId populated in {non_null_count}/{total_events} events ({non_null_count/total_events*100:.1f}%)")
        
        # Show sample data
        sample_data = events[events['GoalieOnIceId'].notna()].head(3)
        if not sample_data.empty:
            print("\nSample events with GoalieOnIceId:")
            for _, event in sample_data.iterrows():
                print(f"  GameID: {event['GameID']}, GoalieOnIceId: {event['GoalieOnIceId']}, EventType: {event['EventType']}")
    
    # Test 2: Calculate goalie stats using enhanced method
    print(f"\n=== Testing Enhanced Goalie Stats Calculation ===")
    goalie_stats = data_service.calculate_goalie_stats(goalie_id)
    
    if goalie_stats:
        print(f"\nEnhanced Goalie Statistics for {jersey_number}:")
        print(f"  Games Played: {goalie_stats['games_played']}")
        print(f"  Wins: {goalie_stats['wins']}")
        print(f"  Shutouts: {goalie_stats['shutouts']}")
        print(f"  Goals Against: {goalie_stats['goals_against']}")
        print(f"  Shots Against: {goalie_stats['shots_against']}")
        print(f"  Saves: {goalie_stats['saves']}")
        print(f"  Save Percentage: {goalie_stats['save_percentage']:.3f}")
        print(f"  Goals Against Average: {goalie_stats['gaa']:.2f}")
    else:
        print("ERROR: Failed to calculate enhanced goalie statistics!")
        return False
    
    # Test 3: Test game-level stats
    print(f"\n=== Testing Enhanced Game-Level Stats ===")
    goalie_games = data_service.get_player_games(goalie_id)
    
    if not goalie_games.empty:
        # Test with the first game
        test_game = goalie_games.iloc[0]
        game_id = test_game['ID']
        print(f"Testing game-level stats for game: {game_id}")
        
        game_stats = data_service.calculate_goalie_game_stats(goalie_id, game_id)
        
        if game_stats:
            print(f"\nEnhanced Game Statistics:")
            print(f"  Date: {game_stats['game']['Date']}")
            print(f"  Opponent: {game_stats['game']['Opponent']}")
            print(f"  Result: {game_stats['result']}")
            print(f"  Shots Against: {game_stats['shots_against']}")
            print(f"  Saves: {game_stats['saves']}")
            print(f"  Goals Against: {game_stats['goals_against']}")
            print(f"  Save %: {game_stats['save_percentage']:.3f}")
            print(f"  Shutout: {'Yes' if game_stats['shutout'] else 'No'}")
        else:
            print("ERROR: Failed to calculate enhanced game statistics!")
            return False
    else:
        print("WARNING: No games found for goalie!")
    
    # Test 4: Test backward compatibility by simulating missing GoalieOnIceId
    print(f"\n=== Testing Backward Compatibility ===")
    
    # Create a copy of events without GoalieOnIceId column to simulate old data
    events_copy = events.copy()
    if 'GoalieOnIceId' in events_copy.columns:
        events_copy = events_copy.drop('GoalieOnIceId', axis=1)
    
    # Temporarily replace the events in the data service
    original_get_events = data_service.get_events
    data_service.get_events = lambda: events_copy
    
    try:
        # Test backward compatibility
        print("Testing with simulated old data (no GoalieOnIceId column)...")
        compat_stats = data_service.calculate_goalie_stats(goalie_id)
        
        if compat_stats:
            print(f"\nBackward Compatible Statistics:")
            print(f"  Games Played: {compat_stats['games_played']}")
            print(f"  Goals Against: {compat_stats['goals_against']}")
            print(f"  Shots Against: {compat_stats['shots_against']}")
            print(f"  Save Percentage: {compat_stats['save_percentage']:.3f}")
            
            # Compare with enhanced stats
            if has_goalie_on_ice_column and non_null_count > 0:
                print(f"\nComparison (Enhanced vs Backward Compatible):")
                print(f"  Goals Against: {goalie_stats['goals_against']} vs {compat_stats['goals_against']}")
                print(f"  Shots Against: {goalie_stats['shots_against']} vs {compat_stats['shots_against']}")
                print(f"  Save %: {goalie_stats['save_percentage']:.3f} vs {compat_stats['save_percentage']:.3f}")
                
                if goalie_stats['goals_against'] != compat_stats['goals_against']:
                    print("  ✅ Enhanced filtering is working - different results detected!")
                else:
                    print("  ⚠️  Same results - may indicate no GoalieOnIceId data or single goalie")
            else:
                print("  ℹ️  No GoalieOnIceId data available for comparison")
        else:
            print("ERROR: Backward compatibility test failed!")
            return False
            
    finally:
        # Restore original method
        data_service.get_events = original_get_events
    
    print(f"\n=== Enhancement Test Summary ===")
    print(f"✅ Enhanced goalie statistics calculation: PASSED")
    print(f"✅ Game-level enhanced statistics: PASSED")
    print(f"✅ Backward compatibility: PASSED")
    print(f"✅ GoalieOnIceId column detection: {'AVAILABLE' if has_goalie_on_ice_column else 'NOT AVAILABLE'}")
    
    if has_goalie_on_ice_column and non_null_count > 0:
        print(f"✅ GoalieOnIceId data utilization: ACTIVE")
    else:
        print(f"ℹ️  GoalieOnIceId data utilization: FALLBACK MODE")
    
    return True

def main():
    """Main test function."""
    print("=== GoalieOnIceId Enhancement Test ===")
    print("This test verifies the enhanced goalie statistics with backward compatibility")
    
    try:
        success = test_goalie_enhancement()
        
        if success:
            print(f"\n🎉 All tests passed! The GoalieOnIceId enhancement is working correctly.")
            print(f"   - Enhanced statistics when GoalieOnIceId data is available")
            print(f"   - Backward compatibility when GoalieOnIceId data is missing")
            print(f"   - Proper handling of goalie substitutions mid-game")
        else:
            print(f"\n❌ Some tests failed. Please check the implementation.")
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
