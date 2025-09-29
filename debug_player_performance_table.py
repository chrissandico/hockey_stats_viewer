#!/usr/bin/env python3
"""
Debug script to investigate why the player performance table is not showing all players.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def debug_player_performance_table():
    """Debug the player performance table issue."""
    
    print('=== DEBUGGING PLAYER PERFORMANCE TABLE ISSUE ===')
    
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Get all teams to test
    teams = sheets_service.get_teams()
    
    for _, team in teams.iterrows():
        team_id = team['TeamID']
        team_name = team['TeamName']
        
        print(f'\n--- Testing team: {team_name} ({team_id}) ---')
        
        # Get completed games for this team
        games = data_service.get_games(team_id)
        completed_games = data_service._filter_games_by_date(games, include_future=False)
        
        if completed_games.empty:
            print(f'No completed games for team {team_id}')
            continue
        
        # Test the first few completed games
        test_games = completed_games.head(3)
        
        for _, game in test_games.iterrows():
            game_id = game['ID']
            game_date = game['Date']
            opponent = game.get('Opponent', 'Unknown')
            
            print(f'\n  Game {game_id}: {game_date} vs {opponent}')
            
            # Get all players for this team
            all_players = data_service.get_players(team_id)
            total_players = len(all_players)
            
            # Get players shown in performance table (using the same method as the webapp)
            performance_table_players = data_service.get_game_player_stats(game_id, None, team_id)
            shown_players = len(performance_table_players)
            
            print(f'    Total team players: {total_players}')
            print(f'    Players in performance table: {shown_players}')
            
            if shown_players < total_players:
                print(f'    ⚠️  ISSUE: Missing {total_players - shown_players} players from performance table')
                
                # Find which players are missing
                shown_player_ids = [stats['player']['ID'] for stats in performance_table_players]
                missing_players = all_players[~all_players['ID'].isin(shown_player_ids)]
                
                print(f'    Missing players:')
                for _, missing_player in missing_players.iterrows():
                    player_id = missing_player['ID']
                    jersey = missing_player['JerseyNumber']
                    position = missing_player['Position']
                    
                    # Check if player has roster entry for this game
                    game_roster = data_service.get_game_roster()
                    roster_entry = game_roster[(game_roster['GameID'] == game_id) & 
                                             (game_roster['PlayerID'] == player_id)]
                    
                    if roster_entry.empty:
                        print(f'      #{jersey} ({player_id}, {position}): NO ROSTER ENTRY')
                    else:
                        status = roster_entry.iloc[0]['Status']
                        print(f'      #{jersey} ({player_id}, {position}): Roster status = {status}')
            else:
                print(f'    ✅ All players showing correctly')
    
    print('\n=== SUMMARY ===')
    print('If players are missing from the performance table, it\'s likely due to:')
    print('1. Missing entries in the GameRoster sheet')
    print('2. Roster entries with Status != "Present"')
    print('\nNext step: Run fix_all_missing_roster_entries.py to add missing entries')

if __name__ == "__main__":
    debug_player_performance_table()
