#!/usr/bin/env python3
"""
Test script to verify sortable columns functionality for team F/D leaderboards.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

from services.data_service import DataService
from services.sheets_service import SheetsService
from services.auth_service import AuthService
from layouts.team_layout import create_team_layout
import config
from flask import Flask
import dash
from dash import html, dash_table

def test_team_sortable_leaderboards():
    """Test that team leaderboards use sortable DataTables."""
    print("Testing team sortable leaderboards...")
    
    # Initialize services
    sheets_service = SheetsService()
    auth_service = AuthService(sheets_service)
    data_service = DataService(sheets_service)
    
    # Create Flask app and Dash app for testing
    flask_app = Flask(__name__)
    flask_app.secret_key = 'test_key'
    dash_app = dash.Dash(__name__, server=flask_app)
    
    # Test with authenticated team context
    with flask_app.test_request_context():
        # Simulate authenticated session
        from flask import session
        session['authenticated'] = True
        session['team_id'] = 'TESTTEAM'
        session['is_coach'] = True
        
        print(f"Testing with team_id: {session['team_id']}")
        print(f"Testing with coach status: {session['is_coach']}")
        
        # Create team layout
        layout = create_team_layout(data_service)
        
        # Verify layout structure
        print("\n=== LAYOUT STRUCTURE VERIFICATION ===")
        
        # Check if layout is a Div
        assert isinstance(layout, html.Div), "Layout should be an html.Div"
        print("✓ Layout is html.Div")
        
        # Find leaderboards loading component
        leaderboards_loading = None
        for child in layout.children:
            if hasattr(child, 'id') and child.id == 'team-leaderboards-loading':
                leaderboards_loading = child
                break
        
        assert leaderboards_loading is not None, "Should find team-leaderboards-loading component"
        print("✓ Found team-leaderboards-loading component")
        
        # Get the leaderboards content
        leaderboards_content = leaderboards_loading.children[0]  # First row
        forwards_col = leaderboards_content.children[0]  # First column (Forwards)
        defense_col = leaderboards_content.children[1]   # Second column (Defense)
        
        # Check Forwards leaderboard
        forwards_card = forwards_col.children[0]
        forwards_body = forwards_card.children[1]  # CardBody
        forwards_table = forwards_body.children[0]
        
        print(f"\n=== FORWARDS LEADERBOARD VERIFICATION ===")
        print(f"Forwards table type: {type(forwards_table)}")
        
        # Verify it's a DataTable, not HTML Table
        assert isinstance(forwards_table, dash_table.DataTable), "Forwards leaderboard should be a DataTable"
        print("✓ Forwards leaderboard is a DataTable")
        
        # Check sorting configuration
        assert forwards_table.sort_action == 'native', "Should have native sorting enabled"
        print("✓ Forwards table has native sorting enabled")
        
        assert forwards_table.sort_mode == 'single', "Should have single column sorting"
        print("✓ Forwards table has single column sorting")
        
        # Check columns
        expected_columns = ['Player', 'Goals', 'Assists', 'Points', 'PlusMinus']
        actual_columns = [col['id'] for col in forwards_table.columns]
        print(f"Forwards columns: {actual_columns}")
        
        # Should have at least Player, Goals, Assists, Points
        assert 'Player' in actual_columns, "Should have Player column"
        assert 'Goals' in actual_columns, "Should have Goals column"
        assert 'Assists' in actual_columns, "Should have Assists column"
        assert 'Points' in actual_columns, "Should have Points column"
        print("✓ Forwards table has required columns")
        
        # Check Defense leaderboard
        defense_card = defense_col.children[0]
        defense_body = defense_card.children[1]  # CardBody
        defense_table = defense_body.children[0]
        
        print(f"\n=== DEFENSE LEADERBOARD VERIFICATION ===")
        print(f"Defense table type: {type(defense_table)}")
        
        # Verify it's a DataTable, not HTML Table
        assert isinstance(defense_table, dash_table.DataTable), "Defense leaderboard should be a DataTable"
        print("✓ Defense leaderboard is a DataTable")
        
        # Check sorting configuration
        assert defense_table.sort_action == 'native', "Should have native sorting enabled"
        print("✓ Defense table has native sorting enabled")
        
        assert defense_table.sort_mode == 'single', "Should have single column sorting"
        print("✓ Defense table has single column sorting")
        
        # Check columns
        actual_columns = [col['id'] for col in defense_table.columns]
        print(f"Defense columns: {actual_columns}")
        
        # Should have at least Player, Goals, Assists, Points
        assert 'Player' in actual_columns, "Should have Player column"
        assert 'Goals' in actual_columns, "Should have Goals column"
        assert 'Assists' in actual_columns, "Should have Assists column"
        assert 'Points' in actual_columns, "Should have Points column"
        print("✓ Defense table has required columns")
        
        # Test data structure
        print(f"\n=== DATA STRUCTURE VERIFICATION ===")
        
        if forwards_table.data:
            sample_row = forwards_table.data[0]
            print(f"Sample forwards row: {sample_row}")
            
            # Check required fields
            assert 'Player' in sample_row, "Should have Player field"
            assert 'Goals' in sample_row, "Should have Goals field"
            assert 'Assists' in sample_row, "Should have Assists field"
            assert 'Points' in sample_row, "Should have Points field"
            print("✓ Forwards data has required fields")
            
            # Check data types
            assert isinstance(sample_row['Goals'], int), "Goals should be integer"
            assert isinstance(sample_row['Assists'], int), "Assists should be integer"
            assert isinstance(sample_row['Points'], int), "Points should be integer"
            print("✓ Forwards data has correct types")
        
        if defense_table.data:
            sample_row = defense_table.data[0]
            print(f"Sample defense row: {sample_row}")
            
            # Check required fields
            assert 'Player' in sample_row, "Should have Player field"
            assert 'Goals' in sample_row, "Should have Goals field"
            assert 'Assists' in sample_row, "Should have Assists field"
            assert 'Points' in sample_row, "Should have Points field"
            print("✓ Defense data has required fields")
            
            # Check data types
            assert isinstance(sample_row['Goals'], int), "Goals should be integer"
            assert isinstance(sample_row['Assists'], int), "Assists should be integer"
            assert isinstance(sample_row['Points'], int), "Points should be integer"
            print("✓ Defense data has correct types")
        
        print(f"\n=== SORTING FUNCTIONALITY TEST ===")
        
        # Test that columns are marked as sortable
        for col in forwards_table.columns:
            if col['id'] in ['Goals', 'Assists', 'Points', 'PlusMinus']:
                assert col['type'] == 'numeric', f"Column {col['id']} should be numeric type for proper sorting"
        print("✓ Numeric columns are properly typed for sorting")
        
        for col in defense_table.columns:
            if col['id'] in ['Goals', 'Assists', 'Points', 'PlusMinus']:
                assert col['type'] == 'numeric', f"Column {col['id']} should be numeric type for proper sorting"
        print("✓ Defense numeric columns are properly typed for sorting")
        
        print(f"\n=== COACH-SPECIFIC FEATURES TEST ===")
        
        # Test coach-specific columns (Plus/Minus)
        if session['is_coach']:
            forwards_columns = [col['id'] for col in forwards_table.columns]
            defense_columns = [col['id'] for col in defense_table.columns]
            
            # Check if Plus/Minus column exists for coaches
            if not config.is_coaches_only_stat('plus_minus'):
                print("Plus/Minus is not coach-only, should be visible to all users")
            else:
                assert 'PlusMinus' in forwards_columns, "Coaches should see Plus/Minus column in forwards"
                assert 'PlusMinus' in defense_columns, "Coaches should see Plus/Minus column in defense"
                print("✓ Coach can see Plus/Minus columns")
        
        print(f"\n=== SUCCESS: All tests passed! ===")
        print("✓ Forwards and Defense leaderboards now use sortable DataTables")
        print("✓ Users can sort by Goals, Assists, Points, and Plus/Minus (if coach)")
        print("✓ Sorting is configured with native Dash functionality")
        print("✓ Data types are properly set for numeric sorting")
        print("✓ Coach-specific visibility rules are maintained")
        
        return True

def test_non_coach_view():
    """Test that non-coach users see appropriate columns."""
    print("\n" + "="*50)
    print("TESTING NON-COACH VIEW")
    print("="*50)
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Create Flask app for testing
    flask_app = Flask(__name__)
    flask_app.secret_key = 'test_key'
    
    # Test with non-coach context
    with flask_app.test_request_context():
        # Simulate authenticated non-coach session
        from flask import session
        session['authenticated'] = True
        session['team_id'] = 'TESTTEAM'
        session['is_coach'] = False
        
        print(f"Testing with team_id: {session['team_id']}")
        print(f"Testing with coach status: {session['is_coach']}")
        
        # Create team layout
        layout = create_team_layout(data_service)
        
        # Find leaderboards
        leaderboards_loading = None
        for child in layout.children:
            if hasattr(child, 'id') and child.id == 'team-leaderboards-loading':
                leaderboards_loading = child
                break
        
        leaderboards_content = leaderboards_loading.children[0]
        forwards_col = leaderboards_content.children[0]
        defense_col = leaderboards_content.children[1]
        
        forwards_card = forwards_col.children[0]
        forwards_body = forwards_card.children[1]
        forwards_table = forwards_body.children[0]
        
        defense_card = defense_col.children[0]
        defense_body = defense_card.children[1]
        defense_table = defense_body.children[0]
        
        # Check column visibility for non-coaches
        forwards_columns = [col['id'] for col in forwards_table.columns]
        defense_columns = [col['id'] for col in defense_table.columns]
        
        print(f"Non-coach forwards columns: {forwards_columns}")
        print(f"Non-coach defense columns: {defense_columns}")
        
        # If plus_minus is coach-only, non-coaches shouldn't see it
        if config.is_coaches_only_stat('plus_minus'):
            assert 'PlusMinus' not in forwards_columns, "Non-coaches should not see Plus/Minus in forwards"
            assert 'PlusMinus' not in defense_columns, "Non-coaches should not see Plus/Minus in defense"
            print("✓ Non-coaches cannot see Plus/Minus columns (coach-only)")
        else:
            print("✓ Plus/Minus is visible to all users (not coach-only)")
        
        print("✓ Non-coach view test passed!")
        return True

if __name__ == "__main__":
    try:
        # Test coach view
        test_team_sortable_leaderboards()
        
        # Test non-coach view
        test_non_coach_view()
        
        print(f"\n" + "="*60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("="*60)
        print("Team leaderboards now have sortable columns!")
        print("Users can click column headers to sort by:")
        print("  • Goals (G)")
        print("  • Assists (A)")  
        print("  • Points (P)")
        print("  • Plus/Minus (+/-) - if coach or not coach-only")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
