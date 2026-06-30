import dash
from dash import html, dcc, dash_table, Output, Input, ALL, callback_context, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import json
import plotly.graph_objects as go
from components.unified_filter_bar import create_unified_filter_bar
from utils import format_player_label
import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers for roster grid
# ---------------------------------------------------------------------------

def _initials(row):
    label = format_player_label(row)  # e.g. "PS #12" or "#12"
    if label and not label.startswith('#'):
        return label.split()[0]  # "PS" from "PS #12"
    # Direct fallback for when format_player_label also falls through
    f = str(row.get('FirstName', '') or '')[:1]
    l = str(row.get('LastName', '') or '')[:1]
    return f"{f}{l}" if (f or l) else "#"


def _initials_class(pos):
    if pos == 'G':
        return "player-initials goalie"
    if pos == 'D':
        return "player-initials defense"
    return "player-initials"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def create_player_layout(data_service, team_context=None):
    """
    Create the player statistics layout with a visual roster grid.

    Args:
        data_service (DataService): The data service for retrieving player data
        team_context (dict, optional): Team context containing team_id and team_name

    Returns:
        dash.html.Div: The player statistics layout
    """
    team_id = (team_context or {}).get('team_id')
    players_df = data_service.get_players(team_id) if data_service else None

    cards = []
    if players_df is not None and not players_df.empty:
        for _, row in players_df.iterrows():
            pos = str(row.get('Position', 'F') or 'F')
            cards.append(dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div(_initials(row), className=_initials_class(pos)),
                        html.P(format_player_label(row),
                               className="fw-bold mb-0 text-center small"),
                        html.P(pos,
                               className="text-muted text-center mb-0",
                               style={"fontSize": "11px"}),
                    ]),
                    id={'type': 'player-card', 'index': str(row['JerseyNumber'])},
                    className="player-card mb-3",
                    n_clicks=0,
                ),
                xs=6, sm=4, md=3, lg=2,
            ))

    roster_grid = dbc.Row(cards) if cards else html.P(
        "No players found.", className="text-muted"
    )

    return html.Div([
        dcc.Store(id='player-selected-store'),
        create_unified_filter_bar(screen_specific_controls=None, show_recent_games=False),
        dbc.Container([
            html.H1("Players", className="fw-bold mb-4"),
            roster_grid,
            html.Hr(className="my-4"),
            dcc.Loading(html.Div(id='player-info-container')),
            dcc.Loading(html.Div(id='player-game-log-container')),
        ], fluid=True),
    ])


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def register_player_callbacks(app, data_service):
    """
    Register callbacks for the player statistics layout.

    Args:
        app (dash.Dash): The Dash application
        data_service (DataService): The data service for retrieving player data
    """

    # ------------------------------------------------------------------
    # Card selection — pattern-matching callback
    # ------------------------------------------------------------------

    @app.callback(
        Output('player-selected-store', 'data'),
        Input({'type': 'player-card', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True,
    )
    def select_player(n_clicks_list):
        """Store the jersey number of the clicked player card."""
        if not callback_context.triggered:
            return no_update
        triggered_id = callback_context.triggered[0]['prop_id']
        return json.loads(triggered_id.split('.')[0])['index']

    # ------------------------------------------------------------------
    # Player detail — info card + game log
    # ------------------------------------------------------------------

    @app.callback(
        [Output('player-info-container', 'children'),
         Output('player-game-log-container', 'children')],
        [Input('player-selected-store', 'data'),
         Input('game-type-session-store', 'data')],
    )
    def update_player_info(jersey_number, game_type_data):
        """Populate the player info card and game log for the selected player."""
        empty_prompt = html.P(
            "Select a player above to view their stats.",
            className="text-muted text-center py-4",
        )

        # Handle missing data service
        if data_service is None:
            if jersey_number is not None:
                return (
                    html.Div(dbc.Alert([
                        html.H5("Service Unavailable", className="alert-heading"),
                        html.P("Player statistics are not available because the "
                               "application could not connect to the data source."),
                        html.P("This typically occurs when credentials are missing "
                               "in local development.", className="mb-0"),
                    ], color="warning")),
                    html.Div(),
                )
            return empty_prompt, html.Div()

        # Read session context
        from flask import session
        team_id = session.get('team_id') if session.get('authenticated', False) else None
        is_coach = session.get('is_coach', False)

        # Resolve game type
        game_type = game_type_data if isinstance(game_type_data, str) else None
        if game_type_data and isinstance(game_type_data, dict):
            game_type = game_type_data.get('game_type')
        if game_type == 'all':
            game_type = None

        # ---------------------------------------------------------------
        # Cache management: clear stale entries when player or game type
        # changes so the user always gets fresh data.
        # ---------------------------------------------------------------
        previous_game_type = session.get('player_previous_game_type')
        previous_jersey_number = session.get('player_previous_jersey_number')

        if previous_game_type != game_type or previous_jersey_number != jersey_number:
            try:
                logger.info(
                    f"Player layout: State changed — game type: {previous_game_type} → {game_type}, "
                    f"player: {previous_jersey_number} → {jersey_number}, clearing cache for team {team_id}"
                )
                # Clear cache for the previous game type
                if previous_game_type is not None:
                    try:
                        result = data_service.clear_games_cache_optimized(
                            team_id=team_id, game_type=previous_game_type
                        )
                        if result['cleared']:
                            logger.debug(
                                f"Player layout: Cleared {result['entries_removed']} cache entries "
                                f"for previous game type {previous_game_type}"
                            )
                    except Exception as e:
                        logger.warning(f"Player layout: Cache clear for previous game type failed: {e}")
                        try:
                            data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
                        except Exception:
                            pass

                # Clear cache for the current game type
                try:
                    result = data_service.clear_games_cache_optimized(
                        team_id=team_id, game_type=game_type
                    )
                    if result['cleared']:
                        logger.debug(
                            f"Player layout: Cleared {result['entries_removed']} cache entries "
                            f"for current game type {game_type}"
                        )
                except Exception as e:
                    logger.warning(f"Player layout: Cache clear for current game type failed: {e}")
                    try:
                        data_service.clear_games_cache(team_id=team_id, game_type=game_type)
                    except Exception:
                        pass

                session['player_previous_game_type'] = game_type
                session['player_previous_jersey_number'] = jersey_number

            except Exception as e:
                logger.error(f"Player layout: Unexpected cache management error: {e}")
                session['player_previous_game_type'] = game_type
                session['player_previous_jersey_number'] = jersey_number

        # No player selected
        if not jersey_number or jersey_number == '':
            return empty_prompt, html.Div()

        # Resolve player
        team_players = data_service.get_players(team_id)
        try:
            jersey_number_int = int(jersey_number)
        except (ValueError, TypeError):
            return html.Div(dbc.Alert("Invalid player selection", color="danger")), html.Div()

        matching_players = team_players[team_players['JerseyNumber'] == jersey_number_int]
        if matching_players.empty:
            return html.Div(dbc.Alert("Player not found", color="danger")), html.Div()

        player = matching_players.iloc[0]

        player_id = data_service._get_player_id_from_series(player)
        if player_id is None:
            return html.Div(dbc.Alert("Player ID not found", color="danger")), html.Div()

        is_goalie = player['Position'] == 'G'

        # Calculate stats
        try:
            if is_goalie:
                stats = data_service.calculate_goalie_stats(player_id, team_id, game_type)
            else:
                stats = data_service.calculate_player_stats(player_id, team_id, game_type)
        except Exception as e:
            logger.error(f"Player layout: Error calculating stats for player {player_id}: {e}")
            stats = None

        if stats is None:
            return html.Div(dbc.Alert("Could not calculate player statistics", color="danger")), html.Div()

        # ---------------------------------------------------------------
        # KPI tiles
        # ---------------------------------------------------------------
        if is_goalie:
            sv_pct = stats.get('save_percentage', 0)
            gaa = stats.get('gaa', 0)
            kpi_tiles = [
                html.Div([
                    html.Div(str(stats.get('wins', 0)), className="kpi-value"),
                    html.Div("WINS", className="kpi-label"),
                ], className="kpi-tile"),
                html.Div([
                    html.Div(str(stats.get('shutouts', 0)), className="kpi-value"),
                    html.Div("SHUTOUTS", className="kpi-label"),
                ], className="kpi-tile"),
                html.Div([
                    html.Div(f"{sv_pct:.3f}", className="kpi-value"),
                    html.Div("SV%", className="kpi-label"),
                ], className="kpi-tile"),
                html.Div([
                    html.Div(f"{gaa:.2f}", className="kpi-value"),
                    html.Div("GAA", className="kpi-label"),
                ], className="kpi-tile"),
            ]
        else:
            kpi_tiles = [
                html.Div([
                    html.Div(str(stats.get('goals', 0)), className="kpi-value"),
                    html.Div("GOALS", className="kpi-label"),
                ], className="kpi-tile"),
                html.Div([
                    html.Div(str(stats.get('assists', 0)), className="kpi-value"),
                    html.Div("ASSISTS", className="kpi-label"),
                ], className="kpi-tile"),
                html.Div([
                    html.Div(str(stats.get('points', 0)), className="kpi-value"),
                    html.Div("POINTS", className="kpi-label"),
                ], className="kpi-tile"),
                html.Div([
                    html.Div(str(stats.get('shots', 0)), className="kpi-value"),
                    html.Div("SHOTS", className="kpi-label"),
                ], className="kpi-tile"),
            ]
            if is_coach or not config.is_coaches_only_stat('plus_minus'):
                kpi_tiles.append(html.Div([
                    html.Div(str(stats.get('plus_minus', 0)), className="kpi-value"),
                    html.Div("+/-", className="kpi-label"),
                ], className="kpi-tile"))
            if is_coach or not config.is_coaches_only_stat('penalty_minutes'):
                kpi_tiles.append(html.Div([
                    html.Div(str(stats.get('penalty_minutes', 0)), className="kpi-value"),
                    html.Div("PIM", className="kpi-label"),
                ], className="kpi-tile"))

        player_info = dbc.Card([
            dbc.CardHeader(html.H4(format_player_label(player), className="card-title")),
            dbc.CardBody([
                html.P(f"Position: {player['Position']}", className="text-muted mb-3"),
                html.Div(kpi_tiles, className="d-flex flex-wrap gap-3"),
            ]),
        ], className="mb-4 shadow-sm")

        # ---------------------------------------------------------------
        # Game log
        # ---------------------------------------------------------------
        game_log = data_service.get_player_game_log(player_id, team_id, game_type)

        if game_log:
            game_log_data = []
            for game_stats in game_log:
                if is_goalie:
                    game_log_data.append({
                        'Date': game_stats['game']['Date'],
                        'Game Type': config.get_game_type_name(game_stats['game'].get('GameType', 'E')),
                        'Opponent': game_stats['game']['Opponent'],
                        'Result': game_stats['result'],
                        'SA': game_stats['shots_against'],
                        'SV': game_stats['saves'],
                        'GA': game_stats['goals_against'],
                        'SV%': f"{game_stats['save_percentage']:.3f}",
                        'SO': 'Yes' if game_stats['shutout'] else 'No',
                    })
                else:
                    entry = {
                        'Date': game_stats['game']['Date'],
                        'Game Type': config.get_game_type_name(game_stats['game'].get('GameType', 'E')),
                        'Opponent': game_stats['game']['Opponent'],
                        'Result': game_stats['game']['Result'],
                        'Goals': game_stats['goals'],
                        'Assists': game_stats['assists'],
                        'Points': game_stats['points'],
                    }
                    if is_coach or not config.is_coaches_only_stat('plus_minus'):
                        entry['+/-'] = game_stats['plus_minus']
                    if is_coach or not config.is_coaches_only_stat('PIM'):
                        entry['PIM'] = game_stats['penalty_minutes']
                    game_log_data.append(entry)

            game_log_df = pd.DataFrame(game_log_data)
            dates = [e['Date'] for e in game_log_data]

            # Chart
            if is_goalie:
                sv_pct_list = [float(e['SV%']) for e in game_log_data]
                fig = go.Figure(go.Scatter(
                    x=dates, y=sv_pct_list,
                    mode='lines+markers',
                    line=dict(color='#0042bb', width=2),
                ))
                fig.update_layout(
                    title="Save Percentage by Game",
                    height=220,
                    margin=dict(l=40, r=20, t=40, b=40),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    yaxis=dict(tickformat='.3f'),
                )
            else:
                goals_list = [e['Goals'] for e in game_log_data]
                assists_list = [e['Assists'] for e in game_log_data]
                points_list = [e['Points'] for e in game_log_data]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=dates, y=goals_list, name='Goals', marker_color='#00843d'))
                fig.add_trace(go.Bar(x=dates, y=assists_list, name='Assists', marker_color='#0042bb'))
                fig.add_trace(go.Bar(x=dates, y=points_list, name='Points', marker_color='#eca200'))
                fig.update_layout(
                    barmode='group',
                    height=220,
                    margin=dict(l=40, r=20, t=20, b=40),
                    legend=dict(orientation='h', y=-0.3),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                )

            # Table columns
            if is_goalie:
                columns = [
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Game Type', 'id': 'Game Type'},
                    {'name': 'Opponent', 'id': 'Opponent'},
                    {'name': 'Result', 'id': 'Result'},
                    {'name': 'Shots Against', 'id': 'SA'},
                    {'name': 'Saves', 'id': 'SV'},
                    {'name': 'Goals Against', 'id': 'GA'},
                    {'name': 'Save %', 'id': 'SV%'},
                    {'name': 'Shutout', 'id': 'SO'},
                ]
            else:
                columns = [
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Game Type', 'id': 'Game Type'},
                    {'name': 'Opponent', 'id': 'Opponent'},
                    {'name': 'Result', 'id': 'Result'},
                    {'name': 'Goals', 'id': 'Goals'},
                    {'name': 'Assists', 'id': 'Assists'},
                    {'name': 'Points', 'id': 'Points'},
                ]
                if is_coach or not config.is_coaches_only_stat('plus_minus'):
                    columns.append({'name': '+/-', 'id': '+/-'})
                if is_coach or not config.is_coaches_only_stat('PIM'):
                    columns.append({'name': 'PIM', 'id': 'PIM'})

            game_log_card = dbc.Card([
                dbc.CardHeader(html.H4("Game Log", className="card-title")),
                dbc.CardBody([
                    dcc.Graph(figure=fig, config={'displayModeBar': False}),
                    dash_table.DataTable(
                        id='game-log-table',
                        columns=columns,
                        data=game_log_df.to_dict('records'),
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px',
                            'minWidth': '80px',
                        },
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold',
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)',
                            },
                            {
                                'if': {'filter_query': '{Result} = "W"'},
                                'backgroundColor': 'rgba(0, 255, 0, 0.1)',
                            },
                            {
                                'if': {'filter_query': '{Result} = "L"'},
                                'backgroundColor': 'rgba(255, 0, 0, 0.1)',
                            },
                        ],
                    ),
                ]),
            ], className="shadow-sm")
        else:
            game_log_card = dbc.Card([
                dbc.CardHeader(html.H4("Game Log", className="card-title")),
                dbc.CardBody([
                    html.P("No games found for this player.")
                ]),
            ], className="shadow-sm")

        return player_info, game_log_card
