#!/usr/bin/env python3
"""
Final verification script to confirm that all player game logs are now working correctly.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def verify_game_log_fix():
    """Verify that all player game logs are now working correctly."""
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    print('=== VERIFYING GAME LOG FIX ===')
    
    # Test specific players that had issues
    test_cases = [
        ('player_7', 'your_team', 'Player #7 from your_team'),
        ('player_1', 'your_team', 'Player #7 from your_team (player_1)'),
        ('player_66', 'test_team', 'Player #12 from test_team'),
    ]
    
    all_passed = True
    
    for player_id, team_id, description in test_cases:
        print(f'\n--- Testing {description} ---')
        
        try:
            # Get player games and game log
            player_games = data_service.get_player_games(player_id, team_id)
            game_log = data_service.get_player_game_log(player_id, team_id)
            
            # Get completed games for the team
            completed_games = data_service.get_games(team_id)
            completed_games = data_service._filter_games_by_date(completed_games, include_future=False)
            total_completed_games = len(completed_games)
            
            # Get roster entries
            game_roster = data_service.get_game_roster()
            player_roster_entries = game_roster[game_roster['PlayerID'] == player_id]
            present_games = player_roster_entries[player_roster_entries['Status'] == 'Present']
            roster_count = len(present_games)
            
            print(f'  Team completed games: {total_completed_games}')
            print(f'  Player roster entries: {roster_count}')
            print(f'  Player games returned: {len(player_games)}')
            print(f'  Game log entries: {len(game_log)}')
            
            # Check if everything matches
            if len(player_games) == len(game_log) == roster_count:
                print(f'  ✅ PASS: All counts match ({len(game_log)} games)')
            else:
                print(f'  ❌ FAIL: Counts do not match')
                all_passed = False
                
        except Exception as e:
            print(f'  ❌ ERROR: {str(e)}')
            all_passed = False
    
    # Summary
    print(f'\n=== VERIFICATION SUMMARY ===')
    if all_passed:
        print('✅ SUCCESS: All test cases passed!')
        print('The player game log issue has been successfully resolved.')
        print('Players should now see all their games when viewing their individual stats.')
    else:
        print('❌ Some test cases failed. Additional investigation may be needed.')
    
    return all_passed

if __name__ == "__main__":
    verify_game_log_fix()
