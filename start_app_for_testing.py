#!/usr/bin/env python3
"""
Script to start the hockey stats app for testing purposes.
"""

import os
import sys
import subprocess
import time
import requests
import signal
import threading

def start_app():
    """Start the hockey stats application"""
    print("Starting hockey stats application...")
    
    # Change to the app directory
    app_dir = "hockey_stats_webapp"
    
    # Start the app
    try:
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"App started with PID: {process.pid}")
        return process
        
    except Exception as e:
        print(f"Failed to start app: {e}")
        return None

def wait_for_app(base_url="http://localhost:8050", timeout=60):
    """Wait for the app to be ready"""
    print(f"Waiting for app to be ready at {base_url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                print("✅ App is ready!")
                return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print(f"\n❌ App did not become ready within {timeout} seconds")
    return False

def run_tests():
    """Run the web interface tests"""
    print("\nRunning web interface tests...")
    
    try:
        # Run the API test
        result = subprocess.run([sys.executable, "test_web_api_score_fix.py"], 
                              capture_output=True, text=True)
        
        print("Test output:")
        print(result.stdout)
        if result.stderr:
            print("Test errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Failed to run tests: {e}")
        return False

def main():
    """Main function"""
    app_process = None
    
    try:
        # Start the app
        app_process = start_app()
        if not app_process:
            print("Failed to start application")
            return 1
        
        # Wait for app to be ready
        if not wait_for_app():
            print("App failed to start properly")
            return 1
        
        # Run tests
        test_success = run_tests()
        
        if test_success:
            print("\n🎉 All tests completed successfully!")
            return 0
        else:
            print("\n⚠️  Some tests failed")
            return 1
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
        
    finally:
        # Clean up - stop the app
        if app_process:
            print(f"\nStopping app (PID: {app_process.pid})...")
            try:
                app_process.terminate()
                app_process.wait(timeout=10)
                print("✅ App stopped successfully")
            except:
                print("⚠️  Force killing app...")
                app_process.kill()

if __name__ == "__main__":
    sys.exit(main())