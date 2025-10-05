#!/usr/bin/env python3
"""
Test to verify the layout structure and imports are correct for game type filtering.
This test doesn't require Google Sheets credentials - it just verifies code structure.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

def test_player_layout_structure():
    """Test that Player Layout has correct game type filtering structure."""
    print("=" * 60)
    print("TESTING PLAYER LAYOUT STRUCTURE")
    print("=" * 60)
    
    try:
        # Read the player layout file
        with open('hockey_stats_webapp/layouts/player_layout.py', 'r') as f:
            content = f.read()
        
        # Check for required imports
        required_imports = [
            'from components.game_type_filter import create_game_type_filter_component, create_game_type_session_store',
        ]
        
        missing_imports = []
        for import_line in required_imports:
            if import_line not in content:
                missing_imports.append(import_line)
        
        if missing_imports:
            print("❌ Missing required imports:")
            for imp in missing_imports:
                print(f"   - {imp}")
            return False
        else:
            print("✓ All required imports present")
        
        # Check for game type filter component usage
        if 'create_game_type_filter_component()' in content:
            print("✓ Game type filter component added to layout")
        else:
            print("❌ Game type filter component not found in layout")
            return False
        
        # Check for session store
        if 'create_game_type_session_store()' in content:
            print("✓ Game type session store added to layout")
        else:
            print("❌ Game type session store not found in layout")
            return False
        
        # Check that hard-coded game_type=None was removed
        if 'game_type=None' in content:
            print("❌ Hard-coded game_type=None still present")
            return False
        else:
            print("✓ Hard-coded game_type=None removed")
        
        # Check for game-type-session-store input in callbacks
        if 'game-type-session-store' in content:
            print("✓ Game type session store input added to callbacks")
        else:
            print("❌ Game type session store input not found in callbacks")
            return False
        
        print("✓ Player Layout structure verification PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Player Layout: {e}")
        return False

def test_game_layout_structure():
    """Test that Game Layout has correct game type filtering structure."""
    print("\n" + "=" * 60)
    print("TESTING GAME LAYOUT STRUCTURE")
    print("=" * 60)
    
    try:
        # Read the game layout file
        with open('hockey_stats_webapp/layouts/game_layout.py', 'r') as f:
            content = f.read()
        
        # Check for required imports
        required_imports = [
            'from components.game_type_filter import create_game_type_badge, create_game_type_filter_component, create_game_type_session_store',
        ]
        
        missing_imports = []
        for import_line in required_imports:
            if import_line not in content:
                missing_imports.append(import_line)
        
        if missing_imports:
            print("❌ Missing required imports:")
            for imp in missing_imports:
                print(f"   - {imp}")
            return False
        else:
            print("✓ All required imports present")
        
        # Check for game type filter component usage
        if 'create_game_type_filter_component()' in content:
            print("✓ Game type filter component added to layout")
        else:
            print("❌ Game type filter component not found in layout")
            return False
        
        # Check for session store
        if 'create_game_type_session_store()' in content:
            print("✓ Game type session store added to layout")
        else:
            print("❌ Game type session store not found in layout")
            return False
        
        # Check for game dropdown callback with game type input
        if 'game-type-session-store' in content and 'game-dropdown' in content:
            print("✓ Game dropdown callback with game type filtering added")
        else:
            print("❌ Game dropdown callback with game type filtering not found")
            return False
        
        # Check that get_games() now uses game_type parameter
        if 'data_service.get_games(effective_team_id, game_type=game_type)' in content:
            print("✓ Game filtering uses game_type parameter")
        else:
            print("❌ Game filtering doesn't use game_type parameter")
            return False
        
        print("✓ Game Layout structure verification PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Game Layout: {e}")
        return False

def test_team_layout_structure():
    """Test that Team Layout already has correct game type filtering structure."""
    print("\n" + "=" * 60)
    print("TESTING TEAM LAYOUT STRUCTURE")
    print("=" * 60)
    
    try:
        # Read the team layout file
        with open('hockey_stats_webapp/layouts/team_layout.py', 'r') as f:
            content = f.read()
        
        # Check for game type filter component usage
        if 'create_game_type_filter_component()' in content:
            print("✓ Game type filter component present in layout")
        else:
            print("❌ Game type filter component not found in layout")
            return False
        
        # Check for session store
        if 'create_game_type_session_store()' in content:
            print("✓ Game type session store present in layout")
        else:
            print("❌ Game type session store not found in layout")
            return False
        
        # Check for game type session store input in callbacks
        if 'game-type-session-store' in content:
            print("✓ Game type session store input used in callbacks")
        else:
            print("❌ Game type session store input not found in callbacks")
            return False
        
        print("✓ Team Layout structure verification PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Team Layout: {e}")
        return False

def test_game_type_filter_component():
    """Test that the game type filter component exists and has required functions."""
    print("\n" + "=" * 60)
    print("TESTING GAME TYPE FILTER COMPONENT")
    print("=" * 60)
    
    try:
        # Read the game type filter component file
        with open('hockey_stats_webapp/components/game_type_filter.py', 'r') as f:
            content = f.read()
        
        # Check for required functions
        required_functions = [
            'def create_game_type_filter_component(',
            'def create_game_type_badge(',
            'def create_game_type_session_store(',
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print("❌ Missing required functions:")
            for func in missing_functions:
                print(f"   - {func}")
            return False
        else:
            print("✓ All required functions present")
        
        print("✓ Game Type Filter Component verification PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Game Type Filter Component: {e}")
        return False

def main():
    """Run layout structure verification tests."""
    print("LAYOUT STRUCTURE VERIFICATION TEST")
    print("Verifying game type filtering implementation across all layouts")
    print("=" * 80)
    
    # Run all tests
    tests = [
        ("Player Layout Structure", test_player_layout_structure),
        ("Game Layout Structure", test_game_layout_structure),
        ("Team Layout Structure", test_team_layout_structure),
        ("Game Type Filter Component", test_game_type_filter_component)
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
        print("\n🎉 ALL STRUCTURE TESTS PASSED!")
        print("\nKey fixes verified:")
        print("- Player Layout: ✓ Game type filter added, hard-coded None removed")
        print("- Game Layout: ✓ Game type filter added, callback with filtering implemented")
        print("- Team Layout: ✓ Already had correct game type filtering")
        print("- All layouts: ✓ Use centralized game type filter component")
        print("\nThe Regular Season filtering issue should now be resolved!")
        print("All layouts now consistently use the centralized DataService with game_type parameter.")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Review the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
