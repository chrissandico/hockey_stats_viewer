import pandas as pd
import numpy as np
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
        
        # Always force refresh all data to avoid caching issues
        print("Forcing refresh of all data...")
        self.sheets_service.refresh_all_data()
        
        # Cache busting - initialize with empty caches
        self._players_cache = None
        self._games_cache = None
        self._events_cache = None
        self._game_roster_cache = None
    
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
    
    def _get_team_identifier_for_events(self, team_id):
        """
        Get the correct team identifier to use when filtering events.
        Enhanced version with better matching logic.
        
        Args:
            team_id (str): Team ID from games/teams data
            
        Returns:
            str: Team identifier used in events data
        """
        if team_id is None:
            return None
            
        # Get all unique teams from events to understand the mapping
        events = self.sheets_service.get_events()
        unique_event_teams = events['Team'].unique() if not events.empty and 'Team' in events.columns else []
        
        print(f"=== TEAM IDENTIFIER MAPPING ===")
        print(f"Available teams in events: {unique_event_teams}")
        print(f"Looking for team_id: '{team_id}'")
        
        # Method 1: Try direct match first
        if team_id in unique_event_teams:
            print(f"✅ Direct match found: {team_id}")
            return team_id
        
        # Method 2: Try normalized TeamID matching
        normalized_team_id = self._normalize_team_name(team_id)
        for event_team in unique_event_teams:
            normalized_event_team = self._normalize_team_name(event_team)
            if normalized_team_id == normalized_event_team:
                print(f"✅ Normalized TeamID match found: '{team_id}' -> '{event_team}'")
                print(f"   (normalized: '{normalized_team_id}' == '{normalized_event_team}')")
                return event_team
        
        # Method 3: Try to find a mapping based on team names
        try:
            teams = self.sheets_service.get_teams()
            team_row = teams[teams['TeamID'] == team_id]
            
            if not team_row.empty:
                team_name = team_row.iloc[0]['TeamName']
                print(f"Team name from Teams sheet: '{team_name}'")
                
                # Method 3a: Check if team name appears in events (original logic)
                for event_team in unique_event_teams:
                    if team_name.lower() in event_team.lower() or event_team.lower() in team_name.lower():
                        print(f"✅ Team name substring match found: '{team_id}' -> '{event_team}' (via team name: '{team_name}')")
                        return event_team
                
                # Method 3b: Try normalized team name matching
                normalized_team_name = self._normalize_team_name(team_name)
                for event_team in unique_event_teams:
                    normalized_event_team = self._normalize_team_name(event_team)
                    if normalized_team_name == normalized_event_team:
                        print(f"✅ Normalized team name match found: '{team_id}' -> '{event_team}'")
                        print(f"   (team name '{team_name}' normalized: '{normalized_team_name}' == '{normalized_event_team}')")
                        return event_team
                
                # Method 3c: Try partial normalized matching (team name contains event team or vice versa)
                for event_team in unique_event_teams:
                    normalized_event_team = self._normalize_team_name(event_team)
                    if (normalized_team_name in normalized_event_team or 
                        normalized_event_team in normalized_team_name) and len(normalized_event_team) > 2:
                        print(f"✅ Partial normalized match found: '{team_id}' -> '{event_team}'")
                        print(f"   ('{normalized_team_name}' <-> '{normalized_event_team}')")
                        return event_team
                
                # Special handling for common patterns
                if 'your_team' == team_id and len(unique_event_teams) > 0:
                    # Find the team that's not 'opponent'
                    non_opponent_teams = [t for t in unique_event_teams if t.lower() != 'opponent']
                    if non_opponent_teams:
                        mapped_team = non_opponent_teams[0]
                        print(f"✅ Special 'your_team' mapping: {mapped_team}")
                        return mapped_team
        except Exception as e:
            print(f"❌ Error in team mapping: {e}")
        
        # Fallback - return the team_id as-is
        print(f"⚠️  No mapping found, using team_id as-is: '{team_id}'")
        print(f"   This may cause issues if '{team_id}' doesn't exist in events data")
        return team_id
    
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
    
    def get_games(self, team_id=None):
        """
        Get all games with calculated goal statistics, optionally filtered by team.
        
        Args:
            team_id (str, optional): Team ID to filter by
            
        Returns:
            pd.DataFrame: DataFrame containing game data with calculated columns
        """
        # Create a cache key based on team_id
        cache_key = f"games_{team_id}" if team_id else "games_all"
        
        # Check if we have cached results
        if not hasattr(self, '_games_calculated_cache'):
            self._games_calculated_cache = {}
        
        if cache_key in self._games_calculated_cache:
            print(f"Using cached games data for {cache_key}")
            return self._games_calculated_cache[cache_key].copy()
        
        games = self.sheets_service.get_games()
        events = self.sheets_service.get_events()
        
        # Filter games by team if specified
        if team_id is not None:
            games = self._filter_by_team(games, team_id)
        
        # Print columns for debugging
        print("Games columns:", games.columns.tolist())
        
        # Get team identifier for event filtering using the new mapping method
        if team_id is not None:
            team_identifier = self._get_team_identifier_for_events(team_id)
            print(f"Mapped team identifier: '{team_identifier}' for team ID: '{team_id}'")
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
        
        # Add GoalsFor and GoalsAgainst columns
        if not games.empty:
            # Create a copy to avoid pandas warnings
            games = games.copy()
            # Initialize columns with zeros
            games['GoalsFor'] = 0
            games['GoalsAgainst'] = 0
            
            # Calculate goals for each game - but only do this expensive operation once
            print(f"Calculating goals for {len(games)} games (team: {team_identifier})")
            for idx, game in games.iterrows():
                game_events = events[events['GameID'] == game['ID']]
                
                # Use IsGoal column for goal determination with proper team identification
                goals_for = len(game_events[(game_events['IsGoal'] == True) & 
                                          (game_events['Team'] == team_identifier)])
                goals_against = len(game_events[(game_events['IsGoal'] == True) & 
                                              (game_events['Team'] != team_identifier)])
                
                games.at[idx, 'GoalsFor'] = goals_for
                games.at[idx, 'GoalsAgainst'] = goals_against
            
            print(f"Completed goal calculations for {len(games)} games")
            if not games.empty:
                print("Sample game data:", games.iloc[0].to_dict())
        
        # Always ensure Result column exists (after GoalsFor/GoalsAgainst are calculated)
        games = self._ensure_result_column(games)
        
        # Cache the results
        self._games_calculated_cache[cache_key] = games.copy()
        print(f"Cached games data for {cache_key}")
        
        return games
    
    def _ensure_result_column(self, games):
        """
        Ensure the Result column exists in the games DataFrame.
        
        Args:
            games (pd.DataFrame): DataFrame containing game data
            
        Returns:
            pd.DataFrame: DataFrame with Result column added if needed
        """
        # Always work with a copy to avoid pandas warnings
        games = games.copy()
        
        # Check if Result column already exists
        if 'Result' not in games.columns:
            # Check if we can calculate it
            if not games.empty and 'GoalsFor' in games.columns and 'GoalsAgainst' in games.columns:
                # Create a new Result column
                games['Result'] = games.apply(
                    lambda row: 'W' if row['GoalsFor'] > row['GoalsAgainst'] else 
                               'L' if row['GoalsFor'] < row['GoalsAgainst'] else 'T', 
                    axis=1
                )
                print(f"Added Result column to {len(games)} games")
            else:
                # If we can't calculate it, add a placeholder
                games['Result'] = 'Unknown'
                print("Warning: Could not calculate Result column. Using placeholder values.")
        
        return games
    
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
        return players[players['ID'] == player_id].iloc[0] if not players[players['ID'] == player_id].empty else None
    
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
    
    def get_player_games(self, player_id, team_id=None, include_future=False):
        """
        Get all games a player participated in, optionally filtered by team and date.
        
        Args:
            player_id (str): The player ID
            team_id (str, optional): Team ID to filter by
            include_future (bool): If True, include future games. If False, only past/current games.
            
        Returns:
            pd.DataFrame: DataFrame containing game data
        """
        # Force refresh game roster to ensure it's up to date, passing team_id for proper filtering
        game_roster = self.get_game_roster(team_id)
        
        # Get games filtered by team if specified
        games = self.get_games(team_id)
        
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
        Calculate goals for a player based on events.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            
        Returns:
            int: Number of goals scored
        """
        player_events = events[events['PrimaryPlayerID'] == player_id]
        goals = len(player_events[(player_events['IsGoal'] == True)])
        print(f"Calculated {goals} goals for player {player_id}")
        return goals

    def calculate_assists_for_events(self, player_id, events):
        """
        Calculate assists for a player based on events.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            
        Returns:
            int: Number of assists
        """
        assist1_events = events[events['AssistPlayer1ID'] == player_id]
        assist2_events = events[events['AssistPlayer2ID'] == player_id]
        assists = len(assist1_events) + len(assist2_events)
        print(f"Calculated {assists} assists for player {player_id} ({len(assist1_events)} primary + {len(assist2_events)} secondary)")
        return assists

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
        Calculate penalty minutes for a player based on events.
        
        Args:
            player_id (str): The player ID
            events (pd.DataFrame): Events data to analyze
            
        Returns:
            int: Number of penalty minutes
        """
        player_events = events[events['PrimaryPlayerID'] == player_id]
        penalty_events = player_events[player_events['EventType'] == 'Penalty']
        penalty_minutes = penalty_events['PenaltyDuration'].sum() if not penalty_events.empty else 0
        print(f"Calculated {penalty_minutes} penalty minutes for player {player_id}")
        return penalty_minutes

    def calculate_player_stats(self, player_id, team_id=None):
        """
        Calculate statistics for a player.
        
        Args:
            player_id (str): The player ID
            team_id (str, optional): Team ID to filter by
            
        Returns:
            dict: Dictionary containing player statistics
        """
        player = self.get_player_by_id(player_id)
        if player is None:
            return None
        
        events = self.get_events()
        games = self.get_player_games(player_id, team_id)
        
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
        
        # Calculate all stats using centralized functions
        goals = self.calculate_goals_for_events(player_id, events)
        assists = self.calculate_assists_for_events(player_id, events)
        points = self.calculate_points_for_events(player_id, events)
        plus_minus = self.calculate_plus_minus_for_events(player_id, events, team_identifier)
        shots = self.calculate_shots_for_events(player_id, events)
        penalty_minutes = self.calculate_penalty_minutes_for_events(player_id, events)
        
        # Calculate games played
        games_played = len(games)
        
        # Calculate goals per game
        goals_per_game = goals / games_played if games_played > 0 else 0
        
        return {
            'player': player,
            'goals': goals,
            'assists': assists,
            'points': points,
            'plus_minus': plus_minus,
            'shots': shots,
            'penalty_minutes': penalty_minutes,
            'games_played': games_played,
            'goals_per_game': goals_per_game
        }
    
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
        Calculate statistics for a goalie in a specific game.
        
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
        
        # Filter events for this game
        game_events = events[events['GameID'] == game_id]
        
        # Calculate goals against - always use IsGoal and proper team identification
        goals_against_events = game_events[(game_events['IsGoal'] == True) & 
                                         (game_events['Team'] != your_team)]
        
        print(f"DEBUG: Found {len(goals_against_events)} goals against events for game {game_id}")
        print(f"DEBUG: Game events shape: {game_events.shape}")
        print(f"DEBUG: Game events columns: {game_events.columns.tolist()}")
        
        # Debug: Check team distribution in goal events
        if not game_events.empty:
            team_counts = game_events['Team'].value_counts()
            print(f"DEBUG: Team distribution in game events: {team_counts.to_dict()}")
            
            # Debug: Check IsGoal distribution
            if 'IsGoal' in game_events.columns:
                isgoal_counts = game_events['IsGoal'].value_counts()
                print(f"DEBUG: IsGoal distribution in game events: {isgoal_counts.to_dict()}")
        
        goals_against = len(goals_against_events)
        
        # Calculate shots against - ensure we count both shots and goals as shots
        # Count all shots and goals from opponents
        shots_events = game_events[(game_events['EventType'] == 'Shot') & 
                                 (game_events['Team'] != your_team)]
        
        # Also count goals as shots (if they're not already counted as shots)
        goals_as_shots = game_events[(game_events['IsGoal'] == True) & 
                                   (game_events['Team'] != your_team) &
                                   (game_events['EventType'] != 'Shot')]
        
        print(f"DEBUG: Found {len(shots_events)} shot events for game {game_id}")
        print(f"DEBUG: Found {len(goals_as_shots)} goal events counted as shots for game {game_id}")
        
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
        
        # Determine if this was a shutout
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
        
        print(f"DEBUG: Returning goalie game stats for game {game_id}: {result_dict}")
        return result_dict
    
    def get_player_game_log(self, player_id, team_id=None):
        """
        Get a game log for a player, optionally filtered by team.
        
        Args:
            player_id (str): The player ID
            team_id (str, optional): Team ID to filter by
            
        Returns:
            list: List of dictionaries containing game statistics
        """
        player_games = self.get_player_games(player_id, team_id)
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
        
        # Sort by game date
        game_log.sort(key=lambda x: x['game']['Date'])
        
        return game_log
    
    def calculate_team_stats(self, team_id=None):
        """
        Calculate team statistics.
        
        Args:
            team_id (str, optional): Team ID to filter by
            
        Returns:
            dict: Dictionary containing team statistics
        """
        games = self.get_games(team_id)
        
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
    
    def get_team_leaderboard(self, stat='points', position=None, limit=None, team_id=None):
        """
        Get a team leaderboard for a specific statistic.
        
        Args:
            stat (str): The statistic to rank by (points, goals, assists, plus_minus, jersey_number)
            position (str, optional): Filter by position (F, D, G)
            limit (int, optional): Maximum number of players to include. If None, includes all players.
            team_id (str, optional): Team ID to filter by
            
        Returns:
            list: List of dictionaries containing player statistics
        """
        players = self.get_players(team_id)
        
        # Filter by position if specified
        if position:
            players = players[players['Position'] == position]
        
        # Calculate stats for each player
        player_stats = []
        for _, player in players.iterrows():
            stats = self.calculate_player_stats(player['ID'], team_id)
            if stats:
                player_stats.append(stats)
        
        # Sort by the specified statistic
        if stat == 'jersey_number':
            # Sort by jersey number (ascending)
            player_stats.sort(key=lambda x: int(x['player']['JerseyNumber']) if str(x['player']['JerseyNumber']).isdigit() else float('inf'))
        elif stat in ['points', 'goals', 'assists', 'plus_minus', 'shots', 'penalty_minutes', 'games_played', 'goals_per_game']:
            player_stats.sort(key=lambda x: x[stat], reverse=True)
        
        # Limit the number of players if a limit is specified
        if limit is not None:
            return player_stats[:limit]
        else:
            # Return all players if no limit is specified
            return player_stats
    
    def calculate_goalie_stats(self, player_id, team_id=None):
        """
        Calculate statistics for a goalie.
        
        Args:
            player_id (str): The player ID
            team_id (str, optional): Team ID to filter by
            
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
        
        print(f"Calculating stats for goalie: {player_id}")
        
        events = self.get_events()
        print(f"Total events: {len(events)}")
        
        games = self.get_player_games(player_id, team_id)
        print(f"Goalie games count: {len(games)}")
        
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
        
        # Calculate goals against - always use IsGoal and proper team identification
        if your_team is not None:
            goals_against_events = events[(events['IsGoal'] == True) & 
                                         (events['Team'] != your_team) & 
                                         (events['GameID'].isin(games['ID']))]
        else:
            # Fallback to original logic if team detection fails
            goals_against_events = events[(events['IsGoal'] == True) & 
                                         (events['Team'] != 'your_team') & 
                                         (events['GameID'].isin(games['ID']))]
        
        print(f"Found {len(goals_against_events)} goals against for goalie {player_id}")
        
        # Debug: Check if there are any goal events for the goalie's games
        all_goal_events = events[(events['IsGoal'] == True) & 
                               (events['GameID'].isin(games['ID']))]
        print(f"Total goal events in goalie's games: {len(all_goal_events)}")
        
        # Debug: Check team distribution in goal events
        if not all_goal_events.empty:
            team_counts = all_goal_events['Team'].value_counts()
            print(f"Team distribution in goal events: {team_counts.to_dict()}")
        
        goals_against = len(goals_against_events)
        
        # Calculate shots against - ensure we count both shots and goals as shots
        if your_team is not None:
            # Count all shots and goals from opponents
            shots_events = events[(events['EventType'] == 'Shot') & 
                                 (events['Team'] != your_team) & 
                                 (events['GameID'].isin(games['ID']))]
            print(f"Shot events against: {len(shots_events)}")
            
            # Also count goals as shots (if they're not already counted as shots)
            goals_as_shots = events[(events['IsGoal'] == True) & 
                                   (events['Team'] != your_team) & 
                                   (events['GameID'].isin(games['ID'])) &
                                   (events['EventType'] != 'Shot')]
            print(f"Goal events counted as shots: {len(goals_as_shots)}")
            
            # Combine unique events
            shots_against = len(shots_events) + len(goals_as_shots)
        else:
            # Fallback to improved logic if team detection fails
            shots_against_events = events[((events['EventType'] == 'Shot') | (events['IsGoal'] == True)) & 
                                         (events['Team'] != 'your_team') & 
                                         (events['GameID'].isin(games['ID']))]
            shots_against = len(shots_against_events)
        
        print(f"Found {shots_against} shots against for goalie {player_id}")
        
        # Debug: Check if there are any shot events for the goalie's games
        all_shot_events = events[(events['EventType'] == 'Shot') & 
                               (events['GameID'].isin(games['ID']))]
        print(f"Total shot events in goalie's games: {len(all_shot_events)}")
        
        # Debug: Check team distribution in shot events
        if not all_shot_events.empty:
            team_counts = all_shot_events['Team'].value_counts()
            print(f"Team distribution in shot events: {team_counts.to_dict()}")
        
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
        
        # Calculate wins with error handling
        try:
            wins = len(games[games['Result'] == 'W'])
        except KeyError as e:
            print(f"Error calculating goalie wins: {e}")
            wins = 0
        
        # Special handling for goalies not in game roster
        if games_played == 0:
            print(f"WARNING: Goalie {player_id} not found in game roster for team {team_id}")
            print("This may indicate the goalie needs to be added to game rosters")
        
        # Calculate shutouts (games where goals against is 0)
        shutouts = 0
        for _, game in games.iterrows():
            game_goals_against = len(goals_against_events[goals_against_events['GameID'] == game['ID']])
            if game_goals_against == 0:
                shutouts += 1
        
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
        
        # Join with players to get position
        game_players = pd.merge(game_players, players[['ID', 'Position']], 
                               left_on='PlayerID', right_on='ID')
        
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
                print(f"Found {mask.sum()} events with IsGoal=True but EventType!='Goal', updating EventType")
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
