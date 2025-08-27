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
                try:
                    creds_dict = json.loads(creds_json)
                    credentials = Credentials.from_service_account_info(
                        creds_dict, scopes=scope)
                    print("Using credentials from environment variable")
                except Exception as e:
                    print(f"Error parsing credentials from environment: {e}")
                    # Fall back to file
                    credentials = Credentials.from_service_account_file(
                        self.credentials_path, scopes=scope)
                    print("Using credentials from file")
            else:
                # Get credentials from file
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
            worksheet = self._get_worksheet('Events')
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Convert string boolean values to Python boolean values
            boolean_columns = ['IsGoal', 'IsPowerPlay', 'IsShortHanded']
            for col in boolean_columns:
                if col in df.columns:
                    # Convert 'TRUE'/'FALSE' strings to Python bool
                    df[col] = df[col].map({'TRUE': True, 'FALSE': False, True: True, False: False})
                    print(f"Converted {col} column values: {df[col].unique()}")
            
            self.cache[key] = df
            self.last_refresh[key] = time.time()
        
        return self.cache[key]
    
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
    
    def refresh_all_data(self):
        """
        Refresh all cached data.
        """
        self.get_players(force_refresh=True)
        self.get_games(force_refresh=True)
        self.get_events(force_refresh=True)
        self.get_game_roster(force_refresh=True)
        
        print("All data refreshed.")
