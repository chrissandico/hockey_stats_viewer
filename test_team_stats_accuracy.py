#!/usr/bin/env python3
"""
Comprehensive test script to diagnose and fix team stats accuracy issues.
This script will identify problems with team identifier mapping and ensure
accurate stats for all teams, including newly added ones.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService
from services.auth_service import AuthService
import pandas as pd
import importlib

# Force reload of modules to avoid caching issues
print("=== Forcing module reloads to avoid caching ===")
if 'hockey_stats_webapp.services.data_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.data_service'])
if 'hockey_stats_webapp.services.sheets_service' in sys.modules:
    importlib.reload(sys.modules['hockey_stats_webapp.services.sheets_service'])

def test_team_identifier_mapping():
    """Test the team identifier mapping for all teams."""
    print("\n=== Testing Team Identifier Mapping ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Get all teams
    teams = sheets_service.get_teams()
    events = sheets_service.get_events()
    
    print(f"Found {len(teams)} teams in Teams sheet")
    print(f"Found {len(events)} events in Events sheet")
    
    # Get unique team identifiers in events
    unique_event_teams = events['Team'].unique() if not events.empty and 'Team' in events.columns else []
    print(f"Unique team identifiers in Events sheet: {unique_event_teams}")
    
    mapping_results = {}
    
    for _, team in teams.iterrows():
        team_id = team['TeamID']
        team_name = team['TeamName']
        
        print(f"\n--- Testing team: {team_name} (ID: {team_id}) ---")
        
        # Test the mapping function
        mapped_identifier = data_service._get_team_identifier_for_events(team_id)
        print(f"Mapped identifier: '{mapped_identifier}'")
        
        # Check if mapped identifier exists in events
        events_for_team = events[events['Team'] == mapped_identifier] if not events.empty else pd.DataFrame()
        event_count = len(events_for_team)
        print(f"Events found with this identifier: {event_count}")
        
        # Store results
        mapping_results[team_id] = {
            'team_name': team_name,
            'mapped_identifier': mapped_identifier,
            'event_count': event_count,
            'mapping_successful': event_count > 0
        }
        
        if event_count > 0:
            print(f"✅ Mapping successful - found {event_count} events")
        else:
            print(f"❌ Mapping failed - no events found")
    
    return mapping_results

def test_stats_calculation_accuracy():
    """Test stats calculation accuracy for all teams."""
    print("\n=== Testing Stats Calculation Accuracy ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service, force_refresh=True)
    
    # Get all teams
    teams = sheets_service.get_teams()
    
    stats_results = {}
    
    for _, team in teams.iterrows():
        team_id = team['TeamID']
        team_name = team['TeamName']
        
        print(f"\n--- Testing stats for team: {team_name} (ID: {team_id}) ---")
        
        try:
            # Test team stats
            team_stats = data_service.calculate_team_stats(team_id)
            print(f"Team stats: GP={team_stats['games_played']}, W={team_stats['wins']}, L={team_stats['losses']}")
            print(f"Goals: For={team_stats['goals_for']}, Against={team_stats['goals_against']}")
            
            # Test player stats
            players = data_service.get_players(team_id)
            print(f"Players on team: {len(players)}")
            
            if not players.empty:
                # Test first player's stats
                first_player = players.iloc[0]
                player_stats = data_service.calculate_player_stats(first_player['ID'], team_id)
                
                if player_stats:
                    print(f"Sample player stats (#{first_player['JerseyNumber']}): "
                          f"G={player_stats['goals']}, A={player_stats['assists']}, "
                          f"P={player_stats['points']}, +/-={player_stats['plus_minus']}")
                else:
                    print("❌ Failed to calculate player stats")
            
            # Test games
            games = data_service.get_games(team_id)
            print(f"Games for team: {len(games)}")
            
            stats_results[team_id] = {
                'team_name': team_name,
                'team_stats_calculated': team_stats is not None,
                'games_count': len(games),
                'players_count': len(players),
                'stats_accurate': team_stats['games_played'] == len(games)
            }
            
            if team_stats['games_played'] == len(games):
                print(f"✅ Stats appear accurate")
            else:
                print(f"❌ Stats mismatch: calculated GP={team_stats['games_played']}, actual games={len(games)}")
                
        except Exception as e:
            print(f"❌ Error calculating stats: {str(e)}")
            stats_results[team_id] = {
                'team_name': team_name,
                'team_stats_calculated': False,
                'error': str(e)
            }
    
    return stats_results

def test_authentication_integration():
    """Test that authentication works with all teams."""
    print("\n=== Testing Authentication Integration ===")
    
    # Initialize services
    sheets_service = SheetsService()
    auth_service = AuthService(sheets_service)
    
    # Get all teams
    teams = sheets_service.get_teams()
    
    auth_results = {}
    
    for _, team in teams.iterrows():
        team_id = team['TeamID']
        team_name = team['TeamName']
        password = team['Password']
        
        print(f"\n--- Testing authentication for: {team_name} ---")
        
        try:
            # Test authentication
            auth_result = auth_service.verify_password(password)
            
            if auth_result:
                print(f"✅ Authentication successful")
                print(f"   Authenticated team: {auth_result['team_name']} (ID: {auth_result['team_id']})")
                
                auth_results[team_id] = {
                    'team_name': team_name,
                    'password': password,
                    'auth_successful': True,
                    'auth_team_id': auth_result['team_id']
                }
            else:
                print(f"❌ Authentication failed")
                auth_results[team_id] = {
                    'team_name': team_name,
                    'password': password,
                    'auth_successful': False
                }
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            auth_results[team_id] = {
                'team_name': team_name,
                'password': password,
                'auth_successful': False,
                'error': str(e)
            }
    
    return auth_results

def generate_diagnostic_report(mapping_results, stats_results, auth_results):
    """Generate a comprehensive diagnostic report."""
    print("\n" + "="*60)
    print("COMPREHENSIVE DIAGNOSTIC REPORT")
    print("="*60)
    
    # Summary statistics
    total_teams = len(mapping_results)
    successful_mappings = sum(1 for r in mapping_results.values() if r['mapping_successful'])
    successful_stats = sum(1 for r in stats_results.values() if r.get('team_stats_calculated', False))
    successful_auth = sum(1 for r in auth_results.values() if r['auth_successful'])
    
    print(f"\nSUMMARY:")
    print(f"Total teams: {total_teams}")
    print(f"Successful team identifier mappings: {successful_mappings}/{total_teams}")
    print(f"Successful stats calculations: {successful_stats}/{total_teams}")
    print(f"Successful authentications: {successful_auth}/{total_teams}")
    
    # Detailed results
    print(f"\nDETAILED RESULTS:")
    for team_id in mapping_results.keys():
        team_name = mapping_results[team_id]['team_name']
        mapping_ok = mapping_results[team_id]['mapping_successful']
        stats_ok = stats_results.get(team_id, {}).get('team_stats_calculated', False)
        auth_ok = auth_results.get(team_id, {}).get('auth_successful', False)
        
        status = "✅ ALL OK" if (mapping_ok and stats_ok and auth_ok) else "❌ ISSUES"
        
        print(f"\n{team_name} (ID: {team_id}): {status}")
        print(f"  - Team identifier mapping: {'✅' if mapping_ok else '❌'}")
        print(f"  - Stats calculation: {'✅' if stats_ok else '❌'}")
        print(f"  - Authentication: {'✅' if auth_ok else '❌'}")
        
        if not mapping_ok:
            mapped_id = mapping_results[team_id]['mapped_identifier']
            event_count = mapping_results[team_id]['event_count']
            print(f"    Issue: Mapped to '{mapped_id}' but found {event_count} events")
        
        if not stats_ok and team_id in stats_results:
            if 'error' in stats_results[team_id]:
                print(f"    Issue: {stats_results[team_id]['error']}")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    
    if successful_mappings < total_teams:
        print("- Fix team identifier mapping issues for teams with no events found")
        print("- Ensure Events sheet uses consistent team identifiers")
    
    if successful_stats < total_teams:
        print("- Debug stats calculation errors")
        print("- Verify data consistency across sheets")
    
    if successful_auth < total_teams:
        print("- Check for duplicate or invalid passwords in Teams sheet")
    
    if successful_mappings == total_teams and successful_stats == total_teams and successful_auth == total_teams:
        print("🎉 All teams are working correctly!")
        print("- Team identifier mapping is working")
        print("- Stats calculations are accurate")
        print("- Authentication is functional")
        print("- New teams should work automatically when properly added to sheets")

def main():
    """Main diagnostic function."""
    print("=== HOCKEY STATS WEBAPP - TEAM STATS ACCURACY DIAGNOSTIC ===")
    print("This script will test team identifier mapping, stats calculation, and authentication")
    print("for all teams to ensure accuracy and identify any issues.")
    
    try:
        # Run all tests
        mapping_results = test_team_identifier_mapping()
        stats_results = test_stats_calculation_accuracy()
        auth_results = test_authentication_integration()
        
        # Generate comprehensive report
        generate_diagnostic_report(mapping_results, stats_results, auth_results)
        
        print(f"\n🔍 Diagnostic completed successfully!")
        print(f"   Review the report above to identify any issues that need fixing.")
        
    except Exception as e:
        print(f"\n💥 Diagnostic failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
