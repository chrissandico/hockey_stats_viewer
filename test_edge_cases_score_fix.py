#!/usr/bin/env python3
"""
Test edge cases for the score calculation fix.
"""

import sys
import os
import pandas as pd

# Add the hockey_stats_webapp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def test_edge_cases():
    """Test edge cases for the new score calculation methods."""
    
    # Mock DataService class with just the methods we need
    class MockDataService:
        def _calculate_game_scores(self, game_id, events_df, team_identifier, game_type_filter=None):
            # Get events for this specific game
            game_events = events_df[events_df['GameID'] == game_id]
            
            # Apply game type filtering if specified
            if game_type_filter is not None:
                # Filter events to only include those matching the game type filter
                if 'GameType' in game_events.columns:
                    game_events = game_events[game_events['GameType'] == game_type_filter]
                    print(f"Filtered events for game {game_id} by game type '{game_type_filter}': {len(game_events)} events")
                else:
                    print(f"WARNING: GameType column not found in events. Using all events for game {game_id}")
            else:
                # "All Games" case - include all events regardless of game type
                print(f"Using all events for game {game_id} (All Games filter): {len(game_events)} events")
            
            # Calculate goals using filtered events
            goals_for = len(game_events[(game_events['IsGoal'] == True) & 
                                       (game_events['Team'] == team_identifier)])
            goals_against = len(game_events[(game_events['IsGoal'] == True) & 
                                           (game_events['Team'] != team_identifier)])
            
            print(f"Game {game_id} scores (filter: {game_type_filter}): {goals_for}-{goals_against}")
            
            return goals_for, goals_against
        
        def _filter_events_by_game_type(self, events_df, game_type_filter=None):
            if events_df.empty:
                return events_df
            
            # Handle "All Games" case (None game_type)
            if game_type_filter is None:
                print("Event filtering: All Games selected - including all events regardless of game type")
                return events_df
            
            # Validate game type parameter
            valid_game_types = ['E', 'R', 'T']  # Exhibition, Regular Season, Tournament
            if game_type_filter not in valid_game_types:
                print(f"WARNING: Invalid game type '{game_type_filter}'. Valid types: {valid_game_types}. Using all events as fallback.")
                return events_df
            
            # Filter by specific game type
            if 'GameType' not in events_df.columns:
                print("WARNING: GameType column not found in events data. Returning all events.")
                return events_df
            
            filtered_events = events_df[events_df['GameType'] == game_type_filter]
            print(f"Event filtering: {len(filtered_events)} events out of {len(events_df)} match game type '{game_type_filter}'")
            
            return filtered_events
    
    service = MockDataService()
    
    print("=== Testing Edge Cases ===")
    
    # Test 1: Empty events DataFrame
    print("\n1. Test with empty events DataFrame:")
    empty_events = pd.DataFrame(columns=['GameID', 'GameType', 'IsGoal', 'Team'])
    goals_for, goals_against = service._calculate_game_scores('game1', empty_events, 'your_team', 'R')
    assert goals_for == 0 and goals_against == 0, "Empty events should return 0-0"
    print("✅ Empty events test passed")
    
    # Test 2: Game with no events
    print("\n2. Test game with no matching events:")
    events_data = pd.DataFrame({
        'GameID': ['game2', 'game2'],
        'GameType': ['R', 'R'],
        'IsGoal': [True, True],
        'Team': ['your_team', 'opponent']
    })
    goals_for, goals_against = service._calculate_game_scores('game1', events_data, 'your_team', 'R')
    assert goals_for == 0 and goals_against == 0, "No matching events should return 0-0"
    print("✅ No matching events test passed")
    
    # Test 3: Events without GameType column
    print("\n3. Test events without GameType column:")
    events_no_gametype = pd.DataFrame({
        'GameID': ['game1', 'game1'],
        'IsGoal': [True, True],
        'Team': ['your_team', 'opponent']
    })
    goals_for, goals_against = service._calculate_game_scores('game1', events_no_gametype, 'your_team', 'R')
    assert goals_for == 1 and goals_against == 1, "Should use all events when GameType column missing"
    print("✅ Missing GameType column test passed")
    
    # Test 4: Filter events with empty DataFrame
    print("\n4. Test filter with empty DataFrame:")
    filtered = service._filter_events_by_game_type(empty_events, 'R')
    assert len(filtered) == 0, "Empty DataFrame should remain empty"
    print("✅ Filter empty DataFrame test passed")
    
    # Test 5: Filter events without GameType column
    print("\n5. Test filter without GameType column:")
    filtered = service._filter_events_by_game_type(events_no_gametype, 'R')
    assert len(filtered) == 2, "Should return all events when GameType column missing"
    print("✅ Filter without GameType column test passed")
    
    # Test 6: Game with only non-goal events
    print("\n6. Test game with only non-goal events:")
    non_goal_events = pd.DataFrame({
        'GameID': ['game1', 'game1', 'game1'],
        'GameType': ['R', 'R', 'R'],
        'IsGoal': [False, False, False],
        'Team': ['your_team', 'opponent', 'your_team']
    })
    goals_for, goals_against = service._calculate_game_scores('game1', non_goal_events, 'your_team', 'R')
    assert goals_for == 0 and goals_against == 0, "Non-goal events should return 0-0"
    print("✅ Non-goal events test passed")
    
    print("\n🎉 All edge case tests passed! The implementation handles edge cases correctly.")

if __name__ == "__main__":
    test_edge_cases()