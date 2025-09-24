#!/usr/bin/env python3
"""
Script to add a new test team to the Teams sheet.
This will add a team with TeamID 'TEST', TeamName 'Test Team', and Password 'testteam'.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService

def add_test_team():
    """Add the test team to the Teams sheet."""
    try:
        # Initialize the sheets service
        print("Initializing connection to Google Sheets...")
        sheets_service = SheetsService()
        
        # Get current teams to check if test team already exists
        print("Checking existing teams...")
        teams_df = sheets_service.get_teams()
        
        # Check if test team already exists
        existing_test_team = teams_df[teams_df['Password'] == 'testteam']
        if not existing_test_team.empty:
            print("Test team with password 'testteam' already exists:")
            print(existing_test_team.to_string(index=False))
            return
        
        # Check if TeamID 'TEST' already exists
        existing_test_id = teams_df[teams_df['TeamID'] == 'TEST']
        if not existing_test_id.empty:
            print("Team with ID 'TEST' already exists:")
            print(existing_test_id.to_string(index=False))
            return
        
        # Get the Teams worksheet
        teams_worksheet = sheets_service._get_worksheet('Teams')
        
        # Get all current data
        all_data = teams_worksheet.get_all_values()
        
        # Find the next empty row
        next_row = len(all_data) + 1
        
        # Add the new test team
        new_team_data = ['TEST', 'Test Team', 'testteam']
        
        print(f"Adding test team to row {next_row}...")
        teams_worksheet.insert_row(new_team_data, next_row)
        
        print("✅ Test team added successfully!")
        print("Team Details:")
        print(f"  TeamID: TEST")
        print(f"  TeamName: Test Team")
        print(f"  Password: testteam")
        
        # Refresh the cache to verify
        print("\nVerifying the addition...")
        teams_df = sheets_service.get_teams(force_refresh=True)
        test_team = teams_df[teams_df['Password'] == 'testteam']
        
        if not test_team.empty:
            print("✅ Verification successful! Test team found in sheet:")
            print(test_team.to_string(index=False))
        else:
            print("❌ Verification failed - test team not found after addition")
        
    except Exception as e:
        print(f"❌ Error adding test team: {str(e)}")
        return False
    
    return True

def test_authentication():
    """Test the authentication with the new test team."""
    try:
        print("\n" + "="*50)
        print("Testing Authentication")
        print("="*50)
        
        # Initialize services
        sheets_service = SheetsService()
        
        # Import auth service
        from services.auth_service import AuthService
        auth_service = AuthService(sheets_service)
        
        # Test authentication with the test team password
        print("Testing authentication with password 'testteam'...")
        result = auth_service.verify_password('testteam')
        
        if result:
            print("✅ Authentication successful!")
            print("Team Info:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print("❌ Authentication failed!")
            
        return result is not False
        
    except Exception as e:
        print(f"❌ Error testing authentication: {str(e)}")
        return False

if __name__ == "__main__":
    print("Hockey Stats Webapp - Add Test Team")
    print("="*40)
    
    # Add the test team
    success = add_test_team()
    
    if success:
        # Test the authentication
        test_authentication()
    
    print("\nScript completed.")
