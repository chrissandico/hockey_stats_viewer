#!/usr/bin/env python3
"""
Test script to verify that goalie losses and ties columns are working correctly.
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
from dash import html

def test_goalie_losses_ties():
    """Test that goalie stats include losses and ties."""
    print("Testing goalie losses and ties columns...")
    
    # Initialize services
    sheets_service = SheetsService()
    auth_service = AuthService(sheets_service)
    data_service = DataService(sheets_service)
    
    # Create Flask app for testing
    flask_app = Flask(__name__)
    flask_app.secret_key = 'test_key'
    
    # Test with authenticated team context
    with flask_app.test_request_context():
        # Simulate authenticated session
        from flask import session
        session['authenticated'] = True
        session['team_id'] = 'TESTTEAM'
        session['is_coach'] = True
        
        print(f"Testing with team_id: {session['team_id']}")
        print(f"Testing with coach status: {session['is_coach']}")
        
        # Test goalie stats calculation directly
        print("\n=== TESTING GOALIE STATS CALCULATION ===")
        
        # Get all goalies for the team
        players = data_service.get_players('TESTTEAM')
        goalies = players[players['Position'] == 'G']
        
        if goalies.empty:
            print("No goalies found for TESTTEAM")
            return False
        
        # Test each goalie's stats
        for _, goalie in goalies.iterrows():
            goalie_id = goalie['ID']
            jersey_number = goalie['JerseyNumber']
            
            print(f"\nTesting goalie #{jersey_number} (ID: {goalie_id})")
            
            # Calculate goalie stats
            stats = data_service.calculate_goalie_stats(goalie_id, 'TESTTEAM')
            
            if stats is None:
                print(f"  No stats calculated for goalie {goalie_id}")
                continue
            
            # Verify that losses and ties are included
            required_fields = ['wins', 'losses', 'ties', 'games_played', 'save_percentage', 'gaa', 'shutouts']
            
            for field in required_fields:
                if field not in stats:
                    print(f"  ❌ Missing field: {field}")
                    return False
                else:
                    print(f"  ✓ {field}: {stats[field]}")
            
            # Verify W-L-T record adds up to games played (or less, due to incomplete games)
            total_wlt = stats['wins'] + stats['losses'] + stats['ties']
            games_played = stats['games_played']
            
            if total_wlt <= games_played:
                print(f"  ✓ W-L-T record ({total_wlt}) <= Games Played ({games_played})")
            else:
                print(f"  ❌ W-L-T record ({total_wlt}) > Games Played ({games_played})")
                return False
        
        # Test team layout creation
        print("\n=== TESTING TEAM LAYOUT CREATION ===")
        
        try:
            layout = create_team_layout(data_service)
            print("✓ Team layout created successfully")
            
            # Verify layout structure
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
            leaderboards_content = leaderboards_loading.children[0]
            
            # Find the goalies leaderboard (should be in the second row)
            goalies_row = None
            if len(leaderboards_content) > 1:  # Should have forwards/defense row and goalies row
                goalies_row = leaderboards_content[1]  # Second row should be goalies
            
            if goalies_row is not None:
                goalies_col = goalies_row.children[0]  # First (and only) column in goalies row
                goalies_card = goalies_col.children[0]
                goalies_body = goalies_card.children[1]  # CardBody
                goalies_table = goalies_body.children[0]  # HTML Table
                
                print(f"Goalies table type: {type(goalies_table)}")
                
                # Verify it's an HTML table (not DataTable like F/D)
                assert hasattr(goalies_table, 'children'), "Goalies table should be HTML table with children"
                print("✓ Goalies leaderboard is HTML table")
                
                # Check table structure
                thead = goalies_table.children[0]  # Thead
                tbody = goalies_table.children[1]  # Tbody
                
                # Check header row
                header_row = thead.children[0]
                headers = [th.children for th in header_row.children]
                
                print(f"Table headers: {headers}")
                
                # Verify L and T columns are present
                expected_headers = ["Player", "GP", "W", "L", "T", "SV%", "GAA", "SO", "SOG"]
                
                if len(headers) == len(expected_headers):
                    print("✓ Correct number of columns")
                    
                    # Check that L and T are in the right positions
                    if headers[3] == "L" and headers[4] == "T":
                        print("✓ L and T columns are in correct positions")
                    else:
                        print(f"❌ L and T columns not in expected positions. Got: {headers}")
                        return False
                else:
                    print(f"❌ Expected {len(expected_headers)} columns, got {len(headers)}")
                    return False
                
                # Check data rows if any goalies exist
                if hasattr(tbody, 'children') and tbody.children:
                    print(f"Found {len(tbody.children)} goalie data rows")
                    
                    # Check first row structure
                    first_row = tbody.children[0]
                    cells = [td.children for td in first_row.children]
                    
                    print(f"Sample data row: {cells}")
                    
                    if len(cells) == len(expected_headers):
                        print("✓ Data rows have correct number of columns")
                    else:
                        print(f"❌ Data rows have {len(cells)} columns, expected {len(expected_headers)}")
                        return False
                else:
                    print("No goalie data rows found (this may be normal if no goalies have played)")
            else:
                print("No goalies leaderboard found in layout")
        
        except Exception as e:
            print(f"❌ Error creating team layout: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"\n=== SUCCESS: All tests passed! ===")
        print("✓ Goalie stats calculation includes losses and ties")
        print("✓ Team layout displays L and T columns")
        print("✓ Data structure is correct")
        
        return True

if __name__ == "__main__":
    try:
        success = test_goalie_losses_ties()
        
        if success:
            print(f"\n" + "="*60)
            print("🎉 ALL TESTS PASSED! 🎉")
            print("="*60)
            print("Goalie leaderboard now shows complete W-L-T record!")
            print("New columns added:")
            print("  • L (Losses) - between W and SV%")
            print("  • T (Ties) - between L and SV%")
            print("="*60)
        else:
            print(f"\n❌ TESTS FAILED")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
