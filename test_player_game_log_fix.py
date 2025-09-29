#!/usr/bin/env python3
"""
Test script to verify that player game logs are working correctly for all players.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def test_all_player_game_logs():
    """Test game logs for all players to ensure they show all games."""
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    print('=== TESTING ALL PLAYER GAME LOGS ===')
    
    # Get all teams
    teams = sheets_service.get_teams()
    
    for _, team in teams.iterrows():
        team_id = team['TeamID']
        team_name = team['TeamName']
        
        print(f'\n--- Testing team: {team_name} ({team_id}) ---')
        
        # Get all players for this team
        players = data_service.get_players(team_id)
        
        if players.empty:
            print(f'No players found for team {team_id}')
            continue
        
        # Get completed games for this team
        completed_games = data_service.get_games(team_id)
        completed_games = data_service._filter_games_by_date(completed_games, include_future=False)
        total_completed_games = len(completed_games)
        
        print(f'Total completed games for team: {total_completed_games}')
        
        if total_completed_games == 0:
            print(f'No completed games for team {team_id}')
            continue
        
        # Test each player
        issues_found = []
        
        for _, player in players.iterrows():
            player_id = player['ID']
            jersey_number = player['JerseyNumber']
            position = player['Position']
            
            # Get player's game log
            game_log = data_service.get_player_game_log(player_id, team_id)
            game_log_count = len(game_log)
            
            # Get player's roster entries
            game_roster = data_service.get_game_roster()
            player_roster_entries = game_roster[game_roster['PlayerID'] == player_id]
            present_games = player_roster_entries[player_roster_entries['Status'] == 'Present']
            roster_count = len(present_games)
            
            # Check if there's a discrepancy
            if game_log_count != roster_count:
                issues_found.append({
                    'player_id': player_id,
                    'jersey_number': jersey_number,
                    'position': position,
                    'roster_count': roster_count,
                    'game_log_count': game_log_count,
                    'issue': f'Roster has {roster_count} games but game log shows {game_log_count}'
                })
            
            print(f'  Player #{jersey_number} ({position}): {game_log_count} games in log, {roster_count} in roster')
        
        # Report issues
        if issues_found:
            print(f'\n❌ ISSUES FOUND for team {team_name}:')
            for issue in issues_found:
                print(f'  Player #{issue["jersey_number"]} ({issue["player_id"]}): {issue["issue"]}')
        else:
            print(f'\n✅ All players in team {team_name} have consistent game logs')

def create_roster_fix_script():
    """Create a general script to fix roster issues for any player."""
    script_content = '''#!/usr/bin/env python3
"""
General script to fix missing roster entries for any player.
Usage: python fix_player_roster_general.py <player_id> <team_id>
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def fix_player_roster(player_id, team_id):
    """Add missing roster entries for a specific player."""
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    print(f'=== FIXING ROSTER ENTRIES FOR {player_id} ===')
    
    # Get all completed games for the team
    all_games = data_service.get_games(team_id)
    completed_games = data_service._filter_games_by_date(all_games, include_future=False)
    
    print(f'Total completed games for team {team_id}: {len(completed_games)}')
    completed_game_ids = completed_games['ID'].tolist()
    
    # Get current roster entries for the player
    game_roster = data_service.get_game_roster()
    player_roster_entries = game_roster[game_roster['PlayerID'] == player_id]
    current_game_ids = player_roster_entries['GameID'].tolist()
    
    print(f'Current roster entries for {player_id}: {len(player_roster_entries)}')
    
    # Find missing games
    missing_game_ids = [gid for gid in completed_game_ids if gid not in current_game_ids]
    
    print(f'Missing roster entries for {len(missing_game_ids)} games: {missing_game_ids}')
    
    if not missing_game_ids:
        print('✅ No missing roster entries found.')
        return
    
    # Add missing entries
    try:
        worksheet = sheets_service._get_worksheet('GameRoster')
        current_data = worksheet.get_all_records()
        next_row = len(current_data) + 2
        
        rows_to_add = []
        for game_id in missing_game_ids:
            rows_to_add.append([game_id, player_id, 'Present'])
        
        if rows_to_add:
            start_row = next_row
            end_row = start_row + len(rows_to_add) - 1
            range_name = f'A{start_row}:C{end_row}'
            
            worksheet.update(values=rows_to_add, range_name=range_name)
            print(f'✅ Successfully added {len(rows_to_add)} roster entries')
            
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_player_roster_general.py <player_id> <team_id>")
        sys.exit(1)
    
    player_id = sys.argv[1]
    team_id = sys.argv[2]
    fix_player_roster(player_id, team_id)
'''
    
    with open('fix_player_roster_general.py', 'w') as f:
        f.write(script_content)
    
    print('✅ Created fix_player_roster_general.py for future use')

if __name__ == "__main__":
    test_all_player_game_logs()
    create_roster_fix_script()
