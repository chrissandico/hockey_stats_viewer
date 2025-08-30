#!/usr/bin/env python3
"""
Test script to verify team stats functionality after fixes.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_team_stats():
    print("=== Testing Team Stats Functionality ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Get teams
    teams = sheets_service.get_teams()
    print(f"\nAvailable teams:")
    for _, team in teams.iterrows():
        print(f"  TeamID: {team['TeamID']}, TeamName: {team['TeamName']}, Password: {team['Password']}")
    
    # Test each team
    for _, team in teams.iterrows():
        team_id = team['TeamID']
        team_name = team['TeamName']
        print(f"\n=== Testing Team: {team_name} (ID: {team_id}) ===")
        
        # Test team stats calculation
        team_stats = data_service.calculate_team_stats(team_id)
        print(f"Team Stats:")
        print(f"  Games Played: {team_stats['games_played']}")
        print(f"  Wins: {team_stats['wins']}")
        print(f"  Losses: {team_stats['losses']}")
        print(f"  Ties: {team_stats['ties']}")
        print(f"  Goals For: {team_stats['goals_for']}")
        print(f"  Goals Against: {team_stats['goals_against']}")
        print(f"  Win Percentage: {team_stats['win_percentage']:.3f}")
        
        # Test goalie stats for this team
        players = data_service.get_players(team_id)
        goalies = players[players['Position'] == 'G']
        print(f"\nGoalies for {team_name}: {len(goalies)}")
        
        for _, goalie in goalies.iterrows():
            goalie_stats = data_service.calculate_goalie_stats(goalie['ID'], team_id)
            if goalie_stats:
                print(f"  Goalie #{goalie['JerseyNumber']}:")
                print(f"    Games Played: {goalie_stats['games_played']}")
                print(f"    Wins: {goalie_stats['wins']}")
                print(f"    GAA: {goalie_stats['gaa']:.2f}")
                print(f"    Save %: {goalie_stats['save_percentage']:.3f}")

if __name__ == "__main__":
    test_team_stats()
