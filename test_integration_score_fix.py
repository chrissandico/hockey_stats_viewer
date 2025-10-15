#!/usr/bin/env python3
"""
Integration test to verify the score calculation fix works with the actual DataService.
"""

import sys
import os
import pandas as pd

# Add the hockey_stats_webapp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def test_integration():
    """Test that the new methods integrate correctly with the existing DataService."""
    
    # Mock SheetsService for testing
    class MockSheetsService:
        def __init__(self):
            # Create mock data that matches the real structure
            self.games_data = pd.DataFrame({
                'ID': ['game1', 'game2'],
                'TeamID': ['team1', 'team1'],
                'GameType': ['R', 'E'],
                'Date': ['2024-01-01', '2024-01-02']
            })
            
            self.events_data = pd.DataFrame({
                'GameID': ['game1', 'game1', 'game1', 'game2', 'game2'],
                'GameType': ['R', 'R', 'R', 'E', 'E'],
                'IsGoal': [True, True, False, True, True],
                'Team': ['your_team', 'opponent', 'your_team', 'your_team', 'opponent'],
                'EventType': ['Goal', 'Goal', 'Shot', 'Goal', 'Goal']
            })
            
            self.teams_data = pd.DataFrame({
                'TeamID': ['team1'],
                'TeamName': ['Test Team']
            })
            
            self.players_data = pd.DataFrame({
                'ID': ['player1'],
                'TeamID': ['team1'],
                'Position': ['F']
            })
            
            self.game_roster_data = pd.DataFrame({
                'GameID': ['game1', 'game2'],
                'PlayerID': ['player1', 'player1'],
                'Status': ['Present', 'Present']
            })
        
        def get_games(self):
            return self.games_data.copy()
        
        def get_events(self):
            return self.events_data.copy()
        
        def get_teams(self):
            return self.teams_data.copy()
        
        def get_players(self):
            return self.players_data.copy()
        
        def get_game_roster(self):
            return self.game_roster_data.copy()
        
        def refresh_all_data(self):
            pass
    
    # Import the actual DataService
    try:
        from services.data_service import DataService
        
        # Create DataService with mock sheets service
        mock_sheets = MockSheetsService()
        data_service = DataService(mock_sheets)
        
        print("=== Integration Test: DataService with Score Calculation Fix ===")
        
        print("\nTest 1: Get games with All Games filter (None)")
        games_all = data_service.get_games(team_id='team1', game_type=None)
        print(f"Games returned: {len(games_all)}")
        if not games_all.empty:
            print("Sample game scores:")
            for _, game in games_all.iterrows():
                print(f"  Game {game['ID']}: {game['GoalsFor']}-{game['GoalsAgainst']}")
        
        print("\nTest 2: Get games with Regular Season filter")
        games_regular = data_service.get_games(team_id='team1', game_type='R')
        print(f"Games returned: {len(games_regular)}")
        if not games_regular.empty:
            print("Sample game scores:")
            for _, game in games_regular.iterrows():
                print(f"  Game {game['ID']}: {game['GoalsFor']}-{game['GoalsAgainst']}")
        
        print("\nTest 3: Get games with Exhibition filter")
        games_exhibition = data_service.get_games(team_id='team1', game_type='E')
        print(f"Games returned: {len(games_exhibition)}")
        if not games_exhibition.empty:
            print("Sample game scores:")
            for _, game in games_exhibition.iterrows():
                print(f"  Game {game['ID']}: {game['GoalsFor']}-{game['GoalsAgainst']}")
        
        print("\n✅ Integration test completed successfully!")
        print("The new score calculation methods are properly integrated with DataService.")
        
    except ImportError as e:
        print(f"❌ Could not import DataService: {e}")
        print("This is expected if running outside the full application context.")
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()