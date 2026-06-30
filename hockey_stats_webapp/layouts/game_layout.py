import dash
from dash import html, dcc, dash_table, Output, Input, ALL, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json
import logging
from flask import session as flask_session
import config
from utils import format_player_label
from components.unified_filter_bar import create_unified_filter_bar

logger = logging.getLogger(__name__)


def create_game_layout(data_service, team_context=None):
    """
    Create the game statistics layout with scrollable scorecard list.

    Args:
        data_service (DataService): The data service for retrieving game data
        team_context (dict, optional): Team context containing team_id and team_name

    Returns:
        dash.html.Div: The game statistics layout
    """
    return html.Div([
        dcc.Store(id='game-selected-store'),
        create_unified_filter_bar(screen_specific_controls=None, show_recent_games=False),
        dbc.Container([
            html.H1("Games", className="fw-bold mb-4"),
            dcc.Loading(html.Div(id='game-list-container', className="mb-4")),
            html.Div(id='game-detail-container'),
        ], fluid=True),
    ])


def register_game_callbacks(app, data_service, team_context=None):
    """
    Register callbacks for the game statistics layout.

    Args:
        app (dash.Dash): The Dash application
        data_service (DataService): The data service for retrieving game data
        team_context (dict, optional): Team context containing team_id and team_name
    """
    team_id = team_context['team_id'] if team_context else None

    # ------------------------------------------------------------------ #
    # Callback 1: Populate the scrollable game scorecard list              #
    # ------------------------------------------------------------------ #
    @app.callback(
        Output('game-list-container', 'children'),
        Input('game-type-session-store', 'data'),
        Input('url', 'pathname'),
    )
    def update_game_list(game_type_data, pathname):
        if pathname != '/game':
            return no_update

        session_team_id = flask_session.get('team_id')
        effective_team_id = session_team_id if session_team_id else team_id

        if not effective_team_id or not data_service:
            return html.P("No data available.", className="text-muted")

        # Resolve game_type from the session store value ('all', 'E', 'R', 'T', 'P', or None)
        game_type = None
        if game_type_data and game_type_data != 'all':
            game_type = game_type_data

        try:
            games = data_service.get_games(effective_team_id, game_type=game_type)
            games = data_service._filter_games_by_date(games, include_future=True)
        except Exception as e:
            logger.error(f"Error fetching games for game list: {e}")
            return html.P("Error loading games.", className="text-muted text-danger")

        if games.empty:
            return html.P("No games found.", className="text-muted")

        # Sort most-recent first
        try:
            games = games.sort_values('Date', ascending=False)
        except Exception:
            pass

        gt_colors = {'E': 'info', 'R': 'primary', 'T': 'warning', 'P': 'secondary'}

        cards = []
        for _, row in games.iterrows():
            result_str = str(row.get('Result', '') or '')
            result_upper = result_str.upper()
            if 'W' in result_upper:
                badge_color, result_letter = 'success', 'W'
            elif 'L' in result_upper:
                badge_color, result_letter = 'danger', 'L'
            else:
                badge_color, result_letter = 'warning', 'T'

            game_type_val = str(row.get('GameType', '') or '')
            gt_color = gt_colors.get(game_type_val, 'secondary')
            game_id_val = str(row.get('ID', row.name))

            cards.append(
                dbc.Card(
                    dbc.CardBody(
                        dbc.Row([
                            dbc.Col([
                                html.Div(str(row.get('Date', '')), className="text-muted small"),
                                html.Div(f"vs {row.get('Opponent', '')}", className="fw-bold"),
                            ], width=5),
                            dbc.Col(
                                html.Div(
                                    f"{row.get('GoalsFor', 0)} — {row.get('GoalsAgainst', 0)}",
                                    className="game-score text-center"
                                ),
                                width=3,
                            ),
                            dbc.Col([
                                dbc.Badge(result_letter, color=badge_color, className="me-1"),
                                dbc.Badge(game_type_val, color=gt_color),
                            ], width=4, className="text-end"),
                        ], align='center')
                    ),
                    id={'type': 'game-card', 'index': game_id_val},
                    className="game-scorecard mb-2",
                    style={'cursor': 'pointer'},
                )
            )

        return cards

    # ------------------------------------------------------------------ #
    # Callback 2: Pattern-matching — store which card was clicked          #
    # ------------------------------------------------------------------ #
    @app.callback(
        Output('game-selected-store', 'data'),
        Input({'type': 'game-card', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True,
    )
    def select_game(n_clicks_list):
        if not callback_context.triggered:
            return no_update
        triggered_prop = callback_context.triggered[0]['prop_id']
        try:
            return json.loads(triggered_prop.split('.')[0])['index']
        except Exception:
            return no_update

    # ------------------------------------------------------------------ #
    # Callback 3: Render game detail — score, shots chart, player table   #
    # ------------------------------------------------------------------ #
    @app.callback(
        Output('game-detail-container', 'children'),
        Input('game-selected-store', 'data'),
    )
    def update_game_detail(game_id):
        if not game_id:
            return html.P(
                "Select a game above to view details.",
                className="text-muted text-center py-4",
            )

        session_team_id = flask_session.get('team_id')
        effective_team_id = session_team_id if session_team_id else team_id
        is_coach = flask_session.get('is_coach', False)

        if not effective_team_id or not data_service:
            return html.Div()

        # Try integer conversion for numeric IDs
        try:
            game_id_typed = int(game_id)
        except (ValueError, TypeError):
            game_id_typed = game_id

        try:
            # ---- Game summary (header data + team shots totals) ----
            summary = data_service.get_game_summary(game_id_typed, effective_team_id)
            if summary is None:
                return dbc.Alert("Game not found.", color="danger")

            game = summary['game']
            result_str = str(game.get('Result', '') or '')
            result_upper = result_str.upper()
            if 'W' in result_upper:
                result_color, result_letter = 'success', 'W'
            elif 'L' in result_upper:
                result_color, result_letter = 'danger', 'L'
            else:
                result_color, result_letter = 'warning', 'T'

            game_type_val = str(game.get('GameType', '') or '')
            gt_colors = {'E': 'info', 'R': 'primary', 'T': 'warning', 'P': 'secondary'}
            gt_color = gt_colors.get(game_type_val, 'secondary')

            # ---- Score header card ----
            score_header = dbc.Card(
                dbc.CardBody(
                    dbc.Row([
                        dbc.Col([
                            html.Div(str(game.get('Date', '')), className="text-muted small"),
                            html.H4(f"vs {game.get('Opponent', '')}", className="mb-0"),
                            html.Div(str(game.get('Location', '')), className="text-muted small mt-1"),
                        ], xs=12, md=5),
                        dbc.Col(
                            html.Div(
                                html.Span(
                                    f"{game.get('GoalsFor', 0)} — {game.get('GoalsAgainst', 0)}",
                                    className="game-score",
                                ),
                                className="text-center",
                            ),
                            xs=12, md=4,
                        ),
                        dbc.Col([
                            dbc.Badge(result_letter, color=result_color, className="me-2 fs-6"),
                            dbc.Badge(game_type_val, color=gt_color, className="fs-6"),
                        ], xs=12, md=3, className="d-flex align-items-center justify-content-end"),
                    ], align='center')
                ),
                className="mb-3 shadow-sm",
            )

            # ---- Shots-by-period chart ----
            period_data = data_service.get_period_breakdown(game_id_typed, effective_team_id)
            shots_chart = None
            if period_data:
                periods = ['P1', 'P2', 'P3']
                your_shots = period_data['your_team'].get('shots', [0, 0, 0])
                opp_shots = period_data['opponent'].get('shots', [0, 0, 0])
                your_name = period_data['your_team'].get('name', 'Your Team')
                opp_name = period_data['opponent'].get('name', 'Opponent')

                fig = go.Figure(data=[
                    go.Bar(
                        name=your_name,
                        x=periods,
                        y=your_shots,
                        marker_color='#0042bb',
                    ),
                    go.Bar(
                        name=opp_name,
                        x=periods,
                        y=opp_shots,
                        marker_color='#c8102e',
                    ),
                ])
                fig.update_layout(
                    barmode='group',
                    height=220,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation='h', y=1.1),
                    yaxis=dict(title='Shots'),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                shots_chart = dbc.Card(
                    dbc.CardBody([
                        html.H5("Shots by Period", className="card-title"),
                        dcc.Graph(figure=fig, config={'displayModeBar': False}),
                    ]),
                    className="mb-3 shadow-sm",
                )

            # ---- Player stats ----
            # Skaters: get all player stats, then exclude goalies
            all_player_stats = data_service.get_game_player_stats(
                game_id_typed, None, effective_team_id
            )
            skater_stats = [
                s for s in all_player_stats
                if s['player'].get('Position') != 'G'
            ]

            # Goalies: get goalie list then calc per-game goalie stats
            goalie_list = data_service.get_game_player_stats(
                game_id_typed, 'G', effective_team_id
            )
            goalie_stats = []
            for s in goalie_list:
                player_series = s['player']
                player_id_val = None
                if 'ID' in player_series.index:
                    player_id_val = player_series['ID']
                elif 'Unnamed: 0' in player_series.index:
                    player_id_val = player_series['Unnamed: 0']
                elif '' in player_series.index:
                    player_id_val = player_series['']
                if player_id_val is not None:
                    gs = data_service.calculate_goalie_game_stats(
                        player_id_val, game_id_typed, effective_team_id
                    )
                    if gs:
                        goalie_stats.append(gs)

            # Shared DataTable style
            table_kwargs = dict(
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center', 'padding': '6px 12px'},
                style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
                ],
                sort_action='native',
            )

            # Skater DataTable
            skater_cols = [
                {'name': 'Player', 'id': 'player_label'},
                {'name': 'Pos', 'id': 'position'},
                {'name': 'G', 'id': 'goals'},
                {'name': 'A', 'id': 'assists'},
                {'name': 'Pts', 'id': 'points'},
            ]
            if is_coach or not config.is_coaches_only_stat('plus_minus'):
                skater_cols.append({'name': '+/-', 'id': 'plus_minus'})
            if is_coach or not config.is_coaches_only_stat('PIM'):
                skater_cols.append({'name': 'PIM', 'id': 'penalty_minutes'})

            skater_data = [
                {
                    'player_label': format_player_label(s['player']),
                    'position': s['player'].get('Position', ''),
                    'goals': s.get('goals', 0),
                    'assists': s.get('assists', 0),
                    'points': s.get('points', 0),
                    'plus_minus': s.get('plus_minus', 0),
                    'penalty_minutes': s.get('penalty_minutes', 0),
                }
                for s in skater_stats
            ]

            # Goalie DataTable
            goalie_cols = [
                {'name': 'Goalie', 'id': 'player_label'},
                {'name': 'SA', 'id': 'shots_against'},
                {'name': 'SV', 'id': 'saves'},
                {'name': 'GA', 'id': 'goals_against'},
                {'name': 'SV%', 'id': 'save_pct'},
            ]
            goalie_data = [
                {
                    'player_label': format_player_label(gs['player']),
                    'shots_against': gs.get('shots_against', 0),
                    'saves': gs.get('saves', 0),
                    'goals_against': gs.get('goals_against', 0),
                    'save_pct': f"{gs.get('save_percentage', 0):.3f}",
                }
                for gs in goalie_stats
            ]

            player_section_children = []
            if skater_data:
                player_section_children.append(
                    html.H5("Skaters", className="mt-3 mb-2")
                )
                player_section_children.append(
                    dash_table.DataTable(
                        data=skater_data,
                        columns=skater_cols,
                        page_size=20,
                        **table_kwargs,
                    )
                )
            if goalie_data:
                player_section_children.append(
                    html.H5("Goalies", className="mt-3 mb-2")
                )
                player_section_children.append(
                    dash_table.DataTable(
                        data=goalie_data,
                        columns=goalie_cols,
                        **table_kwargs,
                    )
                )
            if not skater_data and not goalie_data:
                player_section_children.append(
                    dbc.Alert(
                        "No player statistics found for this game.", color="warning"
                    )
                )

            player_card = dbc.Card(
                dbc.CardBody([
                    html.H5("Player Performance", className="card-title"),
                    *player_section_children,
                ]),
                className="mb-3 shadow-sm",
            )

            detail_children = [score_header]
            if shots_chart:
                detail_children.append(shots_chart)
            detail_children.append(player_card)

            return html.Div(detail_children)

        except Exception as e:
            logger.error(f"Error loading game detail for game_id={game_id}: {e}")
            return html.P("Could not load game details.", className="text-muted")
