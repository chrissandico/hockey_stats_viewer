#!/usr/bin/env python3

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.auth_service import AuthService
from services.data_service import DataService
from layouts.team_layout import create_team_layout, register_team_callbacks
from components.game_type_filter import register_game_type_filter_callbacks
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask import Flask

def test_team_web_interface():
    """
    Test the team web interface to see if the callback system is working properly.
    """
    print("=== Testing Team Web Interface Callbacks ===")
    
    # Create a minimal Dash app to test the callbacks
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    server = app.server
    server.secret_key = 'test-secret-key'
    
    # Initialize services
    sheets_service = SheetsService()
    auth_service = AuthService(sheets_service)
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Test authentication
    password = "waxersu12aa"
    team_info = auth_service.verify_password(password)
    if not team_info:
        print("ERROR: Authentication failed!")
        return False
    
    print(f"✅ Authentication successful for team: {team_info['team_name']}")
    team_id = team_info['team_id']
    
    # Simulate session context
    with server.app_context():
        from flask import session
        session['authenticated'] = True
        session['team_id'] = team_id
        session['team_name'] = team_info['team_name']
        session['is_coach'] = team_info.get('is_coach', False)
        
        print(f"\n1. Testing initial team layout creation")
        
        # Create the team layout
        team_context = {
            'team_id': team_id,
            'team_name': team_info['team_name']
        }
        
        layout = create_team_layout(data_service, team_context)
        print(f"   ✅ Team layout created successfully")
        
        # Register callbacks
        try:
            from layouts.team_layout import register_team_callbacks
            register_team_callbacks(app, data_service)
            print(f"   ✅ Team callbacks registered successfully")
        except Exception as e:
            print(f"   ❌ Error registering team callbacks: {e}")
            return False
        
        try:
            register_game_type_filter_callbacks(app, data_service)
            print(f"   ✅ Game type filter callbacks registered successfully")
        except Exception as e:
            print(f"   ❌ Error registering game type filter callbacks: {e}")
            return False
        
        print(f"\n2. Testing callback simulation")
        
        # Test the callback function directly
        from layouts.team_layout import register_team_callbacks
        
        # Get the callback function
        callback_func = None
        for callback in app.callback_map.values():
            if hasattr(callback, 'function') and 'update_team_stats_by_game_type' in str(callback.function):
                callback_func = callback.function
                break
        
        if callback_func:
            print(f"   ✅ Found team stats callback function")
            
            # Test with "all" games
            print(f"\n   Testing 'all' games filter:")
            try:
                result_all = callback_func("all")
                print(f"     ✅ 'All games' callback executed successfully")
                print(f"     Result type: {type(result_all)}")
                if isinstance(result_all, tuple) and len(result_all) >= 3:
                    print(f"     Returns 3 components as expected")
                else:
                    print(f"     ❌ Unexpected result structure: {result_all}")
            except Exception as e:
                print(f"     ❌ Error in 'all games' callback: {e}")
                import traceback
                traceback.print_exc()
            
            # Test with "R" (Regular season) games
            print(f"\n   Testing 'R' (Regular season) filter:")
            try:
                result_regular = callback_func("R")
                print(f"     ✅ 'Regular season' callback executed successfully")
                print(f"     Result type: {type(result_regular)}")
                if isinstance(result_regular, tuple) and len(result_regular) >= 3:
                    print(f"     Returns 3 components as expected")
                else:
                    print(f"     ❌ Unexpected result structure: {result_regular}")
            except Exception as e:
                print(f"     ❌ Error in 'Regular season' callback: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ❌ Could not find team stats callback function")
            print(f"   Available callbacks: {list(app.callback_map.keys())}")
        
        print(f"\n3. Testing data service session methods")
        
        # Test session game type methods
        try:
            # Test setting game type in session
            data_service._set_game_type_in_session('R')
            current_type = data_service._get_game_type_from_session()
            print(f"   ✅ Session game type set to 'R', retrieved: {current_type}")
            
            # Test setting to None (all games)
            data_service._set_game_type_in_session(None)
            current_type = data_service._get_game_type_from_session()
            print(f"   ✅ Session game type set to None, retrieved: {current_type}")
            
        except Exception as e:
            print(f"   ❌ Error testing session methods: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n4. Testing direct leaderboard calls with different game types")
        
        # Test forwards leaderboard
        try:
            forwards_all = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type=None)
            forwards_regular = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type='R')
            
            print(f"   Forwards - All games: {len(forwards_all)} players")
            if forwards_all:
                print(f"     Top player: #{forwards_all[0]['player']['JerseyNumber']} - {forwards_all[0]['games_played']} GP")
            
            print(f"   Forwards - Regular season: {len(forwards_regular)} players")
            if forwards_regular:
                print(f"     Top player: #{forwards_regular[0]['player']['JerseyNumber']} - {forwards_regular[0]['games_played']} GP")
            
            if forwards_all and forwards_regular:
                if forwards_all[0]['games_played'] != forwards_regular[0]['games_played']:
                    print(f"   ✅ Forwards filtering working: {forwards_all[0]['games_played']} vs {forwards_regular[0]['games_played']} GP")
                else:
                    print(f"   ❌ Forwards filtering NOT working: same GP ({forwards_all[0]['games_played']})")
            
        except Exception as e:
            print(f"   ❌ Error testing forwards leaderboard: {e}")
            import traceback
            traceback.print_exc()
    
    return True

if __name__ == "__main__":
    success = test_team_web_interface()
    if success:
        print("\n✅ Web interface tests completed!")
    else:
        print("\n❌ Web interface tests failed!")
