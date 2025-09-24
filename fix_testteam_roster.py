#!/usr/bin/env python3
"""
Script to fix the testteam roster issue by adding roster entries for completed games.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from datetime import datetime, date

def fix_testteam_roster():
    """Fix the testteam roster by adding entries for completed games."""
    print("=== FIXING TESTTEAM ROSTER ISSUE ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    team_id = 'test_team'
    current_date = date.today()
    print(f"Current date: {current_date}")
    
    # Get test team data
    games = sheets_service.get_games()
    players = sheets_service.get_players()
    game_roster = sheets_service.get_game_roster()
    
    # Get test team games and players
    test_games = games[games['TeamID'] == team_id]
    test_players = players[players['TeamID'] == team_id]
    
    print(f"\nTest team games: {len(test_games)}")
    print(f"Test team players: {len(test_players)}")
    
    # Identify completed games (past dates)
    completed_games = []
    future_games = []
    
    for _, game in test_games.iterrows():
        game_date_str = game['Date']
        try:
            # Try to parse the date
            game_date = datetime.strptime(game_date_str, '%Y-%m-%d').date()
            if game_date <= current_date:
                completed_games.append(game)
                print(f"✅ Completed game: {game['ID']} ({game_date})")
            else:
                future_games.append(game)
                print(f"⏳ Future game: {game['ID']} ({game_date})")
        except ValueError:
            print(f"❌ Could not parse date for game {game['ID']}: {game_date_str}")
    
    print(f"\nCompleted games: {len(completed_games)}")
    print(f"Future games: {len(future_games)}")
    
    # Check which games already have roster entries
    existing_roster_games = game_roster[game_roster['GameID'].isin(test_games['ID'])]['GameID'].unique()
    print(f"Games with existing roster entries: {sorted(existing_roster_games)}")
    
    # Find completed games that need roster entries
    completed_game_ids = [game['ID'] for game in completed_games]
    games_needing_roster = [gid for gid in completed_game_ids if gid not in existing_roster_games]
    
    print(f"Completed games needing roster entries: {games_needing_roster}")
    
    if not games_needing_roster:
        print("✅ All completed games already have roster entries!")
        return
    
    # Get the roster worksheet
    try:
        roster_worksheet = sheets_service._get_worksheet('GameRoster')
        
        # Get all current roster data to find the next row
        all_roster_data = roster_worksheet.get_all_values()
        next_row = len(all_roster_data) + 1
        
        print(f"\nAdding roster entries starting at row {next_row}...")
        
        # Add roster entries for each completed game that needs them
        entries_added = 0
        for game_id in games_needing_roster:
            print(f"\nAdding roster for game {game_id}...")
            
            # Add all test team players to this game as "Present"
            for _, player in test_players.iterrows():
                player_id = player['ID']
                jersey = player['JerseyNumber']
                
                # Create roster entry: [GameID, PlayerID, Status]
                roster_entry = [game_id, player_id, 'Present']
                
                print(f"  Adding player {player_id} (#{jersey}) to game {game_id}")
                roster_worksheet.insert_row(roster_entry, next_row)
                next_row += 1
                entries_added += 1
        
        print(f"\n✅ Successfully added {entries_added} roster entries!")
        
        # Verify the additions
        print("\nVerifying additions...")
        updated_game_roster = sheets_service.get_game_roster(force_refresh=True)
        
        for game_id in games_needing_roster:
            game_roster_count = len(updated_game_roster[updated_game_roster['GameID'] == game_id])
            print(f"  Game {game_id}: {game_roster_count} roster entries")
        
        print("\n✅ Roster fix completed successfully!")
        
    except Exception as e:
        print(f"❌ Error adding roster entries: {str(e)}")
        return False
    
    return True

def test_fix():
    """Test that the fix worked."""
    print("\n" + "="*50)
    print("TESTING THE FIX")
    print("="*50)
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    team_id = 'test_team'
    
    # Test with the first player
    players = data_service.get_players(team_id)
    if not players.empty:
        test_player = players.iloc[0]
        player_id = test_player['ID']
        jersey = test_player['JerseyNumber']
        
        print(f"Testing with player {player_id} (#{jersey})...")
        
        # Test get_player_games
        player_games = data_service.get_player_games(player_id, team_id)
        print(f"Player games: {len(player_games)}")
        
        # Test get_player_game_log
        game_log = data_service.get_player_game_log(player_id, team_id)
        print(f"Player game log entries: {len(game_log)}")
        
        if game_log:
            print("✅ Game log now has entries!")
            for entry in game_log[:3]:  # Show first 3 entries
                game = entry['game']
                print(f"  Game {game['ID']} ({game['Date']}): {entry['goals']}G, {entry['assists']}A, {entry['points']}P")
        else:
            print("❌ Game log is still empty")
        
        # Test game player stats for a completed game
        completed_games = data_service.get_games(team_id)
        completed_games = data_service._filter_games_by_date(completed_games, include_future=False)
        
        if not completed_games.empty:
            test_game_id = completed_games.iloc[0]['ID']
            print(f"\nTesting game player stats for game {test_game_id}...")
            
            game_player_stats = data_service.get_game_player_stats(test_game_id, team_id=team_id)
            print(f"Game player stats: {len(game_player_stats)} players")
            
            if game_player_stats:
                print("✅ Game player stats now working!")
                for stats in game_player_stats[:3]:  # Show first 3 players
                    player = stats['player']
                    print(f"  #{player['JerseyNumber']}: {stats['goals']}G, {stats['assists']}A, {stats['points']}P")
            else:
                print("❌ Game player stats still empty")

if __name__ == "__main__":
    success = fix_testteam_roster()
    if success:
        test_fix()
