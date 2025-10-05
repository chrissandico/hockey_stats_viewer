#!/usr/bin/env python3

"""
Debug script to investigate the 500 Internal Server Error when selecting players
in the web application. This will help identify what's causing the callback to fail.
"""

import sys
import os
import traceback

# Add the hockey_stats_webapp directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def debug_player_selection_error():
    """Debug the player selection callback that's causing 500 errors."""
    
    print("=== DEBUGGING PLAYER SELECTION 500 ERROR ===")
    
    try:
        # Import required modules
        from services.sheets_service import SheetsService
        from services.data_service import DataService
        
        print("1. Testing service initialization...")
        
        # Initialize services (this will fail without credentials, but that's expected)
        try:
            sheets_service = SheetsService()
            data_service = DataService(sheets_service)
            print("   ✓ Services initialized successfully")
        except Exception as e:
            print(f"   ⚠ Services failed to initialize (expected): {e}")
            print("   This is expected without credentials.json")
            return
        
        print("\n2. Testing player data retrieval...")
        
        # Test getting roster data
        try:
            roster_data = data_service.get_roster_data()
            print(f"   ✓ Roster data retrieved: {len(roster_data)} players")
            
            # Show first few players
            for i, (_, player) in enumerate(roster_data.head(3).iterrows()):
                print(f"   Player {i+1}: {player}")
                
        except Exception as e:
            print(f"   ✗ Failed to get roster data: {e}")
            traceback.print_exc()
            return
        
        print("\n3. Testing player ID extraction...")
        
        # Test the centralized column detection methods
        try:
            for i, (_, player) in enumerate(roster_data.head(3).iterrows()):
                player_id = data_service._get_player_id_from_series(player)
                print(f"   Player {i+1} ID: {player_id}")
                
                # Test getting individual player data
                player_data = data_service.get_player_by_id(player_id)
                print(f"   Player {i+1} data: {player_data}")
                
        except Exception as e:
            print(f"   ✗ Failed to extract player IDs: {e}")
            traceback.print_exc()
            return
        
        print("\n4. Testing specific player #7 (the one that caused 500 error)...")
        
        try:
            # Find player #7 in roster
            player_7_data = None
            for _, player in roster_data.iterrows():
                if str(player.get('Jersey', '')).strip() == '7':
                    player_7_data = player
                    break
            
            if player_7_data is not None:
                print(f"   Found player #7: {player_7_data}")
                
                # Test getting player ID
                player_7_id = data_service._get_player_id_from_series(player_7_data)
                print(f"   Player #7 ID: {player_7_id}")
                
                # Test getting full player data
                full_player_7_data = data_service.get_player_by_id(player_7_id)
                print(f"   Player #7 full data: {full_player_7_data}")
                
                # Test getting player stats (this might be where the error occurs)
                try:
                    player_stats = data_service.get_player_stats(player_7_id)
                    print(f"   Player #7 stats: {player_stats}")
                except Exception as stats_error:
                    print(f"   ✗ Failed to get player #7 stats: {stats_error}")
                    traceback.print_exc()
                
            else:
                print("   ⚠ Player #7 not found in roster")
                
        except Exception as e:
            print(f"   ✗ Failed to test player #7: {e}")
            traceback.print_exc()
        
        print("\n5. Testing column structure analysis...")
        
        try:
            # Analyze the column structure
            print(f"   Roster columns: {list(roster_data.columns)}")
            print(f"   Roster index: {roster_data.index}")
            
            # Check for the player ID column specifically
            id_column = data_service._get_player_id_column(roster_data)
            print(f"   Detected player ID column: '{id_column}'")
            
        except Exception as e:
            print(f"   ✗ Failed to analyze column structure: {e}")
            traceback.print_exc()
        
        print("\n=== DEBUG COMPLETE ===")
        
    except Exception as e:
        print(f"CRITICAL ERROR in debug script: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_player_selection_error()
