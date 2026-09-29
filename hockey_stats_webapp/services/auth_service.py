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
            clean_pwd = str(password).strip()

            # 1. Check ParentCodes first
            try:
                parent_codes = self.sheets_service.get_parent_codes()
                if parent_codes is not None and not parent_codes.empty and 'ParentCode' in parent_codes.columns:
                    matching_parent = parent_codes[parent_codes['ParentCode'] == clean_pwd]
                    if not matching_parent.empty:
                        parent_row = matching_parent.iloc[0]
                        team_id = str(parent_row.get('TeamID', '')).strip()

                        # Lookup team name
                        teams = self.sheets_service.get_teams()
                        team_name = team_id
                        if teams is not None and not teams.empty and 'TeamID' in teams.columns:
                            t_match = teams[teams['TeamID'] == team_id]
                            if not t_match.empty:
                                team_name = t_match.iloc[0].get('TeamName', team_id)

                        jersey_number = str(parent_row.get('JerseyNumber', '')).strip()
                        player_id = str(parent_row.get('PlayerID', '')).strip()
                        child_name = str(parent_row.get('ChildName', '')).strip()

                        info = {
                            'team_id': team_id,
                            'team_name': team_name,
                            'password': clean_pwd,
                            'is_coach': False,
                            'is_parent': True,
                            'jersey_number': jersey_number,
                            'player_id': player_id,
                            'child_name': child_name
                        }
                        print(f"SUCCESS: Parent login authenticated for Child Jersey #{jersey_number} (Team: {team_name})")
                        return info
            except Exception as pe:
                print(f"DEBUG: Parent code check exception (non-fatal): {pe}")

            # 2. Check Teams sheet for Coach / Team logins
            teams = self.sheets_service.get_teams()
            matching_team = teams[teams['Password'] == clean_pwd]
            
            if matching_team.empty:
                print(f"WARNING: Invalid password attempt: '{clean_pwd}'")
                return False
            
            # Get the first matching team (should be only one due to duplicate check)
            team = matching_team.iloc[0]
            
            # Check if this is a coach login (password starts with 'c')
            is_coach = clean_pwd.startswith('c')
            
            team_info = {
                'team_id': team['TeamID'],
                'team_name': team['TeamName'],
                'password': team['Password'],
                'is_coach': is_coach,
                'is_parent': False,
                'jersey_number': None,
                'player_id': None,
                'child_name': None
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
