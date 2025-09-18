#!/usr/bin/env python3
"""
Debug script to investigate why game logs are empty for Stars U11 A.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def debug_game_log_issue():
    """Debug why game logs are empty."""
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    print('=== DEBUGGING GAME LOG ISSUE ===')
    team_id = 'starsu11a'
    player_id = 'player_37'
    
    print(f'\nDebugging player {player_id} for team {team_id}')
    
    # Check player games
    player_games = data_service.get_player_games(player_id, team_id)
    print(f'Player games: {len(player_games)}')
    if not player_games.empty:
        print('Game IDs:', player_games['ID'].tolist())
        print('Game dates:', player_games['Date'].tolist())
    
    # Check what happens in get_player_game_log
    print('\nDebugging get_player_game_log...')
    game_log = []
    for _, game in player_games.iterrows():
        game_id = game['ID']
        game_date = game['Date']
        print(f'Processing game {game_id} ({game_date})')
        
        # Try to calculate game stats
        game_stats = data_service.calculate_player_game_stats(player_id, game_id)
        if game_stats:
            print(f'  ✅ Game stats calculated successfully')
            print(f'     Goals: {game_stats["goals"]}')
            print(f'     Assists: {game_stats["assists"]}')
            print(f'     Points: {game_stats["points"]}')
            game_log.append(game_stats)
        else:
            print(f'  ❌ ERROR: Game stats returned None')
            
            # Debug why it's None
            print(f'     Checking if player was in game roster...')
            game_roster = data_service.get_game_roster()
            player_in_game = game_roster[(game_roster['GameID'] == game_id) & 
                                       (game_roster['PlayerID'] == player_id)]
            print(f'     Player in game roster: {len(player_in_game)} entries')
            
            if not player_in_game.empty:
                print(f'     Status: {player_in_game.iloc[0]["Status"]}')
    
    print(f'\nFinal game log length: {len(game_log)}')
    
    # Also check the get_player_game_log method directly
    print('\n=== TESTING get_player_game_log METHOD ===')
    direct_game_log = data_service.get_player_game_log(player_id, team_id)
    print(f'Direct method result: {len(direct_game_log)} entries')

if __name__ == "__main__":
    debug_game_log_issue()
