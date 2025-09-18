#!/usr/bin/env python3
"""
Debug script to analyze game roster issues.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def analyze_roster():
    """Analyze game roster data."""
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)

    # Check game roster for Stars U11 A games
    print('=== GAME ROSTER ANALYSIS ===')
    game_roster = sheets_service.get_game_roster()
    print(f'Total game roster entries: {len(game_roster)}')

    # Check which games have roster entries
    games_with_roster = game_roster['GameID'].unique()
    print(f'Games with roster entries: {sorted(games_with_roster)}')

    # Check Stars U11 A games
    games = sheets_service.get_games()
    stars_games = games[games['TeamID'] == 'starsu11a']
    stars_game_ids = stars_games['ID'].tolist()
    print(f'Stars U11 A games: {sorted(stars_game_ids)}')

    # Check if Stars games have roster entries
    stars_roster_entries = game_roster[game_roster['GameID'].isin(stars_game_ids)]
    print(f'Stars roster entries: {len(stars_roster_entries)}')
    
    stars_games_with_roster = stars_roster_entries['GameID'].unique()
    print(f'Stars games with roster: {sorted(stars_games_with_roster)}')

    # Check specific game 5 (the future game we tested)
    game_5_roster = game_roster[game_roster['GameID'] == 5]
    print(f'Game 5 roster entries: {len(game_5_roster)}')
    
    # Check completed vs future games
    print(f'\n=== GAME DATE ANALYSIS ===')
    for _, game in stars_games.iterrows():
        game_id = game['ID']
        game_date = game['Date']
        roster_count = len(game_roster[game_roster['GameID'] == game_id])
        print(f'Game {game_id}: {game_date} - {roster_count} roster entries')

if __name__ == "__main__":
    analyze_roster()
