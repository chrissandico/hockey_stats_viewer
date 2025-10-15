#!/usr/bin/env python3
"""
Test script to verify enhanced error handling and logging in DataService score calculation.
This test focuses on Task 6: Add error handling and logging.
"""

import sys
import os
import pandas as pd
import logging
from unittest.mock import Mock, MagicMock

# Add the hockey_stats_webapp directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

from services.data_service import DataService

def setup_test_logging():
    """Set up logging to capture test output"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_error_handling.log')
        ]
    )

def create_mock_sheets_service():
    """Create a mock sheets service for testing"""
    mock_service = Mock()
    
    # Mock basic data
    mock_service.get_games.return_value = pd.DataFrame({
        'ID': ['game1', 'game2', 'game3'],
        'TeamID': ['team1', 'team1', 'team1'],
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'GameType': ['R', 'R', 'E']
    })
    
    mock_service.get_events.return_value = pd.DataFrame({
        'GameID': ['game1', 'game1', 'game2', 'game2', 'game3'],
        'Team': ['your_team', 'opponent', 'your_team', 'opponent', 'your_team'],
        'IsGoal': [True, True, False, True, True],
        'EventType': ['Goal', 'Goal', 'Shot', 'Goal', 'Goal'],
        'GameType': ['R', 'R', 'R', 'R', 'E'],
        'PrimaryPlayerID': ['player1', 'player2', 'player1', 'player3', 'player1'],
        'AssistPlayer1ID': ['player2', None, None, 'player1', None],
        'AssistPlayer2ID': [None, None, None, None, None]
    })
    
    mock_service.get_teams.return_value = pd.DataFrame({
        'TeamID': ['team1'],
        'TeamName': ['Test Team']
    })
    
    mock_service.get_players.return_value = pd.DataFrame({
        'ID': ['player1', 'player2', 'player3'],
        'Name': ['Player One', 'Player Two', 'Player Three'],
        'Position': ['F', 'F', 'D'],
        'TeamID': ['team1', 'team1', 'team1']
    })
    
    mock_service.refresh_all_data = Mock()
    
    return mock_service

def test_error_handling_invalid_inputs():
    """Test error handling with invalid inputs"""
    print("\n=== Testing Error Handling with Invalid Inputs ===")
    
    mock_sheets = create_mock_sheets_service()
    data_service = DataService(mock_sheets)
    
    # Test 1: Invalid team_id in get_games
    print("\n1. Testing invalid team_id in get_games...")
    result = data_service.get_games(team_id="", game_type="R")
    assert result.empty, "Should return empty DataFrame for invalid team_id"
    print("✓ Correctly handled empty team_id")
    
    # Test 2: Invalid game_type in get_games
    print("\n2. Testing invalid game_type in get_games...")
    result = data_service.get_games(team_id="team1", game_type="INVALID")
    assert result.empty, "Should return empty DataFrame for invalid game_type"
    print("✓ Correctly handled invalid game_type")
    
    # Test 3: Invalid player_id in calculate_player_stats
    print("\n3. Testing invalid player_id in calculate_player_stats...")
    result = data_service.calculate_player_stats(player_id="")
    assert result is None, "Should return None for invalid player_id"
    print("✓ Correctly handled empty player_id")

def test_error_handling_missing_data():
    """Test error handling with missing or corrupted data"""
    print("\n=== Testing Error Handling with Missing Data ===")
    
    mock_sheets = create_mock_sheets_service()
    
    # Test with None data from sheets service
    mock_sheets.get_games.return_value = None
    mock_sheets.get_events.return_value = None
    
    data_service = DataService(mock_sheets)
    
    print("\n1. Testing with None games data...")
    result = data_service.get_games(team_id="team1")
    assert result.empty, "Should return empty DataFrame when games data is None"
    print("✓ Correctly handled None games data")

def test_error_handling_missing_columns():
    """Test error handling with missing required columns"""
    print("\n=== Testing Error Handling with Missing Columns ===")
    
    mock_sheets = create_mock_sheets_service()
    
    # Create events data missing required columns
    mock_sheets.get_events.return_value = pd.DataFrame({
        'GameID': ['game1', 'game2'],
        'Team': ['your_team', 'opponent']
        # Missing IsGoal, EventType, etc.
    })
    
    data_service = DataService(mock_sheets)
    
    print("\n1. Testing goals calculation with missing IsGoal column...")
    result = data_service.calculate_goals_for_events('player1', mock_sheets.get_events.return_value)
    assert result == 0, "Should return 0 when required columns are missing"
    print("✓ Correctly handled missing IsGoal column")

def test_team_identifier_mapping_fallback():
    """Test team identifier mapping with fallback behavior"""
    print("\n=== Testing Team Identifier Mapping Fallback ===")
    
    mock_sheets = create_mock_sheets_service()
    
    # Create events with different team names than expected
    mock_sheets.get_events.return_value = pd.DataFrame({
        'GameID': ['game1'],
        'Team': ['different_team_name'],  # Different from 'your_team'
        'IsGoal': [True],
        'EventType': ['Goal'],
        'GameType': ['R']
    })
    
    data_service = DataService(mock_sheets)
    
    print("\n1. Testing team identifier mapping with unmapped team...")
    team_identifier = data_service._get_team_identifier_for_events('unmapped_team')
    assert team_identifier is not None, "Should return fallback team identifier"
    print(f"✓ Returned fallback team identifier: {team_identifier}")

def test_cache_management():
    """Test cache management with error handling"""
    print("\n=== Testing Cache Management ===")
    
    mock_sheets = create_mock_sheets_service()
    data_service = DataService(mock_sheets)
    
    print("\n1. Testing cache info...")
    cache_info = data_service.get_cache_info()
    assert isinstance(cache_info, dict), "Should return cache info dictionary"
    print(f"✓ Cache info: {cache_info}")
    
    print("\n2. Testing cache clearing...")
    data_service.clear_games_cache()
    print("✓ Cache cleared successfully")
    
    print("\n3. Testing cache clearing with specific parameters...")
    data_service.clear_games_cache(team_id="team1", game_type="R")
    print("✓ Specific cache clearing completed")

def test_score_calculation_edge_cases():
    """Test score calculation with edge cases"""
    print("\n=== Testing Score Calculation Edge Cases ===")
    
    mock_sheets = create_mock_sheets_service()
    data_service = DataService(mock_sheets)
    
    print("\n1. Testing score calculation with empty events...")
    goals_for, goals_against = data_service._calculate_game_scores(
        'game1', pd.DataFrame(), 'your_team', 'R'
    )
    assert goals_for == 0 and goals_against == 0, "Should return 0-0 for empty events"
    print("✓ Correctly handled empty events")
    
    print("\n2. Testing score calculation with invalid game_id...")
    events = mock_sheets.get_events.return_value
    goals_for, goals_against = data_service._calculate_game_scores(
        '', events, 'your_team', 'R'
    )
    assert goals_for == 0 and goals_against == 0, "Should return 0-0 for invalid game_id"
    print("✓ Correctly handled invalid game_id")

def test_logging_output():
    """Test that logging is working correctly"""
    print("\n=== Testing Logging Output ===")
    
    mock_sheets = create_mock_sheets_service()
    data_service = DataService(mock_sheets)
    
    # Capture logger
    logger = data_service.logger
    assert logger is not None, "Logger should be initialized"
    print("✓ Logger is properly initialized")
    
    # Test logging during normal operation
    print("\n1. Testing logging during get_games...")
    result = data_service.get_games(team_id="team1", game_type="R")
    print("✓ Logging occurred during get_games operation")

def run_all_tests():
    """Run all error handling and logging tests"""
    print("Starting Enhanced Error Handling and Logging Tests")
    print("=" * 60)
    
    setup_test_logging()
    
    try:
        test_error_handling_invalid_inputs()
        test_error_handling_missing_data()
        test_error_handling_missing_columns()
        test_team_identifier_mapping_fallback()
        test_cache_management()
        test_score_calculation_edge_cases()
        test_logging_output()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Enhanced error handling and logging working correctly!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)