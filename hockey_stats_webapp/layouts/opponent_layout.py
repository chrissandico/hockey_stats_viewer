"""
Opponent statistics layout for viewing team performance against specific opponents.
"""
import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from flask import session
import pandas as pd
import logging
import plotly.graph_objects as go
from utils import format_player_label, resolve_game_type
import config
from services.data_service import (
    load_opponent_options,
    OPPONENTS_READY,
    OPPONENTS_EMPTY,
    OPPONENTS_LOADING,
)

# Set up logging
logger = logging.getLogger(__name__)

# Bounded self-heal for the opponent dropdown (see load_opponent_options
# in services/data_service.py): after a restart whose boot-time Sheets
# load failed, the dropdown callback re-fires on this interval until the
# data lands — at most MAX_INTERVALS times (~60s) per page view, then
# the dropdown settles into a "tap Refresh" placeholder and stops.
OPPONENT_RETRY_INTERVAL_MS = 5000
OPPONENT_RETRY_MAX_INTERVALS = 12

OPPONENT_LOADING_OPTIONS = [{'label': '-- Loading opponents --', 'value': '', 'disabled': True}]
OPPONENT_SETTLED_OPTIONS = [{'label': '-- Still loading — tap Refresh --', 'value': '', 'disabled': True}]
OPPONENT_NO_OPPONENTS_OPTIONS = [{'label': '-- No opponents found --', 'value': '', 'disabled': True}]
OPPONENT_NO_TEAM_OPTIONS = [{'label': '-- No team selected --', 'value': '', 'disabled': True}]


def create_opponent_layout(data_service, team_context=None):
    """
    Create the opponent statistics layout.

    Args:
        data_service: DataService instance
        team_context (dict, optional): Team context with team_id and team_name

    Returns:
        dash.html.Div: The opponent statistics layout
    """
    # Get team_id from context
    team_id = team_context['team_id'] if team_context else None

    if not team_id:
        return html.Div([
            dbc.Alert("Please log in to view opponent statistics.", color="warning", className="m-4")
        ])

    # Get opponents for initial load (all game types), through the same
    # self-healing fetch the dropdown callback uses: if this worker's
    # boot-time Sheets load failed, the fetch heals the snapshot on the
    # spot, or reports OPPONENTS_LOADING and the retry interval below
    # keeps asking until the data lands.
    try:
        opponents, opponents_state = load_opponent_options(data_service, team_id)
    except Exception as e:
        logger.error(f"Error loading opponents: {e}")
        opponents, opponents_state = None, OPPONENTS_LOADING

    # Create opponent dropdown
    if opponents_state == OPPONENTS_LOADING:
        opponent_dropdown = create_opponent_dropdown(
            None, options=OPPONENT_LOADING_OPTIONS, value='')
    else:
        opponent_dropdown = create_opponent_dropdown(opponents)

    return html.Div([
        # Title
        html.H1("vs. Opponents Performance", className="text-center mt-4 mb-4"),

        # Opponent selection
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    opponent_dropdown
                ], xs=12, sm=8, md=6, className="mx-auto")
            ])
        ], className="mb-4"),

        # Store for opponent selection
        dcc.Store(id='opponent-selection-store', storage_type='session'),

        # Bounded dropdown self-heal: ticks only while the opponent data
        # hasn't loaded (the dropdown callback disables it the moment
        # real options land, and max_intervals caps it regardless).
        dcc.Interval(
            id='opponent-dropdown-retry',
            interval=OPPONENT_RETRY_INTERVAL_MS,
            n_intervals=0,
            max_intervals=OPPONENT_RETRY_MAX_INTERVALS,
            disabled=opponents_state != OPPONENTS_LOADING
        ),

        # Main content container — all five sections below come from a single
        # callback (see update_opponent_stats).
        html.Div([
            html.Div(id='opponent-h2h-chart-container'),
            html.Div(id='opponent-head-to-head-container'),
            html.Div(id='opponent-game-log-container'),
            html.Div(id='opponent-player-leaders-container'),
            html.Div(id='opponent-goalie-stats-container'),
        ], className="container-fluid px-4")
    ])


def _format_opponent_options(opponents):
    """(options, value) for a non-empty opponent list: a disabled
    placeholder first, then opponents alphabetically with game counts,
    with the first opponent pre-selected."""
    sorted_opponents = sorted(opponents, key=lambda x: x['opponent'])

    options = [{'label': '-- Select Opponent --', 'value': '', 'disabled': True}]
    options.extend([
        {
            'label': f"{opp['opponent']} ({opp['games']} games)",
            'value': opp['opponent']
        }
        for opp in sorted_opponents
    ])

    return options, sorted_opponents[0]['opponent']


def create_opponent_dropdown(opponents_list, options=None, value=None):
    """
    Create opponent selection dropdown.

    Args:
        opponents_list (list): List of opponent dictionaries
        options (list, optional): Pre-built options to use verbatim
            (e.g. the loading placeholder while the data snapshot heals);
            takes precedence over opponents_list
        value: Pre-selected value to pair with pre-built options

    Returns:
        dash.html.Div: Dropdown component
    """
    if options is None:
        if not opponents_list:
            options = OPPONENT_NO_OPPONENTS_OPTIONS
            value = ''
        else:
            options, value = _format_opponent_options(opponents_list)

    return html.Div([
        html.Label("Opponent", className="form-label fw-bold mb-1"),
        dbc.Select(
            id='opponent-selection-dropdown',
            options=options,
            value=value,
            className="form-select"
        )
    ])


def create_head_to_head_card(opponent_name, stats):
    """
    Create head-to-head summary card.

    Args:
        opponent_name (str): Name of the opponent
        stats (dict): Head-to-head statistics

    Returns:
        dbc.Card: Head-to-head summary card
    """
    if not stats or stats['games_played'] == 0:
        return dbc.Card([
            dbc.CardHeader(html.H4(f"Head-to-Head vs {opponent_name}", className="mb-0")),
            dbc.CardBody(html.P("No games played against this opponent.", className="text-muted"))
        ], className="mb-4 shadow-sm")

    return dbc.Card([
        dbc.CardHeader(html.H4(f"Head-to-Head vs {opponent_name}", className="card-title mb-0")),
        dbc.CardBody([
            dbc.Row([
                # Column 1: Record
                dbc.Col([
                    html.H5("Record", className="mb-3"),
                    html.Div([
                        html.Div([
                            html.Span("Games Played: ", className="fw-bold"),
                            html.Span(stats['games_played'])
                        ], className="mb-2"),
                        html.Div([
                            html.Span("Wins: ", className="fw-bold"),
                            html.Span(stats['wins'], className="text-success")
                        ], className="mb-2"),
                        html.Div([
                            html.Span("Losses: ", className="fw-bold"),
                            html.Span(stats['losses'], className="text-danger")
                        ], className="mb-2"),
                        html.Div([
                            html.Span("Ties: ", className="fw-bold"),
                            html.Span(stats['ties'], className="text-warning")
                        ], className="mb-2"),
                        html.Div([
                            html.Span("Win %: ", className="fw-bold"),
                            html.Span(f"{stats['win_percentage']:.1f}%")
                        ], className="mb-2")
                    ])
                ], xs=12, md=6),

                # Column 2: Goals
                dbc.Col([
                    html.H5("Goals", className="mb-3"),
                    html.Div([
                        html.Div([
                            html.Span("Goals For: ", className="fw-bold"),
                            html.Span(stats['goals_for'])
                        ], className="mb-2"),
                        html.Div([
                            html.Span("Goals Against: ", className="fw-bold"),
                            html.Span(stats['goals_against'])
                        ], className="mb-2"),
                        html.Div([
                            html.Span("Goal Differential: ", className="fw-bold"),
                            html.Span(
                                f"{stats['goal_differential']:+d}",
                                className="text-success" if stats['goal_differential'] > 0 else ("text-danger" if stats['goal_differential'] < 0 else "")
                            )
                        ], className="mb-2")
                    ])
                ], xs=12, md=6)
            ])
        ])
    ], className="mb-4 shadow-sm")


def create_game_log_card(opponent_name, games):
    """
    Create game log table card.

    Args:
        opponent_name (str): Name of the opponent
        games (DataFrame): Game details

    Returns:
        dbc.Card: Game log table card
    """
    if games.empty:
        return dbc.Card([
            dbc.CardHeader(html.H4(f"Game Log vs {opponent_name}", className="mb-0")),
            dbc.CardBody(html.P("No games found.", className="text-muted"))
        ], className="mb-4 shadow-sm")

    # Prepare table data
    table_data = []
    for _, game in games.iterrows():
        table_data.append({
            'Date': game['Date'],
            'Opponent': game['Opponent'],
            'Location': game.get('Location', 'N/A'),
            'Result': game['Result'],
            'Score': f"{game['GoalsFor']} - {game['GoalsAgainst']}",
            'Game Type': config.get_game_type_name(game.get('GameType', 'R'))
        })

    return dbc.Card([
        dbc.CardHeader(html.H4(f"Game Log vs {opponent_name} ({len(games)} games)", className="card-title mb-0")),
        dbc.CardBody([
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Opponent', 'id': 'Opponent'},
                    {'name': 'Location', 'id': 'Location'},
                    {'name': 'Result', 'id': 'Result'},
                    {'name': 'Score', 'id': 'Score'},
                    {'name': 'Game Type', 'id': 'Game Type'}
                ],
                sort_action='native',
                sort_by=[{'column_id': 'Date', 'direction': 'desc'}],
                style_cell={'textAlign': 'left', 'padding': '10px', 'fontSize': '14px'},
                style_header={
                    'backgroundColor': '#00205b',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'left'
                },
                style_data_conditional=[
                    {'if': {'filter_query': '{Result} = W'}, 'backgroundColor': '#d4edda'},
                    {'if': {'filter_query': '{Result} = L'}, 'backgroundColor': '#f8d7da'},
                    {'if': {'filter_query': '{Result} = T'}, 'backgroundColor': '#fff3cd'}
                ],
                page_size=10
            )
        ])
    ], className="mb-4 shadow-sm")


def create_player_leaders_card(opponent_name, forwards, defense, is_coach=False):
    """
    Create player leaderboards card.

    Args:
        opponent_name (str): Name of the opponent
        forwards (list): Forward player statistics
        defense (list): Defense player statistics
        is_coach (bool): Whether current user is a coach

    Returns:
        dbc.Card: Player leaderboards card
    """
    if not forwards and not defense:
        return html.Div()  # Hide if no data

    return dbc.Card([
        dbc.CardHeader(html.H4(f"Player Leaders vs {opponent_name}", className="card-title mb-0")),
        dbc.CardBody([
            dbc.Row([
                # Forwards column
                dbc.Col([
                    html.H5("Forwards", className="mb-3"),
                    create_player_table(forwards, is_coach)
                ], xs=12, md=6),

                # Defense column
                dbc.Col([
                    html.H5("Defense", className="mb-3"),
                    create_player_table(defense, is_coach)
                ], xs=12, md=6)
            ])
        ])
    ], className="mb-4 shadow-sm")


def create_player_table(players, is_coach=False):
    """
    Create player stats table with conditional plus/minus display.

    Args:
        players (list): List of player statistics
        is_coach (bool): Whether to show coach-only stats (plus/minus)

    Returns:
        dash_table.DataTable or html.P: Player stats table or no data message
    """
    if not players:
        return html.P("No data available", className="text-muted")

    # Build table data and columns based on coach status
    try:
        if is_coach:
            # Coaches see plus/minus and PIM, plus the on-ice shot-share
            # columns (SF / SA / SF%) the main leaderboard carries
            table_data = [
                {
                    'Player': format_player_label(p['player']),
                    'G': p['goals'],
                    'A': p['assists'],
                    'P': p['points'],
                    '+/-': p['plus_minus'],
                    'SF': p.get('on_ice_shots_for', 0),
                    'SA': p.get('on_ice_shots_against', 0),
                    'SF%': f"{p.get('on_ice_shot_share_pct', 0.0):.1f}%",
                    'PIM': p['penalty_minutes']
                }
                for p in players
            ]
            columns = [
                {'name': 'Player', 'id': 'Player'},
                {'name': 'G', 'id': 'G'},
                {'name': 'A', 'id': 'A'},
                {'name': 'P', 'id': 'P'},
                {'name': '+/-', 'id': '+/-'},
                {'name': 'SF', 'id': 'SF'},
                {'name': 'SA', 'id': 'SA'},
                {'name': 'SF%', 'id': 'SF%'},
                {'name': 'PIM', 'id': 'PIM'}
            ]
        else:
            # Players don't see plus/minus or PIM (coaches-only stats)
            table_data = [
                {
                    'Player': format_player_label(p['player']),
                    'G': p['goals'],
                    'A': p['assists'],
                    'P': p['points'],
                    'SF': p.get('on_ice_shots_for', 0),
                    'SA': p.get('on_ice_shots_against', 0),
                    'SF%': f"{p.get('on_ice_shot_share_pct', 0.0):.1f}%"
                }
                for p in players
            ]
            columns = [
                {'name': 'Player', 'id': 'Player'},
                {'name': 'G', 'id': 'G'},
                {'name': 'A', 'id': 'A'},
                {'name': 'P', 'id': 'P'},
                {'name': 'SF', 'id': 'SF'},
                {'name': 'SA', 'id': 'SA'},
                {'name': 'SF%', 'id': 'SF%'}
            ]

    except Exception as e:
        logger.error(f"Error building player table: {e}")
        return html.P(f"Error displaying player data: {str(e)}", className="text-danger")

    return dash_table.DataTable(
        data=table_data,
        columns=columns,
        style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '14px'},
        style_header={
            'backgroundColor': '#00205b',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'left'
        },
        style_data_conditional=[
            # Highlight top scorer
            {'if': {'row_index': 0}, 'fontWeight': 'bold'}
        ]
    )


def create_goalie_stats_card(opponent_name, goalies):
    """
    Create goalie stats card.

    Args:
        opponent_name (str): Name of the opponent
        goalies (list): Goalie statistics

    Returns:
        dbc.Card or html.Div: Goalie stats card or empty div
    """
    if not goalies:
        return html.Div()  # Hide if no goalies

    try:
        table_data = [
            {
                'Player': format_player_label(g['player']),
                'GP': g['games_played'],
                'W': g['wins'],
                'L': g['losses'],
                'T': g['ties'],
                'SV%': f"{g['save_percentage']:.3f}",
                'GAA': f"{g['gaa']:.2f}",
                'SO': g['shutouts'],
                'SOG': g['shots_against']
            }
            for g in goalies
        ]
    except Exception as e:
        logger.error(f"Error building goalie table: {e}")
        return html.Div()  # Hide on error

    return dbc.Card([
        dbc.CardHeader(html.H4(f"Goalie Stats vs {opponent_name}", className="card-title mb-0")),
        dbc.CardBody([
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {'name': 'Player', 'id': 'Player'},
                    {'name': 'GP', 'id': 'GP'},
                    {'name': 'W', 'id': 'W'},
                    {'name': 'L', 'id': 'L'},
                    {'name': 'T', 'id': 'T'},
                    {'name': 'SV%', 'id': 'SV%'},
                    {'name': 'GAA', 'id': 'GAA'},
                    {'name': 'SO', 'id': 'SO'},
                    {'name': 'SOG', 'id': 'SOG'}
                ],
                style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '14px'},
                style_header={
                    'backgroundColor': '#00205b',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'left'
                }
            )
        ])
    ], className="mb-4 shadow-sm")


def register_opponent_callbacks(app, data_service):
    """
    Register callbacks for opponent statistics layout.

    Args:
        app: Dash application instance
        data_service: DataService instance
    """

    # Callback 1: Update opponent dropdown (self-healing — see
    # load_opponent_options in services/data_service.py)
    @app.callback(
        [dash.dependencies.Output('opponent-selection-dropdown', 'options'),
         dash.dependencies.Output('opponent-selection-dropdown', 'value'),
         dash.dependencies.Output('opponent-dropdown-retry', 'disabled')],
        [dash.dependencies.Input('global-refresh-btn', 'n_clicks'),
         dash.dependencies.Input('opponent-dropdown-retry', 'n_intervals')],
        prevent_initial_call=False
    )
    def update_opponent_dropdown(refresh_clicks, retry_intervals):
        """Update opponent dropdown options.

        Third output drives the retry interval: it stays enabled only
        while the sheets snapshot is unusable (a restart whose boot
        load failed). Each tick re-runs the self-healing fetch; real
        options disable the interval at once, and once the bounded
        retry budget is spent the dropdown settles into a
        "tap Refresh" placeholder with the interval disabled — it
        never dead-ends on an error option the way it used to.
        """
        # Get team_id from session
        team_id = session.get('team_id') if session.get('authenticated') else None

        if not team_id:
            return OPPONENT_NO_TEAM_OPTIONS, '', True

        try:
            opponents, state = load_opponent_options(data_service, team_id)
        except Exception as e:
            # load_opponent_options is built not to raise; if it ever
            # does, treat it as "still loading" so the bounded retry
            # below keeps a path to recovery.
            logger.error(f"Error updating opponent dropdown: {e}")
            opponents, state = None, OPPONENTS_LOADING

        if state == OPPONENTS_READY:
            options, value = _format_opponent_options(opponents)
            return options, value, True

        if state == OPPONENTS_EMPTY:
            return OPPONENT_NO_OPPONENTS_OPTIONS, '', True

        # OPPONENTS_LOADING: keep retrying while budget remains.
        if (retry_intervals or 0) >= OPPONENT_RETRY_MAX_INTERVALS:
            return OPPONENT_SETTLED_OPTIONS, '', True
        return OPPONENT_LOADING_OPTIONS, '', False

    # Callback 2: Store opponent selection
    @app.callback(
        dash.dependencies.Output('opponent-selection-store', 'data'),
        [dash.dependencies.Input('opponent-selection-dropdown', 'value')]
    )
    def store_opponent_selection(opponent_name):
        """Store selected opponent in session store."""
        return opponent_name

    # Callback 3: Update all stats when opponent selection changes or refresh is clicked
    @app.callback(
        [dash.dependencies.Output('opponent-h2h-chart-container', 'children'),
         dash.dependencies.Output('opponent-head-to-head-container', 'children'),
         dash.dependencies.Output('opponent-game-log-container', 'children'),
         dash.dependencies.Output('opponent-player-leaders-container', 'children'),
         dash.dependencies.Output('opponent-goalie-stats-container', 'children')],
        [dash.dependencies.Input('opponent-selection-store', 'data'),
         dash.dependencies.Input('global-refresh-btn', 'n_clicks')]
    )
    def update_opponent_stats(opponent_name, refresh_clicks):
        """Update all opponent statistics displays."""
        # Skip if no opponent selected
        if not opponent_name or opponent_name == '':
            return html.Div(), html.Div(), html.Div(), html.Div(), html.Div()

        # Get team_id and coach status from session
        team_id = session.get('team_id') if session.get('authenticated') else None
        is_coach = session.get('is_coach', False)

        if not team_id:
            return html.Div(), html.Div(), html.Div(), html.Div(), html.Div()

        # Always show all games
        game_type = None

        # Check if refresh button triggered the callback
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        if triggered_id == 'global-refresh-btn':
            data_service.force_refresh_all_data()

        # Cache management (track previous values)
        previous_game_type = session.get('opponent_previous_game_type')
        previous_opponent = session.get('opponent_previous_selection')

        if previous_game_type != game_type or previous_opponent != opponent_name:
            try:
                data_service.clear_games_cache_optimized(team_id, game_type)
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")

            session['opponent_previous_game_type'] = game_type
            session['opponent_previous_selection'] = opponent_name

        try:
            # Get stats from data service
            head_to_head = data_service.calculate_opponent_head_to_head(opponent_name, team_id, game_type)
            games = data_service.get_opponent_games(opponent_name, team_id, game_type)
            forwards = data_service.get_opponent_player_leaderboard(opponent_name, team_id, game_type, stat='points', position='F', limit=None)
            defense = data_service.get_opponent_player_leaderboard(opponent_name, team_id, game_type, stat='points', position='D', limit=None)
            goalies = data_service.get_opponent_goalie_stats(opponent_name, team_id, game_type)

            # Build H2H donut chart
            h2h = head_to_head or {}
            wins = h2h.get('wins', 0)
            losses = h2h.get('losses', 0)
            ties = h2h.get('ties', 0)

            if h2h.get('games_played', 0) > 0:
                fig = go.Figure(go.Pie(
                    values=[wins, losses, ties],
                    labels=['W', 'L', 'T'],
                    hole=0.6,
                    marker_colors=['#00843d', '#c8102e', '#eca200'],
                ))
                fig.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=True,
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                h2h_chart = dcc.Graph(figure=fig, config={'displayModeBar': False})
            else:
                h2h_chart = html.Div()

            # Build components (pass is_coach for conditional plus/minus display)
            head_to_head_card = create_head_to_head_card(opponent_name, head_to_head)
            game_log_card = create_game_log_card(opponent_name, games)
            player_leaders_card = create_player_leaders_card(opponent_name, forwards, defense, is_coach)
            goalie_stats_card = create_goalie_stats_card(opponent_name, goalies)

            return h2h_chart, head_to_head_card, game_log_card, player_leaders_card, goalie_stats_card

        except Exception as e:
            logger.error(f"Error updating opponent stats: {e}")
            error_msg = dbc.Alert(f"Error loading opponent statistics: {str(e)}", color="danger")
            return html.Div(), error_msg, html.Div(), html.Div(), html.Div()
