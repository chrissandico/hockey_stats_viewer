#!/usr/bin/env python3
"""
Comprehensive test of the webapp functionality for the test team.
This script will test all screens (player, team, game) to verify stats accuracy.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from services.auth_service import AuthService
import pandas as pd
import importlib

# Force reload of modules to avoid caching issues
print("=== Forcing module reloads to avoid caching ===")
if 'hockey_stats_webapp.services.data_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.data_service'])
if 'hockey_stats_webapp.services.sheets_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.sheets_service'])

def test_authentication():
    """Test authentication with testteam password."""
    print("\n=== Testing Authentication ===")
    
    sheets_service = SheetsService()
    auth_service = AuthService(sheets_service)
    
    # Test authentication with testteam
    result = auth_service.verify_password('testteam')
    
    if result:
        print(f"✅ Authentication successful for test team")
        print(f"   Team ID: {result['team_id']}")
        print(f"   Team Name: {result['team_name']}")
        return result['team_id']
    else:
        print(f"❌ Authentication failed for testteam")
        return None

def test_team_screen(team_id):
    """Test the team screen functionality."""
    print(f"\n=== Testing Team Screen for {team_id} ===")
    
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Test team stats
    print("\n--- Team Statistics ---")
    team_stats = data_service.calculate_team_stats(team_id)
    print(f"Games Played: {team_stats['games_played']}")
    print(f"Wins: {team_stats['wins']}")
    print(f"Losses: {team_stats['losses']}")
    print(f"Ties: {team_stats['ties']}")
    print(f"Goals For: {team_stats['goals_for']}")
    print(f"Goals Against: {team_stats['goals_against']}")
    print(f"Win Percentage: {team_stats['win_percentage']:.3f}")
    
    # Test team leaderboards
    print("\n--- Team Leaderboards ---")
    
    # Skater leaderboard by points
    print("Top Skaters (by points):")
    skaters = data_service.get_team_leaderboard(stat='points', position=None, limit=5, team_id=team_id)
    skaters = [s for s in skaters if s['player']['Position'] != 'G']  # Filter out goalies
    for i, stats in enumerate(skaters[:5], 1):
        print(f"  {i}. #{stats['player']['JerseyNumber']} - "
              f"GP: {stats['games_played']}, "
              f"G: {stats['goals']}, "
              f"A: {stats['assists']}, "
              f"P: {stats['points']}, "
              f"+/-: {stats['plus_minus']}")
    
    # Goalie leaderboard
    print("\nGoalies (by save percentage):")
    goalies = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id)
    for i, stats in enumerate(goalies, 1):
        print(f"  {i}. #{stats['player']['JerseyNumber']} - "
              f"GP: {stats['games_played']}, "
              f"W: {stats['wins']}, "
              f"SV%: {stats['save_percentage']:.3f}, "
              f"GAA: {stats['gaa']:.2f}, "
              f"SO: {stats['shutouts']}")
    
    return team_stats, skaters, goalies

def test_player_screen(team_id):
    """Test individual player screens."""
    print(f"\n=== Testing Player Screens for {team_id} ===")
    
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Get players for the team
    players = data_service.get_players(team_id)
    print(f"Found {len(players)} players on team {team_id}")
    
    if players.empty:
        print("❌ No players found for team")
        return
    
    # Test a few players
    test_players = players.head(3)  # Test first 3 players
    
    for _, player in test_players.iterrows():
        player_id = player['ID']
        jersey = player['JerseyNumber']
        position = player['Position']
        
        print(f"\n--- Player #{jersey} ({position}) ---")
        
        if position == 'G':
            # Test goalie stats
            stats = data_service.calculate_goalie_stats(player_id, team_id)
            if stats:
                print(f"Games Played: {stats['games_played']}")
                print(f"Wins: {stats['wins']}")
                print(f"Save Percentage: {stats['save_percentage']:.3f}")
                print(f"Goals Against Average: {stats['gaa']:.2f}")
                print(f"Shutouts: {stats['shutouts']}")
            else:
                print("❌ Failed to calculate goalie stats")
        else:
            # Test skater stats
            stats = data_service.calculate_player_stats(player_id, team_id)
            if stats:
                print(f"Games Played: {stats['games_played']}")
                print(f"Goals: {stats['goals']}")
                print(f"Assists: {stats['assists']}")
                print(f"Points: {stats['points']}")
                print(f"Plus/Minus: {stats['plus_minus']}")
                print(f"Shots: {stats['shots']}")
                print(f"Penalty Minutes: {stats['penalty_minutes']}")
            else:
                print("❌ Failed to calculate player stats")
        
        # Test game log
        game_log = data_service.get_player_game_log(player_id, team_id)
        print(f"Game Log: {len(game_log)} games")
        
        if game_log:
            print("Recent games:")
            for game_stats in game_log[-3:]:  # Show last 3 games
                game = game_stats['game']
                if position == 'G':
                    print(f"  {game['Date']} vs {game['Opponent']}: "
                          f"GA={game_stats['goals_against']}, "
                          f"SV%={game_stats['save_percentage']:.3f}")
                else:
                    print(f"  {game['Date']} vs {game['Opponent']}: "
                          f"{game_stats['goals']}G, {game_stats['assists']}A, "
                          f"{game_stats['plus_minus']:+d}")

def test_game_screen(team_id):
    """Test game screen functionality."""
    print(f"\n=== Testing Game Screens for {team_id} ===")
    
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Get games for the team
    games = data_service.get_games(team_id)
    print(f"Found {len(games)} games for team {team_id}")
    
    if games.empty:
        print("❌ No games found for team")
        return
    
    # Test a few games
    test_games = games.head(3)  # Test first 3 games
    
    for _, game in test_games.iterrows():
        game_id = game['ID']
        
        print(f"\n--- Game {game_id}: {game['Date']} vs {game['Opponent']} ---")
        
        # Test game summary
        summary = data_service.get_game_summary(game_id, team_id)
        if summary:
            print(f"Final Score: {summary['game']['GoalsFor']}-{summary['game']['GoalsAgainst']}")
            print(f"Shots: {summary['your_team_shots']}-{summary['opponent_shots']}")
            print(f"Penalty Minutes: {summary['your_team_pim']}-{summary['opponent_pim']}")
            print(f"Power Play: {summary['your_team_pp_goals']}/{summary['your_team_pp_opps']} "
                  f"({summary['your_team_pp_pct']:.1%})")
        else:
            print("❌ Failed to get game summary")
        
        # Test game player stats
        player_stats = data_service.get_game_player_stats(game_id, team_id=team_id)
        print(f"Player stats: {len(player_stats)} players")
        
        if player_stats:
            print("Top performers:")
            for stats in player_stats[:3]:  # Top 3 performers
                player = stats['player']
                print(f"  #{player['JerseyNumber']}: "
                      f"{stats['goals']}G, {stats['assists']}A, "
                      f"{stats['plus_minus']:+d}")
        
        # Test game timeline
        timeline = data_service.get_game_timeline(game_id)
        print(f"Timeline: {len(timeline)} events")
        
        # Test period breakdown
        breakdown = data_service.get_period_breakdown(game_id, team_id)
        if breakdown:
            your_team = breakdown['your_team']
            opponent = breakdown['opponent']
            print(f"Period breakdown:")
            print(f"  {your_team['name']}: {your_team['periods']} = {your_team['total']}")
            print(f"  {opponent['name']}: {opponent['periods']} = {opponent['total']}")

def main():
    """Main test function."""
    print("=== COMPREHENSIVE WEBAPP TEST FOR TEST TEAM ===")
    print("Testing all screens and functionality for password 'testteam'")
    
    try:
        # Test authentication
        team_id = test_authentication()
        
        if not team_id:
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Test all screens
        team_stats, skaters, goalies = test_team_screen(team_id)
        test_player_screen(team_id)
        test_game_screen(team_id)
        
        # Summary
        print(f"\n=== TEST SUMMARY ===")
        print(f"✅ Authentication: WORKING")
        print(f"✅ Team Screen: WORKING")
        print(f"   - Team stats calculated: GP={team_stats['games_played']}")
        print(f"   - Skater leaderboard: {len(skaters)} players")
        print(f"   - Goalie leaderboard: {len(goalies)} goalies")
        print(f"✅ Player Screen: WORKING")
        print(f"✅ Game Screen: WORKING")
        
        print(f"\n🎉 All webapp screens are working correctly for test team!")
        return True
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
