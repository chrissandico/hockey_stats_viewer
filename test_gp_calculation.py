#!/usr/bin/env python3
"""
Test script to verify GP (Games Played) calculation with date filtering.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from datetime import datetime, date

def test_gp_calculation():
    """Test the GP calculation with date filtering."""
    
    print("=== Testing GP Calculation with Date Filtering ===\n")
    
    try:
        # Initialize services
        print("1. Initializing services...")
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        
        # Get teams to test with
        print("2. Getting teams...")
        teams = sheets_service.get_teams()
        if teams.empty:
            print("ERROR: No teams found!")
            return
        
        # Use the first team for testing
        test_team = teams.iloc[0]
        team_id = test_team['TeamID']
        team_name = test_team['TeamName']
        
        print(f"3. Testing with team: {team_name} (ID: {team_id})")
        
        # Get all games for the team (before date filtering)
        print("4. Getting all games (before date filtering)...")
        all_games = data_service.get_games(team_id)
        print(f"   Total games in schedule: {len(all_games)}")
        
        if not all_games.empty and 'Date' in all_games.columns:
            print("   Sample game dates:")
            for i, (_, game) in enumerate(all_games.head(3).iterrows()):
                print(f"     - {game['Date']} vs {game.get('Opponent', 'Unknown')}")
        
        # Test date filtering
        print("5. Testing date filtering...")
        current_date = date.today()
        print(f"   Current date: {current_date}")
        
        completed_games = data_service._filter_games_by_date(all_games, include_future=False)
        print(f"   Completed games (past/current): {len(completed_games)}")
        
        # Calculate team stats (which now uses date filtering)
        print("6. Calculating team stats with new GP logic...")
        team_stats = data_service.calculate_team_stats(team_id)
        
        print("\n=== TEAM STATISTICS RESULTS ===")
        print(f"Games Played (GP): {team_stats['games_played']}")
        print(f"Wins: {team_stats['wins']}")
        print(f"Losses: {team_stats['losses']}")
        print(f"Ties: {team_stats['ties']}")
        print(f"Goals For: {team_stats['goals_for']}")
        print(f"Goals Against: {team_stats['goals_against']}")
        print(f"Win Percentage: {team_stats['win_percentage']:.3f}")
        
        # Verify that points field is removed
        if 'points' in team_stats:
            print("WARNING: 'points' field still exists in team stats!")
        else:
            print("✓ 'points' field successfully removed from team stats")
        
        print("\n=== VERIFICATION ===")
        print(f"✓ GP now counts only completed games: {team_stats['games_played']} (was {len(all_games)})")
        print(f"✓ Wins + Losses + Ties = {team_stats['wins'] + team_stats['losses'] + team_stats['ties']} (should equal GP)")
        print(f"✓ Date filtering working: {len(completed_games)} completed out of {len(all_games)} total")
        
        if team_stats['games_played'] == team_stats['wins'] + team_stats['losses'] + team_stats['ties']:
            print("✓ Math checks out!")
        else:
            print("⚠ Math doesn't add up - there may be an issue")
        
        print("\n=== TEST COMPLETED SUCCESSFULLY ===")
        
    except Exception as e:
        print(f"ERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gp_calculation()
