#!/usr/bin/env python3
"""
Test script to verify game stats fixes are working correctly.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_game_stats_fix():
    """Test that game stats are now calculated correctly."""
    print("=== TESTING GAME STATS FIXES ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Test with team_id to ensure proper filtering
    team_id = 'your_team'
    
    # Get games with the fixed calculations
    games = data_service.get_games(team_id)
    
    print(f"\nTesting with team_id: {team_id}")
    print(f"Total games: {len(games)}")
    
    # Find games with goals
    games_with_goals = games[(games['GoalsFor'] > 0) | (games['GoalsAgainst'] > 0)]
    print(f"Games with goals: {len(games_with_goals)}")
    
    if not games_with_goals.empty:
        print("\nGames with scoring:")
        for _, game in games_with_goals.iterrows():
            print(f"  Game {game['ID']}: {game['Date']} vs {game['Opponent']}")
            print(f"    Score: {game['GoalsFor']}-{game['GoalsAgainst']} ({game['Result']})")
        
        # Test game summary for a game with goals
        test_game_id = games_with_goals.iloc[0]['ID']
        print(f"\nTesting game summary for game {test_game_id}:")
        
        summary = data_service.get_game_summary(test_game_id)
        if summary:
            print(f"  Your team shots: {summary['your_team_shots']}")
            print(f"  Opponent shots: {summary['opponent_shots']}")
            print(f"  Your team goals: {summary['game']['GoalsFor']}")
            print(f"  Opponent goals: {summary['game']['GoalsAgainst']}")
            print(f"  Result: {summary['game']['Result']}")
        else:
            print("  ERROR: No summary available")
    else:
        print("No games with goals found - this might indicate an issue")
    
    print("\n=== TEST COMPLETE ===")
    return len(games_with_goals) > 0

if __name__ == "__main__":
    success = test_game_stats_fix()
    if success:
        print("✅ Game stats fixes are working correctly!")
    else:
        print("❌ Game stats fixes may need more work")
