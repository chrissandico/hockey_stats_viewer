#!/usr/bin/env python3
"""
Test script to verify that the KeyError: 'Result' fixes are working properly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

from services.sheets_service import SheetsService
from services.data_service import DataService
from services.auth_service import AuthService

def test_games_columns():
    """Test that games have all required columns including Result, GoalsFor, GoalsAgainst."""
    print("=== Testing Games Columns ===")
    
    try:
        # Initialize services (same order as app.py)
        sheets_service = SheetsService()
        auth_service = AuthService(sheets_service)
        data_service = DataService(sheets_service)
        
        # Get games for the team
        team_id = 'your_team'
        games = data_service.get_games(team_id)
        
        print(f"Games DataFrame shape: {games.shape}")
        print(f"Games columns: {games.columns.tolist()}")
        
        # Check required columns
        required_columns = ['ID', 'Date', 'Opponent', 'Location', 'TeamID', 'GoalsFor', 'GoalsAgainst', 'Result']
        missing_columns = [col for col in required_columns if col not in games.columns]
        
        if missing_columns:
            print(f"ERROR: Missing columns: {missing_columns}")
            return False
        else:
            print("SUCCESS: All required columns present")
        
        # Check sample data
        if not games.empty:
            sample_game = games.iloc[0]
            print(f"Sample game data: {sample_game.to_dict()}")
            
            # Verify Result column values
            result_values = games['Result'].unique()
            print(f"Result column values: {result_values}")
            
            # Verify GoalsFor and GoalsAgainst are numeric
            print(f"GoalsFor data type: {games['GoalsFor'].dtype}")
            print(f"GoalsAgainst data type: {games['GoalsAgainst'].dtype}")
            
            return True
        else:
            print("WARNING: No games found")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_game_layout_creation():
    """Test that game layout can be created without KeyError."""
    print("\n=== Testing Game Layout Creation ===")
    
    try:
        # Initialize services (same order as app.py)
        sheets_service = SheetsService()
        auth_service = AuthService(sheets_service)
        data_service = DataService(sheets_service)
        
        # Import game layout
        from layouts.game_layout import create_game_layout
        
        # Create team context
        team_context = {
            'team_id': 'your_team',
            'team_name': 'WaxersU12AA'
        }
        
        # Try to create the layout
        layout = create_game_layout(data_service, team_context)
        
        print("SUCCESS: Game layout created without errors")
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_team_stats():
    """Test that team stats can be calculated without errors."""
    print("\n=== Testing Team Stats Calculation ===")
    
    try:
        # Initialize services (same order as app.py)
        sheets_service = SheetsService()
        auth_service = AuthService(sheets_service)
        data_service = DataService(sheets_service)
        
        # Calculate team stats
        team_id = 'your_team'
        team_stats = data_service.calculate_team_stats(team_id)
        
        print(f"Team stats: {team_stats}")
        
        # Verify required fields
        required_fields = ['games_played', 'wins', 'losses', 'ties', 'points', 'goals_for', 'goals_against', 'win_percentage']
        missing_fields = [field for field in required_fields if field not in team_stats]
        
        if missing_fields:
            print(f"ERROR: Missing fields: {missing_fields}")
            return False
        else:
            print("SUCCESS: All required team stats fields present")
            return True
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Running fix verification tests...\n")
    
    tests = [
        test_games_columns,
        test_game_layout_creation,
        test_team_stats
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("SUCCESS: All tests passed! Ready to deploy.")
        return 0
    else:
        print("FAILURE: Some tests failed. Do not deploy.")
        return 1

if __name__ == "__main__":
    exit(main())
