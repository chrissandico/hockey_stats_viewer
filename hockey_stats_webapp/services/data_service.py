import pandas as pd
import numpy as np
import logging
from datetime import datetime, date

class DataService:
    """
    Service for processing hockey statistics data.
    Provides functions for calculating player, team, and game statistics.
    """
    
    def __init__(self, sheets_service, force_refresh=False):
        """
        Initialize the DataService.
        
        Args:
            sheets_service (SheetsService): The sheets service for data retrieval
            force_refresh (bool): Whether to force a refresh of all data on initialization
        """
        self.sheets_service = sheets_service
        
        # Set up logging for this service
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            # Configure logging if not already configured
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Always force refresh all data to avoid caching issues
        self.logger.info("Forcing refresh of all data...")
        print("Forcing refresh of all data...")
        self.sheets_service.refresh_all_data()
        
        # Cache busting - initialize with empty caches
        self._players_cache = None
        self._games_cache = None
        self._events_cache = None
        self._game_roster_cache = None
        
        # Initialize games calculated cache
        self._games_calculated_cache = {}
        
        # Force refresh events data to ensure boolean conversion happens
        self.force_refresh_events_data()
    
    def force_refresh_events_data(self):
        """
        Force refresh events data to ensure boolean conversion happens properly.
        This method specifically addresses the IsGoal column conversion issue.
        """
        try:
            self.logger.info("Force refreshing events data to ensure boolean conversion...")
            print("Force refreshing events data to ensure boolean conversion...")
            
            # Force refresh events data
            events = self.sheets_service.get_events(force_refresh=True)
            
            # Verify IsGoal column conversion
            if 'IsGoal' in events.columns:
                isgoal_dtype = events['IsGoal'].dtype
                isgoal_values = events['IsGoal'].unique()
                self.logger.info(f"Events data loaded - IsGoal dtype: {isgoal_dtype}, unique values: {isgoal_values}")
                print(f"Events data loaded - IsGoal dtype: {isgoal_dtype}, unique values: {isgoal_values}")
                
                # If IsGoal is still not boolean, try manual conversion
                if isgoal_dtype != 'bool':
                    self.logger.warning("IsGoal column is not boolean type, attempting manual conversion...")
                    print("WARNING: IsGoal column is not boolean type, attempting manual conversion...")
                    
                    def manual_convert_to_bool(val):
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
                        return False
                    
                    # Apply manual conversion
                    original_values = events['IsGoal'].unique()
                    events['IsGoal'] = events['IsGoal'].apply(manual_convert_to_bool)
                    converted_values = events['IsGoal'].unique()
                    
                    self.logger.info(f"Manual conversion: {original_values} -> {converted_values}")
                    print(f"Manual conversion: {original_values} -> {converted_values}")
                    
                    # Update the cache with converted data
                    self.sheets_service.cache['events'] = events
                    
                # Count goals for verification
                if events['IsGoal'].dtype == 'bool':
                    goal_count = (events['IsGoal'] == True).sum()
                    total_events = len(events)
                    self.logger.info(f"Boolean conversion verified: {goal_count} goals out of {total_events} total events")
                    print(f"Boolean conversion verified: {goal_count} goals out of {total_events} total events")
                    
                    # Clear games cache to force recalculation with corrected boolean data
                    self.logger.info("Clearing games cache to force recalculation with corrected boolean data...")
                    print("Clearing games cache to force recalculation with corrected boolean data...")
                    self.clear_games_cache()
                    
                else:
                    self.logger.error("Failed to convert IsGoal column to boolean type")
                    print("ERROR: Failed to convert IsGoal column to boolean type")
            else:
                self.logger.error("IsGoal column not found in events data")
                print("ERROR: IsGoal column not found in events data")
                
        except Exception as e:
            self.logger.error(f"Error in force_refresh_events_data: {e}")
            print(f"ERROR in force_refresh_events_data: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_player_id_column(self, players_df):
        """
        Centralized helper method to detect the correct player ID column name.
        Handles backward compatibility for different column naming conventions.
        
        Args:
            players_df (pd.DataFrame): Players DataFrame to examine
            
        Returns:
            str: The name of the ID column, or None if not found
        """
        if players_df.empty:
            return None
        
        # Check for ID column variations in order of preference
        if 'ID' in players_df.columns:
            return 'ID'
        elif 'Unnamed: 0' in players_df.columns:
            return 'Unnamed: 0'
        elif '' in players_df.columns:
            return ''
        else:
            print(f"ERROR: No player ID column found. Available columns: {players_df.columns.tolist()}")
            return None
    
    def _get_player_id_from_series(self, player_series):
        """
        Centralized helper method to extract player ID from a pandas Series.
        Handles backward compatibility for different column naming conventions.
        
        Args:
            player_series (pd.Series): Player data series
            
        Returns:
            str: The player ID, or None if not found
        """
        # Check for ID column variations in order of preference
        if 'ID' in player_series.index:
            return player_series['ID']
        elif 'Unnamed: 0' in player_series.index:
            return player_series['Unnamed: 0']
        elif '' in player_series.index:
            return player_series['']
        else:
            print(f"ERROR: No player ID found in series. Available columns: {list(player_series.index)}")
            return None
    
    def _filter_by_team(self, df, team_id):
        """
        Filter a DataFrame by TeamID.
        
        Args:
            df (pd.DataFrame): DataFrame to filter
            team_id (str): Team ID to filter by
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        if df.empty:
            return df
        
        if 'TeamID' not in df.columns:
            error_msg = f"TeamID column not found in data. Available columns: {df.columns.tolist()}"
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        # Filter by team ID
        filtered_df = df[df['TeamID'] == team_id]
        print(f"Filtered data: {len(filtered_df)} records for team {team_id} (from {len(df)} total)")
        
        return filtered_df
    
    def _get_team_name_from_id(self, team_id):
        """
        Get team name from team ID.
        
        Args:
            team_id (str): Team ID
            
        Returns:
            str: Team name or None if not found
        """
        if team_id is None:
            return None
            
        try:
            teams = self.sheets_service.get_teams()
            matching_team = teams[teams['TeamID'] == team_id]
            
            if not matching_team.empty:
                team_name = matching_team.iloc[0]['TeamName']
                print(f"Found team name '{team_name}' for TeamID '{team_id}'")
                return team_name
            else:
                print(f"ERROR: Team name not found for TeamID '{team_id}'")
                return None
                
        except Exception as e:
            print(f"ERROR: Failed to get team name for TeamID '{team_id}': {str(e)}")
            return None
    
    def _normalize_team_name(self, name):
        """
        Normalize a team name for comparison by removing spaces, special characters, and converting to lowercase.
        
        Args:
            name (str): Team name to normalize
            
        Returns:
            str: Normalized team name
        """
        if not name:
            return ""
        
        # Remove spaces, convert to lowercase, remove common special characters
        normalized = name.lower().replace(" ", "").replace("-", "").replace("_", "")
        return normalized
    
    def _filter_goalie_events(self, events, goalie_id, game_id=None):
        """
        Filter events for goalie statistics with backward compatibility for GoalieOnIceId.
        
        Args:
            events (pd.DataFrame): Events data to filter
            goalie_id (str): The goalie's player ID
            game_id (str, optional): Game ID to filter by (if None, uses all events)
            
        Returns:
            pd.DataFrame: Filtered events that should be attributed to this goalie
        """
        # Filter by game if specified
        if game_id is not None:
            events = events[events['GameID'] == game_id]
        
        # Check if GoalieOnIceId column exists and has data
        has_goalie_on_ice_data = ('GoalieOnIceId' in events.columns and 
                                 not events['GoalieOnIceId'].isna().all())
        
        if has_goalie_on_ice_data:
            print(f"Using GoalieOnIceId column for goalie {goalie_id} event filtering")
            # Filter events where this goalie was on ice OR where goalie info is missing (backward compatibility)
            goalie_events = events[
                (events['GoalieOnIceId'] == goalie_id) | 
                (events['GoalieOnIceId'].isna())
            ]
            print(f"Found {len(goalie_events)} events for goalie {goalie_id} using GoalieOnIceId filtering")
        else:
            print(f"GoalieOnIceId column not available, using all events for goalie {goalie_id}")
            # Fall back to using all events (original behavior)
            goalie_events = events
        
        return goalie_events

    def _get_team_identifier_for_events(self, team_id):
        """
        Get the correct team identifier to use when filtering events.
        Enhanced version with comprehensive error handling, logging, and fallback handling.
        
        Args:
            team_id (str): Team ID from games/teams data
            
        Returns:
            str: Team identifier used in events data, or fallback identifier if mapping fails
        """
        try:
            # Validate input
            if team_id is None or team_id == '':
                self.logger.error("Invalid team_id provided: None or empty string")
                return 'your_team'  # Fallback to prevent calculation errors
            
            self.logger.info(f"Starting team identifier mapping for team_id: '{team_id}'")
            
            # Get all unique teams from events to understand the mapping
            try:
                events = self.sheets_service.get_events()
                if events is None or events.empty:
                    self.logger.error("No events data available for team identifier mapping")
                    return 'your_team'
                
                if 'Team' not in events.columns:
                    self.logger.error(f"Team column not found in events data. Available columns: {list(events.columns)}")
                    return 'your_team'
                
                unique_event_teams = events['Team'].unique()
                self.logger.debug(f"Available teams in events: {unique_event_teams}")
                
            except Exception as e:
                self.logger.error(f"Failed to retrieve events data for team mapping: {str(e)}")
                return 'your_team'
            
            print(f"=== TEAM IDENTIFIER MAPPING ===")
            print(f"Available teams in events: {unique_event_teams}")
            print(f"Looking for team_id: '{team_id}'")
            
            # Method 1: Try direct match first
            if team_id in unique_event_teams:
                self.logger.info(f"Direct match found for team_id '{team_id}'")
                print(f"✅ Direct match found: {team_id}")
                return team_id
            
            # Method 2: Try normalized TeamID matching
            try:
                normalized_team_id = self._normalize_team_name(team_id)
                for event_team in unique_event_teams:
                    normalized_event_team = self._normalize_team_name(event_team)
                    if normalized_team_id == normalized_event_team:
                        self.logger.info(f"Normalized TeamID match found: '{team_id}' -> '{event_team}'")
                        print(f"✅ Normalized TeamID match found: '{team_id}' -> '{event_team}'")
                        print(f"   (normalized: '{normalized_team_id}' == '{normalized_event_team}')")
                        return event_team
            except Exception as e:
                self.logger.warning(f"Error in normalized team ID matching: {str(e)}")
            
            # Method 3: Try to find a mapping based on team names
            try:
                teams = self.sheets_service.get_teams()
                if teams is None or teams.empty:
                    self.logger.warning("No teams data available for name-based mapping")
                else:
                    team_row = teams[teams['TeamID'] == team_id]
                    
                    if not team_row.empty:
                        team_name = team_row.iloc[0]['TeamName']
                        self.logger.debug(f"Team name from Teams sheet: '{team_name}'")
                        print(f"Team name from Teams sheet: '{team_name}'")
                        
                        # Method 3a: Check if team name appears in events (original logic)
                        try:
                            for event_team in unique_event_teams:
                                if (team_name and event_team and 
                                    (team_name.lower() in event_team.lower() or event_team.lower() in team_name.lower())):
                                    self.logger.info(f"Team name substring match found: '{team_id}' -> '{event_team}' (via team name: '{team_name}')")
                                    print(f"✅ Team name substring match found: '{team_id}' -> '{event_team}' (via team name: '{team_name}')")
                                    return event_team
                        except Exception as e:
                            self.logger.warning(f"Error in team name substring matching: {str(e)}")
                        
                        # Method 3b: Try normalized team name matching
                        try:
                            normalized_team_name = self._normalize_team_name(team_name)
                            for event_team in unique_event_teams:
                                normalized_event_team = self._normalize_team_name(event_team)
                                if normalized_team_name == normalized_event_team:
                                    self.logger.info(f"Normalized team name match found: '{team_id}' -> '{event_team}'")
                                    print(f"✅ Normalized team name match found: '{team_id}' -> '{event_team}'")
                                    print(f"   (team name '{team_name}' normalized: '{normalized_team_name}' == '{normalized_event_team}')")
                                    return event_team
                        except Exception as e:
                            self.logger.warning(f"Error in normalized team name matching: {str(e)}")
                        
                        # Method 3c: Try partial normalized matching (team name contains event team or vice versa)
                        try:
                            for event_team in unique_event_teams:
                                normalized_event_team = self._normalize_team_name(event_team)
                                if (normalized_team_name in normalized_event_team or 
                                    normalized_event_team in normalized_team_name) and len(normalized_event_team) > 2:
                                    self.logger.info(f"Partial normalized match found: '{team_id}' -> '{event_team}'")
                                    print(f"✅ Partial normalized match found: '{team_id}' -> '{event_team}'")
                                    print(f"   ('{normalized_team_name}' <-> '{normalized_event_team}')")
                                    return event_team
                        except Exception as e:
                            self.logger.warning(f"Error in partial normalized matching: {str(e)}")
                    else:
                        self.logger.warning(f"Team ID '{team_id}' not found in Teams sheet")
                        
            except Exception as e:
                self.logger.error(f"Error accessing teams data for mapping: {str(e)}")
            
            # Special handling for common patterns
            try:
                if 'your_team' == team_id and len(unique_event_teams) > 0:
                    # Find the team that's not 'opponent'
                    non_opponent_teams = [t for t in unique_event_teams if t.lower() != 'opponent']
                    if non_opponent_teams:
                        mapped_team = non_opponent_teams[0]
                        self.logger.info(f"Special 'your_team' mapping applied: {mapped_team}")
                        print(f"✅ Special 'your_team' mapping: {mapped_team}")
                        return mapped_team
            except Exception as e:
                self.logger.warning(f"Error in special pattern matching: {str(e)}")
            
            # Enhanced fallback handling
            self.logger.warning(f"No mapping found for team_id '{team_id}' in events data")
            print(f"⚠️  No mapping found for '{team_id}' in events data")
            
            # Try to use the most common team in events as fallback
            fallback_team = 'your_team'  # Default fallback
            try:
                if len(unique_event_teams) > 0:
                    # Use the first non-opponent team as fallback
                    non_opponent_teams = [t for t in unique_event_teams if t.lower() != 'opponent']
                    if non_opponent_teams:
                        fallback_team = non_opponent_teams[0]
                        self.logger.info(f"Using first available team as fallback: '{fallback_team}'")
                    else:
                        fallback_team = unique_event_teams[0]
                        self.logger.info(f"Using first team in events as fallback: '{fallback_team}'")
            except Exception as e:
                self.logger.warning(f"Error determining fallback team: {str(e)}")
            
            self.logger.warning(f"Using fallback team identifier '{fallback_team}' for team_id '{team_id}'")
            print(f"   Using '{fallback_team}' as fallback to prevent stats calculation errors")
            print(f"   Note: This team may need events added to the Events sheet")
            
            return fallback_team
            
        except Exception as e:
            self.logger.error(f"Unexpected error in _get_team_identifier_for_events for team_id '{team_id}': {str(e)}")
            return 'your_team'  # Ultimate fallback
    
    def _filter_games_by_date(self, games, include_future=False):
        """
        Filter games to only include those on or before the current date.
        
        Args:
            games (pd.DataFrame): DataFrame containing game data
            include_future (bool): If True, include future games. If False, only past/current games.
            
        Returns:
            pd.DataFrame: Filtered DataFrame containing only completed games
        """
        if games.empty:
            return games
        
        if 'Date' not in games.columns:
            print("WARNING: No Date column found in games data. Returning all games.")
            return games
        
        # Get current date
        current_date = date.today()
        print(f"Current date for filtering: {current_date}")
        
        # Create a copy to avoid pandas warnings
        filtered_games = games.copy()
        
        # Parse dates and filter
        def parse_game_date(date_str):
            """Parse various date formats"""
            if pd.isna(date_str) or date_str == '':
                return None
            
            # Try different date formats
            date_formats = [
                '%m/%d/%Y',    # MM/DD/YYYY
                '%Y-%m-%d',    # YYYY-MM-DD
                '%d/%m/%Y',    # DD/MM/YYYY
                '%m-%d-%Y',    # MM-DD-YYYY
                '%Y/%m/%d',    # YYYY/MM/DD
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(str(date_str), fmt).date()
                    return parsed_date
                except ValueError:
                    continue
            
            print(f"WARNING: Could not parse date '{date_str}'. Treating as future game.")
            return None
        
        # Apply date parsing
        filtered_games['ParsedDate'] = filtered_games['Date'].apply(parse_game_date)
        
        # Filter based on include_future parameter
        if include_future:
            # Return all games (no filtering)
            result = filtered_games.drop('ParsedDate', axis=1)
        else:
            # Only include games on or before current date
            mask = (filtered_games['ParsedDate'].notna()) & (filtered_games['ParsedDate'] <= current_date)
            result = filtered_games[mask].drop('ParsedDate', axis=1)
            
            print(f"Date filtering: {len(result)} games out of {len(games)} are completed (on or before {current_date})")
        
        return result
    
    def _filter_games_by_type(self, games, game_type=None):
        """
        Filter games by game type.
        
        Args:
            games (pd.DataFrame): DataFrame containing game data
            game_type (str, optional): Game type to filter by (E, R, T). If None, returns all games.
            
        Returns:
            pd.DataFrame: Filtered DataFrame containing only games of the specified type
        """
        if games.empty or game_type is None:
            return games
        
        if 'GameType' not in games.columns:
            print("WARNING: No GameType column found in games data. Returning all games.")
            return games
        
        # Filter by game type
        filtered_games = games[games['GameType'] == game_type]
        print(f"Game type filtering: {len(filtered_games)} games out of {len(games)} are of type '{game_type}'")
        
        return filtered_games
    
    def _calculate_game_scores(self, game_id, events_df, team_identifier, game_type_filter=None):
        """
        Calculate goals for and against for a specific game with proper event filtering.
        Enhanced with comprehensive error handling and logging.
        
        Args:
            game_id (str): The game ID to calculate scores for
            events_df (pd.DataFrame): DataFrame containing all events
            team_identifier (str): Team identifier used in events data
            game_type_filter (str, optional): Game type to filter events by (E, R, T). 
                                            If None, includes all events regardless of game type.
            
        Returns:
            tuple: (goals_for, goals_against) as integers
        """
        try:
            # Log calculation context
            self.logger.info(f"Calculating scores for game {game_id} with team '{team_identifier}' and filter '{game_type_filter}'")
            
            # Validate inputs
            if game_id is None or game_id == '':
                self.logger.error(f"Invalid game_id provided: '{game_id}'")
                return 0, 0
            
            if events_df is None or events_df.empty:
                self.logger.warning(f"No events data provided for game {game_id}")
                return 0, 0
            
            if team_identifier is None or team_identifier == '':
                self.logger.error(f"Invalid team_identifier provided: '{team_identifier}' for game {game_id}")
                return 0, 0
            
            # Validate required columns exist
            required_columns = ['GameID', 'IsGoal', 'Team']
            missing_columns = [col for col in required_columns if col not in events_df.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns in events data: {missing_columns}")
                return 0, 0
            
            # Get events for this specific game
            try:
                game_events = events_df[events_df['GameID'] == game_id]
                self.logger.debug(f"Found {len(game_events)} total events for game {game_id}")
            except Exception as e:
                self.logger.error(f"Failed to filter events by GameID for game {game_id}: {str(e)}")
                return 0, 0
            
            # Apply game type filtering if specified
            if game_type_filter is not None:
                try:
                    # Validate game type filter
                    valid_game_types = ['E', 'R', 'T']
                    if game_type_filter not in valid_game_types:
                        self.logger.warning(f"Invalid game type filter '{game_type_filter}' for game {game_id}. Valid types: {valid_game_types}")
                        # Continue with unfiltered events as fallback
                    else:
                        # Filter events to only include those matching the game type filter
                        if 'GameType' in game_events.columns:
                            original_count = len(game_events)
                            game_events = game_events[game_events['GameType'] == game_type_filter]
                            filtered_count = len(game_events)
                            self.logger.info(f"Filtered events for game {game_id} by game type '{game_type_filter}': {filtered_count} events (from {original_count})")
                            print(f"Filtered events for game {game_id} by game type '{game_type_filter}': {filtered_count} events")
                        else:
                            self.logger.warning(f"GameType column not found in events for game {game_id}. Using all events as fallback")
                            print(f"WARNING: GameType column not found in events. Using all events for game {game_id}")
                except Exception as e:
                    self.logger.error(f"Error applying game type filter '{game_type_filter}' for game {game_id}: {str(e)}")
                    # Continue with unfiltered events as fallback
            else:
                # "All Games" case - include all events regardless of game type
                self.logger.info(f"Using all events for game {game_id} (All Games filter): {len(game_events)} events")
                print(f"Using all events for game {game_id} (All Games filter): {len(game_events)} events")
            
            # Calculate goals using filtered events with error handling
            try:
                # Validate team identifier exists in events
                unique_teams = game_events['Team'].unique() if not game_events.empty else []
                if team_identifier not in unique_teams and len(unique_teams) > 0:
                    self.logger.warning(f"Team identifier '{team_identifier}' not found in game {game_id} events. Available teams: {unique_teams}")
                    # Continue with calculation - may result in 0 goals for this team
                
                # Debug IsGoal column before calculation
                if 'IsGoal' in game_events.columns:
                    isgoal_dtype = game_events['IsGoal'].dtype
                    isgoal_values = game_events['IsGoal'].unique()
                    print(f"DEBUG: Game {game_id} IsGoal column - dtype: {isgoal_dtype}, values: {isgoal_values}")
                    
                    # Count events by IsGoal value
                    if len(game_events) > 0:
                        isgoal_counts = game_events['IsGoal'].value_counts()
                        print(f"DEBUG: Game {game_id} IsGoal distribution: {isgoal_counts.to_dict()}")
                        
                        # Show sample events for debugging
                        print(f"DEBUG: Sample events for game {game_id}:")
                        for i, (_, event) in enumerate(game_events.head(3).iterrows()):
                            event_type = event.get('EventType', 'Unknown')
                            is_goal = event.get('IsGoal', 'Missing')
                            team = event.get('Team', 'Unknown')
                            print(f"  Event {i+1}: {event_type} by {team}, IsGoal={is_goal} ({type(is_goal).__name__})")
                
                # Calculate goals for the team
                goals_for_mask = (game_events['IsGoal'] == True) & (game_events['Team'] == team_identifier)
                goals_for = len(game_events[goals_for_mask])
                
                # Calculate goals against the team
                goals_against_mask = (game_events['IsGoal'] == True) & (game_events['Team'] != team_identifier)
                goals_against = len(game_events[goals_against_mask])
                
                # Debug the mask results
                print(f"DEBUG: Game {game_id} goal masks - goals_for_mask: {goals_for_mask.sum()}, goals_against_mask: {goals_against_mask.sum()}")
                
                # Log calculation results
                self.logger.info(f"Game {game_id} score calculation complete: {goals_for}-{goals_against} (team: {team_identifier}, filter: {game_type_filter})")
                print(f"Game {game_id} scores (filter: {game_type_filter}): {goals_for}-{goals_against}")
                
                # Validate results are reasonable
                if goals_for < 0 or goals_against < 0:
                    self.logger.error(f"Invalid negative scores calculated for game {game_id}: {goals_for}-{goals_against}")
                    return 0, 0
                
                if goals_for > 50 or goals_against > 50:
                    self.logger.warning(f"Unusually high scores calculated for game {game_id}: {goals_for}-{goals_against}")
                
                return goals_for, goals_against
                
            except Exception as e:
                self.logger.error(f"Error calculating goals for game {game_id}: {str(e)}")
                return 0, 0
                
        except Exception as e:
            self.logger.error(f"Unexpected error in _calculate_game_scores for game {game_id}: {str(e)}")
            return 0, 0
    
    def _filter_events_by_game_type(self, events_df, game_type_filter=None):
        """
        Filter events by game type with proper handling of "All Games" case.
        Enhanced with comprehensive error handling and logging.
        
        This method provides centralized event filtering logic that handles:
        - "All Games" case (None filter) - returns all events regardless of game type
        - Specific game type filtering (E, R, T) - returns only matching events
        - Validation of game type values with fallback behavior
        - Graceful handling of missing GameType column or empty data
        - Comprehensive error handling and logging
        
        Args:
            events_df (pd.DataFrame): DataFrame containing events to filter
            game_type_filter (str, optional): Game type to filter by:
                                            - 'E': Exhibition games
                                            - 'R': Regular Season games  
                                            - 'T': Tournament games
                                            - None: All Games (no filtering)
            
        Returns:
            pd.DataFrame: Filtered events DataFrame. Returns original DataFrame if:
                         - events_df is empty
                         - game_type_filter is None (All Games)
                         - game_type_filter is invalid (fallback behavior)
                         - GameType column is missing (fallback behavior)
                         - Any error occurs during filtering
        
        Raises:
            None: Method uses fallback behavior instead of raising exceptions
        """
        try:
            # Handle empty DataFrame
            if events_df is None or events_df.empty:
                self.logger.warning("Event filtering: Empty or None events DataFrame provided")
                print("Event filtering: Empty events DataFrame provided, returning as-is")
                return events_df if events_df is not None else pd.DataFrame()
            
            # Handle "All Games" case (None game_type)
            if game_type_filter is None:
                self.logger.info(f"Event filtering: All Games selected - including all {len(events_df)} events regardless of game type")
                print("Event filtering: All Games selected - including all events regardless of game type")
                return events_df
            
            # Validate game type parameter
            valid_game_types = ['E', 'R', 'T']  # Exhibition, Regular Season, Tournament
            if game_type_filter not in valid_game_types:
                self.logger.warning(f"Invalid game type filter '{game_type_filter}'. Valid types: {valid_game_types}. Using all events as fallback.")
                print(f"WARNING: Invalid game type '{game_type_filter}'. Valid types: {valid_game_types}. Using all events as fallback.")
                return events_df
            
            # Check for GameType column existence
            if 'GameType' not in events_df.columns:
                self.logger.warning(f"GameType column not found in events data. Available columns: {list(events_df.columns)}. Returning all events.")
                print("WARNING: GameType column not found in events data. Returning all events.")
                print(f"Available columns: {list(events_df.columns)}")
                return events_df
            
            # Filter by specific game type
            try:
                original_count = len(events_df)
                filtered_events = events_df[events_df['GameType'] == game_type_filter]
                filtered_count = len(filtered_events)
                
                self.logger.info(f"Event filtering: {filtered_count} events out of {original_count} match game type '{game_type_filter}'")
                print(f"Event filtering: {filtered_count} events out of {original_count} match game type '{game_type_filter}'")
                
                # Additional validation - warn if no events found for valid game type
                if filtered_count == 0:
                    self.logger.info(f"No events found for game type '{game_type_filter}'. This may be expected if no games of this type have been played.")
                    print(f"INFO: No events found for game type '{game_type_filter}'. This may be expected if no games of this type have been played.")
                
                # Validate filtered DataFrame structure
                if not filtered_events.empty and 'GameType' in filtered_events.columns:
                    unique_game_types = filtered_events['GameType'].unique()
                    if len(unique_game_types) > 1:
                        self.logger.warning(f"Filtered events contain multiple game types: {unique_game_types}. Expected only '{game_type_filter}'")
                
                return filtered_events
                
            except KeyError as e:
                self.logger.error(f"KeyError when filtering events by game type '{game_type_filter}': {str(e)}")
                print(f"ERROR: KeyError when filtering events by game type '{game_type_filter}': {str(e)}")
                print("Falling back to returning all events")
                return events_df
                
            except Exception as e:
                self.logger.error(f"Unexpected error filtering events by game type '{game_type_filter}': {str(e)}")
                print(f"ERROR: Failed to filter events by game type '{game_type_filter}': {str(e)}")
                print("Falling back to returning all events")
                return events_df
                
        except Exception as e:
            self.logger.error(f"Critical error in _filter_events_by_game_type: {str(e)}")
            print(f"CRITICAL ERROR in event filtering: {str(e)}")
            # Return empty DataFrame as ultimate fallback to prevent further errors
            return pd.DataFrame() if events_df is None else events_df
    
    def _get_game_type_from_session(self):
        """
        Get the currently selected game type from the Flask session.
        
        Returns:
            str: The selected game type code, or None if not set
        """
        try:
            from flask import session
            return session.get('selected_game_type')
        except RuntimeError:
            # Working outside of request context (e.g., in tests)
            return None
    
    def _set_game_type_in_session(self, game_type):
        """
        Set the currently selected game type in the Flask session.
        
        Args:
            game_type (str): The game type code to set
        """
        from flask import session
        from config import is_valid_game_type, DEFAULT_GAME_TYPE
        
        # Validate game type
        if game_type and is_valid_game_type(game_type):
            session['selected_game_type'] = game_type
        else:
            session['selected_game_type'] = DEFAULT_GAME_TYPE
        
        print(f"Set game type in session: {session['selected_game_type']}")
    
    def get_players(self, team_id=None):
        """
        Get all players, optionally filtered by team.
        
        Args:
            team_id (str, optional): Team ID to filter by
            
        Returns:
            pd.DataFrame: DataFrame containing player data
        """
        players = self.sheets_service.get_players()
        
        if team_id is not None:
            players = self._filter_by_team(players, team_id)
        
        return players
    
    def get_games(self, team_id=None, game_type=None):
        """
        Get all games with calculated goal statistics, optionally filtered by team and game type.
        Enhanced with comprehensive error handling and logging.
        
        Args:
            team_id (str, optional): Team ID to filter by
            game_type (str, optional): Game type to filter by (E, R, T). If None, returns all games.
            
        Returns:
            pd.DataFrame: DataFrame containing game data with calculated columns
        """
        try:
            self.logger.info(f"Getting games with team_id='{team_id}', game_type='{game_type}'")
            
            # Validate input parameters
            if team_id is not None and (not isinstance(team_id, str) or team_id.strip() == ''):
                self.logger.error(f"Invalid team_id parameter: '{team_id}'. Must be a non-empty string or None.")
                return pd.DataFrame()
            
            if game_type is not None and game_type not in ['E', 'R', 'T']:
                self.logger.error(f"Invalid game_type parameter: '{game_type}'. Must be 'E', 'R', 'T', or None.")
                return pd.DataFrame()
            
            # Create a cache key based on team_id and game_type
            cache_key = f"games_{team_id}_{game_type}" if team_id or game_type else "games_all"
            
            # Check if we have cached results
            if not hasattr(self, '_games_calculated_cache'):
                self._games_calculated_cache = {}
            
            if cache_key in self._games_calculated_cache:
                self.logger.debug(f"Using cached games data for {cache_key}")
                print(f"Using cached games data for {cache_key}")
                return self._games_calculated_cache[cache_key].copy()
            
            # Get data from sheets service with error handling
            try:
                games = self.sheets_service.get_games()
                events = self.sheets_service.get_events()
                
                if games is None:
                    self.logger.error("Failed to retrieve games data from sheets service - received None")
                    return pd.DataFrame()
                
                if events is None:
                    self.logger.error("Failed to retrieve events data from sheets service - received None")
                    return pd.DataFrame()
                
                if games.empty:
                    self.logger.warning("Games data is empty - no games available")
                    return pd.DataFrame()
                
                if events.empty:
                    self.logger.warning("Events data is empty - no events available for score calculation")
                    # Continue with empty events - games will have 0-0 scores
                    
            except Exception as e:
                self.logger.error(f"Error retrieving data from sheets service: {str(e)}")
                return pd.DataFrame()
            
            # Filter games by team if specified
            if team_id is not None:
                try:
                    original_count = len(games)
                    games = self._filter_by_team(games, team_id)
                    self.logger.info(f"Filtered games by team '{team_id}': {len(games)} games (from {original_count})")
                except Exception as e:
                    self.logger.error(f"Error filtering games by team '{team_id}': {str(e)}")
                    return pd.DataFrame()
            
            # Filter games by game type if specified
            if game_type is not None:
                try:
                    original_count = len(games)
                    games = self._filter_games_by_type(games, game_type)
                    self.logger.info(f"Filtered games by type '{game_type}': {len(games)} games (from {original_count})")
                except Exception as e:
                    self.logger.error(f"Error filtering games by type '{game_type}': {str(e)}")
                    return pd.DataFrame()
            
            # Print columns for debugging
            self.logger.debug(f"Games columns: {games.columns.tolist()}")
            print("Games columns:", games.columns.tolist())
            
            # Get team identifier for event filtering using the new mapping method
            team_identifier = None
            if team_id is not None:
                try:
                    team_identifier = self._get_team_identifier_for_events(team_id)
                    self.logger.info(f"Mapped team identifier: '{team_identifier}' for team ID: '{team_id}'")
                    print(f"Mapped team identifier: '{team_identifier}' for team ID: '{team_id}'")
                except Exception as e:
                    self.logger.error(f"Error mapping team identifier for team_id '{team_id}': {str(e)}")
                    team_identifier = 'your_team'  # Fallback
            else:
                # For backward compatibility, try to get the first team or use fallback
                try:
                    teams = self.sheets_service.get_teams()
                    if teams is not None and not teams.empty:
                        first_team_id = teams.iloc[0]['TeamID']
                        team_identifier = self._get_team_identifier_for_events(first_team_id)
                        self.logger.info(f"Using first team identifier: '{team_identifier}' (from team ID: '{first_team_id}')")
                        print(f"Using first team identifier: '{team_identifier}' (from team ID: '{first_team_id}')")
                    else:
                        team_identifier = 'your_team'
                        self.logger.warning("No teams data available, using fallback team identifier")
                        print(f"Using fallback team identifier: '{team_identifier}'")
                except Exception as e:
                    self.logger.error(f"Error getting fallback team identifier: {str(e)}")
                    team_identifier = 'your_team'
                    print(f"Using fallback team identifier: '{team_identifier}'")
            
            # Validate team identifier
            if team_identifier is None or team_identifier == '':
                self.logger.error("Failed to determine valid team identifier")
                team_identifier = 'your_team'
            
            # Add GoalsFor and GoalsAgainst columns
            if not games.empty:
                try:
                    # Create a copy to avoid pandas warnings
                    games = games.copy()
                    # Initialize columns with zeros
                    games['GoalsFor'] = 0
                    games['GoalsAgainst'] = 0
                    
                    # Validate required columns exist in games
                    required_game_columns = ['ID']
                    missing_columns = [col for col in required_game_columns if col not in games.columns]
                    if missing_columns:
                        self.logger.error(f"Required columns missing from games data: {missing_columns}. Available columns: {list(games.columns)}")
                        return pd.DataFrame()
                    
                    # Validate team identifier before proceeding
                    if team_identifier is None or team_identifier == '':
                        self.logger.error("Invalid team identifier for score calculation - cannot proceed")
                        # Use fallback but log the issue
                        team_identifier = 'your_team'
                        self.logger.warning(f"Using fallback team identifier: '{team_identifier}'")
                    
                    # Calculate goals for each game using the new centralized method
                    self.logger.info(f"Calculating goals for {len(games)} games (team: {team_identifier}, game_type: {game_type})")
                    print(f"Calculating goals for {len(games)} games (team: {team_identifier}, game_type: {game_type})")
                    
                    successful_calculations = 0
                    failed_calculations = 0
                    calculation_errors = []
                    
                    for idx, game in games.iterrows():
                        try:
                            game_id = game.get('ID')
                            if game_id is None or game_id == '':
                                self.logger.error(f"Invalid game ID at index {idx}: '{game_id}'")
                                failed_calculations += 1
                                calculation_errors.append(f"Invalid game ID: '{game_id}'")
                                continue
                            
                            goals_for, goals_against = self._calculate_game_scores(
                                game_id, events, team_identifier, game_type
                            )
                            
                            # Validate calculated scores
                            if not isinstance(goals_for, (int, float)) or not isinstance(goals_against, (int, float)):
                                self.logger.error(f"Invalid score types returned for game {game_id}: goals_for={type(goals_for)}, goals_against={type(goals_against)}")
                                goals_for, goals_against = 0, 0
                                failed_calculations += 1
                                calculation_errors.append(f"Invalid score types for game {game_id}")
                            elif goals_for < 0 or goals_against < 0:
                                self.logger.error(f"Negative scores calculated for game {game_id}: {goals_for}-{goals_against}")
                                goals_for, goals_against = 0, 0
                                failed_calculations += 1
                                calculation_errors.append(f"Negative scores for game {game_id}")
                            else:
                                successful_calculations += 1
                            
                            games.at[idx, 'GoalsFor'] = int(goals_for)
                            games.at[idx, 'GoalsAgainst'] = int(goals_against)
                            
                        except Exception as e:
                            self.logger.error(f"Error calculating scores for game {game.get('ID', 'unknown')}: {str(e)}")
                            # Keep default values (0, 0) for failed calculations
                            games.at[idx, 'GoalsFor'] = 0
                            games.at[idx, 'GoalsAgainst'] = 0
                            failed_calculations += 1
                            calculation_errors.append(f"Exception for game {game.get('ID', 'unknown')}: {str(e)}")
                    
                    # Log comprehensive calculation summary
                    self.logger.info(f"Goal calculation summary: {successful_calculations} successful, {failed_calculations} failed out of {len(games)} total games")
                    if failed_calculations > 0:
                        self.logger.warning(f"Failed calculations details: {calculation_errors[:5]}")  # Log first 5 errors
                        if len(calculation_errors) > 5:
                            self.logger.warning(f"... and {len(calculation_errors) - 5} more errors")
                    
                    print(f"Completed goal calculations for {len(games)} games")
                    
                    if not games.empty:
                        # Log sample of calculated data for verification
                        sample_game = games.iloc[0]
                        self.logger.debug(f"Sample calculated game data: ID={sample_game.get('ID')}, GoalsFor={sample_game.get('GoalsFor')}, GoalsAgainst={sample_game.get('GoalsAgainst')}")
                        print("Sample game data:", games.iloc[0].to_dict())
                        
                except Exception as e:
                    self.logger.error(f"Critical error during goal calculations: {str(e)}")
                    # Return games without calculated scores rather than failing completely
                    if 'GoalsFor' not in games.columns:
                        games['GoalsFor'] = 0
                        self.logger.warning("Added default GoalsFor column with zeros due to calculation failure")
                    if 'GoalsAgainst' not in games.columns:
                        games['GoalsAgainst'] = 0
                        self.logger.warning("Added default GoalsAgainst column with zeros due to calculation failure")
            else:
                self.logger.info("No games to process (empty games DataFrame)")
            
            # Always ensure Result column exists (after GoalsFor/GoalsAgainst are calculated)
            try:
                games = self._ensure_result_column(games)
            except Exception as e:
                self.logger.error(f"Error ensuring Result column: {str(e)}")
                # Add basic Result column as fallback
                if not games.empty and 'Result' not in games.columns:
                    games['Result'] = 'Unknown'
                    self.logger.warning("Added fallback Result column due to calculation error")
            
            # Cache the results with enhanced error handling
            try:
                # Validate games DataFrame before caching
                if games is not None and not games.empty:
                    # Ensure cache dictionary exists
                    if not hasattr(self, '_games_calculated_cache'):
                        self._games_calculated_cache = {}
                    
                    # Create a deep copy for caching to prevent reference issues
                    cached_games = games.copy()
                    
                    # Validate cache key
                    if cache_key and isinstance(cache_key, str):
                        # Check cache size before adding new entry
                        self._manage_cache_size_before_add()
                        
                        self._games_calculated_cache[cache_key] = cached_games
                        self.logger.info(f"Successfully cached {len(cached_games)} games for key '{cache_key}'")
                        print(f"Cached games data for {cache_key}")
                        
                        # Check if cache management is needed after adding
                        self._manage_cache_size_after_add()
                    else:
                        self.logger.error(f"Invalid cache key for games caching: '{cache_key}'")
                else:
                    self.logger.warning(f"Cannot cache empty or None games DataFrame for key '{cache_key}'")
                    
            except Exception as e:
                self.logger.error(f"Failed to cache games data for {cache_key}: {str(e)}")
                # Continue without caching - not a critical failure
            
            return games
            
        except Exception as e:
            self.logger.error(f"Unexpected error in get_games: {str(e)}")
            return pd.DataFrame()  # Return empty DataFrame as ultimate fallback
    
    def clear_games_cache(self, team_id=None, game_type=None):
        """
        Clear cached games data with enhanced error handling and logging.
        
        Args:
            team_id (str, optional): If specified, only clear cache for this team
            game_type (str, optional): If specified, only clear cache for this game type
        """
        try:
            if not hasattr(self, '_games_calculated_cache'):
                self.logger.info("No games cache to clear - cache not initialized")
                return
            
            if not self._games_calculated_cache:
                self.logger.info("Games cache is already empty")
                return
            
            original_cache_size = len(self._games_calculated_cache)
            
            if team_id is None and game_type is None:
                # Clear all cache
                self._games_calculated_cache.clear()
                self.logger.info(f"Cleared all games cache ({original_cache_size} entries)")
                print("Cleared all games cache")
            else:
                # Clear specific cache entries
                keys_to_remove = []
                
                for cache_key in self._games_calculated_cache.keys():
                    should_remove = False
                    
                    # Parse cache key format: "games_{team_id}_{game_type}" or "games_all"
                    if cache_key.startswith("games_"):
                        parts = cache_key.split("_")
                        if len(parts) >= 3:
                            cached_team_id = parts[1] if parts[1] != 'None' else None
                            cached_game_type = parts[2] if parts[2] != 'None' else None
                            
                            # Check if this entry should be removed
                            if team_id is not None and cached_team_id == team_id:
                                should_remove = True
                            if game_type is not None and cached_game_type == game_type:
                                should_remove = True
                        elif cache_key == "games_all" and team_id is None and game_type is None:
                            should_remove = True
                    
                    if should_remove:
                        keys_to_remove.append(cache_key)
                
                # Remove identified keys
                for key in keys_to_remove:
                    try:
                        del self._games_calculated_cache[key]
                        self.logger.debug(f"Removed cache entry: {key}")
                    except KeyError:
                        self.logger.warning(f"Cache key {key} not found during removal")
                
                removed_count = len(keys_to_remove)
                self.logger.info(f"Cleared {removed_count} games cache entries (team_id={team_id}, game_type={game_type})")
                print(f"Cleared {removed_count} games cache entries")
                
        except Exception as e:
            self.logger.error(f"Error clearing games cache: {str(e)}")
            # Try to clear all cache as fallback
            try:
                if hasattr(self, '_games_calculated_cache'):
                    self._games_calculated_cache.clear()
                    self.logger.warning("Cleared all games cache as fallback due to error")
            except Exception as fallback_error:
                self.logger.error(f"Failed to clear cache even as fallback: {str(fallback_error)}")
    
    def clear_games_cache_optimized(self, team_id=None, game_type=None, force_clear=False):
        """
        Optimized cache clearing strategy that minimizes performance impact.
        Only clears cache when necessary and implements selective clearing with size management.
        
        Args:
            team_id (str, optional): If specified, only clear cache for this team
            game_type (str, optional): If specified, only clear cache for this game type
            force_clear (bool): If True, forces cache clearing regardless of optimization checks
            
        Returns:
            dict: Information about the cache clearing operation including:
                - cleared: Whether any cache was actually cleared
                - entries_removed: Number of cache entries removed
                - memory_freed: Amount of memory freed in bytes
                - reason: Reason for clearing or not clearing
        """
        try:
            if not hasattr(self, '_games_calculated_cache'):
                self.logger.debug("Optimized cache clear: No cache to clear - not initialized")
                return {"cleared": False, "entries_removed": 0, "memory_freed": 0, "reason": "cache_not_initialized"}
            
            if not self._games_calculated_cache:
                self.logger.debug("Optimized cache clear: Cache is already empty")
                return {"cleared": False, "entries_removed": 0, "memory_freed": 0, "reason": "cache_already_empty"}
            
            # Get current cache info for optimization decisions
            cache_info = self.get_cache_info()
            current_size = cache_info.get('cache_size', 0)
            current_memory = cache_info.get('cache_memory_usage', 0)
            performance_metrics = cache_info.get('cache_performance_metrics', {})
            
            # Define cache size thresholds for optimization
            MAX_CACHE_ENTRIES = 50  # Maximum number of cache entries before forced cleanup
            MAX_CACHE_MEMORY = 100 * 1024 * 1024  # 100MB maximum cache memory
            MIN_EFFICIENCY_THRESHOLD = 70  # Minimum cache efficiency percentage
            
            # Check if cache clearing is necessary (unless forced)
            if not force_clear:
                # Skip clearing if cache is small and efficient
                if (current_size <= 10 and 
                    current_memory <= 10 * 1024 * 1024 and  # 10MB
                    performance_metrics.get('memory_efficiency', 100) >= MIN_EFFICIENCY_THRESHOLD):
                    self.logger.debug(f"Optimized cache clear: Skipping - cache is small and efficient "
                                    f"(size={current_size}, memory={current_memory:,.0f}B, "
                                    f"efficiency={performance_metrics.get('memory_efficiency', 100):.1f}%)")
                    return {"cleared": False, "entries_removed": 0, "memory_freed": 0, "reason": "cache_small_and_efficient"}
                
                # Check if we're clearing the same cache key that was recently cleared
                cache_key = f"games_{team_id}_{game_type}"
                if hasattr(self, '_last_cleared_keys'):
                    if cache_key in self._last_cleared_keys:
                        self.logger.debug(f"Optimized cache clear: Skipping - key '{cache_key}' was recently cleared")
                        return {"cleared": False, "entries_removed": 0, "memory_freed": 0, "reason": "recently_cleared"}
                else:
                    self._last_cleared_keys = set()
            
            # Determine clearing strategy based on cache state
            original_cache_size = len(self._games_calculated_cache)
            memory_before = current_memory
            
            if (current_size >= MAX_CACHE_ENTRIES or 
                current_memory >= MAX_CACHE_MEMORY or 
                performance_metrics.get('memory_efficiency', 100) < MIN_EFFICIENCY_THRESHOLD or
                force_clear):
                
                # Aggressive clearing needed
                if team_id is None and game_type is None:
                    # Clear all cache
                    self._games_calculated_cache.clear()
                    self._last_cleared_keys.clear() if hasattr(self, '_last_cleared_keys') else None
                    entries_removed = original_cache_size
                    reason = "full_clear_due_to_limits" if not force_clear else "full_clear_forced"
                    self.logger.info(f"Optimized cache clear: Cleared all {entries_removed} entries "
                                   f"(reason: {reason}, memory: {memory_before:,.0f}B)")
                else:
                    # Selective clearing with optimization
                    entries_removed = self._selective_cache_clear_optimized(team_id, game_type)
                    reason = "selective_clear_optimized"
                    self.logger.info(f"Optimized cache clear: Selectively cleared {entries_removed} entries "
                                   f"for team_id={team_id}, game_type={game_type}")
            else:
                # Minimal selective clearing
                entries_removed = self._selective_cache_clear_optimized(team_id, game_type)
                reason = "minimal_selective_clear"
                self.logger.debug(f"Optimized cache clear: Minimal selective clearing - {entries_removed} entries removed")
            
            # Calculate memory freed
            post_cache_info = self.get_cache_info()
            memory_after = post_cache_info.get('cache_memory_usage', 0)
            memory_freed = memory_before - memory_after
            
            # Track cleared keys to avoid redundant clearing
            if team_id is not None or game_type is not None:
                cache_key = f"games_{team_id}_{game_type}"
                if not hasattr(self, '_last_cleared_keys'):
                    self._last_cleared_keys = set()
                self._last_cleared_keys.add(cache_key)
                
                # Limit the size of tracked keys to prevent memory growth
                if len(self._last_cleared_keys) > 20:
                    # Remove oldest entries (simple FIFO by converting to list and back)
                    keys_list = list(self._last_cleared_keys)
                    self._last_cleared_keys = set(keys_list[-15:])  # Keep last 15 entries
            
            return {
                "cleared": entries_removed > 0,
                "entries_removed": entries_removed,
                "memory_freed": memory_freed,
                "reason": reason,
                "cache_size_before": original_cache_size,
                "cache_size_after": post_cache_info.get('cache_size', 0),
                "memory_before": memory_before,
                "memory_after": memory_after
            }
            
        except Exception as e:
            self.logger.error(f"Error in optimized cache clearing: {str(e)}")
            # Fallback to regular cache clearing
            try:
                self.clear_games_cache(team_id, game_type)
                return {"cleared": True, "entries_removed": -1, "memory_freed": -1, "reason": "fallback_to_regular_clear", "error": str(e)}
            except Exception as fallback_error:
                self.logger.error(f"Fallback cache clearing also failed: {str(fallback_error)}")
                return {"cleared": False, "entries_removed": 0, "memory_freed": 0, "reason": "clearing_failed", "error": str(e)}
    
    def _selective_cache_clear_optimized(self, team_id=None, game_type=None):
        """
        Helper method for optimized selective cache clearing.
        
        Args:
            team_id (str, optional): Team ID to clear cache for
            game_type (str, optional): Game type to clear cache for
            
        Returns:
            int: Number of cache entries removed
        """
        try:
            keys_to_remove = []
            
            for cache_key in self._games_calculated_cache.keys():
                should_remove = False
                
                # Parse cache key format: "games_{team_id}_{game_type}"
                if cache_key.startswith("games_"):
                    parts = cache_key.split("_")
                    if len(parts) >= 3:
                        cached_team_id = parts[1] if parts[1] != 'None' else None
                        cached_game_type = parts[2] if parts[2] != 'None' else None
                        
                        # More precise matching logic
                        team_match = (team_id is None or cached_team_id == team_id)
                        game_type_match = (game_type is None or cached_game_type == game_type)
                        
                        # Only remove if both conditions match (when specified)
                        if team_id is not None and game_type is not None:
                            should_remove = (cached_team_id == team_id and cached_game_type == game_type)
                        elif team_id is not None:
                            should_remove = (cached_team_id == team_id)
                        elif game_type is not None:
                            should_remove = (cached_game_type == game_type)
                
                if should_remove:
                    keys_to_remove.append(cache_key)
            
            # Remove identified keys
            for key in keys_to_remove:
                try:
                    del self._games_calculated_cache[key]
                    self.logger.debug(f"Optimized selective clear: Removed cache entry {key}")
                except KeyError:
                    self.logger.warning(f"Optimized selective clear: Cache key {key} not found during removal")
            
            return len(keys_to_remove)
            
        except Exception as e:
            self.logger.error(f"Error in selective cache clearing: {str(e)}")
            return 0
    
    def _manage_cache_size_before_add(self):
        """
        Manage cache size before adding a new entry to prevent excessive memory usage.
        Implements proactive cache management with size and memory limits.
        """
        try:
            if not hasattr(self, '_games_calculated_cache') or not self._games_calculated_cache:
                return
            
            cache_info = self.get_cache_info()
            current_size = cache_info.get('cache_size', 0)
            current_memory = cache_info.get('cache_memory_usage', 0)
            
            # Define thresholds
            MAX_ENTRIES_BEFORE_CLEANUP = 40  # Start cleanup before hitting the hard limit
            MAX_MEMORY_BEFORE_CLEANUP = 80 * 1024 * 1024  # 80MB
            
            # Check if proactive cleanup is needed
            if current_size >= MAX_ENTRIES_BEFORE_CLEANUP or current_memory >= MAX_MEMORY_BEFORE_CLEANUP:
                self.logger.info(f"Cache size management: Proactive cleanup triggered - "
                               f"size={current_size}, memory={current_memory:,.0f}B")
                
                # Remove oldest or least efficient cache entries
                self._cleanup_cache_entries(target_reduction=0.3)  # Remove 30% of entries
                
        except Exception as e:
            self.logger.warning(f"Error in proactive cache size management: {str(e)}")
    
    def _manage_cache_size_after_add(self):
        """
        Manage cache size after adding a new entry to ensure limits are maintained.
        Implements reactive cache management for hard limits.
        """
        try:
            if not hasattr(self, '_games_calculated_cache') or not self._games_calculated_cache:
                return
            
            cache_info = self.get_cache_info()
            current_size = cache_info.get('cache_size', 0)
            current_memory = cache_info.get('cache_memory_usage', 0)
            
            # Define hard limits
            MAX_ENTRIES_HARD_LIMIT = 50
            MAX_MEMORY_HARD_LIMIT = 100 * 1024 * 1024  # 100MB
            
            # Check if hard cleanup is needed
            if current_size >= MAX_ENTRIES_HARD_LIMIT or current_memory >= MAX_MEMORY_HARD_LIMIT:
                self.logger.warning(f"Cache size management: Hard limit reached - "
                                  f"size={current_size}, memory={current_memory:,.0f}B")
                
                # More aggressive cleanup
                self._cleanup_cache_entries(target_reduction=0.5)  # Remove 50% of entries
                
        except Exception as e:
            self.logger.warning(f"Error in reactive cache size management: {str(e)}")
    
    def _cleanup_cache_entries(self, target_reduction=0.3):
        """
        Clean up cache entries based on usage patterns and memory efficiency.
        
        Args:
            target_reduction (float): Target percentage of entries to remove (0.0 to 1.0)
        """
        try:
            if not hasattr(self, '_games_calculated_cache') or not self._games_calculated_cache:
                return
            
            current_size = len(self._games_calculated_cache)
            target_removals = max(1, int(current_size * target_reduction))
            
            # Analyze cache entries for cleanup priority
            entry_analysis = []
            
            for key, df in self._games_calculated_cache.items():
                if df is not None and not df.empty:
                    memory_usage = df.memory_usage(deep=True).sum()
                    row_count = len(df)
                    memory_per_row = memory_usage / row_count if row_count > 0 else 0
                    
                    # Calculate cleanup priority (higher = more likely to be removed)
                    # Factors: large memory usage, low efficiency, generic keys
                    priority = 0
                    
                    # Memory factor (larger entries get higher priority for removal)
                    if memory_usage > 5 * 1024 * 1024:  # 5MB
                        priority += 3
                    elif memory_usage > 1 * 1024 * 1024:  # 1MB
                        priority += 2
                    elif memory_usage > 500 * 1024:  # 500KB
                        priority += 1
                    
                    # Efficiency factor (inefficient entries get higher priority)
                    if memory_per_row > 10000:  # High memory per row
                        priority += 2
                    
                    # Key specificity factor (generic keys get higher priority)
                    if 'None' in key or 'all' in key:
                        priority += 1
                    
                    entry_analysis.append({
                        'key': key,
                        'memory_usage': memory_usage,
                        'row_count': row_count,
                        'priority': priority
                    })
                else:
                    # Empty or None entries get highest priority for removal
                    entry_analysis.append({
                        'key': key,
                        'memory_usage': 0,
                        'row_count': 0,
                        'priority': 10
                    })
            
            # Sort by priority (highest first) and remove entries
            entry_analysis.sort(key=lambda x: x['priority'], reverse=True)
            
            removed_count = 0
            total_memory_freed = 0
            
            for entry in entry_analysis[:target_removals]:
                try:
                    key = entry['key']
                    memory_freed = entry['memory_usage']
                    
                    del self._games_calculated_cache[key]
                    removed_count += 1
                    total_memory_freed += memory_freed
                    
                    self.logger.debug(f"Cache cleanup: Removed entry '{key}' "
                                    f"(priority={entry['priority']}, memory={memory_freed:,.0f}B)")
                    
                except KeyError:
                    self.logger.warning(f"Cache cleanup: Entry '{key}' not found during removal")
            
            self.logger.info(f"Cache cleanup completed: Removed {removed_count} entries, "
                           f"freed {total_memory_freed:,.0f} bytes")
            print(f"Cache cleanup: Removed {removed_count} entries, freed {total_memory_freed:,.0f}B")
            
        except Exception as e:
            self.logger.error(f"Error in cache cleanup: {str(e)}")
            # Fallback to simple cleanup
            try:
                if hasattr(self, '_games_calculated_cache') and self._games_calculated_cache:
                    # Remove half the cache entries as emergency cleanup
                    keys_to_remove = list(self._games_calculated_cache.keys())[:len(self._games_calculated_cache)//2]
                    for key in keys_to_remove:
                        try:
                            del self._games_calculated_cache[key]
                        except KeyError:
                            pass
                    self.logger.warning(f"Emergency cache cleanup: Removed {len(keys_to_remove)} entries")
            except Exception as emergency_error:
                self.logger.error(f"Emergency cache cleanup also failed: {str(emergency_error)}")
    def get_cache_info(self):
        """
        Get comprehensive information about the current cache state for debugging and monitoring.
        Enhanced with detailed performance metrics and memory usage analysis.
        
        Returns:
            dict: Dictionary containing detailed cache information including:
                - cache_initialized: Whether cache is properly initialized
                - cache_size: Number of cache entries
                - cache_keys: List of all cache keys
                - cache_memory_usage: Total memory usage in bytes
                - cache_entries_detail: Detailed info about each cache entry
                - cache_performance_metrics: Performance-related metrics
        """
        try:
            if not hasattr(self, '_games_calculated_cache'):
                return {
                    "cache_initialized": False, 
                    "cache_size": 0, 
                    "cache_keys": [],
                    "cache_memory_usage": 0,
                    "cache_entries_detail": {},
                    "cache_performance_metrics": {
                        "total_entries": 0,
                        "empty_entries": 0,
                        "valid_entries": 0,
                        "average_entry_size": 0,
                        "largest_entry_size": 0,
                        "smallest_entry_size": 0
                    }
                }
            
            # Calculate detailed cache metrics
            cache_entries_detail = {}
            total_memory = 0
            valid_entries = 0
            empty_entries = 0
            entry_sizes = []
            
            for key, df in self._games_calculated_cache.items():
                if df is not None and not df.empty:
                    entry_memory = df.memory_usage(deep=True).sum()
                    entry_rows = len(df)
                    cache_entries_detail[key] = {
                        "memory_usage": entry_memory,
                        "row_count": entry_rows,
                        "columns": list(df.columns) if hasattr(df, 'columns') else [],
                        "memory_per_row": entry_memory / entry_rows if entry_rows > 0 else 0
                    }
                    total_memory += entry_memory
                    entry_sizes.append(entry_memory)
                    valid_entries += 1
                else:
                    cache_entries_detail[key] = {
                        "memory_usage": 0,
                        "row_count": 0,
                        "columns": [],
                        "memory_per_row": 0,
                        "status": "empty_or_none"
                    }
                    empty_entries += 1
            
            # Calculate performance metrics
            performance_metrics = {
                "total_entries": len(self._games_calculated_cache),
                "empty_entries": empty_entries,
                "valid_entries": valid_entries,
                "average_entry_size": sum(entry_sizes) / len(entry_sizes) if entry_sizes else 0,
                "largest_entry_size": max(entry_sizes) if entry_sizes else 0,
                "smallest_entry_size": min(entry_sizes) if entry_sizes else 0,
                "memory_efficiency": (valid_entries / len(self._games_calculated_cache)) * 100 if self._games_calculated_cache else 0
            }
            
            cache_info = {
                "cache_initialized": True,
                "cache_size": len(self._games_calculated_cache),
                "cache_keys": list(self._games_calculated_cache.keys()),
                "cache_memory_usage": total_memory,
                "cache_entries_detail": cache_entries_detail,
                "cache_performance_metrics": performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.debug(f"Enhanced cache info: Size={cache_info['cache_size']}, "
                            f"Memory={total_memory:,.0f}B, Valid={valid_entries}, Empty={empty_entries}")
            return cache_info
            
        except Exception as e:
            self.logger.error(f"Error getting enhanced cache info: {str(e)}")
            return {
                "error": str(e), 
                "cache_initialized": False, 
                "cache_size": 0, 
                "cache_keys": [],
                "cache_memory_usage": 0,
                "cache_entries_detail": {},
                "cache_performance_metrics": {"error": str(e)}
            }
    
    def _ensure_result_column(self, games):
        """
        Ensure the Result column exists in the games DataFrame with comprehensive error handling.
        
        Args:
            games (pd.DataFrame): DataFrame containing game data
            
        Returns:
            pd.DataFrame: DataFrame with Result column added if needed
        """
        try:
            # Validate input
            if games is None:
                self.logger.error("Cannot ensure Result column: games DataFrame is None")
                return pd.DataFrame()
            
            if games.empty:
                self.logger.info("Cannot ensure Result column: games DataFrame is empty")
                return games
            
            # Always work with a copy to avoid pandas warnings
            games = games.copy()
            
            # Check if Result column already exists
            if 'Result' in games.columns:
                self.logger.debug("Result column already exists in games DataFrame")
                return games
            
            # Check if we can calculate it
            required_columns = ['GoalsFor', 'GoalsAgainst']
            missing_columns = [col for col in required_columns if col not in games.columns]
            
            if missing_columns:
                self.logger.warning(f"Cannot calculate Result column: missing columns {missing_columns}. Available columns: {list(games.columns)}")
                # Add placeholder Result column
                games['Result'] = 'Unknown'
                self.logger.info(f"Added placeholder Result column to {len(games)} games")
                print("Warning: Could not calculate Result column. Using placeholder values.")
                return games
            
            # Validate data types and values
            try:
                # Check for non-numeric values in score columns
                if not pd.api.types.is_numeric_dtype(games['GoalsFor']):
                    self.logger.warning("GoalsFor column contains non-numeric values, attempting conversion")
                    games['GoalsFor'] = pd.to_numeric(games['GoalsFor'], errors='coerce').fillna(0)
                
                if not pd.api.types.is_numeric_dtype(games['GoalsAgainst']):
                    self.logger.warning("GoalsAgainst column contains non-numeric values, attempting conversion")
                    games['GoalsAgainst'] = pd.to_numeric(games['GoalsAgainst'], errors='coerce').fillna(0)
                
                # Check for negative values
                negative_goals_for = games['GoalsFor'] < 0
                negative_goals_against = games['GoalsAgainst'] < 0
                
                if negative_goals_for.any():
                    self.logger.warning(f"Found {negative_goals_for.sum()} games with negative GoalsFor values, setting to 0")
                    games.loc[negative_goals_for, 'GoalsFor'] = 0
                
                if negative_goals_against.any():
                    self.logger.warning(f"Found {negative_goals_against.sum()} games with negative GoalsAgainst values, setting to 0")
                    games.loc[negative_goals_against, 'GoalsAgainst'] = 0
                
                # Create a new Result column with error handling for each row
                def calculate_result(row):
                    try:
                        goals_for = row['GoalsFor']
                        goals_against = row['GoalsAgainst']
                        
                        # Handle NaN values
                        if pd.isna(goals_for) or pd.isna(goals_against):
                            return 'Unknown'
                        
                        if goals_for > goals_against:
                            return 'W'
                        elif goals_for < goals_against:
                            return 'L'
                        else:
                            return 'T'
                    except Exception as e:
                        self.logger.error(f"Error calculating result for row: {str(e)}")
                        return 'Unknown'
                
                games['Result'] = games.apply(calculate_result, axis=1)
                
                # Validate results
                valid_results = ['W', 'L', 'T', 'Unknown']
                invalid_results = ~games['Result'].isin(valid_results)
                if invalid_results.any():
                    self.logger.warning(f"Found {invalid_results.sum()} games with invalid Result values, setting to 'Unknown'")
                    games.loc[invalid_results, 'Result'] = 'Unknown'
                
                # Log summary
                result_counts = games['Result'].value_counts()
                self.logger.info(f"Added Result column to {len(games)} games: {result_counts.to_dict()}")
                print(f"Added Result column to {len(games)} games")
                
                return games
                
            except Exception as e:
                self.logger.error(f"Error during Result column calculation: {str(e)}")
                # Fallback to placeholder values
                games['Result'] = 'Unknown'
                self.logger.warning(f"Used fallback Result values for {len(games)} games due to calculation error")
                print("Warning: Error calculating Result column. Using placeholder values.")
                return games
                
        except Exception as e:
            self.logger.error(f"Critical error in _ensure_result_column: {str(e)}")
            # Return original games or empty DataFrame as ultimate fallback
            if games is not None and not games.empty:
                if 'Result' not in games.columns:
                    games['Result'] = 'Unknown'
                return games
            else:
                return pd.DataFrame()
    
    def get_events(self):
        """
        Get all events.
        
        Returns:
            pd.DataFrame: DataFrame containing event data
        """
        return self.sheets_service.get_events()
    
    def get_game_roster(self, team_id=None):
        """
        Get all game roster data, optionally filtered by team.
        
        Args:
            team_id (str, optional): Team ID to filter by
            
        Returns:
            pd.DataFrame: DataFrame containing game roster data
        """
        game_roster = self.sheets_service.get_game_roster()
        print(f"Original game roster size: {len(game_roster)}")
        
        # If team_id is specified, filter the game roster to only include games for that team
        if team_id is not None:
            # Get games for the specified team
            games = self.sheets_service.get_games()
            team_games = self._filter_by_team(games, team_id)
            team_game_ids = team_games['ID'].tolist()
            
            # Filter game roster to only include entries for team games
            game_roster = game_roster[game_roster['GameID'].isin(team_game_ids)]
            print(f"Filtered game roster to {len(game_roster)} entries for team {team_id} games")
        
        print(f"Final game roster size: {len(game_roster)}")
        return game_roster
    
    def get_player_by_jersey(self, jersey_number):
        """
        Get a player by jersey number.
        
        Args:
            jersey_number (int): The jersey number
            
        Returns:
            pd.Series: The player data
        """
        players = self.get_players()
        return players[players['JerseyNumber'] == jersey_number].iloc[0] if not players[players['JerseyNumber'] == jersey_number].empty else None
    
    def get_player_by_id(self, player_id):
        """
        Get a player by ID.
        
        Args:
            player_id (str): The player ID
            
        Returns:
            pd.Series: The player data
        """
        players = self.get_players()
        
        # Use centralized helper method for column detection
        id_column = self._get_player_id_column(players)
        if id_column is None:
            return None
        
        matching_players = players[players[id_column] == player_id]
        return matching_players.iloc[0] if not matching_players.empty else None
    
    def get_game_by_id(self, game_id, team_id=None):
        """
        Get a game by ID.
        
        Args:
            game_id (str): The game ID
            team_id (str, optional): Team ID to filter by
            
        Returns:
            pd.Series: The game data
        """
        # Always use team-specific games when team_id is provided to ensure consistent data
        games = self.get_games(team_id)
        matching_games = games[games['ID'] == game_id]
        if not matching_games.empty:
            game = matching_games.iloc[0]
            print(f"get_game_by_id: Found game {game_id} with GoalsFor={game.get('GoalsFor', 'N/A')}, GoalsAgainst={game.get('GoalsAgainst', 'N/A')} (team_id={team_id})")
            return game
        else:
            print(f"get_game_by_id: Game {game_id} not found (team_id={team_id})")
            return None
    
    def get_player_games(self, player_id, team_id=None, include_future=False, game_type=None):
        """
        Get all games a player participated in, optionally filtered by team, date, and game type.
        For goalies, only includes games where they faced at least 1 shot on goal (SOG > 0).
        
        Args:
            player_id (str): The player ID
            team_id (str, optional): Team ID to filter by
            include_future (bool): If True, include future games. If False, only past/current games.
            game_type (str, optional): Game type to filter by (E, R, T). If None, uses all games.
            
        Returns:
            pd.DataFrame: DataFrame containing game data
        """
        # Force refresh game roster to ensure it's up to date, passing team_id for proper filtering
        game_roster = self.get_game_roster(team_id)
        
        # Get games filtered by team and game type if specified
        games = self.get_games(team_id, game_type)
        
        # Apply date filtering to only show completed games by default
        games = self._filter_games_by_date(games, include_future=include_future)
        
        # Check if player is a goalie
        player = self.get_player_by_id(player_id)
        is_goalie = player is not None and player['Position'] == 'G'
        
        # Get game IDs where the player was present
        player_game_ids = game_roster[(game_roster['PlayerID'] == player_id) & 
                                     (game_roster['Status'] == 'Present')]['GameID'].tolist()
        
        print(f"Player {player_id} has {len(player_game_ids)} games in roster (team: {team_id})")
        
        # Filter games by these IDs (games are already team-filtered and date-filtered)
        player_games = games[games['ID'].isin(player_game_ids)]
        print(f"Found {len(player_games)} game records for player {player_id} (team: {team_id}, include_future: {include_future})")
        
        # Special handling for goalies: only count games where they faced at least 1 shot
        if is_goalie and not player_games.empty:
            print(f"Applying goalie-specific filtering for player {player_id} (Position: G)")
            
            # Get events data for filtering
            events = self.get_events()
            
            # Get team identifier for proper event filtering
            if team_id is not None:
                team_identifier = self._get_team_identifier_for_events(team_id)
            else:
                # For backward compatibility, try to get the first team or use fallback
                try:
                    teams = self.sheets_service.get_teams()
                    if not teams.empty:
                        first_team_id = teams.iloc[0]['TeamID']
                        team_identifier = self._get_team_identifier_for_events(first_team_id)
                    else:
                        team_identifier = 'your_team'
                except:
                    team_identifier = 'your_team'
            
            # Filter games to only include those where the goalie faced shots
            valid_game_ids = []
            
            for _, game in player_games.iterrows():
                game_id = game['ID']
                
                # Use the existing helper method to filter events for this goalie and game
                goalie_events = self._filter_goalie_events(events, player_id, game_id)
                
                # Calculate shots against for this game
                shots_events = goalie_events[(goalie_events['EventType'] == 'Shot') & 
                                           (goalie_events['Team'] != team_identifier)]
                
                # Also count goals as shots (if they're not already counted as shots)
                goals_as_shots = goalie_events[(goalie_events['IsGoal'] == True) & 
                                             (goalie_events['Team'] != team_identifier) &
                                             (goalie_events['EventType'] != 'Shot')]
                
                # Total shots against for this game
                shots_against = len(shots_events) + len(goals_as_shots)
                
                # Only include games where the goalie faced at least 1 shot
                if shots_against > 0:
                    valid_game_ids.append(game_id)
                    print(f"  Game {game_id}: {shots_against} shots against - COUNTED")
                else:
                    print(f"  Game {game_id}: 0 shots against - EXCLUDED from GP")
            
            # Filter to only valid games
            player_games = player_games[player_games['ID'].isin(valid_game_ids)]
            print(f"After goalie filtering: {len(player_games)} games count as played for goalie {player_id}")
        
        return player_games
    
    def calculate_plus_minus_for_events(self, player_id, events, team_identifier):
        """
        Calculate plus/minus for a player based on events using the proper decision tree logic.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            team_identifier (str): Team identifier for filtering events
            
        Returns:
            int: Plus/minus value
        """
        def is_player_on_ice(players_str, pid):
            """Helper function to check if player is on ice"""
            if not players_str or pd.isna(players_str):
                return False
            # Try to parse as a list if it's a string representation of a list
            if isinstance(players_str, str):
                try:
                    # Remove brackets and split by commas
                    players_list = players_str.strip('[]').replace(' ', '').split(',')
                    return pid in players_list
                except:
                    # Fallback to simple string contains check
                    return pid in players_str
            return False
        
        plus_minus = 0
        
        # Filter to only goal events where the player was on ice
        goal_events = events[
            (events['IsGoal'] == True) & 
            (events['YourTeamPlayersOnIce'].apply(lambda x: is_player_on_ice(x, player_id)))
        ]
        
        print(f"Processing {len(goal_events)} goal events for player {player_id}")
        
        for _, goal_event in goal_events.iterrows():
            # Check for penalty shot goals first (no plus/minus awarded)
            if goal_event.get('IsPenaltyShot', False):
                print(f"Penalty shot goal - no plus/minus awarded")
                continue
            
            # Get skater counts for decision tree
            scoring_team = goal_event['Team']
            
            # Parse player counts from the event data
            # This is a simplified approach - in a real implementation, you'd need actual skater counts
            # For now, we'll use the GoalSituation field if available, otherwise infer from team
            goal_situation = goal_event.get('GoalSituation', '')
            
            # Apply the decision tree logic
            if 'Power Play' in goal_situation or goal_event.get('IsPowerPlay', False):
                # Rule 1: Power Play Goal (No +/- Awarded)
                print(f"Power play goal - no plus/minus awarded")
                continue
            elif 'Even Strength' in goal_situation or goal_situation == '':
                # Rule 2: Even Strength Goal (+/- Awarded)
                if scoring_team == team_identifier:
                    plus_minus += 1
                    print(f"Even strength goal FOR team - player gets +1")
                else:
                    plus_minus -= 1
                    print(f"Even strength goal AGAINST team - player gets -1")
            elif 'Short Handed' in goal_situation or goal_event.get('IsShortHanded', False):
                # Rule 3: Short-Handed Goal (+/- Awarded)
                if scoring_team == team_identifier:
                    plus_minus += 1
                    print(f"Short-handed goal FOR team - player gets +1")
                else:
                    plus_minus -= 1
                    print(f"Short-handed goal AGAINST team - player gets -1")
            else:
                # Default case - treat as even strength if situation is unclear
                if scoring_team == team_identifier:
                    plus_minus += 1
                    print(f"Unknown situation goal FOR team - treating as even strength, player gets +1")
                else:
                    plus_minus -= 1
                    print(f"Unknown situation goal AGAINST team - treating as even strength, player gets -1")
        
        print(f"Final plus/minus for player {player_id}: {plus_minus}")
        return plus_minus

    def calculate_goals_for_events(self, player_id, events):
        """
        Calculate goals for a player based on events with enhanced error handling.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            
        Returns:
            int: Number of goals scored
        """
        try:
            # Validate inputs
            if player_id is None or player_id == '':
                self.logger.error(f"Invalid player_id for goals calculation: '{player_id}'")
                return 0
            
            if events is None or events.empty:
                self.logger.warning(f"No events data provided for goals calculation for player '{player_id}'")
                return 0
            
            # Check required columns
            required_columns = ['PrimaryPlayerID', 'IsGoal']
            missing_columns = [col for col in required_columns if col not in events.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns for goals calculation: {missing_columns}. Available: {list(events.columns)}")
                return 0
            
            # Filter events for this player
            try:
                player_events = events[events['PrimaryPlayerID'] == player_id]
                self.logger.debug(f"Found {len(player_events)} events for player '{player_id}' in goals calculation")
            except Exception as e:
                self.logger.error(f"Error filtering events by PrimaryPlayerID for player '{player_id}': {str(e)}")
                return 0
            
            # Calculate goals
            try:
                goal_events = player_events[player_events['IsGoal'] == True]
                goals = len(goal_events)
                
                # Validate result
                if goals < 0:
                    self.logger.error(f"Negative goals calculated for player '{player_id}': {goals}")
                    return 0
                
                self.logger.debug(f"Calculated {goals} goals for player '{player_id}'")
                print(f"Calculated {goals} goals for player {player_id}")
                return goals
                
            except Exception as e:
                self.logger.error(f"Error calculating goals from events for player '{player_id}': {str(e)}")
                return 0
                
        except Exception as e:
            self.logger.error(f"Unexpected error in calculate_goals_for_events for player '{player_id}': {str(e)}")
            return 0

    def calculate_assists_for_events(self, player_id, events):
        """
        Calculate assists for a player based on events with enhanced error handling.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            
        Returns:
            int: Number of assists
        """
        try:
            # Validate inputs
            if player_id is None or player_id == '':
                self.logger.error(f"Invalid player_id for assists calculation: '{player_id}'")
                return 0
            
            if events is None or events.empty:
                self.logger.warning(f"No events data provided for assists calculation for player '{player_id}'")
                return 0
            
            # Check required columns
            required_columns = ['AssistPlayer1ID', 'AssistPlayer2ID']
            missing_columns = [col for col in required_columns if col not in events.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns for assists calculation: {missing_columns}. Available: {list(events.columns)}")
                return 0
            
            # Calculate assists with error handling
            try:
                assist1_events = events[events['AssistPlayer1ID'] == player_id]
                primary_assists = len(assist1_events)
                
                assist2_events = events[events['AssistPlayer2ID'] == player_id]
                secondary_assists = len(assist2_events)
                
                total_assists = primary_assists + secondary_assists
                
                # Validate results
                if primary_assists < 0 or secondary_assists < 0 or total_assists < 0:
                    self.logger.error(f"Negative assists calculated for player '{player_id}': primary={primary_assists}, secondary={secondary_assists}, total={total_assists}")
                    return 0
                
                self.logger.debug(f"Calculated {total_assists} assists for player '{player_id}' ({primary_assists} primary + {secondary_assists} secondary)")
                print(f"Calculated {total_assists} assists for player {player_id} ({primary_assists} primary + {secondary_assists} secondary)")
                return total_assists
                
            except Exception as e:
                self.logger.error(f"Error calculating assists from events for player '{player_id}': {str(e)}")
                return 0
                
        except Exception as e:
            self.logger.error(f"Unexpected error in calculate_assists_for_events for player '{player_id}': {str(e)}")
            return 0

    def calculate_points_for_events(self, player_id, events):
        """
        Calculate points (goals + assists) for a player based on events.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            
        Returns:
            int: Number of points (goals + assists)
        """
        goals = self.calculate_goals_for_events(player_id, events)
        assists = self.calculate_assists_for_events(player_id, events)
        points = goals + assists
        print(f"Calculated {points} points for player {player_id} ({goals}G + {assists}A)")
        return points

    def calculate_shots_for_events(self, player_id, events):
        """
        Calculate shots for a player based on events.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            
        Returns:
            int: Number of shots
        """
        player_events = events[events['PrimaryPlayerID'] == player_id]
        shots = len(player_events[player_events['EventType'] == 'Shot'])
        print(f"Calculated {shots} shots for player {player_id}")
        return shots

    def calculate_penalty_minutes_for_events(self, player_id, events):
        """
        Calculate penalty minutes for a player based on events with enhanced error handling.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            
        Returns:
            int: Number of penalty minutes
        """
        try:
            # Validate inputs
            if player_id is None or player_id == '':
                self.logger.error(f"Invalid player_id for penalty minutes calculation: '{player_id}'")
                return 0
            
            if events is None or events.empty:
                self.logger.warning(f"No events data provided for penalty minutes calculation for player '{player_id}'")
                return 0
            
            # Check required columns
            required_columns = ['PrimaryPlayerID', 'EventType']
            missing_columns = [col for col in required_columns if col not in events.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns for penalty minutes calculation: {missing_columns}. Available: {list(events.columns)}")
                return 0
            
            # Calculate penalty minutes with error handling
            try:
                player_events = events[events['PrimaryPlayerID'] == player_id]
                penalty_events = player_events[player_events['EventType'] == 'Penalty']
                
                if penalty_events.empty:
                    self.logger.debug(f"No penalty events found for player '{player_id}'")
                    print(f"Calculated 0 penalty minutes for player {player_id}")
                    return 0
                
                # Check if PenaltyDuration column exists
                if 'PenaltyDuration' not in penalty_events.columns:
                    self.logger.warning(f"PenaltyDuration column not found for penalty calculation for player '{player_id}'. Available columns: {list(penalty_events.columns)}")
                    # Assume standard 2-minute penalties as fallback
                    penalty_minutes = len(penalty_events) * 2
                    self.logger.warning(f"Using fallback calculation: {len(penalty_events)} penalties × 2 minutes = {penalty_minutes} minutes")
                else:
                    # Calculate using actual penalty durations
                    try:
                        penalty_minutes = penalty_events['PenaltyDuration'].sum()
                        
                        # Validate penalty duration values
                        if pd.isna(penalty_minutes):
                            self.logger.warning(f"NaN penalty minutes calculated for player '{player_id}', using fallback")
                            penalty_minutes = len(penalty_events) * 2  # Fallback to 2-minute penalties
                        elif penalty_minutes < 0:
                            self.logger.error(f"Negative penalty minutes calculated for player '{player_id}': {penalty_minutes}")
                            return 0
                        
                    except Exception as e:
                        self.logger.error(f"Error summing penalty durations for player '{player_id}': {str(e)}")
                        # Fallback calculation
                        penalty_minutes = len(penalty_events) * 2
                        self.logger.warning(f"Using fallback calculation due to error: {penalty_minutes} minutes")
                
                penalty_minutes = int(penalty_minutes)  # Ensure integer result
                self.logger.debug(f"Calculated {penalty_minutes} penalty minutes for player '{player_id}' from {len(penalty_events)} penalty events")
                print(f"Calculated {penalty_minutes} penalty minutes for player {player_id}")
                return penalty_minutes
                
            except Exception as e:
                self.logger.error(f"Error calculating penalty minutes from events for player '{player_id}': {str(e)}")
                return 0
                
        except Exception as e:
            self.logger.error(f"Unexpected error in calculate_penalty_minutes_for_events for player '{player_id}': {str(e)}")
            return 0

    def calculate_player_stats(self, player_id, team_id=None, game_type=None):
        """
        Calculate statistics for a player with comprehensive error handling and logging.
        
        Args:
            player_id (str): The player ID
            team_id (str, optional): Team ID to filter by
            game_type (str, optional): Game type to filter by (E, R, T). If None, uses all games.
            
        Returns:
            dict: Dictionary containing player statistics, or None if calculation fails
        """
        try:
            # Validate input parameters
            if player_id is None or player_id == '':
                self.logger.error(f"Invalid player_id provided: '{player_id}'")
                return None
            
            if team_id is not None and (not isinstance(team_id, str) or team_id.strip() == ''):
                self.logger.error(f"Invalid team_id provided: '{team_id}'")
                return None
            
            if game_type is not None and game_type not in ['E', 'R', 'T']:
                self.logger.error(f"Invalid game_type provided: '{game_type}'. Must be 'E', 'R', 'T', or None")
                return None
            
            self.logger.info(f"Calculating player stats for player_id='{player_id}', team_id='{team_id}', game_type='{game_type}'")
            
            # Get player data with error handling
            try:
                player = self.get_player_by_id(player_id)
                if player is None:
                    self.logger.error(f"Player not found with ID: '{player_id}'")
                    return None
            except Exception as e:
                self.logger.error(f"Error retrieving player data for ID '{player_id}': {str(e)}")
                return None
            
            # Get events and games data with error handling
            try:
                events = self.get_events()
                if events is None:
                    self.logger.error("Failed to retrieve events data for player stats calculation")
                    return None
                
                games = self.get_player_games(player_id, team_id, game_type=game_type)
                if games is None:
                    self.logger.warning(f"No games data returned for player '{player_id}' - using empty DataFrame")
                    games = pd.DataFrame()
                    
            except Exception as e:
                self.logger.error(f"Error retrieving events/games data for player '{player_id}': {str(e)}")
                return None
            
            # CRITICAL FIX: Always filter events by game type, even if no games are found
            # This ensures that when filtering by Regular Season but no completed Regular Season games exist,
            # we don't fall back to using ALL events (which was the bug)
            if game_type is not None:
                # Get all games of the specified type for proper event filtering
                all_games_of_type = self.get_games(team_id, game_type)
                if not all_games_of_type.empty:
                    game_ids_of_type = all_games_of_type['ID'].tolist()
                    events = events[events['GameID'].isin(game_ids_of_type)]
                    print(f"Filtered events to {len(events)} events from {len(game_ids_of_type)} games of type '{game_type}'")
                else:
                    # No games of this type exist, so no events should be included
                    events = events[events['GameID'].isin([])]  # Empty filter
                    print(f"No games of type '{game_type}' found - using 0 events for stats calculation")
            else:
                # When game_type is None (All Games), we need to filter events by ALL player games across all game types
                # This fixes the "All Games" aggregation issue where Player #25 showed 0 games played
                if not games.empty:
                    # Only filter by player games if no game type filter is specified
                    game_ids = games['ID'].tolist()
                    events = events[events['GameID'].isin(game_ids)]
                    print(f"Filtered events to {len(events)} events from {len(game_ids)} player games (no game_type filter)")
                else:
                    # CRITICAL FIX: When no games found with current filtering, 
                    # get ALL player games across ALL game types for proper aggregation
                    print(f"No games found for player {player_id} with current filters, trying all game types...")
                    
                    # Get player games for each game type individually and combine
                    all_player_games = []
                    for gt in ['E', 'R', 'T']:  # Exhibition, Regular Season, Tournament
                        gt_games = self.get_player_games(player_id, team_id, game_type=gt)
                        if not gt_games.empty:
                            all_player_games.append(gt_games)
                            print(f"Found {len(gt_games)} games for player {player_id} in game type '{gt}'")
                    
                    if all_player_games:
                        # Combine all games and remove duplicates
                        combined_games = pd.concat(all_player_games, ignore_index=True)
                        combined_games = combined_games.drop_duplicates(subset=['ID'], keep='first')
                        
                        # Filter events by these combined game IDs
                        combined_game_ids = combined_games['ID'].tolist()
                        events = events[events['GameID'].isin(combined_game_ids)]
                        
                        # Update games variable for games_played calculation
                        games = combined_games
                        
                        print(f"FIXED: Combined {len(combined_games)} games across all types for player {player_id}")
                        print(f"Filtered events to {len(events)} events from combined games")
                    else:
                        print(f"No games found for player {player_id} in any game type")
            
            # Get all teams in events
            unique_teams = events['Team'].unique()
            print(f"Unique teams in events: {unique_teams}")
            
            # Get team identifier for event filtering (same as game stats method)
            if team_id is not None:
                team_identifier = self._get_team_identifier_for_events(team_id)
                print(f"Using team identifier: '{team_identifier}' for team ID: '{team_id}'")
            else:
                # For backward compatibility, try to get the first team or use fallback
                try:
                    teams = self.sheets_service.get_teams()
                    if not teams.empty:
                        first_team_id = teams.iloc[0]['TeamID']
                        team_identifier = self._get_team_identifier_for_events(first_team_id)
                        print(f"Using first team identifier: '{team_identifier}' (from team ID: '{first_team_id}')")
                    else:
                        team_identifier = 'your_team'
                        print(f"Using fallback team identifier: '{team_identifier}'")
                except:
                    team_identifier = 'your_team'
                    print(f"Using fallback team identifier: '{team_identifier}'")
            
            # Calculate all stats using centralized functions with filtered events and error handling
            try:
                goals = self.calculate_goals_for_events(player_id, events)
                if not isinstance(goals, (int, float)) or goals < 0:
                    self.logger.warning(f"Invalid goals calculated for player '{player_id}': {goals}. Using 0.")
                    goals = 0
            except Exception as e:
                self.logger.error(f"Error calculating goals for player '{player_id}': {str(e)}")
                goals = 0
            
            try:
                assists = self.calculate_assists_for_events(player_id, events)
                if not isinstance(assists, (int, float)) or assists < 0:
                    self.logger.warning(f"Invalid assists calculated for player '{player_id}': {assists}. Using 0.")
                    assists = 0
            except Exception as e:
                self.logger.error(f"Error calculating assists for player '{player_id}': {str(e)}")
                assists = 0
            
            try:
                points = self.calculate_points_for_events(player_id, events)
                if not isinstance(points, (int, float)) or points < 0:
                    self.logger.warning(f"Invalid points calculated for player '{player_id}': {points}. Using 0.")
                    points = 0
                
                # Validate points consistency
                expected_points = goals + assists
                if points != expected_points:
                    self.logger.warning(f"Points inconsistency for player '{player_id}': calculated={points}, expected={expected_points}. Using expected value.")
                    points = expected_points
            except Exception as e:
                self.logger.error(f"Error calculating points for player '{player_id}': {str(e)}")
                points = goals + assists  # Fallback calculation
            
            try:
                plus_minus = self.calculate_plus_minus_for_events(player_id, events, team_identifier)
                if not isinstance(plus_minus, (int, float)):
                    self.logger.warning(f"Invalid plus_minus calculated for player '{player_id}': {plus_minus}. Using 0.")
                    plus_minus = 0
            except Exception as e:
                self.logger.error(f"Error calculating plus_minus for player '{player_id}': {str(e)}")
                plus_minus = 0
            
            try:
                shots = self.calculate_shots_for_events(player_id, events)
                if not isinstance(shots, (int, float)) or shots < 0:
                    self.logger.warning(f"Invalid shots calculated for player '{player_id}': {shots}. Using 0.")
                    shots = 0
            except Exception as e:
                self.logger.error(f"Error calculating shots for player '{player_id}': {str(e)}")
                shots = 0
            
            try:
                penalty_minutes = self.calculate_penalty_minutes_for_events(player_id, events)
                if not isinstance(penalty_minutes, (int, float)) or penalty_minutes < 0:
                    self.logger.warning(f"Invalid penalty_minutes calculated for player '{player_id}': {penalty_minutes}. Using 0.")
                    penalty_minutes = 0
            except Exception as e:
                self.logger.error(f"Error calculating penalty_minutes for player '{player_id}': {str(e)}")
                penalty_minutes = 0
            
            # Calculate games played with validation
            try:
                games_played = len(games) if games is not None else 0
                if games_played < 0:
                    self.logger.warning(f"Invalid games_played for player '{player_id}': {games_played}. Using 0.")
                    games_played = 0
            except Exception as e:
                self.logger.error(f"Error calculating games_played for player '{player_id}': {str(e)}")
                games_played = 0
            
            # Calculate goals per game with division by zero protection
            try:
                goals_per_game = goals / games_played if games_played > 0 else 0.0
                if not isinstance(goals_per_game, (int, float)) or goals_per_game < 0:
                    self.logger.warning(f"Invalid goals_per_game calculated for player '{player_id}': {goals_per_game}. Using 0.")
                    goals_per_game = 0.0
            except Exception as e:
                self.logger.error(f"Error calculating goals_per_game for player '{player_id}': {str(e)}")
                goals_per_game = 0.0
            
            # Log calculation summary
            self.logger.info(f"Player stats calculated for '{player_id}': G={goals}, A={assists}, P={points}, +/-={plus_minus}, S={shots}, PIM={penalty_minutes}, GP={games_played}")
            
            # Return comprehensive stats dictionary
            try:
                stats_dict = {
                    'player': player,
                    'goals': int(goals),
                    'assists': int(assists),
                    'points': int(points),
                    'plus_minus': int(plus_minus),
                    'shots': int(shots),
                    'penalty_minutes': int(penalty_minutes),
                    'games_played': int(games_played),
                    'goals_per_game': float(goals_per_game)
                }
                
                self.logger.debug(f"Returning stats dictionary for player '{player_id}': {stats_dict}")
                return stats_dict
                
            except Exception as e:
                self.logger.error(f"Error creating stats dictionary for player '{player_id}': {str(e)}")
                return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error in calculate_player_stats for player '{player_id}': {str(e)}")
            return None
    
    def calculate_player_game_stats(self, player_id, game_id, team_id=None):
        """
        Calculate statistics for a player in a specific game.
        
        Args:
            player_id (str): The player ID
            game_id (str): The game ID
            team_id (str, optional): Team ID to use for proper team context
            
        Returns:
            dict: Dictionary containing player game statistics
        """
        player = self.get_player_by_id(player_id)
        
        # Use the provided team_id, or get the player's team_id from the player data
        player_team_id = team_id
        if player_team_id is None and player is not None:
            # Get team_id from player data
            player_team_id = player.get('TeamID')
            
        # If still no team_id, try to get it from the game
        if player_team_id is None:
            game_temp = self.sheets_service.get_games()
            game_row = game_temp[game_temp['ID'] == game_id]
            if not game_row.empty:
                player_team_id = game_row.iloc[0].get('TeamID')
        
        game = self.get_game_by_id(game_id, player_team_id)
        
        if player is None or game is None:
            return None
        
        events = self.get_events()
        
        # Get all teams in events
        unique_teams = events['Team'].unique()
        print(f"Unique teams in events: {unique_teams}")
        
        # Get the proper team identifier from the game's TeamID using the same logic as season stats
        game_team_id = game.get('TeamID', 'your_team')
        team_identifier = self._get_team_identifier_for_events(game_team_id)
        print(f"Using team identifier: '{team_identifier}' for game team ID: '{game_team_id}'")
        
        # Filter events for this game
        game_events = events[events['GameID'] == game_id]
        
        # Calculate all stats using centralized functions
        goals = self.calculate_goals_for_events(player_id, game_events)
        assists = self.calculate_assists_for_events(player_id, game_events)
        points = self.calculate_points_for_events(player_id, game_events)
        plus_minus = self.calculate_plus_minus_for_events(player_id, game_events, team_identifier)
        shots = self.calculate_shots_for_events(player_id, game_events)
        penalty_minutes = self.calculate_penalty_minutes_for_events(player_id, game_events)
        
        return {
            'player': player,
            'game': game,
            'goals': goals,
            'assists': assists,
            'points': points,
            'plus_minus': plus_minus,
            'shots': shots,
            'penalty_minutes': penalty_minutes
        }
    
    def calculate_goalie_game_stats(self, player_id, game_id, team_id=None):
        """
        Calculate statistics for a goalie in a specific game with GoalieOnIceId support.
        
        Args:
            player_id (str): The player ID
            game_id (str): The game ID
            team_id (str, optional): Team ID to filter by
            
        Returns:
            dict: Dictionary containing goalie game statistics
        """
        print(f"DEBUG: calculate_goalie_game_stats called for player_id={player_id}, game_id={game_id}")
        player = self.get_player_by_id(player_id)
        game = self.get_game_by_id(game_id)
        
        if player is None:
            print(f"DEBUG: Player with ID {player_id} not found")
            return None
        
        if game is None:
            print(f"DEBUG: Game with ID {game_id} not found")
            return None
        
        if player['Position'] != 'G':
            print(f"Player with ID {player_id} is not a goalie (position: {player['Position']})")
            return None
        
        events = self.get_events()
        
        # Get all teams in events
        unique_teams = events['Team'].unique()
        print(f"Unique teams in events: {unique_teams}")
        
        # Use the team_id parameter for proper team identification
        if team_id is not None:
            your_team = team_id  # Use team_id directly for event filtering
            print(f"Using team identifier: '{your_team}' for team ID: '{team_id}'")
        else:
            # For backward compatibility, try to get the first team or use fallback
            try:
                teams = self.sheets_service.get_teams()
                if not teams.empty:
                    your_team = teams.iloc[0]['TeamID']  # Use TeamID instead of TeamName
                    print(f"Using first team identifier: '{your_team}'")
                else:
                    your_team = 'your_team'
                    print(f"Using fallback team identifier: '{your_team}'")
            except:
                your_team = 'your_team'
                print(f"Using fallback team identifier: '{your_team}'")
        
        # Use the new helper method to filter events for this goalie and game
        goalie_events = self._filter_goalie_events(events, player_id, game_id)
        
        print(f"DEBUG: Filtered to {len(goalie_events)} events for goalie {player_id} in game {game_id}")
        print(f"DEBUG: Game events columns: {goalie_events.columns.tolist()}")
        
        # Debug: Check team distribution in filtered events
        if not goalie_events.empty:
            team_counts = goalie_events['Team'].value_counts()
            print(f"DEBUG: Team distribution in filtered events: {team_counts.to_dict()}")
            
            # Debug: Check IsGoal distribution
            if 'IsGoal' in goalie_events.columns:
                isgoal_counts = goalie_events['IsGoal'].value_counts()
                print(f"DEBUG: IsGoal distribution in filtered events: {isgoal_counts.to_dict()}")
        
        # Calculate goals against - use filtered events and proper team identification
        goals_against_events = goalie_events[(goalie_events['IsGoal'] == True) & 
                                           (goalie_events['Team'] != your_team)]
        
        print(f"DEBUG: Found {len(goals_against_events)} goals against events for goalie {player_id} in game {game_id}")
        goals_against = len(goals_against_events)
        
        # Calculate shots against - ensure we count both shots and goals as shots from filtered events
        # Count all shots from opponents when this goalie was on ice
        shots_events = goalie_events[(goalie_events['EventType'] == 'Shot') & 
                                   (goalie_events['Team'] != your_team)]
        
        # Also count goals as shots (if they're not already counted as shots)
        goals_as_shots = goalie_events[(goalie_events['IsGoal'] == True) & 
                                     (goalie_events['Team'] != your_team) &
                                     (goalie_events['EventType'] != 'Shot')]
        
        print(f"DEBUG: Found {len(shots_events)} shot events for goalie {player_id} in game {game_id}")
        print(f"DEBUG: Found {len(goals_as_shots)} goal events counted as shots for goalie {player_id} in game {game_id}")
        
        # Combine unique events
        shots_against = len(shots_events) + len(goals_as_shots)
        
        # Calculate saves with validation
        saves = max(0, shots_against - goals_against)  # Ensure saves is not negative
        
        # Calculate save percentage with error handling
        try:
            save_percentage = saves / shots_against if shots_against > 0 else 0
            # Validate save percentage is between 0 and 1
            save_percentage = max(0, min(1, save_percentage))
        except Exception as e:
            print(f"Error calculating save percentage: {e}")
            save_percentage = 0
        
        # Determine if this was a shutout (no goals against when this goalie was on ice)
        shutout = goals_against == 0
        
        # Get the game result
        result = game.get('Result', 'Unknown')
        
        result_dict = {
            'player': player,
            'game': game,
            'goals_against': goals_against,
            'shots_against': shots_against,
            'saves': saves,
            'save_percentage': save_percentage,
            'shutout': shutout,
            'result': result
        }
        
        print(f"DEBUG: Returning enhanced goalie game stats for game {game_id}: {result_dict}")
        return result_dict
    
    def get_player_game_log(self, player_id, team_id=None, game_type=None):
        """
        Get a game log for a player, optionally filtered by team and game type.
        
        Args:
            player_id (str): The player ID
            team_id (str, optional): Team ID to filter by
            game_type (str, optional): Game type to filter by (E, R, T). If None, uses all games.
            
        Returns:
            list: List of dictionaries containing game statistics
        """
        player_games = self.get_player_games(player_id, team_id, game_type=game_type)
        player = self.get_player_by_id(player_id)
        
        game_log = []
        for _, game in player_games.iterrows():
            # Check if player is a goalie
            if player is not None and player['Position'] == 'G':
                game_stats = self.calculate_goalie_game_stats(player_id, game['ID'], team_id)
            else:
                game_stats = self.calculate_player_game_stats(player_id, game['ID'], team_id)
                
            if game_stats:
                game_log.append(game_stats)
        
        # Sort by game date (most recent first)
        game_log.sort(key=lambda x: x['game']['Date'], reverse=True)
        
        return game_log
    

    def get_completed_games_count(self, team_id=None):
        """
        Get the count of completed games (past dates only) for a team.
        This ensures consistency between team stats and game counts.
        
        Args:
            team_id (str, optional): Team ID to filter by
            
        Returns:
            int: Number of completed games
        """
        games = self.get_games(team_id)
        completed_games = self._filter_games_by_date(games, include_future=False)
        return len(completed_games)
    def calculate_team_stats(self, team_id=None, game_type=None):
        """
        Calculate team statistics.
        
        Args:
            team_id (str, optional): Team ID to filter by
            game_type (str, optional): Game type to filter by (E, R, T). If None, uses all games.
            
        Returns:
            dict: Dictionary containing team statistics
        """
        # Use the provided game_type parameter directly - don't get from session
        # This ensures consistency between UI selection and actual calculation
        games = self.get_games(team_id, game_type)
        
        # Ensure Result column exists
        games = self._ensure_result_column(games)
        
        # Filter games to only include completed games (past dates)
        completed_games = self._filter_games_by_date(games, include_future=False)
        print(f"Team stats calculation: Using {len(completed_games)} completed games out of {len(games)} total games")
        
        # Calculate wins, losses, and ties with error handling - only from completed games
        try:
            wins = len(completed_games[completed_games['Result'] == 'W'])
            losses = len(completed_games[completed_games['Result'] == 'L'])
            ties = len(completed_games[completed_games['Result'] == 'T'])
        except KeyError as e:
            print(f"Error calculating team stats: {e}")
            wins = 0
            losses = 0
            ties = 0
        
        # Calculate goals for and against with error handling - only from completed games
        try:
            goals_for = completed_games['GoalsFor'].sum()
            goals_against = completed_games['GoalsAgainst'].sum()
        except KeyError as e:
            print(f"Error calculating goals: {e}")
            goals_for = 0
            goals_against = 0
        
        # Calculate win percentage - only from completed games
        games_played = len(completed_games)
        win_percentage = wins / games_played if games_played > 0 else 0
        
        return {
            'games_played': games_played,
            'wins': wins,
            'losses': losses,
            'ties': ties,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'win_percentage': win_percentage
        }
    
    def get_team_leaderboard(self, stat='points', position=None, limit=None, team_id=None, game_type=None):
        """
        Get a team leaderboard for a specific statistic.
        
        Args:
            stat (str): The statistic to rank by (points, goals, assists, plus_minus, jersey_number, save_percentage, gaa, wins, shutouts)
            position (str, optional): Filter by position (F, D, G)
            limit (int, optional): Maximum number of players to include. If None, includes all players.
            team_id (str, optional): Team ID to filter by
            game_type (str, optional): Game type to filter by (E, R, T). If None, uses all games.
            
        Returns:
            list: List of dictionaries containing player statistics
        """
        # First check if there are any games of the specified type
        if game_type is not None:
            games = self.get_games(team_id, game_type)
            completed_games = self._filter_games_by_date(games, include_future=False)
            if completed_games.empty:
                print(f"No completed games found for game type '{game_type}' - returning empty leaderboard")
                return []
        
        players = self.get_players(team_id)
        
        # Filter by position if specified
        if position:
            players = players[players['Position'] == position]
        
        # Calculate stats for each player - use appropriate method based on position
        player_stats = []
        for _, player in players.iterrows():
            # Use centralized helper method for column detection
            player_id = self._get_player_id_from_series(player)
            if player_id is None:
                print(f"ERROR: No player ID found for leaderboard player. Skipping.")
                continue
            
            if player['Position'] == 'G':
                # Use goalie stats calculation for goalies
                stats = self.calculate_goalie_stats(player_id, team_id, game_type)
                # Add missing fields for goalies to match skater stats structure
                if stats:
                    stats['points'] = 0  # Goalies don't have points
                    stats['goals'] = 0
                    stats['assists'] = 0
                    stats['plus_minus'] = 0
                    stats['shots'] = 0
                    stats['penalty_minutes'] = 0
                    stats['goals_per_game'] = 0
            else:
                # Use regular player stats calculation for skaters
                stats = self.calculate_player_stats(player_id, team_id, game_type)
                # Add missing fields for skaters to match goalie stats structure
                if stats:
                    stats['wins'] = 0  # Skaters don't have wins
                    stats['shutouts'] = 0
                    stats['goals_against'] = 0
                    stats['shots_against'] = 0
                    stats['saves'] = 0
                    stats['save_percentage'] = 0
                    stats['gaa'] = 0
            
            if stats:
                player_stats.append(stats)
        
        # Sort by the specified statistic
        if stat == 'jersey_number':
            # Sort by jersey number (ascending)
            player_stats.sort(key=lambda x: int(x['player']['JerseyNumber']) if str(x['player']['JerseyNumber']).isdigit() else float('inf'))
        elif stat in ['points', 'goals', 'assists', 'plus_minus', 'shots', 'penalty_minutes', 'games_played', 'goals_per_game']:
            # Skater stats - sort descending (higher is better)
            player_stats.sort(key=lambda x: x[stat], reverse=True)
        elif stat in ['save_percentage', 'wins', 'shutouts']:
            # Goalie stats where higher is better - sort descending
            player_stats.sort(key=lambda x: x[stat], reverse=True)
        elif stat == 'gaa':
            # Goals Against Average - lower is better, sort ascending
            player_stats.sort(key=lambda x: x[stat], reverse=False)
        
        # Limit the number of players if a limit is specified
        if limit is not None:
            return player_stats[:limit]
        else:
            # Return all players if no limit is specified
            return player_stats
    
    def calculate_goalie_stats(self, player_id, team_id=None, game_type=None):
        """
        Calculate statistics for a goalie with GoalieOnIceId support.
        
        Args:
            player_id (str): The player ID
            team_id (str, optional): Team ID to filter by
            game_type (str, optional): Game type to filter by (E, R, T). If None, uses all games.
            
        Returns:
            dict: Dictionary containing goalie statistics
        """
        player = self.get_player_by_id(player_id)
        if player is None:
            print(f"Player with ID {player_id} not found")
            return None
        
        if player['Position'] != 'G':
            print(f"Player with ID {player_id} is not a goalie (position: {player['Position']})")
            return None
        
        print(f"Calculating enhanced stats for goalie: {player_id}")
        
        events = self.get_events()
        print(f"Total events: {len(events)}")
        
        games = self.get_player_games(player_id, team_id, game_type=game_type)
        print(f"Goalie games count: {len(games)}")
        
        # CRITICAL FIX: Apply the same game type filtering logic as for skaters
        # This ensures goalies are also properly filtered by game type
        if game_type is not None:
            # Get all games of the specified type for proper event filtering
            all_games_of_type = self.get_games(team_id, game_type)
            if not all_games_of_type.empty:
                game_ids_of_type = all_games_of_type['ID'].tolist()
                events = events[events['GameID'].isin(game_ids_of_type)]
                print(f"Filtered events to {len(events)} events from {len(game_ids_of_type)} games of type '{game_type}' for goalie")
            else:
                # No games of this type exist, so no events should be included
                events = events[events['GameID'].isin([])]  # Empty filter
                print(f"No games of type '{game_type}' found - using 0 events for goalie stats calculation")
        
        if games.empty:
            print(f"WARNING: No games found for goalie {player_id}")
            return {
                'player': player,
                'games_played': 0,
                'wins': 0,
                'shutouts': 0,
                'goals_against': 0,
                'shots_against': 0,
                'saves': 0,
                'save_percentage': 0,
                'gaa': 0
            }
        
        # Ensure Result column exists
        games = self._ensure_result_column(games)
        
        # Get all teams in events
        unique_teams = events['Team'].unique()
        print(f"Unique teams in events: {unique_teams}")
        
        # Use the team_id parameter for proper team identification
        if team_id is not None:
            your_team = team_id  # Use team_id directly for event filtering
            print(f"Using team identifier: '{your_team}' for team ID: '{team_id}'")
        else:
            # For backward compatibility, try to get the first team or use fallback
            try:
                teams = self.sheets_service.get_teams()
                if not teams.empty:
                    your_team = teams.iloc[0]['TeamID']  # Use TeamID instead of TeamName
                    print(f"Using first team identifier: '{your_team}'")
                else:
                    your_team = 'your_team'
                    print(f"Using fallback team identifier: '{your_team}'")
            except:
                your_team = 'your_team'
                print(f"Using fallback team identifier: '{your_team}'")
        
        # Print game IDs for debugging
        game_ids = games['ID'].tolist()
        print(f"Goalie game IDs: {game_ids}")
        
        # Use the new helper method to filter events for this goalie across all their games
        # Filter events to only include games this goalie played in (events are already filtered by game type above)
        goalie_game_events = events[events['GameID'].isin(game_ids)] if not games.empty else events
        goalie_events = self._filter_goalie_events(goalie_game_events, player_id)
        
        print(f"Filtered to {len(goalie_events)} events for goalie {player_id} across all games")
        
        # Debug: Check team distribution in filtered events
        if not goalie_events.empty:
            team_counts = goalie_events['Team'].value_counts()
            print(f"Team distribution in filtered events: {team_counts.to_dict()}")
        
        # Calculate goals against using filtered events and proper team identification
        goals_against_events = goalie_events[(goalie_events['IsGoal'] == True) & 
                                           (goalie_events['Team'] != your_team)]
        
        print(f"Found {len(goals_against_events)} goals against for goalie {player_id} using enhanced filtering")
        goals_against = len(goals_against_events)
        
        # Calculate shots against using filtered events - ensure we count both shots and goals as shots
        # Count all shots from opponents when this goalie was on ice
        shots_events = goalie_events[(goalie_events['EventType'] == 'Shot') & 
                                   (goalie_events['Team'] != your_team)]
        
        # Also count goals as shots (if they're not already counted as shots)
        goals_as_shots = goalie_events[(goalie_events['IsGoal'] == True) & 
                                     (goalie_events['Team'] != your_team) &
                                     (goalie_events['EventType'] != 'Shot')]
        
        print(f"Shot events against goalie {player_id}: {len(shots_events)}")
        print(f"Goal events counted as shots for goalie {player_id}: {len(goals_as_shots)}")
        
        # Combine unique events
        shots_against = len(shots_events) + len(goals_as_shots)
        
        print(f"Found {shots_against} total shots against for goalie {player_id} using enhanced filtering")
        
        # Calculate saves with validation
        saves = max(0, shots_against - goals_against)  # Ensure saves is not negative
        
        # Calculate save percentage with error handling
        try:
            save_percentage = saves / shots_against if shots_against > 0 else 0
            # Validate save percentage is between 0 and 1
            save_percentage = max(0, min(1, save_percentage))
        except Exception as e:
            print(f"Error calculating save percentage: {e}")
            save_percentage = 0
        
        # Calculate games played
        games_played = len(games)
        
        # Calculate wins, losses, and ties with error handling
        try:
            wins = len(games[games['Result'] == 'W'])
            losses = len(games[games['Result'] == 'L'])
            ties = len(games[games['Result'] == 'T'])
        except KeyError as e:
            print(f"Error calculating goalie W-L-T record: {e}")
            wins = 0
            losses = 0
            ties = 0
        
        # Special handling for goalies not in game roster
        if games_played == 0:
            print(f"WARNING: Goalie {player_id} not found in game roster for team {team_id}")
            print("This may indicate the goalie needs to be added to game rosters")
        
        # Calculate shutouts using enhanced filtering (games where no goals against when this goalie was on ice)
        shutouts = 0
        for _, game in games.iterrows():
            game_goalie_events = self._filter_goalie_events(events, player_id, game['ID'])
            game_goals_against = len(game_goalie_events[(game_goalie_events['IsGoal'] == True) & 
                                                       (game_goalie_events['Team'] != your_team)])
            if game_goals_against == 0:
                shutouts += 1
        
        print(f"Calculated {shutouts} shutouts for goalie {player_id} using enhanced filtering")
        
        # Calculate goals against average with error handling
        try:
            gaa = goals_against / games_played if games_played > 0 else 0
        except Exception as e:
            print(f"Error calculating GAA: {e}")
            gaa = 0
        
        return {
            'player': player,
            'games_played': games_played,
            'wins': wins,
            'losses': losses,
            'ties': ties,
            'shutouts': shutouts,
            'goals_against': goals_against,
            'shots_against': shots_against,
            'saves': saves,
            'save_percentage': save_percentage,
            'gaa': gaa
        }
    
    def get_game_events(self, game_id):
        """
        Get all events for a specific game.
        
        Args:
            game_id (str): The game ID
            
        Returns:
            pd.DataFrame: DataFrame containing game events
        """
        events = self.get_events()
        # Print columns for debugging
        print("Events columns in get_game_events:", events.columns.tolist())
        
        # Filter events for this game
        game_events = events[events['GameID'] == game_id]
        
        # If IsGoal column exists, make sure EventType is consistent with IsGoal
        if 'IsGoal' in game_events.columns:
            # For events where IsGoal is True but EventType is not 'Goal', update EventType
            mask = (game_events['IsGoal'] == True) & (game_events['EventType'] != 'Goal')
            if mask.any():
                print(f"Found {mask.sum()} events with IsGoal=True but EventType!='Goal', updating EventType")
                game_events.loc[mask, 'EventType'] = 'Goal'
        
        # Sort by Period
        return game_events.sort_values(by=['Period'])
    
    def get_game_player_stats(self, game_id, position=None, team_id=None):
        """
        Get player statistics for a specific game.
        
        Args:
            game_id (str): The game ID
            position (str, optional): Filter by position (F, D, G)
            team_id (str, optional): Team ID to filter by
            
        Returns:
            list: List of dictionaries containing player game statistics
        """
        game_roster = self.get_game_roster(team_id)
        players = self.get_players(team_id)
        
        # Get players who were present for this game
        game_players = game_roster[(game_roster['GameID'] == game_id) & 
                                  (game_roster['Status'] == 'Present')]
        
        # Join with players to get position - use centralized helper method for column detection
        id_column = self._get_player_id_column(players)
        if id_column is None:
            print(f"ERROR: No player ID column found in players data for game player stats merge")
            return []
        
        print(f"Using player ID column: '{id_column}' for game player stats merge")
        game_players = pd.merge(game_players, players[[id_column, 'Position']], 
                               left_on='PlayerID', right_on=id_column)
        
        # Remove duplicate players (same PlayerID for same game)
        original_count = len(game_players)
        game_players = game_players.drop_duplicates(subset=['PlayerID'], keep='first')
        deduplicated_count = len(game_players)
        
        if original_count > deduplicated_count:
            print(f"Deduplicated game roster: removed {original_count - deduplicated_count} duplicate entries for game {game_id}")
        
        # Filter by position if specified
        if position:
            game_players = game_players[game_players['Position'] == position]
        
        # Calculate stats for each player
        player_stats = []
        for _, player_row in game_players.iterrows():
            stats = self.calculate_player_game_stats(player_row['PlayerID'], game_id, team_id)
            if stats:
                player_stats.append(stats)
        
        # Sort by points
        player_stats.sort(key=lambda x: x['points'], reverse=True)
        
        return player_stats
    
    def get_game_summary(self, game_id, team_id=None):
        """
        Get a summary of a game.
        
        Args:
            game_id (str): The game ID
            team_id (str, optional): Team ID to ensure consistent data source
            
        Returns:
            dict: Dictionary containing game summary
        """
        # Use team_id to get the game from the same data source as other methods
        game = self.get_game_by_id(game_id, team_id)
        if game is None:
            return None
        
        events = self.get_events()
        game_events = events[events['GameID'] == game_id]
        
        # Get all teams in events
        unique_teams = events['Team'].unique()
        print(f"Unique teams in events: {unique_teams}")
        
        # Get the proper team identifier from the game's TeamID
        game_team_id = game.get('TeamID', 'your_team')
        team_identifier = self._get_team_identifier_for_events(game_team_id)
        print(f"Using team identifier: '{team_identifier}' for game team ID: '{game_team_id}'")
        
        # Calculate shots with proper team identification
        your_team_shots = len(game_events[(game_events['EventType'].isin(['Goal', 'Shot'])) & 
                                         (game_events['Team'] == team_identifier)])
        opponent_shots = len(game_events[(game_events['EventType'].isin(['Goal', 'Shot'])) & 
                                        (game_events['Team'] != team_identifier)])
        
        # Calculate penalty minutes with proper team identification
        your_team_penalties = game_events[(game_events['EventType'] == 'Penalty') & 
                                         (game_events['Team'] == team_identifier)]
        opponent_penalties = game_events[(game_events['EventType'] == 'Penalty') & 
                                        (game_events['Team'] != team_identifier)]
        
        your_team_pim = your_team_penalties['PenaltyDuration'].sum() if not your_team_penalties.empty else 0
        opponent_pim = opponent_penalties['PenaltyDuration'].sum() if not opponent_penalties.empty else 0
        
        # Calculate power play goals - always use IsGoal with proper team identification
        your_team_pp_goals = len(game_events[(game_events['IsGoal'] == True) & 
                                           (game_events['Team'] == team_identifier) & 
                                           (game_events.get('IsPowerPlay', False) == True)])
        opponent_pp_goals = len(game_events[(game_events['IsGoal'] == True) & 
                                          (game_events['Team'] != team_identifier) & 
                                          (game_events.get('IsPowerPlay', False) == True)])
        print(f"Using IsGoal column for power play goals in game {game_id}")
        
        # If IsPowerPlay column doesn't exist, try to estimate power play goals
        if your_team_pp_goals == 0 and opponent_pp_goals == 0:
            # Check if there are penalties in the game
            if not your_team_penalties.empty or not opponent_penalties.empty:
                # Estimate power play goals based on timing of goals and penalties
                # This is a simplified approach - in a real app, you'd need more detailed logic
                your_team_pp_goals = len(game_events[(game_events['IsGoal'] == True) & 
                                                   (game_events['Team'] == team_identifier) & 
                                                   (~game_events.get('IsShortHanded', False))])
                opponent_pp_goals = len(game_events[(game_events['IsGoal'] == True) & 
                                                  (game_events['Team'] != team_identifier) & 
                                                  (~game_events.get('IsShortHanded', False))])
        
        # Calculate power play opportunities
        your_team_pp_opps = len(opponent_penalties)
        opponent_pp_opps = len(your_team_penalties)
        
        # Calculate power play percentage
        your_team_pp_pct = your_team_pp_goals / your_team_pp_opps if your_team_pp_opps > 0 else 0
        opponent_pp_pct = opponent_pp_goals / opponent_pp_opps if opponent_pp_opps > 0 else 0
        
        print(f"Game summary for {game_id}: Using consistent goals data from get_games method")
        print(f"Goals For: {game.get('GoalsFor', 0)}, Goals Against: {game.get('GoalsAgainst', 0)}")
        
        return {
            'game': game,
            'your_team_shots': your_team_shots,
            'opponent_shots': opponent_shots,
            'your_team_pim': your_team_pim,
            'opponent_pim': opponent_pim,
            'your_team_pp_goals': your_team_pp_goals,
            'opponent_pp_goals': opponent_pp_goals,
            'your_team_pp_opps': your_team_pp_opps,
            'opponent_pp_opps': opponent_pp_opps,
            'your_team_pp_pct': your_team_pp_pct,
            'opponent_pp_pct': opponent_pp_pct
        }
    
    def get_game_timeline(self, game_id):
        """
        Get a timeline of events for a game.
        
        Args:
            game_id (str): The game ID
            
        Returns:
            list: List of dictionaries containing event details
        """
        events = self.get_events()
        players = self.get_players()
        
        # Get all teams in events
        unique_teams = events['Team'].unique()
        print(f"Unique teams in events: {unique_teams}")
        
        # Always use 'your_team' as the team name
        your_team = 'your_team'
        print(f"Using team name: {your_team}")
        
        # Print columns for debugging
        print("Events columns:", events.columns.tolist())
        
        # Filter events for this game
        game_events = events[events['GameID'] == game_id]
        
        # If IsGoal column exists, make sure EventType is consistent with IsGoal
        if 'IsGoal' in game_events.columns:
            # For events where IsGoal is True but EventType is not 'Goal', update EventType
            mask = (game_events['IsGoal'] == True) & (game_events['EventType'] != 'Goal')
            if mask.any():
                print(f"Found {game_events.sum()} events with IsGoal=True but EventType!='Goal', updating EventType")
                game_events.loc[mask, 'EventType'] = 'Goal'
        
        # Sort by Period
        game_events = game_events.sort_values(by=['Period'])
        
        timeline = []
        for _, event in game_events.iterrows():
            event_dict = event.to_dict()
            
            # Add player jersey numbers instead of names for security
            if event['PrimaryPlayerID']:
                primary_player = self.get_player_by_id(event['PrimaryPlayerID'])
                if primary_player is not None:
                    # Use jersey number for player identification
                    jersey = primary_player.get('JerseyNumber', 'Unknown')
                    event_dict['PrimaryPlayerName'] = f"#{jersey}"
            
            if event['AssistPlayer1ID']:
                assist1_player = self.get_player_by_id(event['AssistPlayer1ID'])
                if assist1_player is not None:
                    # Use jersey number for player identification
                    jersey = assist1_player.get('JerseyNumber', 'Unknown')
                    event_dict['AssistPlayer1Name'] = f"#{jersey}"
            
            if event['AssistPlayer2ID']:
                assist2_player = self.get_player_by_id(event['AssistPlayer2ID'])
                if assist2_player is not None:
                    # Use jersey number for player identification
                    jersey = assist2_player.get('JerseyNumber', 'Unknown')
                    event_dict['AssistPlayer2Name'] = f"#{jersey}"
            
            timeline.append(event_dict)
        
        return timeline
    
    def get_period_breakdown(self, game_id, team_id=None):
        """
        Get period-by-period scoring and shots breakdown for a game.
        
        Args:
            game_id (str): The game ID
            team_id (str, optional): Team ID to filter by
            
        Returns:
            dict: Dictionary containing period-by-period scoring and shots data with structure:
                {
                    'your_team': {
                        'name': 'Team Name',
                        'goals': [goals_p1, goals_p2, goals_p3],
                        'shots': [shots_p1, shots_p2, shots_p3],
                        'total_goals': total_goals,
                        'total_shots': total_shots
                    },
                    'opponent': {
                        'name': 'Opponent Name', 
                        'goals': [goals_p1, goals_p2, goals_p3],
                        'shots': [shots_p1, shots_p2, shots_p3],
                        'total_goals': total_goals,
                        'total_shots': total_shots
                    }
                }
        """
        # Get game data to extract team and opponent names
        game = self.get_game_by_id(game_id, team_id)
        if game is None:
            print(f"Game {game_id} not found")
            return None
        
        # Get events for this game
        events = self.get_events()
        game_events = events[events['GameID'] == game_id]
        
        if game_events.empty:
            print(f"No events found for game {game_id}")
            return None
        
        # Get team identifier for event filtering using the same logic as other methods
        game_team_id = game.get('TeamID', 'your_team')
        team_identifier = self._get_team_identifier_for_events(game_team_id)
        print(f"Using team identifier: '{team_identifier}' for game team ID: '{game_team_id}'")
        
        # Get team names
        your_team_name = self._get_team_name_from_id(game_team_id) or game_team_id
        opponent_name = game.get('Opponent', 'Opponent')
        
        # Initialize period data structure with both goals and shots
        period_data = {
            'your_team': {
                'name': your_team_name,
                'goals': [0, 0, 0],  # Goals in periods 1, 2, 3
                'shots': [0, 0, 0],  # Shots in periods 1, 2, 3
                'total_goals': 0,
                'total_shots': 0,
                # Keep 'periods' and 'total' for backward compatibility
                'periods': [0, 0, 0],
                'total': 0
            },
            'opponent': {
                'name': opponent_name,
                'goals': [0, 0, 0],  # Goals in periods 1, 2, 3
                'shots': [0, 0, 0],  # Shots in periods 1, 2, 3
                'total_goals': 0,
                'total_shots': 0,
                # Keep 'periods' and 'total' for backward compatibility
                'periods': [0, 0, 0],
                'total': 0
            }
        }
        
        # Filter to goal events
        goal_events = game_events[game_events['IsGoal'] == True]
        print(f"Found {len(goal_events)} goal events for game {game_id}")
        
        # Filter to shot events (including goals as shots)
        shot_events = game_events[game_events['EventType'].isin(['Shot', 'Goal'])]
        print(f"Found {len(shot_events)} shot events (including goals) for game {game_id}")
        
        # Count goals by period and team
        for _, goal_event in goal_events.iterrows():
            period = goal_event.get('Period', 1)
            scoring_team = goal_event.get('Team', '')
            
            # Ensure period is valid (1, 2, or 3)
            if period not in [1, 2, 3]:
                print(f"Invalid period {period} found, skipping goal event")
                continue
            
            # Convert period to array index (0, 1, 2)
            period_index = period - 1
            
            # Determine which team scored
            if scoring_team == team_identifier:
                # Your team scored
                period_data['your_team']['goals'][period_index] += 1
                period_data['your_team']['total_goals'] += 1
                # Maintain backward compatibility
                period_data['your_team']['periods'][period_index] += 1
                period_data['your_team']['total'] += 1
                print(f"Your team goal in period {period}")
            else:
                # Opponent scored
                period_data['opponent']['goals'][period_index] += 1
                period_data['opponent']['total_goals'] += 1
                # Maintain backward compatibility
                period_data['opponent']['periods'][period_index] += 1
                period_data['opponent']['total'] += 1
                print(f"Opponent goal in period {period}")
        
        # Count shots by period and team
        for _, shot_event in shot_events.iterrows():
            period = shot_event.get('Period', 1)
            shooting_team = shot_event.get('Team', '')
            
            # Ensure period is valid (1, 2, or 3)
            if period not in [1, 2, 3]:
                print(f"Invalid period {period} found, skipping shot event")
                continue
            
            # Convert period to array index (0, 1, 2)
            period_index = period - 1
            
            # Determine which team took the shot
            if shooting_team == team_identifier:
                # Your team shot
                period_data['your_team']['shots'][period_index] += 1
                period_data['your_team']['total_shots'] += 1
            else:
                # Opponent shot
                period_data['opponent']['shots'][period_index] += 1
                period_data['opponent']['total_shots'] += 1
        
        print(f"Period breakdown for game {game_id}:")
        print(f"  {your_team_name} Goals: {period_data['your_team']['goals']} (Total: {period_data['your_team']['total_goals']})")
        print(f"  {your_team_name} Shots: {period_data['your_team']['shots']} (Total: {period_data['your_team']['total_shots']})")
        print(f"  {opponent_name} Goals: {period_data['opponent']['goals']} (Total: {period_data['opponent']['total_goals']})")
        print(f"  {opponent_name} Shots: {period_data['opponent']['shots']} (Total: {period_data['opponent']['total_shots']})")
        
        return period_data
