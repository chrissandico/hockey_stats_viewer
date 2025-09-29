#!/usr/bin/env python3
"""
Verification script to confirm the player performance table is working correctly.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def verify_player_performance_table():
    """Verify that the player performance table shows all players correctly."""
    
    print('=== VERIFYING PLAYER PERFORMANCE TABLE ===')
    
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Test specific scenarios that might cause issues
    test_cases = [
        {
            'team_id': 'your_team',
            'team_name': 'Waxers U12 AA',
            'game_id': 2,
            'description': 'Recent completed game with events'
        },
        {
            'team_id': 'starsu11a', 
            'team_name': 'Stars U11 A',
            'game_id': 32,
            'description': 'Stars team game'
        },
        {
            'team_id': 'test_team',
            'team_name': 'Leafs U18 AAA', 
            'game_id': 38,
            'description': 'Test team with high-scoring game'
        }
    ]
    
    all_tests_passed = True
    
    for test_case in test_cases:
        team_id = test_case['team_id']
        team_name = test_case['team_name']
        game_id = test_case['game_id']
        description = test_case['description']
        
        print(f'\n--- Testing: {description} ---')
        print(f'Team: {team_name} ({team_id})')
        print(f'Game ID: {game_id}')
        
        try:
            # Get all players for this team
            all_players = data_service.get_players(team_id)
            total_players = len(all_players)
            
            # Test the player performance table functionality
            # This is the same method called by the webapp
            performance_stats = data_service.get_game_player_stats(game_id, None, team_id)
            shown_players = len(performance_stats)
            
            print(f'Total team players: {total_players}')
            print(f'Players in performance table: {shown_players}')
            
            if shown_players == total_players:
                print('✅ PASS: All players showing in performance table')
            else:
                print(f'❌ FAIL: Missing {total_players - shown_players} players')
                all_tests_passed = False
                
                # Show which players are missing
                shown_player_ids = [stats['player']['ID'] for stats in performance_stats]
                missing_players = all_players[~all_players['ID'].isin(shown_player_ids)]
                
                print('Missing players:')
                for _, missing_player in missing_players.iterrows():
                    print(f'  - #{missing_player["JerseyNumber"]} ({missing_player["ID"]}, {missing_player["Position"]})')
            
            # Test position filtering
            positions = ['F', 'D', 'G']
            for position in positions:
                position_players = all_players[all_players['Position'] == position]
                expected_count = len(position_players)
                
                if expected_count > 0:
                    position_stats = data_service.get_game_player_stats(game_id, position, team_id)
                    actual_count = len(position_stats)
                    
                    if actual_count == expected_count:
                        print(f'✅ Position {position}: {actual_count}/{expected_count} players showing')
                    else:
                        print(f'❌ Position {position}: {actual_count}/{expected_count} players showing')
                        all_tests_passed = False
            
            # Test game summary (related functionality)
            game_summary = data_service.get_game_summary(game_id, team_id)
            if game_summary:
                print('✅ Game summary loads correctly')
            else:
                print('❌ Game summary failed to load')
                all_tests_passed = False
                
        except Exception as e:
            print(f'❌ ERROR: {str(e)}')
            all_tests_passed = False
    
    print(f'\n=== VERIFICATION SUMMARY ===')
    if all_tests_passed:
        print('✅ SUCCESS: All player performance table tests passed!')
        print('The player performance table is working correctly.')
        print('All players are showing up in the game stats screen.')
    else:
        print('❌ FAILURE: Some tests failed.')
        print('There may still be issues with the player performance table.')
    
    return all_tests_passed

if __name__ == "__main__":
    success = verify_player_performance_table()
    sys.exit(0 if success else 1)
