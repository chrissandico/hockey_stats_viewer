import os
import json
import time
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

class SheetsService:
    """
    Service for interacting with Google Sheets.
    Handles authentication, data retrieval, and caching.
    """
    
    def __init__(self, credentials_path='credentials.json', sheet_id=None, cache_ttl=3600):
        """
        Initialize the SheetsService.
        
        Args:
            credentials_path (str): Path to the service account credentials JSON file
            sheet_id (str): ID of the Google Sheet to connect to
            cache_ttl (int): Cache time-to-live in seconds (default: 3600)
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id or '1u4olfiYFjXW0Z88U3Q1wOxI7gz04KYbg6LNn8h-rfno'
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.last_refresh = {}
        
        # Initialize the connection
        self._connect()
    
    def _connect(self):
        """
        Connect to Google Sheets using the service account credentials.
        Tries to load credentials from environment variables first, then falls back to file.
        """
        try:
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            # Try to get credentials from environment variable first
            creds_json = os.environ.get('GOOGLE_CREDENTIALS')
            if creds_json:
                # Strip BOM and surrounding whitespace that can corrupt JSON parsing
                creds_json = creds_json.strip().lstrip('\ufeff')
                print(f"GOOGLE_CREDENTIALS env var found (length: {len(creds_json)} chars, first char: {repr(creds_json[0]) if creds_json else 'EMPTY'})")
                try:
                    creds_dict = json.loads(creds_json)
                    credentials = Credentials.from_service_account_info(
                        creds_dict, scopes=scope)
                    print("Using credentials from environment variable")
                except json.JSONDecodeError as e:
                    print(f"FATAL: GOOGLE_CREDENTIALS is not valid JSON: {e}")
                    raise ValueError(f"GOOGLE_CREDENTIALS env var contains invalid JSON: {e}")
                except Exception as e:
                    print(f"FATAL: Failed to create credentials from GOOGLE_CREDENTIALS: {e}")
                    raise
            else:
                print("GOOGLE_CREDENTIALS env var not set, trying credentials.json file")
                credentials = Credentials.from_service_account_file(
                    self.credentials_path, scopes=scope)
                print("Using credentials from file")
            
            # Authorize the client
            self.client = gspread.authorize(credentials)
            
            # Open the spreadsheet
            sheet_id = os.environ.get('GOOGLE_SHEET_ID', self.sheet_id)
            self.sheet = self.client.open_by_key(sheet_id)
            
            print(f"Connected to Google Sheet: {self.sheet.title}")
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            raise
    
    def _get_worksheet(self, name):
        """
        Get a worksheet by name.
        
        Args:
            name (str): Name of the worksheet
            
        Returns:
            gspread.Worksheet: The worksheet object
        """
        try:
            return self.sheet.worksheet(name)
        except Exception as e:
            print(f"Error getting worksheet '{name}': {e}")
            raise
    
    def _should_refresh_cache(self, key):
        """
        Check if the cache for a given key should be refreshed.
        
        Args:
            key (str): Cache key
            
        Returns:
            bool: True if cache should be refreshed, False otherwise
        """
        if key not in self.cache or key not in self.last_refresh:
            return True
        
        current_time = time.time()
        time_since_refresh = current_time - self.last_refresh[key]
        
        return time_since_refresh > self.cache_ttl
    
    def get_players(self, force_refresh=False):
        """
        Get all players from the Players sheet.
        
        Args:
            force_refresh (bool): Force a refresh of the cache
            
        Returns:
            pd.DataFrame: DataFrame containing player data
        """
        key = 'players'
        
        if force_refresh or self._should_refresh_cache(key):
            worksheet = self._get_worksheet('Players')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            self.cache[key] = df
            self.last_refresh[key] = time.time()
        
        return self.cache[key]
    
    def get_games(self, force_refresh=False):
        """
        Get all games from the Games sheet.
        
        Args:
            force_refresh (bool): Force a refresh of the cache
            
        Returns:
            pd.DataFrame: DataFrame containing game data
        """
        key = 'games'
        
        if force_refresh or self._should_refresh_cache(key):
            worksheet = self._get_worksheet('Games')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Handle game type data from column F
            # If GameType column doesn't exist or has empty values, default to 'E' (Exhibition)
            if 'GameType' not in df.columns:
                print("GameType column not found in Games sheet, adding default values")
                df['GameType'] = 'E'  # Default to Exhibition
            else:
                # Fill empty/null game type values with default
                df['GameType'] = df['GameType'].fillna('E')
                df['GameType'] = df['GameType'].replace('', 'E')
                
                # Validate game type values and replace invalid ones with default
                from config import is_valid_game_type, DEFAULT_GAME_TYPE
                invalid_mask = ~df['GameType'].apply(is_valid_game_type)
                if invalid_mask.any():
                    invalid_count = invalid_mask.sum()
                    print(f"Found {invalid_count} invalid game type values, replacing with default '{DEFAULT_GAME_TYPE}'")
                    df.loc[invalid_mask, 'GameType'] = DEFAULT_GAME_TYPE
                
                print(f"Game type distribution: {df['GameType'].value_counts().to_dict()}")
            
            self.cache[key] = df
            self.last_refresh[key] = time.time()
        
        return self.cache[key]
    
    def get_events(self, force_refresh=False):
        """
        Get all events from the Events sheet.
        
        Args:
            force_refresh (bool): Force a refresh of the cache
            
        Returns:
            pd.DataFrame: DataFrame containing event data
        """
        key = 'events'
        
        if force_refresh or self._should_refresh_cache(key):
            print(f"Loading Events data from Google Sheets (force_refresh={force_refresh})")
            worksheet = self._get_worksheet('Events')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            print(f"Loaded {len(df)} events from Google Sheets")
            
            # Convert string boolean values to Python boolean values with enhanced error handling
            boolean_columns = ['IsGoal', 'IsPowerPlay', 'IsShortHanded']
            print(f"Starting boolean conversion for Events sheet. Available columns: {list(df.columns)}")
            
            for col in boolean_columns:
                if col in df.columns:
                    print(f"Converting {col} column...")
                    original_values = df[col].unique()
                    original_dtype = df[col].dtype
                    print(f"  Original {col} values: {original_values} (dtype: {original_dtype})")
                    
                    # Enhanced boolean conversion to handle more formats
                    def convert_to_bool(val):
                        try:
                            if isinstance(val, bool):
                                return val
                            if isinstance(val, str):
                                val_lower = val.lower().strip()
                                if val_lower in ('true', 'yes', 'y', '1', 't'):
                                    return True
                                if val_lower in ('false', 'no', 'n', '0', 'f'):
                                    return False
                            if isinstance(val, (int, float)):
                                return bool(val)
                            # Log unexpected values
                            print(f"  Warning: Unexpected value for {col}: '{val}' ({type(val)}), defaulting to False")
                            return False  # Default to False for None or other values
                        except Exception as e:
                            print(f"  Error converting {col} value '{val}': {e}, defaulting to False")
                            return False
                    
                    try:
                        df[col] = df[col].apply(convert_to_bool)
                        converted_values = df[col].unique()
                        converted_dtype = df[col].dtype
                        print(f"  Successfully converted {col}: {converted_values} (dtype: {converted_dtype})")
                        
                        # Verify conversion worked
                        if converted_dtype == 'bool':
                            true_count = (df[col] == True).sum()
                            false_count = (df[col] == False).sum()
                            print(f"  {col} conversion verified: {true_count} True, {false_count} False")
                        else:
                            print(f"  WARNING: {col} conversion may have failed - dtype is {converted_dtype}, not bool")
                            
                    except Exception as e:
                        print(f"  ERROR: Failed to convert {col} column: {e}")
                        # Keep original values if conversion fails
                        
                else:
                    print(f"  Column {col} not found in Events sheet")
            
            self.cache[key] = df
            self.last_refresh[key] = time.time()
            print(f"Events data cached successfully with {len(df)} records")
        else:
            print(f"Using cached Events data ({len(self.cache[key])} records)")
        
        # Final verification of IsGoal column before returning
        result_df = self.cache[key]
        if 'IsGoal' in result_df.columns:
            isgoal_dtype = result_df['IsGoal'].dtype
            isgoal_values = result_df['IsGoal'].unique()
            print(f"Returning Events data - IsGoal dtype: {isgoal_dtype}, values: {isgoal_values}")
            
            # Count True/False values if boolean
            if isgoal_dtype == 'bool':
                true_count = (result_df['IsGoal'] == True).sum()
                false_count = (result_df['IsGoal'] == False).sum()
                print(f"IsGoal boolean counts: {true_count} True, {false_count} False")
        
        return result_df
    
    def get_game_roster(self, force_refresh=False):
        """
        Get all game roster data from the Game Roster sheet.
        
        Args:
            force_refresh (bool): Force a refresh of the cache
            
        Returns:
            pd.DataFrame: DataFrame containing game roster data
        """
        key = 'game_roster'
        
        if force_refresh or self._should_refresh_cache(key):
            worksheet = self._get_worksheet('GameRoster')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            self.cache[key] = df
            self.last_refresh[key] = time.time()
        
        return self.cache[key]
    
    def get_teams(self, force_refresh=False):
        """
        Get all teams from the Teams sheet.
        
        Args:
            force_refresh (bool): Force a refresh of the cache
            
        Returns:
            pd.DataFrame: DataFrame containing team data
        """
        key = 'teams'
        
        if force_refresh or self._should_refresh_cache(key):
            try:
                worksheet = self._get_worksheet('Teams')
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)

                # Validate required columns
                required_columns = ['TeamID', 'TeamName', 'Password']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    error_msg = f"Teams sheet missing required columns: {missing_columns}"
                    print(f"ERROR: {error_msg}")
                    raise ValueError(error_msg)

                # Validate data integrity
                if df.empty:
                    error_msg = "Teams sheet is empty - no team data available"
                    print(f"ERROR: {error_msg}")
                    raise ValueError(error_msg)

                # Normalize Password column to strings and strip whitespace so that
                # numeric passwords (gspread may return them as int) compare correctly
                df['Password'] = df['Password'].astype(str).str.strip()

                # Check for duplicate passwords, ignoring blank/empty entries
                non_empty = df[df['Password'] != '']
                duplicate_passwords = non_empty[non_empty.duplicated(subset=['Password'], keep=False)]
                if not duplicate_passwords.empty:
                    error_msg = f"Duplicate passwords found in Teams sheet: {duplicate_passwords['Password'].tolist()}"
                    print(f"ERROR: {error_msg}")
                    raise ValueError(error_msg)
                
                print(f"Successfully loaded {len(df)} teams from Teams sheet")
                
                self.cache[key] = df
                self.last_refresh[key] = time.time()
                
            except Exception as e:
                error_msg = f"Failed to load Teams sheet: {str(e)}"
                print(f"CRITICAL ERROR: {error_msg}")
                raise Exception(error_msg)
        
        return self.cache[key]
    
    def refresh_all_data(self):
        """
        Refresh all cached data.
        """
        self.get_teams(force_refresh=True)
        self.get_players(force_refresh=True)
        self.get_games(force_refresh=True)
        self.get_events(force_refresh=True)
        self.get_game_roster(force_refresh=True)
        
        print("All data refreshed.")
