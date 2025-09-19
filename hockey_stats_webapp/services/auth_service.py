import hashlib
import os

class AuthService:
    """
    Service for handling authentication.
    Implements team-based password verification using the Teams sheet.
    """
    
    def __init__(self, sheets_service=None):
        """
        Initialize the AuthService.
        
        Args:
            sheets_service (SheetsService): The sheets service for team data retrieval
        """
        self.sheets_service = sheets_service
        print("Team-based authentication service initialized")
    
    def _hash_password(self, password):
        """
        Hash a password using SHA-256.
        
        Args:
            password (str): The password to hash
            
        Returns:
            str: The hashed password
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Create a new SHA-256 hash object
        sha256 = hashlib.sha256()
        
        # Update the hash object with the password bytes
        sha256.update(password.encode('utf-8'))
        
        # Get the hexadecimal digest of the hash
        return sha256.hexdigest()
    
    def verify_password(self, password):
        """
        Verify if a password matches any team in the Teams sheet.
        
        Args:
            password (str): The password to verify
            
        Returns:
            dict or False: Team information if password matches, False otherwise
        """
        if not password:
            print("ERROR: Empty password provided")
            return False
        
        if not self.sheets_service:
            print("ERROR: No sheets service available for team authentication")
            return False
        
        try:
            # Get teams data
            teams = self.sheets_service.get_teams()
            
            # Look for matching password
            matching_team = teams[teams['Password'] == password]
            
            if matching_team.empty:
                print(f"WARNING: Invalid password attempt: '{password}'")
                return False
            
            # Get the first matching team (should be only one due to duplicate check)
            team = matching_team.iloc[0]
            
            # Check if this is a coach login (password starts with 'c')
            is_coach = password.startswith('c')
            
            team_info = {
                'team_id': team['TeamID'],
                'team_name': team['TeamName'],
                'password': team['Password'],
                'is_coach': is_coach
            }
            
            print(f"SUCCESS: Authentication successful for team '{team_info['team_name']}' (ID: {team_info['team_id']}, Coach: {is_coach})")
            return team_info
            
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return False
    
    def get_team_by_password(self, password):
        """
        Get team information by password.
        
        Args:
            password (str): The team password
            
        Returns:
            dict or None: Team information if found, None otherwise
        """
        return self.verify_password(password)
