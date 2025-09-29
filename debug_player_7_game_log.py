#!/usr/bin/env python3
"""
Debug script to investigate why player_7's game log is missing games.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from datetime import datetime, date

def debug_player_7_game_log():
    """Debug why player_7's game log is missing games."""
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    print('=== DEBUGGING PLAYER_7 GAME LOG ISSUE ===')
    player_id = 'player_7'
    team_id = 'your_team'
    
    print(f'\nDebugging player {player_id} for team {team_id}')
    
    # Step 1: Check all games for the team
    print('\n1. Checking all games for the team...')
    all_games = data_service.get_games(team_id)
    print(f'Total games for team {team_id}: {len(all_games)}')
    if not all_games.empty:
        print('Game IDs:', all_games['ID'].tolist())
        print('Game dates:', all_games['Date'].tolist())
    
    # Step 2: Check game roster for player_7
    print(f'\n2. Checking game roster for player {player_id}...')
    game_roster = data_service.get_game_roster()
    player_roster_entries = game_roster[game_roster['PlayerID'] == player_id]
    print(f'Total roster entries for player {player_id}: {len(player_roster_entries)}')
    
    if not player_roster_entries.empty:
        print('\nRoster entries:')
        for _, entry in player_roster_entries.iterrows():
            print(f'  Game: {entry["GameID"]}, Status: {entry["Status"]}')
    
    # Step 3: Check which games player is marked as Present
    present_games = player_roster_entries[player_roster_entries['Status'] == 'Present']
    print(f'\nGames where player is marked as Present: {len(present_games)}')
    present_game_ids = present_games['GameID'].tolist()
    print('Present game IDs:', present_game_ids)
    
    # Step 4: Check date filtering
    print(f'\n3. Checking date filtering...')
    current_date = date.today()
    print(f'Current date: {current_date}')
    
    # Parse dates for present games
    present_game_details = []
    for game_id in present_game_ids:
        game_row = all_games[all_games['ID'] == game_id]
        if not game_row.empty:
            game_date_str = game_row.iloc[0]['Date']
            print(f'Game {game_id}: Date = {game_date_str}')
            
            # Try to parse the date
            try:
                # Try different date formats
                date_formats = ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y', '%Y/%m/%d']
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(str(game_date_str), fmt).date()
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    is_completed = parsed_date <= current_date
                    print(f'  Parsed date: {parsed_date}, Completed: {is_completed}')
                    present_game_details.append({
                        'game_id': game_id,
                        'date_str': game_date_str,
                        'parsed_date': parsed_date,
                        'is_completed': is_completed
                    })
                else:
                    print(f'  Could not parse date: {game_date_str}')
            except Exception as e:
                print(f'  Error parsing date {game_date_str}: {e}')
    
    # Step 5: Check what get_player_games returns
    print(f'\n4. Testing get_player_games method...')
    player_games = data_service.get_player_games(player_id, team_id)
    print(f'get_player_games returned: {len(player_games)} games')
    if not player_games.empty:
        print('Returned game IDs:', player_games['ID'].tolist())
        print('Returned game dates:', player_games['Date'].tolist())
    
    # Step 6: Test with include_future=True
    print(f'\n5. Testing get_player_games with include_future=True...')
    player_games_all = data_service.get_player_games(player_id, team_id, include_future=True)
    print(f'get_player_games (include_future=True) returned: {len(player_games_all)} games')
    if not player_games_all.empty:
        print('All game IDs:', player_games_all['ID'].tolist())
        print('All game dates:', player_games_all['Date'].tolist())
    
    # Step 7: Check game log generation
    print(f'\n6. Testing get_player_game_log method...')
    game_log = data_service.get_player_game_log(player_id, team_id)
    print(f'get_player_game_log returned: {len(game_log)} entries')
    
    # Summary
    print(f'\n=== SUMMARY ===')
    print(f'Total games for team: {len(all_games)}')
    print(f'Player roster entries: {len(player_roster_entries)}')
    print(f'Games marked as Present: {len(present_games)}')
    print(f'Completed games (date filtered): {len(player_games)}')
    print(f'All games (no date filter): {len(player_games_all)}')
    print(f'Final game log entries: {len(game_log)}')
    
    # Identify the issue
    if len(present_games) < 5:
        print(f'\n❌ ISSUE FOUND: Player is only marked as Present in {len(present_games)} games, but should be in 5 games')
        print('   Solution: Update GameRoster sheet to mark player as Present for missing games')
    elif len(player_games) < len(present_games):
        print(f'\n❌ ISSUE FOUND: Date filtering is removing {len(present_games) - len(player_games)} games')
        print('   This suggests some games have future dates')
    elif len(game_log) < len(player_games):
        print(f'\n❌ ISSUE FOUND: Game log generation is failing for {len(player_games) - len(game_log)} games')
        print('   This suggests an issue in calculate_player_game_stats method')
    else:
        print('\n✅ No obvious issue found. All numbers match expected values.')

if __name__ == "__main__":
    debug_player_7_game_log()
