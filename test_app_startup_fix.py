#!/usr/bin/env python3

"""
Test script to verify the app startup fix works correctly
"""

import sys
import os
import subprocess
import time

def test_app_startup():
    """Test that the app can start without the KeyError."""
    
    print("=== TESTING APP STARTUP FIX ===")
    
    # Change to the webapp directory
    webapp_dir = os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp')
    
    try:
        # Try to import the app module to test startup
        print("Testing app import and initialization...")
        
        # Set environment variables for testing (if needed)
        os.environ['PORT'] = '8051'  # Use different port for testing
        
        # Add the webapp directory to Python path
        sys.path.insert(0, webapp_dir)
        
        # Try to import the app
        print("Importing app module...")
        import app
        
        print("✅ App imported successfully!")
        print("✅ No KeyError during startup!")
        
        # Test that the server object exists
        if hasattr(app, 'server'):
            print("✅ Flask server object created successfully!")
        else:
            print("❌ Flask server object not found!")
            
        # Test that data service exists
        if hasattr(app, 'data_service'):
            print("✅ DataService initialized successfully!")
        else:
            print("❌ DataService not found!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during app startup test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_render_compatibility():
    """Test that the app structure is compatible with Render deployment."""
    
    print("\n=== TESTING RENDER COMPATIBILITY ===")
    
    webapp_dir = os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp')
    
    # Check required files exist
    required_files = [
        'app.py',
        'requirements.txt',
        'services/sheets_service.py',
        'services/data_service.py',
        'services/auth_service.py'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        full_path = os.path.join(webapp_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_files_exist = False
    
    # Check Procfile exists in root
    procfile_path = os.path.join(os.path.dirname(__file__), 'Procfile')
    if os.path.exists(procfile_path):
        print("✅ Procfile exists")
        
        # Check Procfile content
        with open(procfile_path, 'r') as f:
            content = f.read().strip()
            print(f"Procfile content: {content}")
            
            if 'gunicorn' in content and 'app:server' in content:
                print("✅ Procfile has correct gunicorn configuration")
            else:
                print("❌ Procfile may have incorrect configuration")
    else:
        print("❌ Procfile missing")
        all_files_exist = False
    
    return all_files_exist

if __name__ == "__main__":
    print("Testing app startup fix for Render deployment...")
    
    startup_success = test_app_startup()
    compatibility_success = test_render_compatibility()
    
    print(f"\n=== TEST RESULTS ===")
    print(f"App Startup Test: {'✅ PASSED' if startup_success else '❌ FAILED'}")
    print(f"Render Compatibility: {'✅ PASSED' if compatibility_success else '❌ FAILED'}")
    
    if startup_success and compatibility_success:
        print("\n🎉 All tests passed! The fix should resolve the Render deployment issue.")
    else:
        print("\n⚠️  Some tests failed. Additional fixes may be needed.")
