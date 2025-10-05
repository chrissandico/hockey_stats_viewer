#!/usr/bin/env python3

"""
Debug script to identify the correct column structure in the Players sheet
and fix the KeyError: 'ID' issue in app.py
"""

import sys
import os

# Add the hockey_stats_webapp directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

from services.sheets_service import SheetsService

def debug_player_columns():
    """Debug the player data structure to identify correct column names."""
    
    print("=== DEBUGGING PLAYER COLUMN STRUCTURE ===")
    
    try:
        # Initialize sheets service
        sheets_service = SheetsService()
        
        # Get players data
        players = sheets_service.get_players()
        
        print(f"Players DataFrame shape: {players.shape}")
        print(f"Players columns: {players.columns.tolist()}")
        
        if not players.empty:
            print("\nFirst player record:")
            first_player = players.iloc[0]
            for col in players.columns:
                print(f"  {col}: {first_player[col]}")
            
            # Check for goalies
            if 'Position' in players.columns:
                goalies = players[players['Position'] == 'G']
                print(f"\nFound {len(goalies)} goalies")
                
                if not goalies.empty:
                    print("\nFirst goalie record:")
                    first_goalie = goalies.iloc[0]
                    for col in goalies.columns:
                        print(f"  {col}: {first_goalie[col]}")
                    
                    # Test different possible ID column names
                    possible_id_columns = ['ID', 'PlayerID', 'id', 'player_id', 'Id']
                    print(f"\nTesting possible ID column names: {possible_id_columns}")
                    
                    for col_name in possible_id_columns:
                        if col_name in goalies.columns:
                            try:
                                goalie_id = first_goalie[col_name]
                                print(f"  ✅ {col_name}: {goalie_id} (SUCCESS)")
                            except Exception as e:
                                print(f"  ❌ {col_name}: Error - {e}")
                        else:
                            print(f"  ❌ {col_name}: Column not found")
                else:
                    print("No goalies found in player data")
            else:
                print("No 'Position' column found in players data")
        else:
            print("Players DataFrame is empty")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_player_columns()
