#!/usr/bin/env python3
"""
Debug script to investigate why the testteam login doesn't show players in game stats or player game logs.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from services.auth_service import AuthService

def debug_testteam_issue():
    """Debug the testteam login issues."""
    print("=== DEBUGGING TESTTEAM LOGIN ISSUES ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    auth_service = AuthService(sheets_service)
    
    # Test authentication first
    print("\n1. Testing Authentication")
    print("-" * 30)
    auth_result = auth_service.verify_password('testteam')
    if auth_result:
        print("✅ Authentication successful!")
        print(f"   Team ID: {auth_result['team_id']}")
        print(f"   Team Name: {auth_result['team_name']}")
        print(f"   Is Coach: {auth_result['is_coach']}")
        team_id = auth_result['team_id']
    else:
        print("❌ Authentication failed!")
        return
    
    # Check Teams sheet
    print("\n2. Checking Teams Sheet")
    print("-" * 30)
    teams = sheets_service.get_teams()
    test_team = teams[teams['TeamID'] == team_id]
    if not test_team.empty:
        print(f"✅ Test team found in Teams sheet:")
        print(f"   TeamID: {test_team.iloc[0]['TeamID']}")
        print(f"   TeamName: {test_team.iloc[0]['TeamName']}")
        print(f"   Password: {test_team.iloc[0]['Password']}")
    else:
        print(f"❌ Test team with TeamID '{team_id}' not found in Teams sheet")
    
    # Check Players sheet
    print("\n3. Checking Players Sheet")
    print("-" * 30)
    players = sheets_service.get_players()
    test_players = players[players['TeamID'] == team_id]
    print(f"Players with TeamID '{team_id}': {len(test_players)}")
    if not test_players.empty:
        print("✅ Test team players found:")
        for _, player in test_players.iterrows():
            print(f"   Player ID: {player['ID']}, Jersey: {player['JerseyNumber']}, Position: {player['Position']}")
    else:
        print(f"❌ No players found with TeamID '{team_id}'")
        print("Available TeamIDs in Players sheet:")
        unique_team_ids = players['TeamID'].unique()
        for tid in sorted(unique_team_ids):
            count = len(players[players['TeamID'] == tid])
            print(f"   {tid}: {count} players")
    
    # Check Games sheet
    print("\n4. Checking Games Sheet")
    print("-" * 30)
    games = sheets_service.get_games()
    test_games = games[games['TeamID'] == team_id]
    print(f"Games with TeamID '{team_id}': {len(test_games)}")
    if not test_games.empty:
        print("✅ Test team games found:")
        for _, game in test_games.iterrows():
            print(f"   Game ID: {game['ID']}, Date: {game['Date']}, Opponent: {game['Opponent']}")
    else:
        print(f"❌ No games found with TeamID '{team_id}'")
        print("Available TeamIDs in Games sheet:")
        unique_team_ids = games['TeamID'].unique()
        for tid in sorted(unique_team_ids):
            count = len(games[games['TeamID'] == tid])
            print(f"   {tid}: {count} games")
    
    # Check GameRoster sheet
    print("\n5. Checking GameRoster Sheet")
    print("-" * 30)
    game_roster = sheets_service.get_game_roster()
    
    # If we have test games, check if there are roster entries for them
    if not test_games.empty:
        test_game_ids = test_games['ID'].tolist()
        test_roster_entries = game_roster[game_roster['GameID'].isin(test_game_ids)]
        print(f"GameRoster entries for test team games: {len(test_roster_entries)}")
        if not test_roster_entries.empty:
            print("✅ Test team roster entries found:")
            for _, entry in test_roster_entries.iterrows():
                print(f"   Game ID: {entry['GameID']}, Player ID: {entry['PlayerID']}, Status: {entry['Status']}")
        else:
            print(f"❌ No roster entries found for test team games")
    else:
        print("❌ Cannot check roster entries - no test team games found")
    
    # Check Events sheet for test team
    print("\n6. Checking Events Sheet")
    print("-" * 30)
    events = sheets_service.get_events()
    
    # Check what teams are in events
    unique_event_teams = events['Team'].unique() if not events.empty else []
    print(f"Teams in Events sheet: {sorted(unique_event_teams)}")
    
    # Try to find events for test team games
    if not test_games.empty:
        test_game_ids = test_games['ID'].tolist()
        test_events = events[events['GameID'].isin(test_game_ids)]
        print(f"Events for test team games: {len(test_events)}")
        if not test_events.empty:
            print("✅ Test team events found")
            event_teams = test_events['Team'].unique()
            print(f"   Event teams: {sorted(event_teams)}")
        else:
            print(f"❌ No events found for test team games")
    
    # Test data service methods
    print("\n7. Testing Data Service Methods")
    print("-" * 30)
    
    # Test get_players with team filter
    filtered_players = data_service.get_players(team_id)
    print(f"data_service.get_players('{team_id}'): {len(filtered_players)} players")
    
    # Test get_games with team filter
    filtered_games = data_service.get_games(team_id)
    print(f"data_service.get_games('{team_id}'): {len(filtered_games)} games")
    
    # Test get_game_roster with team filter
    filtered_roster = data_service.get_game_roster(team_id)
    print(f"data_service.get_game_roster('{team_id}'): {len(filtered_roster)} entries")
    
    # If we have players, test player-specific methods
    if not test_players.empty:
        test_player = test_players.iloc[0]
        player_id = test_player['ID']
        print(f"\nTesting with player ID: {player_id}")
        
        # Test get_player_games
        player_games = data_service.get_player_games(player_id, team_id)
        print(f"data_service.get_player_games('{player_id}', '{team_id}'): {len(player_games)} games")
        
        # Test get_player_game_log
        game_log = data_service.get_player_game_log(player_id, team_id)
        print(f"data_service.get_player_game_log('{player_id}', '{team_id}'): {len(game_log)} entries")
        
        # Test calculate_player_stats
        player_stats = data_service.calculate_player_stats(player_id, team_id)
        if player_stats:
            print(f"✅ Player stats calculated successfully")
            print(f"   Games Played: {player_stats['games_played']}")
            print(f"   Goals: {player_stats['goals']}")
            print(f"   Assists: {player_stats['assists']}")
            print(f"   Points: {player_stats['points']}")
        else:
            print(f"❌ Failed to calculate player stats")
    
    print("\n" + "="*50)
    print("DIAGNOSIS COMPLETE")
    print("="*50)

if __name__ == "__main__":
    debug_testteam_issue()
