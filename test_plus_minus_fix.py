#!/usr/bin/env python3
"""
Test script to verify plus-minus calculation fixes for game ID=2.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_plus_minus_fix():
    """Test the plus-minus calculation fix with game ID=2."""
    print("=== TESTING PLUS-MINUS CALCULATION FIX ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Test with game ID=2 as specified by the user
    game_id = "2"
    print(f"\nTesting with game ID: {game_id}")
    
    # Get events for this game to understand the data structure
    events = data_service.get_events()
    game_events = events[events['GameID'] == game_id]
    
    print(f"Total events in game {game_id}: {len(game_events)}")
    
    if not game_events.empty:
        print(f"Event columns: {game_events.columns.tolist()}")
        
        # Check for GoalSituation column
        if 'GoalSituation' in game_events.columns:
            goal_situations = game_events['GoalSituation'].value_counts()
            print(f"Goal situations in game {game_id}: {goal_situations.to_dict()}")
        else:
            print("WARNING: GoalSituation column not found in events data")
        
        # Check for goals in this game
        if 'IsGoal' in game_events.columns:
            goal_events = game_events[game_events['IsGoal'] == True]
            print(f"Goal events in game {game_id}: {len(goal_events)}")
            
            if not goal_events.empty:
                print("Goal event details:")
                for _, goal in goal_events.iterrows():
                    team = goal.get('Team', 'Unknown')
                    situation = goal.get('GoalSituation', 'Unknown')
                    players_on_ice = goal.get('YourTeamPlayersOnIce', 'Unknown')
                    print(f"  Team: {team}, Situation: {situation}, Players on ice: {players_on_ice}")
        
        # Check team distribution
        if 'Team' in game_events.columns:
            team_counts = game_events['Team'].value_counts()
            print(f"Team distribution in game {game_id}: {team_counts.to_dict()}")
    
    # Get game player stats to see the plus-minus values
    print(f"\n=== PLAYER STATS FOR GAME {game_id} ===")
    
    # Try to get team ID for proper filtering
    teams = sheets_service.get_teams()
    if not teams.empty:
        team_id = teams.iloc[0]['TeamID']
        print(f"Using team ID: {team_id}")
        
        # Get player stats for this game
        player_stats = data_service.get_game_player_stats(game_id, team_id=team_id)
        
        if player_stats:
            print(f"Found stats for {len(player_stats)} players in game {game_id}:")
            for stats in player_stats:
                player = stats['player']
                jersey = player.get('JerseyNumber', 'Unknown')
                position = player.get('Position', 'Unknown')
                plus_minus = stats.get('plus_minus', 0)
                goals = stats.get('goals', 0)
                assists = stats.get('assists', 0)
                points = stats.get('points', 0)
                
                print(f"  #{jersey} ({position}): {goals}G {assists}A {points}P {plus_minus:+d}")
        else:
            print("No player stats found for this game")
    
    # Test team stats to see overall plus-minus values
    print(f"\n=== TEAM LEADERBOARD (PLUS-MINUS) ===")
    if not teams.empty:
        team_id = teams.iloc[0]['TeamID']
        
        # Get forwards leaderboard
        forwards_stats = data_service.get_team_leaderboard(stat='plus_minus', position='F', team_id=team_id)
        print("Forwards (sorted by plus-minus):")
        for stats in forwards_stats[:5]:  # Top 5
            player = stats['player']
            jersey = player.get('JerseyNumber', 'Unknown')
            plus_minus = stats.get('plus_minus', 0)
            games_played = stats.get('games_played', 0)
            print(f"  #{jersey}: {plus_minus:+d} in {games_played} games")
        
        # Get defense leaderboard
        defense_stats = data_service.get_team_leaderboard(stat='plus_minus', position='D', team_id=team_id)
        print("\nDefense (sorted by plus-minus):")
        for stats in defense_stats[:5]:  # Top 5
            player = stats['player']
            jersey = player.get('JerseyNumber', 'Unknown')
            plus_minus = stats.get('plus_minus', 0)
            games_played = stats.get('games_played', 0)
            print(f"  #{jersey}: {plus_minus:+d} in {games_played} games")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_plus_minus_fix()
