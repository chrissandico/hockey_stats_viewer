import pandas as pd
import numpy as np

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
        
        # Force refresh all data if requested
        if force_refresh:
            print("Forcing refresh of all data...")
            self.sheets_service.refresh_all_data()
    
    def get_players(self):
        """
        Get all players.
        
        Returns:
            pd.DataFrame: DataFrame containing player data
        """
        return self.sheets_service.get_players()
    
    def get_games(self):
        """
        Get all games with calculated goal statistics.
        
        Returns:
            pd.DataFrame: DataFrame containing game data with calculated columns
        """
        games = self.sheets_service.get_games()
        events = self.sheets_service.get_events()
        
        # Print columns for debugging
        print("Games columns:", games.columns.tolist())
        
        # Add GoalsFor and GoalsAgainst columns
        if not games.empty:
            # Initialize columns with zeros
            games['GoalsFor'] = 0
            games['GoalsAgainst'] = 0
            
            # Calculate goals for each game
            for idx, game in games.iterrows():
                game_events = events[events['GameID'] == game['ID']]
                
                # Always use IsGoal column for goal determination
                goals_for = len(game_events[(game_events['IsGoal'] == True) & 
                                          (game_events['Team'] == 'your_team')])
                goals_against = len(game_events[(game_events['IsGoal'] == True) & 
                                              (game_events['Team'] != 'your_team')])
                print(f"Using IsGoal column for game {game['ID']}: {goals_for} goals for, {goals_against} goals against")
                
                games.at[idx, 'GoalsFor'] = goals_for
                games.at[idx, 'GoalsAgainst'] = goals_against
            
            print("Sample game data:", games.iloc[0].to_dict())
        
        # Always ensure Result column exists
        self._ensure_result_column(games)
        
        return games
    
    def _ensure_result_column(self, games):
        """
        Ensure the Result column exists in the games DataFrame.
        
        Args:
            games (pd.DataFrame): DataFrame containing game data
            
        Returns:
            pd.DataFrame: DataFrame with Result column added if needed
        """
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
    
    def get_game_roster(self):
        """
        Get all game roster data.
        
        Returns:
            pd.DataFrame: DataFrame containing game roster data
        """
        return self.sheets_service.get_game_roster()
    
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
    
    def get_game_by_id(self, game_id):
        """
        Get a game by ID.
        
        Args:
            game_id (str): The game ID
            
        Returns:
            pd.Series: The game data
        """
        games = self.get_games()
        return games[games['ID'] == game_id].iloc[0] if not games[games['ID'] == game_id].empty else None
    
    def get_player_games(self, player_id):
        """
        Get all games a player participated in.
        
        Args:
            player_id (str): The player ID
            
        Returns:
            pd.DataFrame: DataFrame containing game data
        """
        game_roster = self.get_game_roster()
        games = self.get_games()
        
        # Get game IDs where the player was present
        player_game_ids = game_roster[(game_roster['PlayerID'] == player_id) & 
                                     (game_roster['Status'] == 'Present')]['GameID'].tolist()
        
        # Filter games by these IDs
        return games[games['ID'].isin(player_game_ids)]
    
    def calculate_player_stats(self, player_id):
        """
        Calculate statistics for a player.
        
        Args:
            player_id (str): The player ID
            
        Returns:
            dict: Dictionary containing player statistics
        """
        player = self.get_player_by_id(player_id)
        if player is None:
            return None
        
        events = self.get_events()
        games = self.get_player_games(player_id)
        
        # Filter events for this player
        player_events = events[events['PrimaryPlayerID'] == player_id]
        
        # Calculate goals - always use IsGoal
        goals = len(player_events[(player_events['IsGoal'] == True)])
        print(f"Using IsGoal column for player {player_id}: {goals} goals")
        
        # Calculate assists
        assist1_events = events[events['AssistPlayer1ID'] == player_id]
        assist2_events = events[events['AssistPlayer2ID'] == player_id]
        assists = len(assist1_events) + len(assist2_events)
        
        # Calculate points
        points = goals + assists
        
        # Calculate plus/minus - always use IsGoal
        # Parse YourTeamPlayersOnIce as a list and check if player_id is in it
        def is_player_on_ice(players_str, pid):
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
        
        plus_events = events[(events['YourTeamPlayersOnIce'].apply(lambda x: is_player_on_ice(x, player_id))) & 
                            (events['IsGoal'] == True) & 
                            (events['Team'] == 'your_team')]
        minus_events = events[(events['YourTeamPlayersOnIce'].apply(lambda x: is_player_on_ice(x, player_id))) & 
                             (events['IsGoal'] == True) & 
                             (events['Team'] != 'your_team')]
        print(f"Using IsGoal column for plus/minus calculation for player {player_id}: +{len(plus_events)}, -{len(minus_events)}")
        
        plus_minus = len(plus_events) - len(minus_events)
        
        # Calculate shots
        shots = len(player_events[player_events['EventType'] == 'Shot'])
        
        # Calculate penalty minutes
        penalty_events = player_events[player_events['EventType'] == 'Penalty']
        penalty_minutes = penalty_events['PenaltyDuration'].sum() if not penalty_events.empty else 0
        
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
    
    def calculate_player_game_stats(self, player_id, game_id):
        """
        Calculate statistics for a player in a specific game.
        
        Args:
            player_id (str): The player ID
            game_id (str): The game ID
            
        Returns:
            dict: Dictionary containing player game statistics
        """
        player = self.get_player_by_id(player_id)
        game = self.get_game_by_id(game_id)
        
        if player is None or game is None:
            return None
        
        events = self.get_events()
        
        # Filter events for this player and game
        game_events = events[events['GameID'] == game_id]
        player_game_events = game_events[game_events['PrimaryPlayerID'] == player_id]
        
        # Calculate goals - always use IsGoal
        goals = len(player_game_events[(player_game_events['IsGoal'] == True)])
        print(f"Using IsGoal column for player {player_id} in game {game_id}: {goals} goals")
        
        # Calculate assists
        assist1_events = game_events[game_events['AssistPlayer1ID'] == player_id]
        assist2_events = game_events[game_events['AssistPlayer2ID'] == player_id]
        assists = len(assist1_events) + len(assist2_events)
        
        # Calculate points
        points = goals + assists
        
        # Calculate plus/minus - always use IsGoal
        # Parse YourTeamPlayersOnIce as a list and check if player_id is in it
        def is_player_on_ice(players_str, pid):
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
        
        plus_events = game_events[(game_events['YourTeamPlayersOnIce'].apply(lambda x: is_player_on_ice(x, player_id))) & 
                                 (game_events['IsGoal'] == True) & 
                                 (game_events['Team'] == 'your_team')]
        minus_events = game_events[(game_events['YourTeamPlayersOnIce'].apply(lambda x: is_player_on_ice(x, player_id))) & 
                                  (game_events['IsGoal'] == True) & 
                                  (game_events['Team'] != 'your_team')]
        print(f"Using IsGoal column for plus/minus calculation for player {player_id} in game {game_id}: +{len(plus_events)}, -{len(minus_events)}")
        
        plus_minus = len(plus_events) - len(minus_events)
        
        # Calculate shots
        shots = len(player_game_events[player_game_events['EventType'] == 'Shot'])
        
        # Calculate penalty minutes
        penalty_events = player_game_events[player_game_events['EventType'] == 'Penalty']
        penalty_minutes = penalty_events['PenaltyDuration'].sum() if not penalty_events.empty else 0
        
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
    
    def get_player_game_log(self, player_id):
        """
        Get a game log for a player.
        
        Args:
            player_id (str): The player ID
            
        Returns:
            list: List of dictionaries containing game statistics
        """
        player_games = self.get_player_games(player_id)
        
        game_log = []
        for _, game in player_games.iterrows():
            game_stats = self.calculate_player_game_stats(player_id, game['ID'])
            if game_stats:
                game_log.append(game_stats)
        
        # Sort by game date
        game_log.sort(key=lambda x: x['game']['Date'])
        
        return game_log
    
    def calculate_team_stats(self):
        """
        Calculate team statistics.
        
        Returns:
            dict: Dictionary containing team statistics
        """
        games = self.get_games()
        
        # Ensure Result column exists
        games = self._ensure_result_column(games)
        
        # Calculate wins, losses, and ties with error handling
        try:
            wins = len(games[games['Result'] == 'W'])
            losses = len(games[games['Result'] == 'L'])
            ties = len(games[games['Result'] == 'T'])
        except KeyError as e:
            print(f"Error calculating team stats: {e}")
            wins = 0
            losses = 0
            ties = 0
        
        # Calculate points (2 for win, 1 for tie)
        points = wins * 2 + ties
        
        # Calculate goals for and against with error handling
        try:
            goals_for = games['GoalsFor'].sum()
            goals_against = games['GoalsAgainst'].sum()
        except KeyError as e:
            print(f"Error calculating goals: {e}")
            goals_for = 0
            goals_against = 0
        
        # Calculate win percentage
        games_played = len(games)
        win_percentage = wins / games_played if games_played > 0 else 0
        
        return {
            'games_played': games_played,
            'wins': wins,
            'losses': losses,
            'ties': ties,
            'points': points,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'win_percentage': win_percentage
        }
    
    def get_team_leaderboard(self, stat='points', position=None, limit=5):
        """
        Get a team leaderboard for a specific statistic.
        
        Args:
            stat (str): The statistic to rank by (points, goals, assists, plus_minus)
            position (str, optional): Filter by position (F, D, G)
            limit (int): Maximum number of players to include
            
        Returns:
            list: List of dictionaries containing player statistics
        """
        players = self.get_players()
        
        # Filter by position if specified
        if position:
            players = players[players['Position'] == position]
        
        # Calculate stats for each player
        player_stats = []
        for _, player in players.iterrows():
            stats = self.calculate_player_stats(player['ID'])
            if stats:
                player_stats.append(stats)
        
        # Sort by the specified statistic
        if stat in ['points', 'goals', 'assists', 'plus_minus', 'shots', 'penalty_minutes', 'games_played', 'goals_per_game']:
            player_stats.sort(key=lambda x: x[stat], reverse=True)
        
        # Limit the number of players
        return player_stats[:limit]
    
    def calculate_goalie_stats(self, player_id):
        """
        Calculate statistics for a goalie.
        
        Args:
            player_id (str): The player ID
            
        Returns:
            dict: Dictionary containing goalie statistics
        """
        player = self.get_player_by_id(player_id)
        if player is None or player['Position'] != 'G':
            return None
        
        events = self.get_events()
        games = self.get_player_games(player_id)
        
        # Ensure Result column exists
        games = self._ensure_result_column(games)
        
        # Calculate goals against - always use IsGoal
        goals_against_events = events[(events['IsGoal'] == True) & 
                                     (events['Team'] != 'your_team') & 
                                     (events['GameID'].isin(games['ID']))]
        print(f"Using IsGoal column for goalie {player_id}: {len(goals_against_events)} goals against")
        
        goals_against = len(goals_against_events)
        
        # Calculate shots against
        shots_against_events = events[(events['EventType'].isin(['Goal', 'Shot'])) & 
                                     (events['Team'] != 'your_team') & 
                                     (events['GameID'].isin(games['ID']))]
        shots_against = len(shots_against_events)
        
        # Calculate saves
        saves = shots_against - goals_against
        
        # Calculate save percentage
        save_percentage = saves / shots_against if shots_against > 0 else 0
        
        # Calculate games played
        games_played = len(games)
        
        # Calculate wins with error handling
        try:
            wins = len(games[games['Result'] == 'W'])
        except KeyError as e:
            print(f"Error calculating goalie wins: {e}")
            wins = 0
        
        # Calculate shutouts (games where goals against is 0)
        shutouts = 0
        for _, game in games.iterrows():
            game_goals_against = len(goals_against_events[goals_against_events['GameID'] == game['ID']])
            if game_goals_against == 0:
                shutouts += 1
        
        # Calculate goals against average
        gaa = goals_against / games_played if games_played > 0 else 0
        
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
    
    def get_game_player_stats(self, game_id, position=None):
        """
        Get player statistics for a specific game.
        
        Args:
            game_id (str): The game ID
            position (str, optional): Filter by position (F, D, G)
            
        Returns:
            list: List of dictionaries containing player game statistics
        """
        game_roster = self.get_game_roster()
        players = self.get_players()
        
        # Get players who were present for this game
        game_players = game_roster[(game_roster['GameID'] == game_id) & 
                                  (game_roster['Status'] == 'Present')]
        
        # Join with players to get position
        game_players = pd.merge(game_players, players[['ID', 'Position']], 
                               left_on='PlayerID', right_on='ID')
        
        # Filter by position if specified
        if position:
            game_players = game_players[game_players['Position'] == position]
        
        # Calculate stats for each player
        player_stats = []
        for _, player_row in game_players.iterrows():
            stats = self.calculate_player_game_stats(player_row['PlayerID'], game_id)
            if stats:
                player_stats.append(stats)
        
        # Sort by points
        player_stats.sort(key=lambda x: x['points'], reverse=True)
        
        return player_stats
    
    def get_game_summary(self, game_id):
        """
        Get a summary of a game.
        
        Args:
            game_id (str): The game ID
            
        Returns:
            dict: Dictionary containing game summary
        """
        game = self.get_game_by_id(game_id)
        if game is None:
            return None
        
        events = self.get_events()
        game_events = events[events['GameID'] == game_id]
        
        # Calculate shots
        your_team_shots = len(game_events[(game_events['EventType'].isin(['Goal', 'Shot'])) & 
                                         (game_events['Team'] == 'your_team')])
        opponent_shots = len(game_events[(game_events['EventType'].isin(['Goal', 'Shot'])) & 
                                        (game_events['Team'] != 'your_team')])
        
        # Calculate penalty minutes
        your_team_penalties = game_events[(game_events['EventType'] == 'Penalty') & 
                                         (game_events['Team'] == 'your_team')]
        opponent_penalties = game_events[(game_events['EventType'] == 'Penalty') & 
                                        (game_events['Team'] != 'your_team')]
        
        your_team_pim = your_team_penalties['PenaltyDuration'].sum() if not your_team_penalties.empty else 0
        opponent_pim = opponent_penalties['PenaltyDuration'].sum() if not opponent_penalties.empty else 0
        
        # Calculate power play goals - always use IsGoal
        your_team_pp_goals = len(game_events[(game_events['IsGoal'] == True) & 
                                           (game_events['Team'] == 'your_team') & 
                                           (game_events.get('IsPowerPlay', False) == True)])
        opponent_pp_goals = len(game_events[(game_events['IsGoal'] == True) & 
                                          (game_events['Team'] != 'your_team') & 
                                          (game_events.get('IsPowerPlay', False) == True)])
        print(f"Using IsGoal column for power play goals in game {game_id}")
        
        # If IsPowerPlay column doesn't exist, try to estimate power play goals
        if your_team_pp_goals == 0 and opponent_pp_goals == 0:
            # Check if there are penalties in the game
            if not your_team_penalties.empty or not opponent_penalties.empty:
                # Estimate power play goals based on timing of goals and penalties
                # This is a simplified approach - in a real app, you'd need more detailed logic
                your_team_pp_goals = len(game_events[(game_events['IsGoal'] == True) & 
                                                   (game_events['Team'] == 'your_team') & 
                                                   (~game_events.get('IsShortHanded', False))])
                opponent_pp_goals = len(game_events[(game_events['IsGoal'] == True) & 
                                                  (game_events['Team'] != 'your_team') & 
                                                  (~game_events.get('IsShortHanded', False))])
        
        # Calculate power play opportunities
        your_team_pp_opps = len(opponent_penalties)
        opponent_pp_opps = len(your_team_penalties)
        
        # Calculate power play percentage
        your_team_pp_pct = your_team_pp_goals / your_team_pp_opps if your_team_pp_opps > 0 else 0
        opponent_pp_pct = opponent_pp_goals / opponent_pp_opps if opponent_pp_opps > 0 else 0
        
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
