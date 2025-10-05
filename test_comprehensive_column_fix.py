#!/usr/bin/env python3

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
import traceback

def test_comprehensive_column_compatibility():
    """
    Test comprehensive column compatibility across all player data access methods.
    """
    print("=== COMPREHENSIVE COLUMN COMPATIBILITY TEST ===")
    
    try:
        # Initialize services
        print("1. Initializing services...")
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        
        # Get players data to examine column structure
        print("\n2. Examining players data structure...")
        players = sheets_service.get_players()
        print(f"Players columns: {players.columns.tolist()}")
        print(f"Players shape: {players.shape}")
        
        if players.empty:
            print("ERROR: No players data found!")
            return False
        
        # Check for ID column variations
        id_column = None
        if 'ID' in players.columns:
            id_column = 'ID'
            print(f"Found standard ID column: '{id_column}'")
        elif 'Unnamed: 0' in players.columns:
            id_column = 'Unnamed: 0'
            print(f"Found unnamed ID column: '{id_column}'")
        elif '' in players.columns:
            id_column = ''
            print(f"Found empty string ID column: '{id_column}'")
        else:
            print("ERROR: No ID column found in any expected format!")
            return False
        
        # Get sample player IDs
        sample_player_ids = players[id_column].head(3).tolist()
        print(f"Sample player IDs: {sample_player_ids}")
        
        # Test each method that accesses player data
        print("\n3. Testing player data access methods...")
        
        # Test get_player_by_id
        print("\n3.1 Testing get_player_by_id...")
        for player_id in sample_player_ids:
            try:
                player = data_service.get_player_by_id(player_id)
                if player is not None:
                    print(f"  ✓ get_player_by_id({player_id}) - SUCCESS")
                else:
                    print(f"  ✗ get_player_by_id({player_id}) - RETURNED None")
            except Exception as e:
                print(f"  ✗ get_player_by_id({player_id}) - ERROR: {str(e)}")
                traceback.print_exc()
        
        # Test get_team_leaderboard
        print("\n3.2 Testing get_team_leaderboard...")
        try:
            leaderboard = data_service.get_team_leaderboard(stat='points', limit=5)
            print(f"  ✓ get_team_leaderboard - SUCCESS ({len(leaderboard)} players)")
        except Exception as e:
            print(f"  ✗ get_team_leaderboard - ERROR: {str(e)}")
            traceback.print_exc()
        
        # Test calculate_player_stats
        print("\n3.3 Testing calculate_player_stats...")
        for player_id in sample_player_ids[:2]:  # Test first 2 players
            try:
                stats = data_service.calculate_player_stats(player_id)
                if stats is not None:
                    print(f"  ✓ calculate_player_stats({player_id}) - SUCCESS")
                else:
                    print(f"  ✗ calculate_player_stats({player_id}) - RETURNED None")
            except Exception as e:
                print(f"  ✗ calculate_player_stats({player_id}) - ERROR: {str(e)}")
                traceback.print_exc()
        
        # Test get_player_game_log
        print("\n3.4 Testing get_player_game_log...")
        for player_id in sample_player_ids[:2]:  # Test first 2 players
            try:
                game_log = data_service.get_player_game_log(player_id)
                print(f"  ✓ get_player_game_log({player_id}) - SUCCESS ({len(game_log)} games)")
            except Exception as e:
                print(f"  ✗ get_player_game_log({player_id}) - ERROR: {str(e)}")
                traceback.print_exc()
        
        # Test get_player_games
        print("\n3.5 Testing get_player_games...")
        for player_id in sample_player_ids[:2]:  # Test first 2 players
            try:
                games = data_service.get_player_games(player_id)
                print(f"  ✓ get_player_games({player_id}) - SUCCESS ({len(games)} games)")
            except Exception as e:
                print(f"  ✗ get_player_games({player_id}) - ERROR: {str(e)}")
                traceback.print_exc()
        
        # Test calculate_goalie_stats for goalies
        print("\n3.6 Testing calculate_goalie_stats for goalies...")
        goalies = players[players['Position'] == 'G']
        if not goalies.empty:
            goalie_ids = goalies[id_column].head(2).tolist()
            for goalie_id in goalie_ids:
                try:
                    stats = data_service.calculate_goalie_stats(goalie_id)
                    if stats is not None:
                        print(f"  ✓ calculate_goalie_stats({goalie_id}) - SUCCESS")
                    else:
                        print(f"  ✗ calculate_goalie_stats({goalie_id}) - RETURNED None")
                except Exception as e:
                    print(f"  ✗ calculate_goalie_stats({goalie_id}) - ERROR: {str(e)}")
                    traceback.print_exc()
        else:
            print("  No goalies found to test")
        
        print("\n4. Testing layout callback simulation...")
        # Simulate the player layout callback logic
        try:
            # Get first player's jersey number
            first_player = players.iloc[0]
            jersey_number = first_player['JerseyNumber']
            
            # Simulate the callback logic from player_layout.py
            team_players = data_service.get_players()  # No team filter for simplicity
            matching_players = team_players[team_players['JerseyNumber'] == jersey_number]
            
            if matching_players.empty:
                print(f"  ✗ Player with jersey {jersey_number} not found!")
            else:
                player = matching_players.iloc[0]
                
                # Test the column detection logic from the callback
                player_id = None
                if 'ID' in player.index:
                    player_id = player['ID']
                elif 'Unnamed: 0' in player.index:
                    player_id = player['Unnamed: 0']
                elif '' in player.index:
                    player_id = player['']
                else:
                    print(f"  ✗ No player ID column found in callback simulation. Available: {list(player.index)}")
                    return False
                
                print(f"  ✓ Callback simulation - Found player ID: {player_id}")
                
                # Test stats calculation in callback context
                if player['Position'] == 'G':
                    stats = data_service.calculate_goalie_stats(player_id)
                else:
                    stats = data_service.calculate_player_stats(player_id)
                
                if stats is not None:
                    print(f"  ✓ Callback stats calculation - SUCCESS")
                else:
                    print(f"  ✗ Callback stats calculation - RETURNED None")
                
        except Exception as e:
            print(f"  ✗ Callback simulation - ERROR: {str(e)}")
            traceback.print_exc()
        
        print("\n=== TEST COMPLETE ===")
        return True
        
    except Exception as e:
        print(f"CRITICAL ERROR in test setup: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comprehensive_column_compatibility()
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
        sys.exit(1)
