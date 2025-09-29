#!/usr/bin/env python3
"""
Fix script to add missing roster entries for player_7.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def fix_player_7_roster():
    """Add missing roster entries for player_7."""
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    print('=== FIXING PLAYER_7 ROSTER ENTRIES ===')
    player_id = 'player_7'
    team_id = 'your_team'
    
    # Get all completed games for the team (games that have already been played)
    all_games = data_service.get_games(team_id)
    completed_games = data_service._filter_games_by_date(all_games, include_future=False)
    
    print(f'Total completed games for team {team_id}: {len(completed_games)}')
    completed_game_ids = completed_games['ID'].tolist()
    print(f'Completed game IDs: {completed_game_ids}')
    
    # Get current roster entries for player_7
    game_roster = data_service.get_game_roster()
    player_roster_entries = game_roster[game_roster['PlayerID'] == player_id]
    current_game_ids = player_roster_entries['GameID'].tolist()
    
    print(f'\nCurrent roster entries for {player_id}: {len(player_roster_entries)}')
    print(f'Current game IDs: {current_game_ids}')
    
    # Find missing games (completed games where player is not in roster)
    missing_game_ids = [gid for gid in completed_game_ids if gid not in current_game_ids]
    
    print(f'\nMissing roster entries for {len(missing_game_ids)} games: {missing_game_ids}')
    
    if not missing_game_ids:
        print('✅ No missing roster entries found. Player is already in all completed games.')
        return
    
    # Get the GameRoster worksheet to add entries
    try:
        worksheet = sheets_service._get_worksheet('GameRoster')
        
        # Get current data to find the next row
        current_data = worksheet.get_all_records()
        next_row = len(current_data) + 2  # +2 because of header row and 1-based indexing
        
        print(f'\nAdding {len(missing_game_ids)} roster entries starting at row {next_row}...')
        
        # Prepare data to add
        rows_to_add = []
        for game_id in missing_game_ids:
            rows_to_add.append([game_id, player_id, 'Present'])
            print(f'  Adding: Game {game_id}, Player {player_id}, Status: Present')
        
        # Add the rows to the worksheet
        if rows_to_add:
            # Get the range to update
            start_row = next_row
            end_row = start_row + len(rows_to_add) - 1
            range_name = f'A{start_row}:C{end_row}'
            
            print(f'Updating range {range_name} with {len(rows_to_add)} rows...')
            worksheet.update(range_name, rows_to_add)
            
            print(f'✅ Successfully added {len(rows_to_add)} roster entries for {player_id}')
        
        # Verify the fix
        print('\n=== VERIFICATION ===')
        # Force refresh to get updated data
        sheets_service.refresh_all_data()
        data_service_new = DataService(sheets_service)
        
        # Check player games again
        player_games_after = data_service_new.get_player_games(player_id, team_id)
        game_log_after = data_service_new.get_player_game_log(player_id, team_id)
        
        print(f'Player games after fix: {len(player_games_after)}')
        print(f'Game log entries after fix: {len(game_log_after)}')
        
        if len(player_games_after) >= 5:
            print('✅ SUCCESS: Player now has 5 or more games in their log!')
        else:
            print(f'⚠️  Player still only has {len(player_games_after)} games. May need to check for additional issues.')
            
    except Exception as e:
        print(f'❌ ERROR: Failed to update GameRoster sheet: {str(e)}')
        print('You may need to manually add the missing roster entries to the GameRoster sheet.')
        print('Missing entries to add:')
        for game_id in missing_game_ids:
            print(f'  GameID: {game_id}, PlayerID: {player_id}, Status: Present')

if __name__ == "__main__":
    fix_player_7_roster()
