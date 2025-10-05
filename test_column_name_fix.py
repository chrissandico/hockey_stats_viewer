#!/usr/bin/env python3

"""
Test script to verify the column name compatibility fixes work with the actual data structure.
This script tests the login with cwaxersu12aa and verifies all screens work without crashes.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.auth_service import AuthService
from services.data_service import DataService

def test_column_name_fixes():
    """Test that the column name fixes work with the actual data structure."""
    
    print("=== TESTING COLUMN NAME COMPATIBILITY FIXES ===")
    
    try:
        # Initialize services
        print("\n1. Initializing services...")
        sheets_service = SheetsService()
        auth_service = AuthService(sheets_service)
        data_service = DataService(sheets_service, force_refresh=True)
        
        print("✅ Services initialized successfully")
        
        # Test authentication with cwaxersu12aa
        print("\n2. Testing authentication with cwaxersu12aa...")
        team_info = auth_service.verify_password('cwaxersu12aa')
        
        if team_info:
            print(f"✅ Authentication successful!")
            print(f"   Team ID: {team_info['team_id']}")
            print(f"   Team Name: {team_info['team_name']}")
            print(f"   Is Coach: {team_info.get('is_coach', False)}")
            
            team_id = team_info['team_id']
        else:
            print("❌ Authentication failed!")
            return False
        
        # Test players data structure
        print("\n3. Testing players data structure...")
        players = data_service.get_players(team_id)
        print(f"✅ Retrieved {len(players)} players for team {team_id}")
        print(f"   Player columns: {players.columns.tolist()}")
        
        if not players.empty:
            # Test get_player_by_id with the new column detection
            first_player_id = None
            if 'Unnamed: 0' in players.columns:
                first_player_id = players.iloc[0]['Unnamed: 0']
                print(f"   Using 'Unnamed: 0' column, first player ID: {first_player_id}")
            elif 'ID' in players.columns:
                first_player_id = players.iloc[0]['ID']
                print(f"   Using 'ID' column, first player ID: {first_player_id}")
            
            if first_player_id:
                player = data_service.get_player_by_id(first_player_id)
                if player is not None:
                    print(f"✅ get_player_by_id works! Player: #{player['JerseyNumber']} ({player['Position']})")
                else:
                    print("❌ get_player_by_id returned None")
                    return False
        
        # Test games data
        print("\n4. Testing games data...")
        games = data_service.get_games(team_id)
        print(f"✅ Retrieved {len(games)} games for team {team_id}")
        
        if not games.empty:
            print(f"   Sample game: {games.iloc[0]['ID']} vs {games.iloc[0]['Opponent']}")
        
        # Test game player stats (the method that was crashing)
        print("\n5. Testing get_game_player_stats (the method that was crashing)...")
        if not games.empty:
            test_game_id = games.iloc[0]['ID']
            try:
                player_stats = data_service.get_game_player_stats(test_game_id, team_id=team_id)
                print(f"✅ get_game_player_stats works! Found stats for {len(player_stats)} players in game {test_game_id}")
                
                if player_stats:
                    sample_stat = player_stats[0]
                    player_info = sample_stat['player']
                    print(f"   Sample player stat: #{player_info['JerseyNumber']} - {sample_stat['points']} points")
                
            except Exception as e:
                print(f"❌ get_game_player_stats failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Test player stats calculation
        print("\n6. Testing player stats calculation...")
        if not players.empty and first_player_id:
            try:
                stats = data_service.calculate_player_stats(first_player_id, team_id)
                if stats:
                    print(f"✅ Player stats calculation works!")
                    print(f"   Player: #{stats['player']['JerseyNumber']} ({stats['player']['Position']})")
                    print(f"   Games Played: {stats['games_played']}")
                    print(f"   Goals: {stats['goals']}")
                    print(f"   Assists: {stats['assists']}")
                    print(f"   Points: {stats['points']}")
                else:
                    print("❌ Player stats calculation returned None")
                    return False
            except Exception as e:
                print(f"❌ Player stats calculation failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Test team leaderboard
        print("\n7. Testing team leaderboard...")
        try:
            leaderboard = data_service.get_team_leaderboard('points', team_id=team_id, limit=5)
            print(f"✅ Team leaderboard works! Found {len(leaderboard)} players")
            
            if leaderboard:
                for i, player_stat in enumerate(leaderboard[:3]):
                    player_info = player_stat['player']
                    print(f"   {i+1}. #{player_info['JerseyNumber']} - {player_stat['points']} points")
        except Exception as e:
            print(f"❌ Team leaderboard failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test team identifier mapping
        print("\n8. Testing team identifier mapping...")
        try:
            team_identifier = data_service._get_team_identifier_for_events(team_id)
            print(f"✅ Team identifier mapping works!")
            print(f"   Team ID '{team_id}' maps to event team '{team_identifier}'")
        except Exception as e:
            print(f"❌ Team identifier mapping failed: {e}")
            return False
        
        print("\n=== ALL TESTS PASSED! ===")
        print("✅ Column name compatibility fixes are working correctly")
        print("✅ Authentication with cwaxersu12aa works")
        print("✅ All data service methods work without crashes")
        print("✅ The app should now work properly on all screens")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_scenarios():
    """Test specific scenarios that were failing before."""
    
    print("\n=== TESTING SPECIFIC FAILURE SCENARIOS ===")
    
    try:
        # Initialize services
        sheets_service = SheetsService()
        data_service = DataService(sheets_service, force_refresh=True)
        
        # Test the exact scenario from the error logs
        print("\n1. Testing the exact scenario that was failing...")
        print("   Simulating: get_game_player_stats with team 'your_team'")
        
        # Get games for your_team
        games = data_service.get_games('your_team')
        if not games.empty:
            test_game_id = games.iloc[0]['ID']
            print(f"   Testing with game ID: {test_game_id}")
            
            # This was the exact call that was failing
            player_stats = data_service.get_game_player_stats(test_game_id, team_id='your_team')
            print(f"✅ SUCCESS! No KeyError crash. Found {len(player_stats)} player stats")
        else:
            print("   No games found for 'your_team'")
        
        print("\n2. Testing column detection logic...")
        players = data_service.get_players('your_team')
        print(f"   Players columns: {players.columns.tolist()}")
        
        if 'Unnamed: 0' in players.columns:
            print("✅ 'Unnamed: 0' column detected correctly")
        elif 'ID' in players.columns:
            print("✅ 'ID' column detected correctly")
        else:
            print("❌ No valid ID column found")
            return False
        
        print("\n✅ All specific failure scenarios now work!")
        return True
        
    except Exception as e:
        print(f"\n❌ Specific scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing column name compatibility fixes...")
    
    # Test the fixes
    success1 = test_column_name_fixes()
    success2 = test_specific_scenarios()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("The column name compatibility fixes are working correctly.")
        print("The app should now work properly with the cwaxersu12aa login.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("There may still be issues that need to be addressed.")
        sys.exit(1)
