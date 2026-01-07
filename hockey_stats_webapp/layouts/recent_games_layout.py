"""
Recent Games Analysis Layout

Coach-only page for viewing aggregated statistics from the last N games.
Allows coaches to analyze recent performance trends for both team and individual players.
"""

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
from flask import session
import pandas as pd
import logging

from layouts.navigation import create_navigation
from components.game_type_filter import create_game_type_filter_component, create_game_type_session_store
import config

logger = logging.getLogger(__name__)


def create_recent_games_layout(data_service, team_context=None):
    """
    Create the recent games analysis layout (coach-only).

    Args:
        data_service (DataService): The data service for retrieving stats
        team_context (dict, optional): Team context containing team_id and team_name

    Returns:
        dash.html.Div: The recent games analysis layout
    """

    return html.Div([
        # Navigation bar
        create_navigation(),

        # Title
        html.Div([
            html.H1([
                html.I(className="fas fa-fire me-3"),
                "Recent Games Analysis"
            ], className="text-center mt-4 mb-2"),
            html.P("Analyze team and player performance over recent games",
                   className="text-center text-muted mb-4")
        ]),

        # Coach access check container
        html.Div(id='recent-games-access-check'),

        # Main content (will be populated by callback if coach)
        html.Div(id='recent-games-content')
    ])


def _create_recent_games_content():
    """Create the main content for recent games analysis (for coaches only)."""

    return dbc.Container([
        # Controls row
        dbc.Row([
            dbc.Col([
                # Game count selector card
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-list-ol me-2"),
                            "Select Number of Games"
                        ], className="card-title mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Select(
                            id='game-count-selector',
                            options=[
                                {'label': f'Last {i} Games', 'value': i}
                                for i in range(2, 11)
                            ],
                            value=5,  # Default to 5 games
                            className="mb-2"
                        ),
                        html.Small("Select how many recent games to analyze",
                                  className="text-muted")
                    ])
                ], className="mb-4 shadow-sm")
            ], md=4),

            dbc.Col([
                # Game type filter
                create_game_type_filter_component()
            ], md=8)
        ]),

        # Session stores
        create_game_type_session_store(),
        dcc.Store(id='recent-games-count-store', storage_type='session', data=5),

        # Team performance section
        dcc.Loading(
            id="team-perf-loading",
            type="default",
            color="#00205b",
            children=[
                html.Div(id='team-performance-section')
            ]
        ),

        # Player leaderboards section
        dcc.Loading(
            id="leaderboards-loading",
            type="default",
            color="#00205b",
            children=[
                html.Div(id='player-leaderboards-section')
            ]
        )
    ], fluid=True)


def _create_access_denied_layout():
    """Create access denied layout for non-coaches."""

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H4("Access Denied", className="alert-heading"),
                    html.P("You don't have permission to access the Recent Games Analysis."),
                    html.Hr(),
                    html.P("This feature is only available to coaches.", className="mb-0"),
                    html.Div([
                        dbc.Button("Go to Home", href="/", color="primary", className="mt-3")
                    ])
                ], color="warning")
            ], md=8, className="mx-auto mt-5")
        ])
    ], className="mt-5")


def _aggregate_recent_games_team_stats(recent_games, data_service, team_id):
    """
    Aggregate team statistics from recent games.

    Args:
        recent_games (pd.DataFrame): DataFrame of recent games
        data_service (DataService): The data service
        team_id (str): Team identifier

    Returns:
        dict: Aggregated team statistics
    """
    if recent_games.empty:
        return {
            'games_played': 0,
            'wins': 0,
            'losses': 0,
            'ties': 0,
            'goals_for': 0,
            'goals_against': 0,
            'shots_for': 0,
            'shots_against': 0,
            'penalties': 0,
            'penalty_minutes': 0,
            'win_percentage': 0.0
        }

    # Ensure we're working with a clean dataframe
    recent_games = recent_games.reset_index(drop=True)

    # Calculate W-L-T record
    if 'Result' in recent_games.columns:
        wins = len(recent_games[recent_games['Result'] == 'W'])
        losses = len(recent_games[recent_games['Result'] == 'L'])
        ties = len(recent_games[recent_games['Result'] == 'T'])
    else:
        wins = losses = ties = 0

    # Calculate goals
    goals_for = recent_games['GoalsFor'].sum() if 'GoalsFor' in recent_games.columns else 0
    goals_against = recent_games['GoalsAgainst'].sum() if 'GoalsAgainst' in recent_games.columns else 0

    # Get game IDs for event-based stats
    game_ids = recent_games['ID'].tolist() if 'ID' in recent_games.columns else []

    if not game_ids:
        games_played = len(recent_games)
        win_percentage = (wins / games_played) if games_played > 0 else 0.0
        return {
            'games_played': games_played,
            'wins': wins,
            'losses': losses,
            'ties': ties,
            'goals_for': int(goals_for),
            'goals_against': int(goals_against),
            'shots_for': 0,
            'shots_against': 0,
            'penalties': 0,
            'penalty_minutes': 0,
            'win_percentage': win_percentage
        }

    # Get events for these games to calculate shots and penalties
    all_events = data_service.get_events()
    recent_events = all_events[all_events['GameID'].isin(game_ids)]

    # Get team identifier for events
    team_identifier = data_service._get_team_identifier_for_events(team_id)

    # Calculate shots (all shot events for this team)
    team_shot_events = recent_events[
        (recent_events['EventType'] == 'Shot') &
        (recent_events['Team'] == team_identifier)
    ]
    shots_for = len(team_shot_events)

    # Shots against (shots by opponent teams)
    opponent_shot_events = recent_events[
        (recent_events['EventType'] == 'Shot') &
        (recent_events['Team'] != team_identifier)
    ]
    shots_against = len(opponent_shot_events)

    # Calculate penalties
    team_penalty_events = recent_events[
        (recent_events['EventType'] == 'Penalty') &
        (recent_events['Team'] == team_identifier)
    ]
    penalties = len(team_penalty_events)
    penalty_minutes = team_penalty_events['PenaltyDuration'].sum() if 'PenaltyDuration' in team_penalty_events.columns else 0

    # Calculate win percentage
    games_played = len(recent_games)
    win_percentage = (wins / games_played) if games_played > 0 else 0.0

    return {
        'games_played': games_played,
        'wins': wins,
        'losses': losses,
        'ties': ties,
        'goals_for': int(goals_for),
        'goals_against': int(goals_against),
        'shots_for': shots_for,
        'shots_against': shots_against,
        'penalties': penalties,
        'penalty_minutes': int(penalty_minutes),
        'win_percentage': win_percentage
    }


def _create_team_performance_card(team_stats, num_games_requested, num_games_actual):
    """
    Create the team performance card display with 4-column layout.

    Args:
        team_stats (dict): Aggregated team statistics
        num_games_requested (int): Number of games requested by user
        num_games_actual (int): Actual number of games available

    Returns:
        dbc.Card: The team performance card
    """
    # Calculate differentials
    goal_diff = team_stats['goals_for'] - team_stats['goals_against']
    shot_diff = team_stats['shots_for'] - team_stats['shots_against']

    # Warning message if fewer games than requested
    warning_msg = None
    if num_games_actual < num_games_requested:
        warning_msg = dbc.Alert(
            f"Showing {num_games_actual} of requested {num_games_requested} games (all available games shown)",
            color="info",
            className="mb-3"
        )

    return dbc.Card([
        dbc.CardHeader(html.H4(f"Summary - Last {num_games_actual} Games", className="card-title")),
        dbc.CardBody([
            warning_msg,
            dbc.Row([
                # Record column
                dbc.Col([
                    html.H5("Record"),
                    html.Div([
                        html.Div([
                            html.Span("Games Played: ", className="fw-bold"),
                            html.Span(f"{team_stats['games_played']}")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("Wins: ", className="fw-bold"),
                            html.Span(f"{team_stats['wins']}")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("Losses: ", className="fw-bold"),
                            html.Span(f"{team_stats['losses']}")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("Ties: ", className="fw-bold"),
                            html.Span(f"{team_stats['ties']}")
                        ], className="mb-1"),
                    ])
                ], md=3),

                # Goals column
                dbc.Col([
                    html.H5("Goals"),
                    html.Div([
                        html.Div([
                            html.Span("Goals For: ", className="fw-bold"),
                            html.Span(f"{team_stats['goals_for']}")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("Goals Against: ", className="fw-bold"),
                            html.Span(f"{team_stats['goals_against']}")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("Goal Differential: ", className="fw-bold"),
                            html.Span(f"{goal_diff}")
                        ], className="mb-1"),
                    ])
                ], md=3),

                # Shots column
                dbc.Col([
                    html.H5("Shots"),
                    html.Div([
                        html.Div([
                            html.Span("Shots For: ", className="fw-bold"),
                            html.Span(f"{team_stats['shots_for']}")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("Shots Against: ", className="fw-bold"),
                            html.Span(f"{team_stats['shots_against']}")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("Shot Differential: ", className="fw-bold"),
                            html.Span(f"{shot_diff}")
                        ], className="mb-1"),
                    ])
                ], md=3),

                # Penalties column
                dbc.Col([
                    html.H5("Penalties"),
                    html.Div([
                        html.Div([
                            html.Span("Penalties: ", className="fw-bold"),
                            html.Span(f"{team_stats['penalties']}")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("Penalty Minutes: ", className="fw-bold"),
                            html.Span(f"{team_stats['penalty_minutes']}")
                        ], className="mb-1"),
                    ])
                ], md=3),
            ])
        ])
    ], className="mb-4 shadow-sm")


def _calculate_player_stats_for_games(player_id, game_ids, data_service, team_id):
    """
    Calculate player statistics for specific games.

    Args:
        player_id (int): Player ID
        game_ids (list): List of game IDs to include
        data_service (DataService): The data service
        team_id (str): Team identifier

    Returns:
        dict: Player statistics for the specified games
    """
    # Get all events
    all_events = data_service.get_events()

    # Filter to only events from specified games
    events = all_events[all_events['GameID'].isin(game_ids)]

    # Get team identifier for filtering
    team_identifier = data_service._get_team_identifier_for_events(team_id)

    # Calculate stats using existing helper methods
    goals = data_service.calculate_goals_for_events(player_id, events)
    assists = data_service.calculate_assists_for_events(player_id, events)
    points = goals + assists
    plus_minus = data_service.calculate_plus_minus_for_events(player_id, events, team_identifier)

    # Count games played
    player_events = events[
        (events['PrimaryPlayerID'] == player_id) |
        (events['AssistPlayer1ID'] == player_id) |
        (events['AssistPlayer2ID'] == player_id)
    ]
    games_played = player_events['GameID'].nunique() if not player_events.empty else 0

    return {
        'goals': goals,
        'assists': assists,
        'points': points,
        'plus_minus': plus_minus,
        'games_played': games_played
    }


def _calculate_goalie_stats_for_games(player_id, game_ids, data_service, team_id):
    """
    Calculate goalie statistics for specific games.

    Args:
        player_id (int): Goalie player ID
        game_ids (list): List of game IDs to include
        data_service (DataService): The data service
        team_id (str): Team identifier

    Returns:
        dict: Goalie statistics for the specified games
    """
    # Get all events
    all_events = data_service.get_events()

    # Filter to only events from specified games
    events = all_events[all_events['GameID'].isin(game_ids)]

    # Get team identifier
    team_identifier = data_service._get_team_identifier_for_events(team_id)

    # Filter events where this goalie was on ice
    goalie_events = events[events['GoalieOnIceId'] == player_id]

    # Calculate stats
    opponent_shot_events = goalie_events[goalie_events['Team'] != team_identifier]
    shots_against = len(opponent_shot_events[opponent_shot_events['EventType'] == 'Shot'])
    goals_against = len(opponent_shot_events[opponent_shot_events['IsGoal'] == True])

    saves = shots_against - goals_against
    save_percentage = (saves / shots_against * 100) if shots_against > 0 else 0.0

    # Count games played - games where goalie faced at least 1 shot
    games_with_shots = goalie_events[
        (goalie_events['Team'] != team_identifier) &
        (goalie_events['EventType'] == 'Shot')
    ]['GameID'].nunique()

    # Calculate wins, losses, ties from game results
    games_data = data_service.get_games(team_id)
    goalie_games = games_data[games_data['ID'].isin(game_ids)]
    wins = len(goalie_games[goalie_games['Result'] == 'W'])
    losses = len(goalie_games[goalie_games['Result'] == 'L'])
    ties = len(goalie_games[goalie_games['Result'] == 'T'])

    # Calculate shutouts (games with 0 goals against)
    shutouts = 0
    for game_id in game_ids:
        game_events = goalie_events[goalie_events['GameID'] == game_id]
        opponent_goals = game_events[
            (game_events['Team'] != team_identifier) &
            (game_events['IsGoal'] == True)
        ]
        if len(game_events) > 0 and len(opponent_goals) == 0:
            shutouts += 1

    # Calculate GAA (goals against average)
    gaa = (goals_against / games_with_shots) if games_with_shots > 0 else 0.0

    return {
        'games_played': games_with_shots,
        'wins': wins,
        'losses': losses,
        'ties': ties,
        'shutouts': shutouts,
        'saves': saves,
        'shots_against': shots_against,
        'goals_against': goals_against,
        'save_percentage': round(save_percentage, 1),
        'gaa': round(gaa, 2)
    }


def _create_leaderboard_table(leaderboard_data, stat_columns, title):
    """
    Create a leaderboard table matching Team Stats screen format.

    Args:
        leaderboard_data (list): List of player stat dicts
        stat_columns (list): List of tuples (column_name, display_name, type)
        title (str): Table title

    Returns:
        dbc.Card: The leaderboard card with table
    """
    if not leaderboard_data:
        return dbc.Card([
            dbc.CardHeader(html.H4(title, className="card-title")),
            dbc.CardBody([
                dbc.Alert("No data available for this period", color="info")
            ])
        ], className="mb-4 shadow-sm")

    # Create DataFrame
    df = pd.DataFrame(leaderboard_data)

    # Create columns for DataTable matching team stats format
    columns = [{'name': 'Player', 'id': 'player', 'type': 'text'}]
    columns.extend([{'name': display, 'id': col, 'type': col_type} for col, display, col_type in stat_columns])

    # Format player display
    for item in leaderboard_data:
        item['player'] = f"#{item['jersey_number']}"

    return dbc.Card([
        dbc.CardHeader(html.H4(title, className="card-title")),
        dbc.CardBody([
            dash_table.DataTable(
                data=leaderboard_data,
                columns=columns,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'minWidth': '80px'
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'player'},
                        'textAlign': 'left'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                sort_action='native',
                sort_mode='single'
            )
        ])
    ], className="mb-4 shadow-sm")


def register_recent_games_callbacks(app, data_service):
    """
    Register callbacks for the recent games analysis page.

    Args:
        app (dash.Dash): The Dash application
        data_service (DataService): The data service
    """

    @app.callback(
        [Output('recent-games-access-check', 'children'),
         Output('recent-games-content', 'children')],
        [Input('url', 'pathname')],
        prevent_initial_call=False
    )
    def check_coach_access(pathname):
        """Check if user is a coach and display appropriate content."""
        if pathname != '/recent-games':
            return [], []

        try:
            # Check if user is authenticated and is a coach
            if 'team_name' not in session or 'is_coach' not in session:
                return _create_access_denied_layout(), []

            if not session.get('is_coach', False):
                return _create_access_denied_layout(), []

            # User is authorized, show the dashboard
            return [], _create_recent_games_content()

        except Exception as e:
            logger.error(f"Error in coach access check: {e}")
            return _create_access_denied_layout(), []

    @app.callback(
        Output('recent-games-count-store', 'data'),
        [Input('game-count-selector', 'value')]
    )
    def update_game_count_store(game_count):
        """Store the selected game count."""
        return game_count

    @app.callback(
        Output('team-performance-section', 'children'),
        [Input('recent-games-count-store', 'data'),
         Input('game-type-session-store', 'data')]
    )
    def update_team_performance(num_games, game_type_data):
        """Update team performance stats for selected recent games."""
        try:
            # Get team context from session
            if not session.get('authenticated', False):
                return dbc.Alert("Not authenticated", color="danger")

            team_id = session.get('team_id')
            if not team_id:
                return dbc.Alert("No team selected", color="danger")

            # Parse game type
            game_type = None if game_type_data == "all" else game_type_data

            # Get games filtered by team and game type
            games = data_service.get_games(team_id, game_type)
            games = data_service._filter_games_by_date(games, include_future=False)

            if games.empty:
                return dbc.Alert("No games found for selected filters", color="info")

            # Sort by date and get N most recent
            # Convert Date to datetime for proper sorting and reset index
            games = games.copy()
            games['DateSortable'] = pd.to_datetime(games['Date'], errors='coerce')
            games_sorted = games.sort_values('DateSortable', ascending=False).reset_index(drop=True)

            # Convert num_games to int (it comes as string from dcc.Store)
            num_games = int(num_games) if num_games else 5
            recent_games = games_sorted.head(num_games)

            # Ensure clean dataframe before passing to aggregation
            recent_games = recent_games.copy()

            # Aggregate team stats
            team_stats = _aggregate_recent_games_team_stats(recent_games, data_service, team_id)

            # Create and return card
            return _create_team_performance_card(team_stats, num_games, len(recent_games))

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error updating team performance: {e}\n{error_details}")
            return dbc.Alert([
                html.H5("Error loading team stats", className="alert-heading"),
                html.P(f"{str(e)}"),
                html.Hr(),
                html.Pre(error_details, style={"fontSize": "10px", "maxHeight": "200px", "overflow": "auto"})
            ], color="danger")

    @app.callback(
        Output('player-leaderboards-section', 'children'),
        [Input('recent-games-count-store', 'data'),
         Input('game-type-session-store', 'data')]
    )
    def update_player_leaderboards(num_games, game_type_data):
        """Update player leaderboards for selected recent games."""
        try:
            # Get team context from session
            if not session.get('authenticated', False):
                return dbc.Alert("Not authenticated", color="danger")

            team_id = session.get('team_id')
            if not team_id:
                return dbc.Alert("No team selected", color="danger")

            # Parse game type
            game_type = None if game_type_data == "all" else game_type_data

            # Get games filtered by team and game type
            games = data_service.get_games(team_id, game_type)
            games = data_service._filter_games_by_date(games, include_future=False)

            if games.empty:
                return dbc.Alert("No games found for selected filters", color="info")

            # Sort by date and get N most recent
            # Convert Date to datetime for proper sorting and reset index
            games = games.copy()
            games['DateSortable'] = pd.to_datetime(games['Date'], errors='coerce')
            games_sorted = games.sort_values('DateSortable', ascending=False).reset_index(drop=True)

            # Convert num_games to int (it comes as string from dcc.Store)
            num_games = int(num_games) if num_games else 5
            recent_games = games_sorted.head(num_games)

            # Ensure clean dataframe
            recent_games = recent_games.copy()
            game_ids = recent_games['ID'].tolist() if 'ID' in recent_games.columns else []

            if not game_ids:
                return dbc.Alert("No game IDs found in selected games", color="warning")

            # Get all players on team
            players = data_service.get_players(team_id)

            # Calculate stats for each player for recent games only
            skater_stats = []
            goalie_stats = []

            for _, player in players.iterrows():
                # Use centralized helper method for player ID
                player_id = data_service._get_player_id_from_series(player)
                if player_id is None:
                    continue  # Skip if no valid player ID

                jersey_num = player.get('JerseyNumber', 0)
                first_name = player.get('FirstName', '')
                last_name = player.get('LastName', '')
                name = f"{first_name} {last_name}".strip()
                position = player.get('Position', 'F')

                if position == 'G':
                    # Goalie stats
                    stats = _calculate_goalie_stats_for_games(player_id, game_ids, data_service, team_id)
                    if stats['games_played'] > 0:  # Only include if played
                        goalie_stats.append({
                            'jersey_number': jersey_num,
                            'name': name,
                            'games_played': stats['games_played'],
                            'wins': stats['wins'],
                            'saves': stats['saves'],
                            'save_percentage': stats['save_percentage']
                        })
                else:
                    # Skater stats
                    stats = _calculate_player_stats_for_games(player_id, game_ids, data_service, team_id)
                    if stats['games_played'] > 0:  # Only include if played
                        skater_stats.append({
                            'jersey_number': jersey_num,
                            'name': name,
                            'games_played': stats['games_played'],
                            'goals': stats['goals'],
                            'assists': stats['assists'],
                            'points': stats['points'],
                            'plus_minus': stats['plus_minus']
                        })

            # Sort leaderboards
            goals_leaders = sorted(skater_stats, key=lambda x: (-x['goals'], -x['points']))[:5]
            points_leaders = sorted(skater_stats, key=lambda x: (-x['points'], -x['goals']))[:5]
            plus_minus_leaders = sorted(skater_stats, key=lambda x: (-x['plus_minus'], -x['points']))[:5]
            goalie_leaders = sorted(goalie_stats, key=lambda x: (-x['save_percentage'], -x['saves']))[:3]

            # Create leaderboard tables matching Team Stats format
            return dbc.Row([
                dbc.Col([
                    _create_leaderboard_table(
                        goals_leaders,
                        [('goals', 'G', 'numeric'), ('games_played', 'GP', 'numeric')],
                        "Goals Leaders"
                    )
                ], md=6),
                dbc.Col([
                    _create_leaderboard_table(
                        points_leaders,
                        [('goals', 'G', 'numeric'), ('assists', 'A', 'numeric'), ('points', 'P', 'numeric')],
                        "Points Leaders"
                    )
                ], md=6),
                dbc.Col([
                    _create_leaderboard_table(
                        plus_minus_leaders,
                        [('goals', 'G', 'numeric'), ('assists', 'A', 'numeric'), ('points', 'P', 'numeric'), ('plus_minus', '+/-', 'numeric')],
                        "Plus/Minus Leaders"
                    )
                ], md=6, className="mt-4"),
                dbc.Col([
                    _create_leaderboard_table(
                        goalie_leaders,
                        [('wins', 'W', 'numeric'), ('saves', 'SVS', 'numeric'), ('save_percentage', 'SV%', 'numeric'), ('games_played', 'GP', 'numeric')],
                        "Goalie Leaders"
                    )
                ], md=6, className="mt-4"),
            ])

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error updating player leaderboards: {e}\n{error_details}")
            return dbc.Alert([
                html.H5("Error loading leaderboards", className="alert-heading"),
                html.P(f"{str(e)}"),
                html.Hr(),
                html.Pre(error_details, style={"fontSize": "10px", "maxHeight": "200px", "overflow": "auto"})
            ], color="danger")
