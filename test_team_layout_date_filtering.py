#!/usr/bin/env python3
"""
Test script to verify that the team layout properly filters games by date.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.data_service import DataService
from datetime import datetime, date
import pandas as pd

def test_team_layout_date_filtering():
    """Test that team layout filters games to only show completed games."""
    print("Testing team layout date filtering...")
    
    # Initialize data service
    data_service = DataService()
    
    # Test with a specific team
    team_id = 1  # Use team 1 for testing
    
    print(f"\n=== Testing Team Layout Date Filtering for Team {team_id} ===")
    
    # Get all games (unfiltered)
    all_games = data_service.get_games(team_id)
    print(f"Total games for team {team_id}: {len(all_games)}")
    
    # Get filtered games (what the layout should show)
    filtered_games = data_service._filter_games_by_date(all_games, include_future=False)
    print(f"Filtered games (completed only): {len(filtered_games)}")
    
    # Show today's date for reference
    today = date.today()
    print(f"Today's date: {today}")
    
    # Show some sample games and their dates
    if len(all_games) > 0:
        print(f"\nSample of all games:")
        for i, (_, game) in enumerate(all_games.head(5).iterrows()):
            print(f"  {game['Date']} - {game['Opponent']} ({game['Location']})")
    
    if len(filtered_games) > 0:
        print(f"\nSample of filtered games (completed only):")
        for i, (_, game) in enumerate(filtered_games.head(5).iterrows()):
            print(f"  {game['Date']} - {game['Opponent']} ({game['Location']})")
    
    # Verify that all filtered games are in the past
    future_games_in_filtered = 0
    if len(filtered_games) > 0:
        for _, game in filtered_games.iterrows():
            try:
                # Try multiple date formats
                game_date = None
                date_str = str(game['Date']).strip()
                
                # Try MM/DD/YYYY format first
                try:
                    game_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                except ValueError:
                    pass
                
                # Try YYYY-MM-DD format
                if game_date is None:
                    try:
                        game_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                # Try MM-DD-YYYY format
                if game_date is None:
                    try:
                        game_date = datetime.strptime(date_str, '%m-%d-%Y').date()
                    except ValueError:
                        pass
                
                if game_date and game_date > today:
                    future_games_in_filtered += 1
                    print(f"WARNING: Future game found in filtered results: {date_str}")
                    
            except Exception as e:
                print(f"Error parsing date '{game['Date']}': {e}")
    
    print(f"\nResults:")
    print(f"- Total games: {len(all_games)}")
    print(f"- Filtered games: {len(filtered_games)}")
    print(f"- Future games in filtered results: {future_games_in_filtered}")
    
    if future_games_in_filtered == 0:
        print("✅ SUCCESS: No future games found in filtered results")
    else:
        print("❌ FAILURE: Future games found in filtered results")
    
    return future_games_in_filtered == 0

if __name__ == "__main__":
    success = test_team_layout_date_filtering()
    if success:
        print("\n🎉 Team layout date filtering test PASSED!")
    else:
        print("\n💥 Team layout date filtering test FAILED!")
    
    sys.exit(0 if success else 1)
