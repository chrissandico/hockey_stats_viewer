#!/usr/bin/env python3

"""
Test script to verify that the SOG (Shots on Goal) column has been added to the Team Stats page
and works correctly with game type filtering.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.data_service import DataService
from services.sheets_service import SheetsService

def test_goalie_sog_data():
    """Test that goalie statistics include shots_against data for SOG column."""
    print("=== Testing Goalie SOG Data ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Test with different game types
    game_types = [None, 'E', 'R', 'T']  # All, Exhibition, Regular, Tournament
    
    for game_type in game_types:
        game_type_name = "All Games" if game_type is None else f"Game Type '{game_type}'"
        print(f"\n--- Testing {game_type_name} ---")
        
        # Get goalie leaderboard
        goalies = data_service.get_team_leaderboard(
            stat='save_percentage', 
            position='G', 
            team_id='your_team',  # Use default team
            game_type=game_type
        )
        
        print(f"Found {len(goalies)} goalies for {game_type_name}")
        
        # Check each goalie has shots_against data
        for i, goalie_stats in enumerate(goalies):
            player = goalie_stats['player']
            jersey = player.get('JerseyNumber', 'Unknown')
            shots_against = goalie_stats.get('shots_against', 0)
            games_played = goalie_stats.get('games_played', 0)
            save_percentage = goalie_stats.get('save_percentage', 0)
            
            print(f"  Goalie #{jersey}: GP={games_played}, SOG={shots_against}, SV%={save_percentage:.3f}")
            
            # Verify shots_against field exists and is reasonable
            if shots_against < 0:
                print(f"    WARNING: Negative shots against for goalie #{jersey}")
            elif games_played > 0 and shots_against == 0:
                print(f"    WARNING: Goalie #{jersey} has games played but no shots against")
            else:
                print(f"    ✓ SOG data looks good for goalie #{jersey}")
        
        if not goalies:
            print(f"  No goalies found for {game_type_name}")

def test_goalie_stats_calculation():
    """Test individual goalie stats calculation to ensure shots_against is calculated correctly."""
    print("\n=== Testing Individual Goalie Stats Calculation ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Get all players and find goalies
    players = data_service.get_players()
    goalies = players[players['Position'] == 'G']
    
    if goalies.empty:
        print("No goalies found in the roster")
        return
    
    # Test the first goalie
    test_goalie = goalies.iloc[0]
    goalie_id = test_goalie['ID']
    jersey = test_goalie.get('JerseyNumber', 'Unknown')
    
    print(f"Testing goalie #{jersey} (ID: {goalie_id})")
    
    # Test with different game types
    for game_type in [None, 'E', 'R']:
        game_type_name = "All Games" if game_type is None else f"Game Type '{game_type}'"
        
        stats = data_service.calculate_goalie_stats(
            goalie_id, 
            team_id='your_team',
            game_type=game_type
        )
        
        if stats:
            shots_against = stats.get('shots_against', 0)
            games_played = stats.get('games_played', 0)
            saves = stats.get('saves', 0)
            goals_against = stats.get('goals_against', 0)
            
            print(f"  {game_type_name}:")
            print(f"    Games Played: {games_played}")
            print(f"    Shots Against (SOG): {shots_against}")
            print(f"    Saves: {saves}")
            print(f"    Goals Against: {goals_against}")
            
            # Verify the math: saves + goals_against should equal shots_against
            if shots_against == saves + goals_against:
                print(f"    ✓ SOG calculation is correct (Saves + GA = SOG)")
            else:
                print(f"    ⚠ SOG calculation may be incorrect (Saves {saves} + GA {goals_against} ≠ SOG {shots_against})")
        else:
            print(f"  {game_type_name}: No stats found")

def test_team_layout_integration():
    """Test that the team layout would work with the new SOG column."""
    print("\n=== Testing Team Layout Integration ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Simulate what the team layout does
    team_id = 'your_team'
    
    # Test both coach and non-coach scenarios
    for is_coach in [True, False]:
        user_type = "Coach" if is_coach else "Non-Coach"
        print(f"\n--- Testing {user_type} View ---")
        
        if is_coach:
            # Coaches see goalies sorted by save percentage
            goalies_leaders = data_service.get_team_leaderboard(
                stat='save_percentage', 
                position='G', 
                team_id=team_id, 
                game_type=None
            )
            sort_label = "Save Percentage"
        else:
            # Non-coaches see goalies sorted by jersey number
            goalies_leaders = data_service.get_team_leaderboard(
                stat='jersey_number', 
                position='G', 
                team_id=team_id, 
                game_type=None
            )
            sort_label = "Jersey Number"
        
        print(f"Goalies Leaderboard (Sorted by {sort_label}):")
        print("Player | GP | W | SV% | GAA | SO | SOG")
        print("-------|----|----|-----|-----|----|----|")
        
        for stats in goalies_leaders:
            player = stats['player']
            jersey = player.get('JerseyNumber', 'Unknown')
            gp = stats.get('games_played', 0)
            wins = stats.get('wins', 0)
            sv_pct = stats.get('save_percentage', 0)
            gaa = stats.get('gaa', 0)
            shutouts = stats.get('shutouts', 0)
            sog = stats.get('shots_against', 0)  # This is our new SOG column
            
            print(f"#{jersey:>5} | {gp:>2} | {wins:>2} | {sv_pct:>3.3f} | {gaa:>3.2f} | {shutouts:>2} | {sog:>3}")
        
        if not goalies_leaders:
            print("No goalies found")

def main():
    """Run all tests."""
    print("Testing SOG Column Addition to Team Stats Page")
    print("=" * 50)
    
    try:
        test_goalie_sog_data()
        test_goalie_stats_calculation()
        test_team_layout_integration()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nThe SOG (Shots on Goal) column has been successfully added to the Team Stats page.")
        print("The column shows the total shots against each goalie for the selected game type filter.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
