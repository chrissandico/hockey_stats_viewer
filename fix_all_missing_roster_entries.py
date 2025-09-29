#!/usr/bin/env python3
"""
Comprehensive fix script to add missing roster entries for all players with incomplete game logs.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def fix_all_missing_roster_entries():
    """Fix missing roster entries for all players across all teams."""
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    print('=== FIXING ALL MISSING ROSTER ENTRIES ===')
    
    # Get all teams
    teams = sheets_service.get_teams()
    all_fixes = []
    
    for _, team in teams.iterrows():
        team_id = team['TeamID']
        team_name = team['TeamName']
        
        print(f'\n--- Processing team: {team_name} ({team_id}) ---')
        
        # Get all players for this team
        players = data_service.get_players(team_id)
        
        if players.empty:
            print(f'No players found for team {team_id}')
            continue
        
        # Get completed games for this team
        completed_games = data_service.get_games(team_id)
        completed_games = data_service._filter_games_by_date(completed_games, include_future=False)
        total_completed_games = len(completed_games)
        completed_game_ids = completed_games['ID'].tolist()
        
        print(f'Total completed games for team: {total_completed_games}')
        print(f'Completed game IDs: {completed_game_ids}')
        
        if total_completed_games == 0:
            print(f'No completed games for team {team_id}')
            continue
        
        # Check each player for missing roster entries
        team_fixes = []
        
        for _, player in players.iterrows():
            player_id = player['ID']
            jersey_number = player['JerseyNumber']
            
            # Get current roster entries for this player
            game_roster = data_service.get_game_roster()
            player_roster_entries = game_roster[game_roster['PlayerID'] == player_id]
            current_game_ids = player_roster_entries['GameID'].tolist()
            
            # Find missing games (completed games where player is not in roster)
            missing_game_ids = [gid for gid in completed_game_ids if gid not in current_game_ids]
            
            if missing_game_ids:
                print(f'  Player #{jersey_number} ({player_id}): Missing {len(missing_game_ids)} roster entries')
                team_fixes.extend([{
                    'player_id': player_id,
                    'jersey_number': jersey_number,
                    'game_id': game_id
                } for game_id in missing_game_ids])
        
        if team_fixes:
            print(f'  Total missing entries for team {team_name}: {len(team_fixes)}')
            all_fixes.extend(team_fixes)
        else:
            print(f'  No missing entries found for team {team_name}')
    
    # Apply all fixes
    if not all_fixes:
        print('\n✅ No missing roster entries found across all teams!')
        return
    
    print(f'\n=== APPLYING {len(all_fixes)} FIXES ===')
    
    try:
        worksheet = sheets_service._get_worksheet('GameRoster')
        
        # Get current data to find the next row
        current_data = worksheet.get_all_records()
        next_row = len(current_data) + 2  # +2 because of header row and 1-based indexing
        
        print(f'Adding {len(all_fixes)} roster entries starting at row {next_row}...')
        
        # Prepare data to add
        rows_to_add = []
        for fix in all_fixes:
            rows_to_add.append([fix['game_id'], fix['player_id'], 'Present'])
            print(f'  Adding: Game {fix["game_id"]}, Player {fix["player_id"]} (#{fix["jersey_number"]}), Status: Present')
        
        # Add the rows to the worksheet in batches to avoid timeout
        batch_size = 100
        total_added = 0
        
        for i in range(0, len(rows_to_add), batch_size):
            batch = rows_to_add[i:i + batch_size]
            start_row = next_row + i
            end_row = start_row + len(batch) - 1
            range_name = f'A{start_row}:C{end_row}'
            
            print(f'Updating batch {i//batch_size + 1}: range {range_name} with {len(batch)} rows...')
            worksheet.update(values=batch, range_name=range_name)
            total_added += len(batch)
            print(f'  Added {len(batch)} entries (total: {total_added}/{len(rows_to_add)})')
        
        print(f'\n✅ Successfully added {total_added} roster entries!')
        
        # Verify the fix
        print('\n=== VERIFICATION ===')
        # Force refresh to get updated data
        sheets_service.refresh_all_data()
        data_service_new = DataService(sheets_service)
        
        # Test a few players to verify the fix
        verification_players = [
            ('player_7', 'your_team'),
            ('player_53', 'leafsu18aaa'),
            ('player_66', 'test_team')
        ]
        
        for player_id, team_id in verification_players:
            try:
                player_games_after = data_service_new.get_player_games(player_id, team_id)
                game_log_after = data_service_new.get_player_game_log(player_id, team_id)
                
                print(f'Player {player_id} ({team_id}): {len(player_games_after)} games, {len(game_log_after)} log entries')
            except Exception as e:
                print(f'Error verifying {player_id}: {str(e)}')
        
        print('\n✅ SUCCESS: All missing roster entries have been added!')
        print('Players should now see all their games in their game logs.')
        
    except Exception as e:
        print(f'\n❌ ERROR: Failed to update GameRoster sheet: {str(e)}')
        print('You may need to manually add the missing roster entries.')
        print(f'Total entries to add: {len(all_fixes)}')
        
        # Save the fixes to a file for manual processing
        with open('missing_roster_entries.txt', 'w') as f:
            f.write('Missing Roster Entries to Add:\n')
            f.write('GameID,PlayerID,Status\n')
            for fix in all_fixes:
                f.write(f'{fix["game_id"]},{fix["player_id"]},Present\n')
        
        print('Saved missing entries to missing_roster_entries.txt')

if __name__ == "__main__":
    fix_all_missing_roster_entries()
