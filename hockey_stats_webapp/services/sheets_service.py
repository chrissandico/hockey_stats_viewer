import os
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime


# Backoff schedule (seconds) for retrying Google Sheets reads that hit
# the per-user rate limit (HTTP 429): the service account may make 60
# reads/minute, and both gunicorn workers bursting at once - at startup
# or on a coordinated refresh - can exhaust it. Retrying with backoff
# lets the burst drain instead of failing the whole load; a failed
# startup load used to poison the worker permanently.
_RATE_LIMIT_DELAYS = (1, 2, 4, 8)


def normalize_game_type_value(val):
    if pd.isna(val) or val is None:
        return 'R'
    s = str(val).strip().strip('"').strip("'").upper()
    if s in ['R', 'REGULAR', 'REGULAR SEASON', 'REG', 'SEASON']:
        return 'R'
    if s in ['T', 'TOURNAMENT', 'TOURNAMENT GAME', 'TOURN', 'TOUR']:
        return 'T'
    if s in ['P', 'PLAYOFF', 'PLAYOFFS', 'POSTSEASON', 'POST']:
        return 'P'
    if s in ['E', 'EXHIBITION', 'EX', 'PRESEASON', 'PRE-SEASON']:
        return 'E'
    return 'R'

class SheetsService:
    """
    Service for interacting with Google Sheets.
    Handles authentication, data retrieval, and caching.
    """
    
    def __init__(self, credentials_path='credentials.json', sheet_id=None, cache_ttl=120):
        """
        Initialize the SheetsService.
        
        Args:
            credentials_path (str): Path to the service account credentials JSON file
            sheet_id (str): ID of the Google Sheet to connect to
            cache_ttl (int): Freshness window in seconds for the shared data snapshot (default: 120)
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id or '1u4olfiYFjXW0Z88U3Q1wOxI7gz04KYbg6LNn8h-rfno'
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.last_refresh = {}
        # One shared freshness clock for every tab: when the epoch lapses,
        # all tabs reload together so pages never mix snapshots.
        self.data_epoch = None
        # Bumps on every tab reload; computed caches key off this.
        self.data_generation = 0
        self._refreshing_all = False
        
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
            self.sheet = self._with_rate_limit_retries(
                'open spreadsheet', lambda: self.client.open_by_key(sheet_id))
            
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
            return self._with_rate_limit_retries(
                f"get worksheet '{name}'", lambda: self.sheet.worksheet(name))
        except Exception as e:
            print(f"Error getting worksheet '{name}': {e}")
            raise
    
    def _is_rate_limit_error(self, exc):
        """True when a Sheets call failed on the per-user read quota (HTTP 429)."""
        response = getattr(exc, 'response', None)
        if response is not None and getattr(response, 'status_code', None) == 429:
            return True
        return '429' in str(exc)

    def _with_rate_limit_retries(self, description, operation):
        """Run a Sheets operation, backing off and retrying on 429 quota errors."""
        delays = _RATE_LIMIT_DELAYS
        for attempt in range(len(delays) + 1):
            try:
                return operation()
            except Exception as e:
                if attempt == len(delays) or not self._is_rate_limit_error(e):
                    raise
                wait = delays[attempt] + random.uniform(0, 0.5)
                print(f"Google Sheets rate limit (429) on {description}; "
                      f"retrying in {wait:.1f}s (attempt {attempt + 2} of {len(delays) + 1})")
                time.sleep(wait)

    def _get_records(self, worksheet, name):
        """worksheet.get_all_records() with 429 backoff."""
        return self._with_rate_limit_retries(
            f"read worksheet '{name}'", worksheet.get_all_records)

    def _mark_refreshed(self, key):
        """Record that a tab was (re)loaded just now."""
        self.last_refresh[key] = time.time()
        self.data_generation += 1

    def _refresh_all_if_stale(self):
        """
        Reload every tab together once the shared freshness window lapses.

        All tabs share one epoch: the first access after the window lapses
        reloads the whole snapshot, so games, events, players and rosters
        served afterwards all come from the same point in time. Reloads are
        lazy (only on access), so an idle site makes no Sheets calls.
        """
        if self._refreshing_all:
            return
        if self.data_epoch is not None and (time.time() - self.data_epoch) <= self.cache_ttl:
            return
        self._refreshing_all = True
        try:
            self.refresh_all_data()
        finally:
            self._refreshing_all = False

    @property
    def last_refresh_datetime(self):
        """Local datetime when the current snapshot was loaded, or None."""
        if self.data_epoch is None:
            return None
        return datetime.fromtimestamp(self.data_epoch)
    
    def get_players(self, force_refresh=False):
        """
        Get all players from the Players sheet.
        
        Args:
            force_refresh (bool): Force a refresh of the cache
            
        Returns:
            pd.DataFrame: DataFrame containing player data
        """
        key = 'players'
        self._refresh_all_if_stale()
        
        if force_refresh or key not in self.cache:
            worksheet = self._get_worksheet('Players')
            data = self._get_records(worksheet, 'Players')
            df = pd.DataFrame(data)
            
            self.cache[key] = df
            self._mark_refreshed(key)
        
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
        self._refresh_all_if_stale()
        
        if force_refresh or key not in self.cache:
            worksheet = self._get_worksheet('Games')
            data = self._get_records(worksheet, 'Games')
            df = pd.DataFrame(data)
            
            # Handle game type data
            if 'GameType' not in df.columns:
                print("GameType column not found in Games sheet, adding default values")
                df['GameType'] = 'R'
            else:
                df['GameType'] = df['GameType'].apply(normalize_game_type_value)
                print(f"Game type distribution from Google Sheets: {df['GameType'].value_counts().to_dict()}")
            
            self.cache[key] = df
            self._mark_refreshed(key)
        
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
        self._refresh_all_if_stale()
        
        if force_refresh or key not in self.cache:
            print(f"Loading Events data from Google Sheets (force_refresh={force_refresh})")
            worksheet = self._get_worksheet('Events')
            data = self._get_records(worksheet, 'Events')
            df = pd.DataFrame(data)
            print(f"Loaded {len(df)} events from Google Sheets")
            
            # Convert string boolean values to Python boolean values with enhanced error handling
            boolean_columns = ['IsGoal', 'IsPowerPlay', 'IsShortHanded', 'IsPenaltyShot']
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
            
            if 'GameType' in df.columns:
                df['GameType'] = df['GameType'].apply(normalize_game_type_value)

            self.cache[key] = df
            self._mark_refreshed(key)
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
        self._refresh_all_if_stale()
        
        if force_refresh or key not in self.cache:
            worksheet = self._get_worksheet('GameRoster')
            data = self._get_records(worksheet, 'GameRoster')
            df = pd.DataFrame(data)
            
            self.cache[key] = df
            self._mark_refreshed(key)
        
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
        self._refresh_all_if_stale()
        
        if force_refresh or key not in self.cache:
            try:
                worksheet = self._get_worksheet('Teams')
                data = self._get_records(worksheet, 'Teams')
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
                self._mark_refreshed(key)
                
            except Exception as e:
                error_msg = f"Failed to load Teams sheet: {str(e)}"
                print(f"CRITICAL ERROR: {error_msg}")
                raise Exception(error_msg)
        
        return self.cache[key]
    
    def get_parent_codes(self, force_refresh=False):
        """
        Get all parent code mappings from the ParentCodes sheet.

        Args:
            force_refresh (bool): Force a refresh of the cache

        Returns:
            pd.DataFrame: DataFrame containing parent code data
        """
        key = 'parent_codes'
        self._refresh_all_if_stale()

        if force_refresh or key not in self.cache:
            try:
                worksheet = self._get_worksheet('ParentCodes')
                data = self._get_records(worksheet, 'ParentCodes')
                df = pd.DataFrame(data)

                if df.empty:
                    print("WARNING: ParentCodes sheet is empty")
                    self.cache[key] = pd.DataFrame(columns=['ParentCode', 'TeamID', 'JerseyNumber', 'ChildName'])
                    self._mark_refreshed(key)
                    return self.cache[key]

                # Standardize column names, ensure string types
                if 'ParentCode' in df.columns:
                    df['ParentCode'] = df['ParentCode'].astype(str).str.strip()
                if 'JerseyNumber' in df.columns:
                    df['JerseyNumber'] = df['JerseyNumber'].astype(str).str.strip()
                if 'TeamID' in df.columns:
                    df['TeamID'] = df['TeamID'].astype(str).str.strip()

                print(f"Successfully loaded {len(df)} parent codes from ParentCodes sheet")
                self.cache[key] = df
                self._mark_refreshed(key)

            except Exception as e:
                print(f"WARNING: Could not load ParentCodes sheet (may not exist yet): {e}")
                self.cache[key] = pd.DataFrame(columns=['ParentCode', 'TeamID', 'JerseyNumber', 'ChildName'])
                self._mark_refreshed(key)

        return self.cache[key]

    def refresh_all_data(self):
        """
        Refresh all cached data.
        """
        self.get_teams(force_refresh=True)
        self.get_parent_codes(force_refresh=True)
        self.get_players(force_refresh=True)
        self.get_games(force_refresh=True)
        self.get_events(force_refresh=True)
        self.get_game_roster(force_refresh=True)
        
        self.data_epoch = time.time()
        print("All data refreshed.")
