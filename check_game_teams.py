#!/usr/bin/env python3
"""
Check which team games 32 and 33 belong to.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def check_game_teams():
    """Check team assignments for games with goals."""
    print("=== CHECKING GAME TEAM ASSIGNMENTS ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Get all games (no team filter)
    all_games = data_service.get_games()
    
    print(f"Total games in system: {len(all_games)}")
    
    # Find games with goals
    games_with_goals = all_games[(all_games['GoalsFor'] > 0) | (all_games['GoalsAgainst'] > 0)]
    print(f"Games with goals: {len(games_with_goals)}")
    
    if not games_with_goals.empty:
        print("\nGames with scoring:")
        for _, game in games_with_goals.iterrows():
            print(f"  Game {game['ID']}: TeamID='{game['TeamID']}', {game['Date']} vs {game['Opponent']}")
            print(f"    Score: {game['GoalsFor']}-{game['GoalsAgainst']} ({game['Result']})")
    
    # Check team distribution
    print(f"\nTeam distribution in all games:")
    team_counts = all_games['TeamID'].value_counts()
    for team_id, count in team_counts.items():
        print(f"  {team_id}: {count} games")
        
        # Get games for this specific team
        team_games = data_service.get_games(team_id)
        team_games_with_goals = team_games[(team_games['GoalsFor'] > 0) | (team_games['GoalsAgainst'] > 0)]
        print(f"    Games with goals: {len(team_games_with_goals)}")

if __name__ == "__main__":
    check_game_teams()
