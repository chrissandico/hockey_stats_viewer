import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import plotly.graph_objects as go
from components.game_type_filter import create_game_type_filter_component, create_game_type_session_store
from components.unified_filter_bar import create_unified_filter_bar
from utils import format_player_label
import config

def create_team_layout(data_service, team_context=None):
    """
    Create the team statistics layout - OPTIMIZED for performance.

    PERFORMANCE OPTIMIZATION:
    - Returns EMPTY/LOADING containers immediately (~500ms)
    - All heavy data fetching moved to callback
    - Callback populates containers asynchronously
    - Page shows skeleton loaders while data loads

    Args:
        data_service (DataService): The data service for retrieving team data
        team_context (dict, optional): Team context containing team_id and team_name

    Returns:
        dash.html.Div: The team statistics layout with empty containers
    """
    logging.info("Team Stats layout rendered (fast - no data fetching)")

    return html.Div([
        # Title
        html.H1("Team Statistics", className="text-center mt-4"),

        # Unified filter bar (no screen-specific controls for Team Stats)
        create_unified_filter_bar(
            screen_specific_controls=None,
            recent_games_selector_id='team-recent-games-selector',
            recent_games_store_id='team-recent-games-store'
        ),

        # **OPTIMIZED**: Empty containers filled by callback
        # Team season summary - callback will populate
        dcc.Loading(
            id="team-stats-loading",
            type="default",
            color="#00205b",
            children=[html.Div(id='team-summary-container')]
        ),

        # Position tabs
        dbc.Tabs([
            dbc.Tab(label="Forwards", tab_id="forwards"),
            dbc.Tab(label="Defense",  tab_id="defense"),
            dbc.Tab(label="Goalies",  tab_id="goalies"),
        ], id='team-position-tabs', active_tab="forwards", className="mb-3"),

        # Season goals trend chart - callback will populate
        html.Div(id='team-trend-chart-container', className="mb-4"),

        # Leaderboards - callback will populate
        dcc.Loading(
            id="team-leaderboards-loading",
            type="default",
            color="#00205b",
            children=[html.Div(id='team-leaderboards-container')]
        ),
    ])


def register_team_callbacks(app, data_service):
    """
    Register callbacks for the team statistics layout.

    PERFORMANCE NOTE:
    - This callback does the heavy lifting (data fetching, calculations)
    - It runs AFTER the page renders, so UI appears instantly
    - Results are cached to avoid redundant calculations

    Args:
        app (dash.Dash): The Dash application
        data_service (DataService): The data service for retrieving team data
    """

    @app.callback(
        dash.dependencies.Output('team-recent-games-store', 'data'),
        [dash.dependencies.Input('team-recent-games-selector', 'value')]
    )
    def update_recent_games_store(recent_games_value):
        """Store the selected recent games count."""
        logging.debug(f"Team recent games selector changed to: {recent_games_value}")
        return recent_games_value

    @app.callback(
        [dash.dependencies.Output('team-summary-container', 'children'),
         dash.dependencies.Output('team-leaderboards-container', 'children'),
         dash.dependencies.Output('team-trend-chart-container', 'children')],
        [dash.dependencies.Input('game-type-session-store', 'data'),
         dash.dependencies.Input('team-recent-games-store', 'data'),
         dash.dependencies.Input('team-position-tabs', 'active_tab')]
    )
    def update_team_stats_by_game_type(game_type_data, recent_games_data, active_tab):
        """
        Update team statistics based on selected game type, recent games filter,
        and active position tab.

        **PERFORMANCE**: This is where the heavy lifting happens, but it's ASYNC
        so the page renders while this loads.
        """
        from flask import session
        import time

        start_time = time.time()

        # Default active tab
        if not active_tab:
            active_tab = "forwards"

        # Get team context from session
        team_id = session.get('team_id') if session.get('authenticated', False) else None
        is_coach = session.get('is_coach', False)

        # Get game type
        game_type = game_type_data if isinstance(game_type_data, str) else None
        if game_type_data and isinstance(game_type_data, dict):
            game_type = game_type_data.get('game_type')

        # Handle "All Games" selection
        if game_type == "all":
            game_type = None

        # Default to Regular Season if no game type selected
        if game_type == "" or game_type is False:
            game_type = 'R'

        logging.debug(f"Team callback: team_id={team_id}, is_coach={is_coach}, game_type={game_type}, active_tab={active_tab}")

        try:
            # **OPTIMIZED**: Fetch all data once, reuse where possible
            team_stats = data_service.calculate_team_stats(team_id, game_type)
            games = data_service.get_games(team_id, game_type)
            games = data_service._filter_games_by_date(games, include_future=False)

            # CRITICAL: Sort games by date descending (newest first) - matches Player Stats behavior
            if not games.empty and 'Date' in games.columns:
                games = games.sort_values('Date', ascending=False)

            # Calculate shots and penalties from events
            if not games.empty:
                game_ids = games['ID'].tolist() if 'ID' in games.columns else []
                all_events = data_service.get_events()
                team_events = all_events[all_events['GameID'].isin(game_ids)]
                team_identifier = data_service._get_team_identifier_for_events(team_id)

                # Calculate shots
                team_shot_events = team_events[
                    (team_events['EventType'] == 'Shot') &
                    (team_events['Team'] == team_identifier)
                ]
                shots_for = len(team_shot_events)

                opponent_shot_events = team_events[
                    (team_events['EventType'] == 'Shot') &
                    (team_events['Team'] != team_identifier)
                ]
                shots_against = len(opponent_shot_events)

                # Calculate penalties
                team_penalty_events = team_events[
                    (team_events['EventType'] == 'Penalty') &
                    (team_events['Team'] == team_identifier)
                ]
                penalties = len(team_penalty_events)
                penalty_minutes = team_penalty_events['PenaltyDuration'].sum() if 'PenaltyDuration' in team_penalty_events.columns else 0

                # Add to team_stats
                team_stats['shots_for'] = shots_for
                team_stats['shots_against'] = shots_against
                team_stats['penalties'] = penalties
                team_stats['penalty_minutes'] = int(penalty_minutes)
            else:
                team_stats['shots_for'] = 0
                team_stats['shots_against'] = 0
                team_stats['penalties'] = 0
                team_stats['penalty_minutes'] = 0

            # **IMPORTANT**: Check for recent games filter BEFORE calculating stats
            # If filtering by recent games, recalculate stats from those games only
            num_recent_games = None
            if isinstance(recent_games_data, str) and recent_games_data.startswith('Last'):
                try:
                    num_recent_games = int(recent_games_data.split()[1])
                    # Games already sorted by date descending (newest first) - just take first N
                    games_for_stats = games.head(num_recent_games).copy()
                    game_ids_recent = games_for_stats['ID'].tolist() if 'ID' in games_for_stats.columns and not games_for_stats.empty else []

                    if game_ids_recent:
                        # Recalculate stats for recent games only
                        from layouts.recent_games_layout import (
                            _aggregate_recent_games_team_stats,
                            _calculate_goalie_stats_for_games,
                            _calculate_player_stats_for_games
                        )
                        team_stats = _aggregate_recent_games_team_stats(games_for_stats, data_service, team_id)

                        # Recalculate leaderboards for recent games
                        players = data_service.get_players(team_id)
                        forwards_points_leaders = []
                        defense_leaders = []
                        goalies_leaders = []

                        for _, player in players.iterrows():
                            player_id = data_service._get_player_id_from_series(player)
                            if player_id is None:
                                continue

                            position = player.get('Position', 'F')

                            if position == 'G':
                                stats = _calculate_goalie_stats_for_games(player_id, game_ids_recent, data_service, team_id)
                                goalies_leaders.append({'player': player.to_dict(), **stats})
                            elif position == 'F':
                                stats = _calculate_player_stats_for_games(player_id, game_ids_recent, data_service, team_id)
                                forwards_points_leaders.append({'player': player.to_dict(), **stats})
                            elif position == 'D':
                                stats = _calculate_player_stats_for_games(player_id, game_ids_recent, data_service, team_id)
                                defense_leaders.append({'player': player.to_dict(), **stats})

                        # Sort leaderboards
                        forwards_points_leaders = sorted(forwards_points_leaders, key=lambda x: (-x.get('points', 0), -x.get('goals', 0)))
                        defense_leaders = sorted(defense_leaders, key=lambda x: (-x.get('plus_minus', 0), -x.get('points', 0)))
                        goalies_leaders = sorted(goalies_leaders, key=lambda x: (-x.get('save_percentage', 0)))

                except (ValueError, TypeError, ImportError) as e:
                    logging.error(f"Error processing recent games filter: {e}")
                    num_recent_games = None

            # If NOT filtering by recent games, use normal leaderboards
            if num_recent_games is None:
                if is_coach:
                    forwards_points_leaders = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type=game_type)
                    defense_leaders = data_service.get_team_leaderboard(stat='plus_minus', position='D', team_id=team_id, game_type=game_type)
                    goalies_leaders = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type=game_type)
                else:
                    forwards_points_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='F', team_id=team_id, game_type=game_type)
                    defense_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='D', team_id=team_id, game_type=game_type)
                    goalies_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='G', team_id=team_id, game_type=game_type)

            # --- Build KPI summary tiles ---
            def _kpi(value, label):
                return dbc.Col(html.Div([
                    html.Div(str(value), className="kpi-value"),
                    html.Div(label, className="kpi-label"),
                ], className="kpi-tile"))

            goal_diff = team_stats['goals_for'] - team_stats['goals_against']
            goal_diff_str = f"+{goal_diff}" if goal_diff > 0 else str(goal_diff)
            kpi_cols = [
                _kpi(team_stats['games_played'], "GP"),
                _kpi(team_stats['wins'], "W"),
                _kpi(team_stats['losses'], "L"),
                _kpi(team_stats['ties'], "T"),
                _kpi(team_stats['goals_for'], "GF"),
                _kpi(team_stats['goals_against'], "GA"),
                _kpi(goal_diff_str, "Goal Diff"),
            ]
            if is_coach:
                kpi_cols.append(_kpi(team_stats['penalty_minutes'], "PIM"))

            summary_card = dbc.Card([
                dbc.CardHeader(html.H4("Summary", className="card-title")),
                dbc.CardBody([
                    dbc.Row(kpi_cols, className="g-3 justify-content-center")
                ])
            ], className="mb-4 shadow-sm")

            # --- Build position-filtered leaderboard ---
            section_label = "Leaderboard" if is_coach else "Roster Stats"
            heading_text = f"{section_label} — {active_tab.title()}"

            if active_tab == "goalies":
                active_leaders = goalies_leaders
                table_columns = [
                    {'name': 'Player', 'id': 'Player', 'type': 'text'},
                    {'name': 'GP', 'id': 'GP', 'type': 'numeric'},
                    {'name': 'W', 'id': 'W', 'type': 'numeric'},
                    {'name': 'L', 'id': 'L', 'type': 'numeric'},
                    {'name': 'SV%', 'id': 'SV%', 'type': 'numeric'},
                    {'name': 'GAA', 'id': 'GAA', 'type': 'numeric'},
                ]
                table_data = [{
                    'Player': format_player_label(stats['player']),
                    'GP': stats['games_played'],
                    'W': stats['wins'],
                    'L': stats['losses'],
                    'SV%': f"{stats['save_percentage']:.3f}",
                    'GAA': f"{stats['gaa']:.2f}",
                } for stats in active_leaders]
            else:
                active_leaders = forwards_points_leaders if active_tab == "forwards" else defense_leaders
                table_columns = [
                    {'name': 'Player', 'id': 'Player', 'type': 'text'},
                    {'name': 'G', 'id': 'Goals', 'type': 'numeric'},
                    {'name': 'A', 'id': 'Assists', 'type': 'numeric'},
                    {'name': 'P', 'id': 'Points', 'type': 'numeric'},
                    *([{'name': '+/-', 'id': 'PlusMinus', 'type': 'numeric'}] if is_coach else [])
                ]
                table_data = [{
                    'Player': format_player_label(stats['player']),
                    'Goals': stats['goals'],
                    'Assists': stats['assists'],
                    'Points': stats['points'],
                    **({'PlusMinus': stats['plus_minus']} if is_coach else {})
                } for stats in active_leaders]

            leaderboard_card = dbc.Card([
                dbc.CardHeader(html.H4(heading_text, className="card-title")),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='position-leaderboard-table',
                        columns=table_columns,
                        data=table_data,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'center', 'padding': '10px', 'minWidth': '80px'},
                        style_cell_conditional=[{'if': {'column_id': 'Player'}, 'textAlign': 'left'}],
                        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}],
                        sort_action='native',
                        sort_mode='single',
                    )
                ])
            ], className="mb-4 shadow-sm")

            # --- Build season goals trend chart ---
            games_for_chart = data_service.get_games(team_id, game_type)
            games_for_chart = data_service._filter_games_by_date(games_for_chart, include_future=False)
            if not games_for_chart.empty and 'Date' in games_for_chart.columns:
                g = games_for_chart.sort_values('Date')
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=g['Date'], y=g['GoalsFor'],
                    mode='lines+markers', name='Goals For',
                    line=dict(color='#00843d', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=g['Date'], y=g['GoalsAgainst'],
                    mode='lines+markers', name='Goals Against',
                    line=dict(color='#c8102e', width=2)
                ))
                fig.update_layout(
                    height=260,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(l=40, r=20, t=20, b=40),
                    legend=dict(orientation='h', y=-0.3)
                )
                trend_chart = dcc.Graph(figure=fig, config={'displayModeBar': False})
            else:
                trend_chart = html.Div()

            elapsed = time.time() - start_time
            logging.info(f"Team stats callback completed in {elapsed:.2f} seconds")

            return summary_card, leaderboard_card, trend_chart

        except Exception as e:
            logging.error(f"Error in team stats callback: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return (
                html.Div(f"Error loading team summary: {str(e)}", className="text-danger"),
                html.Div(f"Error loading leaderboards: {str(e)}", className="text-danger"),
                html.Div()
            )
