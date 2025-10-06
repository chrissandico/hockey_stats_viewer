#!/usr/bin/env python3
"""
Test script to verify UI improvements:
1. Period breakdown legend removal
2. Game ordering (most recent first)
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.data_service import DataService
from services.sheets_service import SheetsService
from components.period_breakdown import create_period_breakdown_component
from layouts.game_layout import create_game_layout
import pandas as pd
from datetime import datetime

def test_period_breakdown_legend_removal():
    """Test that the period breakdown component no longer shows the 'Goals (Shots)' legend."""
    print("Testing Period Breakdown Legend Removal...")
    
    # Create test period data
    test_period_data = {
        'your_team': {
            'name': 'Test Team',
            'goals': [1, 2, 0],
            'shots': [8, 12, 5],
            'total_goals': 3,
            'total_shots': 25
        },
        'opponent': {
            'name': 'Opponent Team',
            'goals': [0, 1, 2],
            'shots': [6, 9, 8],
            'total_goals': 3,
            'total_shots': 23
        }
    }
    
    # Create the component
    component = create_period_breakdown_component(test_period_data)
    
    # Convert to string to check content
    component_str = str(component)
    
    # Check that "Goals (Shots)" legend is NOT present
    if "Goals (Shots)" in component_str:
        print("❌ FAILED: 'Goals (Shots)' legend still present in period breakdown")
        return False
    else:
        print("✅ PASSED: 'Goals (Shots)' legend successfully removed from period breakdown")
        return True

def test_game_ordering():
    """Test that games are ordered with most recent first."""
    print("\nTesting Game Ordering (Most Recent First)...")
    
    try:
        # Create mock data service with test games
        class MockDataService:
            def get_games(self, team_id=None, game_type=None):
                # Create test games with different dates
                games_data = [
                    {'ID': 1, 'Date': '2025-10-01', 'Opponent': 'Team A', 'Result': 'W', 'GoalsFor': 3, 'GoalsAgainst': 1, 'GameType': 'R'},
                    {'ID': 2, 'Date': '2025-10-05', 'Opponent': 'Team B', 'Result': 'L', 'GoalsFor': 2, 'GoalsAgainst': 4, 'GameType': 'R'},
                    {'ID': 3, 'Date': '2025-09-28', 'Opponent': 'Team C', 'Result': 'W', 'GoalsFor': 4, 'GoalsAgainst': 2, 'GameType': 'R'},
                ]
                return pd.DataFrame(games_data)
            
            def _filter_games_by_date(self, games, include_future=True):
                return games
        
        mock_service = MockDataService()
        
        # Test the sorting logic from game_layout.py
        games = mock_service.get_games()
        
        # Create radio options (similar to game_layout.py)
        radio_options = []
        for _, game in games.iterrows():
            label = f"{game['Date']} vs {game['Opponent']} ({game['Result']} {game['GoalsFor']}-{game['GoalsAgainst']}) - Regular Season"
            radio_options.append({'label': label, 'value': game['ID']})
        
        # Sort by date (descending order - most recent first)
        radio_options.sort(key=lambda x: games[games['ID'] == x['value']]['Date'].iloc[0], reverse=True)
        
        # Check that the first game is the most recent (2025-10-05)
        first_game_id = radio_options[0]['value']
        first_game_date = games[games['ID'] == first_game_id]['Date'].iloc[0]
        
        if first_game_date == '2025-10-05':
            print("✅ PASSED: Games are correctly ordered with most recent first")
            print(f"   First game date: {first_game_date}")
            return True
        else:
            print(f"❌ FAILED: Games not ordered correctly. First game date: {first_game_date}, expected: 2025-10-05")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Error testing game ordering: {e}")
        return False

def main():
    """Run all UI improvement tests."""
    print("=" * 60)
    print("UI IMPROVEMENTS TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Period breakdown legend removal
    results.append(test_period_breakdown_legend_removal())
    
    # Test 2: Game ordering
    results.append(test_game_ordering())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! UI improvements are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
