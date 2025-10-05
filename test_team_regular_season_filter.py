#!/usr/bin/env python3

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.auth_service import AuthService
from services.data_service import DataService

def test_team_regular_season_filter():
    """
    Test the team stats regular season filter issue.
    """
    print("=== Testing Team Regular Season Filter Issue ===")
    
    # Initialize services
    sheets_service = SheetsService()
    auth_service = AuthService(sheets_service)
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Test authentication with provided password
    password = "waxersu12aa"
    print(f"\n1. Testing authentication with password: {password}")
    
    team_info = auth_service.verify_password(password)
    if not team_info:
        print("ERROR: Authentication failed!")
        return False
    
    print(f"✅ Authentication successful!")
    print(f"   Team ID: {team_info['team_id']}")
    print(f"   Team Name: {team_info['team_name']}")
    print(f"   Is Coach: {team_info.get('is_coach', False)}")
    
    team_id = team_info['team_id']
    
    # Test games data
    print(f"\n2. Testing games data for team {team_id}")
    
    # Get all games
    all_games = data_service.get_games(team_id, game_type=None)
    print(f"   Total games: {len(all_games)}")
    
    # Get regular season games only
    regular_games = data_service.get_games(team_id, game_type='R')
    print(f"   Regular season games: {len(regular_games)}")
    
    # Get exhibition games only
    exhibition_games = data_service.get_games(team_id, game_type='E')
    print(f"   Exhibition games: {len(exhibition_games)}")
    
    if not regular_games.empty:
        print(f"   Regular season game details:")
        for _, game in regular_games.iterrows():
            print(f"     Game ID: {game['ID']}, Date: {game['Date']}, GameType: {game.get('GameType', 'N/A')}")
    
    # Test team stats calculation
    print(f"\n3. Testing team stats calculation")
    
    # All games stats
    all_stats = data_service.calculate_team_stats(team_id, game_type=None)
    print(f"   All games stats: GP={all_stats['games_played']}, W={all_stats['wins']}, L={all_stats['losses']}")
    
    # Regular season stats
    regular_stats = data_service.calculate_team_stats(team_id, game_type='R')
    print(f"   Regular season stats: GP={regular_stats['games_played']}, W={regular_stats['wins']}, L={regular_stats['losses']}")
    
    # Test leaderboards - this is where the issue likely is
    print(f"\n4. Testing team leaderboards (the problematic part)")
    
    # Get all players for this team
    players = data_service.get_players(team_id)
    forwards = players[players['Position'] == 'F']
    defense = players[players['Position'] == 'D']
    goalies = players[players['Position'] == 'G']
    
    print(f"   Team roster: {len(forwards)} forwards, {len(defense)} defense, {len(goalies)} goalies")
    
    # Test forwards leaderboard
    print(f"\n   Testing Forwards Leaderboard:")
    
    # All games
    forwards_all = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type=None)
    print(f"     All games - {len(forwards_all)} forwards with stats")
    if forwards_all:
        top_forward = forwards_all[0]
        print(f"       Top forward: #{top_forward['player']['JerseyNumber']} - {top_forward['points']} points, {top_forward['games_played']} GP")
    
    # Regular season only
    forwards_regular = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type='R')
    print(f"     Regular season - {len(forwards_regular)} forwards with stats")
    if forwards_regular:
        top_forward = forwards_regular[0]
        print(f"       Top forward: #{top_forward['player']['JerseyNumber']} - {top_forward['points']} points, {top_forward['games_played']} GP")
    
    # Test defense leaderboard
    print(f"\n   Testing Defense Leaderboard:")
    
    # All games
    defense_all = data_service.get_team_leaderboard(stat='points', position='D', team_id=team_id, game_type=None)
    print(f"     All games - {len(defense_all)} defense with stats")
    if defense_all:
        top_defense = defense_all[0]
        print(f"       Top defense: #{top_defense['player']['JerseyNumber']} - {top_defense['points']} points, {top_defense['games_played']} GP")
    
    # Regular season only
    defense_regular = data_service.get_team_leaderboard(stat='points', position='D', team_id=team_id, game_type='R')
    print(f"     Regular season - {len(defense_regular)} defense with stats")
    if defense_regular:
        top_defense = defense_regular[0]
        print(f"       Top defense: #{top_defense['player']['JerseyNumber']} - {top_defense['points']} points, {top_defense['games_played']} GP")
    
    # Test goalies leaderboard
    print(f"\n   Testing Goalies Leaderboard:")
    
    # All games
    goalies_all = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type=None)
    print(f"     All games - {len(goalies_all)} goalies with stats")
    if goalies_all:
        top_goalie = goalies_all[0]
        print(f"       Top goalie: #{top_goalie['player']['JerseyNumber']} - {top_goalie['save_percentage']:.3f} SV%, {top_goalie['games_played']} GP")
    
    # Regular season only
    goalies_regular = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type='R')
    print(f"     Regular season - {len(goalies_regular)} goalies with stats")
    if goalies_regular:
        top_goalie = goalies_regular[0]
        print(f"       Top goalie: #{top_goalie['player']['JerseyNumber']} - {top_goalie['save_percentage']:.3f} SV%, {top_goalie['games_played']} GP")
    
    # Check if the issue is present
    print(f"\n5. Issue Analysis:")
    
    issue_found = False
    
    # Check if regular season stats are different from all games stats
    if regular_stats['games_played'] != all_stats['games_played']:
        print(f"   ✅ Team summary correctly filters: {regular_stats['games_played']} vs {all_stats['games_played']} games")
    else:
        print(f"   ❌ Team summary not filtering correctly")
        issue_found = True
    
    # Check if leaderboards are filtering correctly
    if len(forwards_regular) > 0 and len(forwards_all) > 0:
        if forwards_regular[0]['games_played'] != forwards_all[0]['games_played']:
            print(f"   ✅ Forwards leaderboard correctly filters: {forwards_regular[0]['games_played']} vs {forwards_all[0]['games_played']} games")
        else:
            print(f"   ❌ Forwards leaderboard NOT filtering correctly: {forwards_regular[0]['games_played']} vs {forwards_all[0]['games_played']} games")
            issue_found = True
    
    if len(defense_regular) > 0 and len(defense_all) > 0:
        if defense_regular[0]['games_played'] != defense_all[0]['games_played']:
            print(f"   ✅ Defense leaderboard correctly filters: {defense_regular[0]['games_played']} vs {defense_all[0]['games_played']} games")
        else:
            print(f"   ❌ Defense leaderboard NOT filtering correctly: {defense_regular[0]['games_played']} vs {defense_all[0]['games_played']} games")
            issue_found = True
    
    if len(goalies_regular) > 0 and len(goalies_all) > 0:
        if goalies_regular[0]['games_played'] != goalies_all[0]['games_played']:
            print(f"   ✅ Goalies leaderboard correctly filters: {goalies_regular[0]['games_played']} vs {goalies_all[0]['games_played']} games")
        else:
            print(f"   ❌ Goalies leaderboard NOT filtering correctly: {goalies_regular[0]['games_played']} vs {goalies_all[0]['games_played']} games")
            issue_found = True
    
    if issue_found:
        print(f"\n❌ ISSUE CONFIRMED: Player performance tables are not reflecting the Regular Season filter!")
    else:
        print(f"\n✅ No issues found - filtering appears to be working correctly")
    
    return not issue_found

if __name__ == "__main__":
    success = test_team_regular_season_filter()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Issues found that need to be fixed!")
