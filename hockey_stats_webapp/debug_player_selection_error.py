#!/usr/bin/env python3

import sys
import os

from services.data_service import DataService
from services.auth_service import AuthService
from services.sheets_service import SheetsService
import traceback

def test_player_selection():
    """Test the specific player selection that's causing 500 errors"""
    
    print("=== Testing Player Selection Error ===")
    
    try:
        # Initialize services
        sheets_service = SheetsService()
        auth_service = AuthService(sheets_service)
        data_service = DataService(sheets_service)
        
        # Test authentication first
        print("\n1. Testing authentication...")
        team_info = auth_service.verify_password('cwaxersu12aa')
        if team_info:
            team_id = team_info['team_id']
            print(f"   Team ID: {team_id}")
        else:
            print("   Authentication failed!")
            return
        
        # Get all players to see the structure
        print("\n2. Getting all players...")
        players = data_service.get_players()
        print(f"   Total players: {len(players)}")
        print(f"   Columns: {list(players.columns)}")
        
        # Show first few players
        print("\n3. First few players:")
        for i in range(min(5, len(players))):
            row = players.iloc[i]
            print(f"   Row {i}: {dict(row)}")
        
        # Test getting player by ID (this is likely where the error occurs)
        print("\n4. Testing get_player_by_id...")
        
        # Try to get player_7 (which corresponds to #7 - D)
        try:
            player_7 = data_service.get_player_by_id('player_7')
            print(f"   Player 7 found: {player_7}")
        except Exception as e:
            print(f"   ERROR getting player_7: {e}")
            traceback.print_exc()
        
        # Test getting player stats
        print("\n5. Testing get_player_stats...")
        try:
            stats = data_service.get_player_stats('player_7', team_id)
            print(f"   Player 7 stats: {stats}")
        except Exception as e:
            print(f"   ERROR getting player_7 stats: {e}")
            traceback.print_exc()
        
        # Test getting player game log
        print("\n6. Testing get_player_game_log...")
        try:
            game_log = data_service.get_player_game_log('player_7', team_id)
            print(f"   Player 7 game log entries: {len(game_log) if game_log is not None else 'None'}")
        except Exception as e:
            print(f"   ERROR getting player_7 game log: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_player_selection()
