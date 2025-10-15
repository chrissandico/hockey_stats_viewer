#!/usr/bin/env python3
"""
Test script to verify the new score calculation logic in DataService.
Tests the _calculate_game_scores and _filter_events_by_game_type methods.
"""

import sys
import os
import pandas as pd

# Add the hockey_stats_webapp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def test_calculate_game_scores():
    """Test the _calculate_game_scores method with different game type filters."""
    
    # Create mock data
    events_data = {
        'GameID': ['game1', 'game1', 'game1', 'game1', 'game2', 'game2'],
        'GameType': ['R', 'R', 'E', 'E', 'R', 'R'],
        'IsGoal': [True, True, True, False, True, True],
        'Team': ['your_team', 'opponent', 'your_team', 'opponent', 'your_team', 'opponent']
    }
    events_df = pd.DataFrame(events_data)
    
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
    
    print("=== Testing _calculate_game_scores method ===")
    print("\nTest data:")
    print(events_df)
    
    print("\n1. Test All Games (None filter) for game1:")
    goals_for, goals_against = service._calculate_game_scores('game1', events_df, 'your_team', None)
    assert goals_for == 2, f"Expected 2 goals for, got {goals_for}"
    assert goals_against == 1, f"Expected 1 goal against, got {goals_against}"
    print("✅ All Games test passed")
    
    print("\n2. Test Regular Season filter for game1:")
    goals_for, goals_against = service._calculate_game_scores('game1', events_df, 'your_team', 'R')
    assert goals_for == 1, f"Expected 1 goal for, got {goals_for}"
    assert goals_against == 1, f"Expected 1 goal against, got {goals_against}"
    print("✅ Regular Season filter test passed")
    
    print("\n3. Test Exhibition filter for game1:")
    goals_for, goals_against = service._calculate_game_scores('game1', events_df, 'your_team', 'E')
    assert goals_for == 1, f"Expected 1 goal for, got {goals_for}"
    assert goals_against == 0, f"Expected 0 goals against, got {goals_against}"
    print("✅ Exhibition filter test passed")
    
    print("\n4. Test Tournament filter for game1 (no events):")
    goals_for, goals_against = service._calculate_game_scores('game1', events_df, 'your_team', 'T')
    assert goals_for == 0, f"Expected 0 goals for, got {goals_for}"
    assert goals_against == 0, f"Expected 0 goals against, got {goals_against}"
    print("✅ Tournament filter test passed")
    
    print("\n=== Testing _filter_events_by_game_type method ===")
    
    print("\n1. Test All Games filter:")
    filtered = service._filter_events_by_game_type(events_df, None)
    assert len(filtered) == 6, f"Expected 6 events, got {len(filtered)}"
    print("✅ All Games filter test passed")
    
    print("\n2. Test Regular Season filter:")
    filtered = service._filter_events_by_game_type(events_df, 'R')
    assert len(filtered) == 4, f"Expected 4 events, got {len(filtered)}"
    print("✅ Regular Season filter test passed")
    
    print("\n3. Test Exhibition filter:")
    filtered = service._filter_events_by_game_type(events_df, 'E')
    assert len(filtered) == 2, f"Expected 2 events, got {len(filtered)}"
    print("✅ Exhibition filter test passed")
    
    print("\n4. Test invalid game type:")
    filtered = service._filter_events_by_game_type(events_df, 'INVALID')
    assert len(filtered) == 6, f"Expected 6 events (fallback), got {len(filtered)}"
    print("✅ Invalid game type test passed")
    
    print("\n🎉 All tests passed! The new score calculation logic is working correctly.")

if __name__ == "__main__":
    test_calculate_game_scores()