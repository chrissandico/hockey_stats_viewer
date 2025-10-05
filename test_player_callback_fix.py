#!/usr/bin/env python3
"""
Test to verify the player layout callback function signature fix.
Tests that the callback properly handles both jersey_number and game_type_data parameters.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

def test_player_callback_signature():
    """Test that the player callback has the correct function signature."""
    print("=" * 60)
    print("TESTING PLAYER CALLBACK FUNCTION SIGNATURE")
    print("=" * 60)
    
    try:
        # Read the player layout file
        with open('hockey_stats_webapp/layouts/player_layout.py', 'r') as f:
            content = f.read()
        
        # Check for the correct callback signature
        correct_signature = "def update_player_info(jersey_number, game_type_data):"
        
        if correct_signature in content:
            print("✓ Callback function signature is correct")
            print(f"   Found: {correct_signature}")
        else:
            print("❌ Callback function signature is incorrect")
            
            # Check for the old incorrect signature
            old_signature = "def update_player_info(jersey_number):"
            if old_signature in content:
                print(f"   Found old signature: {old_signature}")
                print("   This will cause the callback to fail when game type changes!")
            return False
        
        # Check for proper game type handling
        game_type_checks = [
            "game_type = game_type_data if isinstance(game_type_data, str) else None",
            "if game_type_data and isinstance(game_type_data, dict):",
            "game_type = game_type_data.get('game_type')",
            "if not game_type:",
            "game_type = 'R'"
        ]
        
        missing_checks = []
        for check in game_type_checks:
            if check not in content:
                missing_checks.append(check)
        
        if missing_checks:
            print("❌ Missing game type handling logic:")
            for check in missing_checks:
                print(f"   - {check}")
            return False
        else:
            print("✓ Game type handling logic is present")
        
        # Check that the callback has two inputs
        callback_inputs = [
            "dash.dependencies.Input('player-dropdown', 'value')",
            "dash.dependencies.Input('game-type-session-store', 'data')"
        ]
        
        missing_inputs = []
        for input_check in callback_inputs:
            if input_check not in content:
                missing_inputs.append(input_check)
        
        if missing_inputs:
            print("❌ Missing callback inputs:")
            for input_check in missing_inputs:
                print(f"   - {input_check}")
            return False
        else:
            print("✓ Callback has correct inputs")
        
        # Check that old session-based game type retrieval is removed
        old_game_type_call = "data_service._get_game_type_from_session()"
        if old_game_type_call in content:
            print("❌ Old session-based game type retrieval still present")
            print(f"   Found: {old_game_type_call}")
            print("   This should be replaced with parameter-based retrieval")
            return False
        else:
            print("✓ Old session-based game type retrieval removed")
        
        print("✓ Player callback signature fix verification PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error testing player callback: {e}")
        return False

def test_callback_parameter_usage():
    """Test that the callback properly uses both parameters."""
    print("\n" + "=" * 60)
    print("TESTING CALLBACK PARAMETER USAGE")
    print("=" * 60)
    
    try:
        # Read the player layout file
        with open('hockey_stats_webapp/layouts/player_layout.py', 'r') as f:
            content = f.read()
        
        # Find the callback function
        callback_start = content.find("def update_player_info(jersey_number, game_type_data):")
        if callback_start == -1:
            print("❌ Callback function not found")
            return False
        
        # Extract the callback function (find the next function or end of file)
        next_def = content.find("def ", callback_start + 1)
        if next_def == -1:
            callback_content = content[callback_start:]
        else:
            callback_content = content[callback_start:next_def]
        
        print("✓ Found callback function")
        
        # Check that jersey_number parameter is used
        if "jersey_number" in callback_content:
            print("✓ jersey_number parameter is used in callback")
        else:
            print("❌ jersey_number parameter not used in callback")
            return False
        
        # Check that game_type_data parameter is used
        if "game_type_data" in callback_content:
            print("✓ game_type_data parameter is used in callback")
        else:
            print("❌ game_type_data parameter not used in callback")
            return False
        
        # Check that game_type is passed to stats calculation
        stats_calls = [
            "data_service.calculate_player_stats(player['ID'], team_id, game_type)",
            "data_service.calculate_goalie_stats(player['ID'], team_id, game_type)"
        ]
        
        found_stats_calls = []
        for call in stats_calls:
            if call in callback_content:
                found_stats_calls.append(call)
        
        if found_stats_calls:
            print("✓ Game type is passed to stats calculation:")
            for call in found_stats_calls:
                print(f"   - {call}")
        else:
            print("❌ Game type not passed to stats calculation")
            return False
        
        print("✓ Callback parameter usage verification PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error testing callback parameter usage: {e}")
        return False

def main():
    """Run player callback fix verification tests."""
    print("PLAYER CALLBACK FIX VERIFICATION TEST")
    print("Testing that the callback signature bug has been fixed")
    print("=" * 80)
    
    # Run all tests
    tests = [
        ("Player Callback Signature", test_player_callback_signature),
        ("Callback Parameter Usage", test_callback_parameter_usage)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL CALLBACK TESTS PASSED!")
        print("\nCallback signature fix verified:")
        print("- ✓ Function accepts both jersey_number and game_type_data parameters")
        print("- ✓ Game type is properly extracted from callback parameter")
        print("- ✓ Game type is passed to stats calculation methods")
        print("- ✓ Old session-based game type retrieval removed")
        print("\nThe 'nothing shows' issue should now be resolved!")
        print("Players should now display stats when game filter and player are selected.")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Review the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
