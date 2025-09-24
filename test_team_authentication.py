#!/usr/bin/env python3
"""
Script to test authentication with the test team password.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.auth_service import AuthService

def test_team_authentication():
    """Test authentication with the test team."""
    try:
        print("Hockey Stats Webapp - Test Team Authentication")
        print("=" * 50)
        
        # Initialize services
        print("Initializing services...")
        sheets_service = SheetsService()
        auth_service = AuthService(sheets_service)
        
        # Test authentication with the test team password
        print("\nTesting authentication with password 'testteam'...")
        result = auth_service.verify_password('testteam')
        
        if result:
            print("✅ Authentication successful!")
            print("\nTeam Information:")
            print(f"  Team ID: {result['team_id']}")
            print(f"  Team Name: {result['team_name']}")
            print(f"  Password: {result['password']}")
            print(f"  Is Coach: {result['is_coach']}")
            
            # Test coach authentication (password starting with 'c')
            print("\n" + "-" * 30)
            print("Testing coach authentication...")
            coach_result = auth_service.verify_password('ctestteam')
            
            if coach_result:
                print("✅ Coach authentication would work with 'ctestteam'")
                print(f"  Is Coach: {coach_result['is_coach']}")
            else:
                print("ℹ️  Coach authentication requires 'ctestteam' password")
            
            # Test invalid password
            print("\n" + "-" * 30)
            print("Testing invalid password...")
            invalid_result = auth_service.verify_password('wrongpassword')
            
            if not invalid_result:
                print("✅ Invalid password correctly rejected")
            else:
                print("❌ Invalid password was incorrectly accepted")
                
        else:
            print("❌ Authentication failed!")
            
        return result is not False
        
    except Exception as e:
        print(f"❌ Error testing authentication: {str(e)}")
        return False

if __name__ == "__main__":
    test_team_authentication()
