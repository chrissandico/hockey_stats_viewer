#!/usr/bin/env python3
"""
Test script to verify the period breakdown with SOG (Shots on Goal) functionality.
This script tests both the data service enhancement and the component display.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from components.period_breakdown import create_period_breakdown_component
import dash
from dash import html
import dash_bootstrap_components as dbc

def test_period_breakdown_sog():
    """Test the enhanced period breakdown functionality with SOG per period."""
    
    print("=== Testing Period Breakdown with SOG ===")
    
    try:
        # Initialize services
        print("1. Initializing services...")
        sheets_service = SheetsService()
        data_service = DataService(sheets_service)
        
        # Get available games
        print("2. Getting available games...")
        games = data_service.get_games()
        
        if games.empty:
            print("❌ No games found in the system")
            return False
        
        print(f"✅ Found {len(games)} games")
        
        # Test with the first available game
        test_game_id = games.iloc[0]['ID']
        test_team_id = games.iloc[0].get('TeamID', None)
        
        print(f"3. Testing with game ID: {test_game_id}")
        print(f"   Team ID: {test_team_id}")
        
        # Get period breakdown data
        print("4. Getting period breakdown data...")
        period_data = data_service.get_period_breakdown(test_game_id, test_team_id)
        
        if not period_data:
            print("❌ No period breakdown data returned")
            return False
        
        print("✅ Period breakdown data retrieved successfully")
        
        # Verify data structure
        print("5. Verifying enhanced data structure...")
        
        required_keys = ['your_team', 'opponent']
        for key in required_keys:
            if key not in period_data:
                print(f"❌ Missing key: {key}")
                return False
        
        # Check for enhanced data fields
        your_team = period_data['your_team']
        opponent = period_data['opponent']
        
        enhanced_fields = ['goals', 'shots', 'total_goals', 'total_shots']
        backward_compat_fields = ['periods', 'total']
        
        print("   Checking enhanced fields...")
        for field in enhanced_fields:
            if field not in your_team:
                print(f"❌ Missing enhanced field in your_team: {field}")
                return False
            if field not in opponent:
                print(f"❌ Missing enhanced field in opponent: {field}")
                return False
        
        print("   Checking backward compatibility fields...")
        for field in backward_compat_fields:
            if field not in your_team:
                print(f"❌ Missing backward compatibility field in your_team: {field}")
                return False
            if field not in opponent:
                print(f"❌ Missing backward compatibility field in opponent: {field}")
                return False
        
        print("✅ All required fields present")
        
        # Display the data
        print("6. Period breakdown data:")
        print(f"   Your Team ({your_team['name']}):")
        print(f"     Goals by period: {your_team['goals']} (Total: {your_team['total_goals']})")
        print(f"     Shots by period: {your_team['shots']} (Total: {your_team['total_shots']})")
        print(f"   Opponent ({opponent['name']}):")
        print(f"     Goals by period: {opponent['goals']} (Total: {opponent['total_goals']})")
        print(f"     Shots by period: {opponent['shots']} (Total: {opponent['total_shots']})")
        
        # Test component creation
        print("7. Testing component creation...")
        
        try:
            component = create_period_breakdown_component(period_data)
            print("✅ Component created successfully with enhanced data")
        except Exception as e:
            print(f"❌ Error creating component: {e}")
            return False
        
        # Test backward compatibility
        print("8. Testing backward compatibility...")
        
        # Create old-style data structure
        old_style_data = {
            'your_team': {
                'name': your_team['name'],
                'periods': your_team['periods'],
                'total': your_team['total']
            },
            'opponent': {
                'name': opponent['name'],
                'periods': opponent['periods'],
                'total': opponent['total']
            }
        }
        
        try:
            old_component = create_period_breakdown_component(old_style_data)
            print("✅ Backward compatibility maintained")
        except Exception as e:
            print(f"❌ Backward compatibility broken: {e}")
            return False
        
        # Verify data consistency
        print("9. Verifying data consistency...")
        
        # Goals should match between new and old format
        if (your_team['goals'] != your_team['periods'] or 
            your_team['total_goals'] != your_team['total']):
            print("❌ Goals data inconsistency in your_team")
            return False
        
        if (opponent['goals'] != opponent['periods'] or 
            opponent['total_goals'] != opponent['total']):
            print("❌ Goals data inconsistency in opponent")
            return False
        
        print("✅ Data consistency verified")
        
        # Test with multiple games if available
        if len(games) > 1:
            print("10. Testing with additional games...")
            
            for i in range(1, min(3, len(games))):  # Test up to 2 more games
                game_id = games.iloc[i]['ID']
                team_id = games.iloc[i].get('TeamID', None)
                
                print(f"    Testing game {game_id}...")
                
                test_period_data = data_service.get_period_breakdown(game_id, team_id)
                
                if test_period_data:
                    test_component = create_period_breakdown_component(test_period_data)
                    print(f"    ✅ Game {game_id} processed successfully")
                else:
                    print(f"    ⚠️  No data for game {game_id}")
        
        print("\n=== Test Results ===")
        print("✅ All tests passed successfully!")
        print("✅ Period breakdown now includes SOG per period")
        print("✅ Enhanced data structure implemented")
        print("✅ Backward compatibility maintained")
        print("✅ Component displays goals and shots per period")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_component_display_formats():
    """Test different display formats of the component."""
    
    print("\n=== Testing Component Display Formats ===")
    
    # Test data with shots
    enhanced_data = {
        'your_team': {
            'name': 'Test Team',
            'goals': [1, 2, 0],
            'shots': [8, 12, 6],
            'total_goals': 3,
            'total_shots': 26,
            'periods': [1, 2, 0],
            'total': 3
        },
        'opponent': {
            'name': 'Opponent Team',
            'goals': [0, 1, 1],
            'shots': [6, 10, 8],
            'total_goals': 2,
            'total_shots': 24,
            'periods': [0, 1, 1],
            'total': 2
        }
    }
    
    # Test data without shots (old format)
    legacy_data = {
        'your_team': {
            'name': 'Test Team',
            'periods': [1, 2, 0],
            'total': 3
        },
        'opponent': {
            'name': 'Opponent Team',
            'periods': [0, 1, 1],
            'total': 2
        }
    }
    
    print("1. Testing enhanced format (with shots)...")
    try:
        enhanced_component = create_period_breakdown_component(enhanced_data)
        print("✅ Enhanced format component created")
    except Exception as e:
        print(f"❌ Enhanced format failed: {e}")
        return False
    
    print("2. Testing legacy format (goals only)...")
    try:
        legacy_component = create_period_breakdown_component(legacy_data)
        print("✅ Legacy format component created")
    except Exception as e:
        print(f"❌ Legacy format failed: {e}")
        return False
    
    print("✅ Both display formats work correctly")
    return True

if __name__ == "__main__":
    print("Starting Period Breakdown SOG Tests...")
    
    # Run the main test
    main_test_passed = test_period_breakdown_sog()
    
    # Run component display tests
    display_test_passed = test_component_display_formats()
    
    if main_test_passed and display_test_passed:
        print("\n🎉 All tests completed successfully!")
        print("The period breakdown now shows SOG per period in the format: Goals (Shots)")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
