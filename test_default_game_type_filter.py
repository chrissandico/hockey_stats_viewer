#!/usr/bin/env python3

"""
Test script to verify that the game type filter defaults to "All Games" instead of "Exhibition".
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from components.game_type_filter import create_game_type_filter_component

def test_default_game_type_filter():
    """Test that the game type filter defaults to 'All Games' when no specific type is selected."""
    print("=== Testing Default Game Type Filter ===")
    
    # Test 1: Default behavior (no selected_game_type specified)
    print("\n--- Test 1: Default behavior (no parameters) ---")
    component = create_game_type_filter_component()
    
    # Extract the active_tab from the component
    tabs_component = None
    for child in component.children:
        if hasattr(child, 'children'):
            for subchild in child.children:
                if hasattr(subchild, 'id') and subchild.id == 'game-type-filter-tabs':
                    tabs_component = subchild
                    break
    
    if tabs_component:
        active_tab = tabs_component.active_tab
        print(f"Active tab: {active_tab}")
        if active_tab == "all":
            print("✅ PASS: Default filter is 'All Games'")
        else:
            print(f"❌ FAIL: Default filter is '{active_tab}', expected 'all'")
    else:
        print("❌ FAIL: Could not find tabs component")
    
    # Test 2: Explicitly setting selected_game_type to None
    print("\n--- Test 2: Explicitly setting selected_game_type=None ---")
    component = create_game_type_filter_component(selected_game_type=None)
    
    # Extract the active_tab from the component
    tabs_component = None
    for child in component.children:
        if hasattr(child, 'children'):
            for subchild in child.children:
                if hasattr(subchild, 'id') and subchild.id == 'game-type-filter-tabs':
                    tabs_component = subchild
                    break
    
    if tabs_component:
        active_tab = tabs_component.active_tab
        print(f"Active tab: {active_tab}")
        if active_tab == "all":
            print("✅ PASS: Filter defaults to 'All Games' when selected_game_type=None")
        else:
            print(f"❌ FAIL: Filter is '{active_tab}', expected 'all'")
    else:
        print("❌ FAIL: Could not find tabs component")
    
    # Test 3: Setting a specific game type should override the default
    print("\n--- Test 3: Setting specific game type (should override default) ---")
    component = create_game_type_filter_component(selected_game_type='E')
    
    # Extract the active_tab from the component
    tabs_component = None
    for child in component.children:
        if hasattr(child, 'children'):
            for subchild in child.children:
                if hasattr(subchild, 'id') and subchild.id == 'game-type-filter-tabs':
                    tabs_component = subchild
                    break
    
    if tabs_component:
        active_tab = tabs_component.active_tab
        print(f"Active tab: {active_tab}")
        if active_tab == "E":
            print("✅ PASS: Specific game type 'E' is selected when explicitly set")
        else:
            print(f"❌ FAIL: Filter is '{active_tab}', expected 'E'")
    else:
        print("❌ FAIL: Could not find tabs component")
    
    # Test 4: When show_all_option=False, should fall back to DEFAULT_GAME_TYPE
    print("\n--- Test 4: show_all_option=False (should use DEFAULT_GAME_TYPE) ---")
    component = create_game_type_filter_component(selected_game_type=None, show_all_option=False)
    
    # Extract the active_tab from the component
    tabs_component = None
    for child in component.children:
        if hasattr(child, 'children'):
            for subchild in child.children:
                if hasattr(subchild, 'id') and subchild.id == 'game-type-filter-tabs':
                    tabs_component = subchild
                    break
    
    if tabs_component:
        active_tab = tabs_component.active_tab
        print(f"Active tab: {active_tab}")
        if active_tab == "E":  # DEFAULT_GAME_TYPE is 'E'
            print("✅ PASS: Falls back to DEFAULT_GAME_TYPE when show_all_option=False")
        else:
            print(f"❌ FAIL: Filter is '{active_tab}', expected 'E' (DEFAULT_GAME_TYPE)")
    else:
        print("❌ FAIL: Could not find tabs component")

def test_component_structure():
    """Test that the component structure includes the 'All Games' tab."""
    print("\n=== Testing Component Structure ===")
    
    component = create_game_type_filter_component()
    
    # Extract the tabs component
    tabs_component = None
    for child in component.children:
        if hasattr(child, 'children'):
            for subchild in child.children:
                if hasattr(subchild, 'id') and subchild.id == 'game-type-filter-tabs':
                    tabs_component = subchild
                    break
    
    if tabs_component and hasattr(tabs_component, 'children'):
        tab_labels = []
        tab_ids = []
        
        for tab in tabs_component.children:
            if hasattr(tab, 'label'):
                tab_labels.append(tab.label)
            if hasattr(tab, 'tab_id'):
                tab_ids.append(tab.tab_id)
        
        print(f"Available tab labels: {tab_labels}")
        print(f"Available tab IDs: {tab_ids}")
        
        if "All Games" in tab_labels and "all" in tab_ids:
            print("✅ PASS: 'All Games' tab is available")
        else:
            print("❌ FAIL: 'All Games' tab is missing")
        
        # Check that other game types are also present
        expected_labels = ["Exhibition", "Regular Season", "Tournament"]
        expected_ids = ["E", "R", "T"]
        
        for label in expected_labels:
            if label in tab_labels:
                print(f"✅ PASS: '{label}' tab is available")
            else:
                print(f"❌ FAIL: '{label}' tab is missing")
        
        for tab_id in expected_ids:
            if tab_id in tab_ids:
                print(f"✅ PASS: Tab ID '{tab_id}' is available")
            else:
                print(f"❌ FAIL: Tab ID '{tab_id}' is missing")
    else:
        print("❌ FAIL: Could not extract tabs structure")

def main():
    """Run all tests."""
    print("Testing Game Type Filter Default Behavior")
    print("=" * 50)
    
    try:
        test_default_game_type_filter()
        test_component_structure()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("\nThe Team Stats page should now default to 'All Games' instead of 'Exhibition'.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
