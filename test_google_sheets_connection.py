#!/usr/bin/env python3

"""
Test script to verify Google Sheets connection and credentials setup
"""

import sys
import os
import json

# Add the hockey_stats_webapp directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def test_credentials_file():
    """Test if credentials.json file exists and is valid."""
    
    print("=== TESTING CREDENTIALS FILE ===")
    
    credentials_path = 'credentials.json'
    
    if os.path.exists(credentials_path):
        print("✅ credentials.json file found")
        
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
            
            # Check required fields
            required_fields = [
                'type', 'project_id', 'private_key_id', 'private_key',
                'client_email', 'client_id', 'auth_uri', 'token_uri'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in creds:
                    missing_fields.append(field)
                elif creds[field] == f"your-{field}" or creds[field] == f"your-{field.replace('_', '-')}":
                    missing_fields.append(f"{field} (still has placeholder value)")
            
            if missing_fields:
                print(f"❌ credentials.json is missing or has placeholder values for: {missing_fields}")
                print("Please update credentials.json with your actual Google Cloud service account credentials")
                return False
            else:
                print("✅ credentials.json has all required fields")
                print(f"Service account email: {creds['client_email']}")
                print(f"Project ID: {creds['project_id']}")
                return True
                
        except json.JSONDecodeError as e:
            print(f"❌ credentials.json is not valid JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Error reading credentials.json: {e}")
            return False
    else:
        print("❌ credentials.json file not found")
        print("Please follow the setup guide in setup_local_credentials.md")
        return False

def test_environment_variable():
    """Test if GOOGLE_CREDENTIALS environment variable is set."""
    
    print("\n=== TESTING ENVIRONMENT VARIABLE ===")
    
    google_creds = os.environ.get('GOOGLE_CREDENTIALS')
    
    if google_creds:
        print("✅ GOOGLE_CREDENTIALS environment variable found")
        
        try:
            creds = json.loads(google_creds)
            print(f"Service account email: {creds.get('client_email', 'Not found')}")
            print(f"Project ID: {creds.get('project_id', 'Not found')}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ GOOGLE_CREDENTIALS is not valid JSON: {e}")
            return False
    else:
        print("ℹ️  GOOGLE_CREDENTIALS environment variable not set (this is OK if using credentials.json)")
        return False

def test_sheets_service():
    """Test the SheetsService connection."""
    
    print("\n=== TESTING SHEETS SERVICE CONNECTION ===")
    
    try:
        from services.sheets_service import SheetsService
        
        print("Attempting to connect to Google Sheets...")
        sheets_service = SheetsService()
        
        print("✅ SheetsService initialized successfully")
        
        # Test getting teams data
        print("Testing teams data retrieval...")
        teams = sheets_service.get_teams()
        print(f"✅ Successfully retrieved {len(teams)} teams")
        
        if not teams.empty:
            print("Team columns:", teams.columns.tolist())
            print("First team:", teams.iloc[0]['TeamName'] if 'TeamName' in teams.columns else "TeamName column not found")
        
        # Test getting players data
        print("Testing players data retrieval...")
        players = sheets_service.get_players()
        print(f"✅ Successfully retrieved {len(players)} players")
        
        if not players.empty:
            print("Player columns:", players.columns.tolist())
            
            # Check for goalies to test the original issue
            if 'Position' in players.columns:
                goalies = players[players['Position'] == 'G']
                print(f"Found {len(goalies)} goalies")
                
                if not goalies.empty:
                    goalie = goalies.iloc[0]
                    print("First goalie columns:", goalie.index.tolist())
                    
                    # Test the ID column access that was causing the original error
                    possible_id_columns = ['ID', 'PlayerID', 'id', 'player_id']
                    id_column_found = None
                    
                    for col_name in possible_id_columns:
                        if col_name in goalie.index:
                            try:
                                goalie_id = goalie[col_name]
                                print(f"✅ Found ID column '{col_name}' with value: {goalie_id}")
                                id_column_found = col_name
                                break
                            except Exception as e:
                                print(f"❌ Error accessing column '{col_name}': {e}")
                    
                    if id_column_found:
                        print(f"✅ The original KeyError issue should be resolved - ID column is '{id_column_found}'")
                    else:
                        print("❌ No valid ID column found - this could cause issues")
                else:
                    print("No goalies found in data")
            else:
                print("No 'Position' column found in players data")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Google Sheets: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_startup():
    """Test that the app can start with the current credentials."""
    
    print("\n=== TESTING APP STARTUP ===")
    
    try:
        # Set a different port to avoid conflicts
        os.environ['PORT'] = '8052'
        
        print("Importing app module...")
        import app
        
        print("✅ App imported successfully!")
        print("✅ No startup errors!")
        
        if hasattr(app, 'services_initialized') and app.services_initialized:
            print("✅ Services initialized successfully!")
        else:
            print("⚠️  Services not initialized (this may be expected)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during app startup: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all connection tests."""
    
    print("Google Sheets Connection Test")
    print("=" * 50)
    
    # Test credentials
    creds_file_ok = test_credentials_file()
    env_var_ok = test_environment_variable()
    
    if not creds_file_ok and not env_var_ok:
        print("\n❌ No valid credentials found!")
        print("Please set up credentials following the guide in setup_local_credentials.md")
        return False
    
    # Test sheets service
    sheets_ok = test_sheets_service()
    
    if not sheets_ok:
        print("\n❌ Google Sheets connection failed!")
        print("Check your credentials and make sure the service account has access to the sheet")
        return False
    
    # Test app startup
    app_ok = test_app_startup()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Credentials File: {'✅ PASS' if creds_file_ok else '❌ FAIL'}")
    print(f"Environment Variable: {'✅ PASS' if env_var_ok else 'ℹ️  N/A'}")
    print(f"Sheets Connection: {'✅ PASS' if sheets_ok else '❌ FAIL'}")
    print(f"App Startup: {'✅ PASS' if app_ok else '❌ FAIL'}")
    
    if sheets_ok and app_ok:
        print("\n🎉 All tests passed! Your local setup is ready.")
        print("You can now run the webapp locally with: python hockey_stats_webapp/app.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above and follow the setup guide.")
    
    return sheets_ok and app_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
