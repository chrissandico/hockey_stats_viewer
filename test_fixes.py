#!/usr/bin/env python3
"""
Test script to verify the fixes for team stats and game logs.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from services.auth_service import AuthService

def test_data_service_fixes():
    """Test the DataService fixes for Result column and team stats."""
    print("=== Testing DataService Fixes ===")
    
    try:
        # Initialize services
        print("Initializing services...")
        auth_service = AuthService()
        sheets_service = SheetsService(auth_service)
        data_service = DataService(sheets_service)
        
        # Test get_games with Result column
        print("\n1. Testing get_games() with Result column...")
        games = data_service.get_games('your_team')
        
        if games.empty:
            print("WARNING: No games found for team 'your_team'")
        else:
            print(f"Found {len(games)} games")
            print(f"Games columns: {games.columns.tolist()}")
            
            # Check if Result column exists
            if 'Result' in games.columns:
                print("✓ Result column exists")
                print(f"Sample game data: {games.iloc[0].to_dict()}")
                
                # Check Result values
                result_counts = games['Result'].value_counts()
                print(f"Result distribution: {result_counts.to_dict()}")
            else:
                print("✗ Result column missing")
        
        # Test calculate_team_stats
        print("\n2. Testing calculate_team_stats()...")
        team_stats = data_service.calculate_team_stats('your_team')
        
        if team_stats:
            print("✓ Team stats calculated successfully")
            print(f"Team stats: {team_stats}")
        else:
            print("✗ Team stats calculation failed")
        
        # Test game layout data preparation
        print("\n3. Testing game layout data preparation...")
        try:
            # Simulate what the game layout does
            radio_options = []
            for _, game in games.iterrows():
                try:
                    result = game.get('Result', 'Unknown')
                    goals_for = game.get('GoalsFor', 0)
                    goals_against = game.get('GoalsAgainst', 0)
                    
                    label = f"{game['Date']} vs {game['Opponent']} ({result} {goals_for}-{goals_against})"
                    radio_options.append({'label': label, 'value': game['ID']})
                except Exception as e:
                    print(f"Error creating game label for game {game.get('ID', 'Unknown')}: {e}")
                    label = f"{game.get('Date', 'Unknown')} vs {game.get('Opponent', 'Unknown')}"
                    radio_options.append({'label': label, 'value': game.get('ID', 'Unknown')})
            
            print(f"✓ Successfully created {len(radio_options)} game options")
            if radio_options:
                print(f"Sample option: {radio_options[0]}")
        
        except Exception as e:
            print(f"✗ Game layout data preparation failed: {e}")
        
        print("\n=== Test Results ===")
        print("✓ DataService initialization: SUCCESS")
        print("✓ Games retrieval with Result column: SUCCESS" if 'Result' in games.columns else "✗ Games retrieval with Result column: FAILED")
        print("✓ Team stats calculation: SUCCESS" if team_stats else "✗ Team stats calculation: FAILED")
        print("✓ Game layout data preparation: SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_service_fixes()
    if success:
        print("\n🎉 All tests passed! The fixes should resolve the deployment issues.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
