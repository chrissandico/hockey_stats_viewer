import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import logging
from layouts.navigation import create_navigation
from components.game_type_filter import create_game_type_filter_component, create_game_type_session_store
import config

def create_team_layout(data_service, team_context=None):
    """
    Create the team statistics layout.
    
    Args:
        data_service (DataService): The data service for retrieving team data
        team_context (dict, optional): Team context containing team_id and team_name
        
    Returns:
        dash.html.Div: The team statistics layout
    """
    # Get team ID and coach status from session context like player layout does
    from flask import session
    team_id = session.get('team_id') if session.get('authenticated', False) else None
    is_coach = session.get('is_coach', False)
    
    print(f"\n=== TEAM LAYOUT: Using team_id from session: {team_id} ===")
    print(f"TEAM LAYOUT: Coach status: {is_coach}")
    
    # Get current game type from session
    game_type = data_service._get_game_type_from_session()
    print(f"TEAM LAYOUT: Using game type from session: {game_type}")
    
    # Calculate team stats with team filtering and game type filtering
    team_stats = data_service.calculate_team_stats(team_id, game_type)
    print(f"TEAM LAYOUT: Team stats calculated: {team_stats}")

    # Get games for the game log with team filtering, game type filtering, and date filtering (only completed games)
    games = data_service.get_games(team_id, game_type)
    games = data_service._filter_games_by_date(games, include_future=False)
    print(f"TEAM LAYOUT: Games retrieved: {len(games)} games (filtered to completed games only)")

    # Calculate shots and penalties from events for 4-column display
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
    
    # Get leaderboards with team filtering and game type filtering - use different sorting based on coach status
    if is_coach:
        # Coaches: Forwards by points, Defense by plus/minus, Goalies by save percentage
        forwards_points_leaders = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type=game_type)
        defense_leaders = data_service.get_team_leaderboard(stat='plus_minus', position='D', team_id=team_id, game_type=game_type)
        goalies_leaders = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type=game_type)
        forwards_sort_label = "Points"
        defense_sort_label = "Plus/Minus"
        goalies_sort_label = "Save Percentage"
    else:
        # Non-coaches: All positions by jersey number
        forwards_points_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='F', team_id=team_id, game_type=game_type)
        defense_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='D', team_id=team_id, game_type=game_type)
        goalies_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='G', team_id=team_id, game_type=game_type)
        forwards_sort_label = "Jersey Number"
        defense_sort_label = "Jersey Number"
        goalies_sort_label = "Jersey Number"
    
    
    return html.Div([
        # Navigation bar
        create_navigation(),
        
        # Title
        html.H1("Team Statistics", className="text-center mt-4"),
        
        # Game type filter
        create_game_type_filter_component(),
        
        # Session store for game type selection
        create_game_type_session_store(),

        # Session store for recent games count
        dcc.Store(id='team-recent-games-store', storage_type='session', data='all'),

        # Recent games filter
        dbc.Card([
            dbc.CardHeader(html.H4("Recent Games Filter", className="card-title")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.P("View stats for:"),
                        dbc.Select(
                            id='team-recent-games-selector',
                            options=[
                                {'label': 'All Games', 'value': 'all'},
                                {'label': 'Last 2 Games', 'value': '2'},
                                {'label': 'Last 3 Games', 'value': '3'},
                                {'label': 'Last 5 Games', 'value': '5'},
                                {'label': 'Last 10 Games', 'value': '10'}
                            ],
                            value='all'
                        )
                    ], md=3)
                ])
            ])
        ], className="mb-4 shadow-sm"),

        # Team season summary with loading
        dcc.Loading(
            id="team-stats-loading",
            type="default",
            color="#00205b",
            children=[
                dbc.Card([
                    dbc.CardHeader(html.H4("Summary", className="card-title")),
                    dbc.CardBody([
                        dbc.Row([
                            # Record
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

                            # Goals
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
                                        html.Span(f"{team_stats['goals_for'] - team_stats['goals_against']}")
                                    ], className="mb-1"),
                                ])
                            ], md=3),

                            # Shots
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
                                        html.Span(f"{team_stats['shots_for'] - team_stats['shots_against']}")
                                    ], className="mb-1"),
                                ])
                            ], md=3),

                            # Penalties
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
            ]
        ),
        
        # Leaderboards with loading
        dcc.Loading(
            id="team-leaderboards-loading",
            type="default",
            color="#00205b",
            children=[
                dbc.Row([
                    # Forwards leaderboard
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H4("Forwards Leaderboard", className="card-title")),
                            dbc.CardBody([
                                dash_table.DataTable(
                                    id='forwards-leaderboard-table',
                                    columns=[
                                        {'name': 'Player', 'id': 'Player', 'type': 'text'},
                                        {'name': 'G', 'id': 'Goals', 'type': 'numeric'},
                                        {'name': 'A', 'id': 'Assists', 'type': 'numeric'},
                                        {'name': 'P', 'id': 'Points', 'type': 'numeric'},
                                        # Only show plus/minus column for coaches
                                        *([{'name': '+/-', 'id': 'PlusMinus', 'type': 'numeric'}] if is_coach or not config.is_coaches_only_stat('plus_minus') else [])
                                    ],
                                    data=[{
                                        'Player': f"#{stats['player']['JerseyNumber']}",
                                        'Goals': stats['goals'],
                                        'Assists': stats['assists'],
                                        'Points': stats['points'],
                                        # Only include plus/minus data for coaches
                                        **({'PlusMinus': stats['plus_minus']} if is_coach or not config.is_coaches_only_stat('plus_minus') else {})
                                    } for stats in forwards_points_leaders],
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'center',
                                        'padding': '10px',
                                        'minWidth': '80px'
                                    },
                                    style_cell_conditional=[
                                        {
                                            'if': {'column_id': 'Player'},
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
                                    sort_mode='single',
                                    sort_by=[{'column_id': 'Points', 'direction': 'desc'}] if is_coach else [{'column_id': 'Player', 'direction': 'asc'}]
                                )
                            ])
                        ], className="mb-4 shadow-sm")
                    ], md=6),
                    
                    # Defense leaderboard
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H4("Defense Leaderboard", className="card-title")),
                            dbc.CardBody([
                                dash_table.DataTable(
                                    id='defense-leaderboard-table',
                                    columns=[
                                        {'name': 'Player', 'id': 'Player', 'type': 'text'},
                                        {'name': 'G', 'id': 'Goals', 'type': 'numeric'},
                                        {'name': 'A', 'id': 'Assists', 'type': 'numeric'},
                                        {'name': 'P', 'id': 'Points', 'type': 'numeric'},
                                        # Only show plus/minus column for coaches
                                        *([{'name': '+/-', 'id': 'PlusMinus', 'type': 'numeric'}] if is_coach or not config.is_coaches_only_stat('plus_minus') else [])
                                    ],
                                    data=[{
                                        'Player': f"#{stats['player']['JerseyNumber']}",
                                        'Goals': stats['goals'],
                                        'Assists': stats['assists'],
                                        'Points': stats['points'],
                                        # Only include plus/minus data for coaches
                                        **({'PlusMinus': stats['plus_minus']} if is_coach or not config.is_coaches_only_stat('plus_minus') else {})
                                    } for stats in defense_leaders],
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'center',
                                        'padding': '10px',
                                        'minWidth': '80px'
                                    },
                                    style_cell_conditional=[
                                        {
                                            'if': {'column_id': 'Player'},
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
                                    sort_mode='single',
                                    sort_by=[{'column_id': 'PlusMinus', 'direction': 'desc'}] if is_coach and (is_coach or not config.is_coaches_only_stat('plus_minus')) else [{'column_id': 'Player', 'direction': 'asc'}]
                                )
                            ])
                        ], className="mb-4 shadow-sm")
                    ], md=6)
                ]),
                
                # Goalies leaderboard - full width row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H4(f"Goalies Leaderboard (Sorted by {goalies_sort_label})", className="card-title")),
                            dbc.CardBody([
                                html.Table([
                                    html.Thead(
                                        html.Tr([
                                            html.Th("Player", className="text-start"),
                                            html.Th("GP", className="text-center"),
                                            html.Th("W", className="text-center"),
                                            html.Th("L", className="text-center"),
                                            html.Th("T", className="text-center"),
                                            html.Th("SV%", className="text-center"),
                                            html.Th("GAA", className="text-center"),
                                            html.Th("SO", className="text-center"),
                                            html.Th("SOG", className="text-center")
                                        ])
                                    ),
                                    html.Tbody([
                                        html.Tr([
                                            html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                                            html.Td(f"{stats['games_played']}", className="text-center"),
                                            html.Td(f"{stats['wins']}", className="text-center"),
                                            html.Td(f"{stats['losses']}", className="text-center"),
                                            html.Td(f"{stats['ties']}", className="text-center"),
                                            html.Td(f"{stats['save_percentage']:.3f}", className="text-center"),
                                            html.Td(f"{stats['gaa']:.2f}", className="text-center"),
                                            html.Td(f"{stats['shutouts']}", className="text-center"),
                                            html.Td(f"{stats['shots_against']}", className="text-center")
                                        ]) for stats in goalies_leaders
                                    ])
                                ], className="table table-striped table-hover")
                            ])
                        ], className="mb-4 shadow-sm")
                    ], md=12)
                ], className="mt-3") if goalies_leaders else html.Div()
            ]
        ),
        
        # Game log with loading
        dcc.Loading(
            id="team-game-log-loading",
            type="default",
            color="#00205b",
            children=[
                dbc.Card([
                    dbc.CardHeader(html.H4("Game Log", className="card-title")),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='team-game-log-table',
                            columns=[
                                {'name': 'Date', 'id': 'Date'},
                                {'name': 'Opponent', 'id': 'Opponent'},
                                {'name': 'Location', 'id': 'Location'},
                                {'name': 'Result', 'id': 'Result'},
                                {'name': 'Score', 'id': 'Score'}
                            ],
                            data=[{
                                'Date': game['Date'],
                                'Opponent': game['Opponent'],
                                'Location': game['Location'],
                                'Result': game['Result'],
                                'Score': f"{game['GoalsFor']} - {game['GoalsAgainst']}"
                            } for _, game in games.iterrows()],
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'center',
                                'padding': '10px',
                                'minWidth': '80px'
                            },
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                },
                                {
                                    'if': {'filter_query': '{Result} = "W"'},
                                    'backgroundColor': 'rgba(0, 255, 0, 0.1)'
                                },
                                {
                                    'if': {'filter_query': '{Result} = "L"'},
                                    'backgroundColor': 'rgba(255, 0, 0, 0.1)'
                                },
                                {
                                    'if': {'filter_query': '{Result} = "T"'},
                                    'backgroundColor': 'rgba(255, 255, 0, 0.1)'
                                }
                            ],
                            sort_action='native',
                            sort_mode='single',
                            sort_by=[{'column_id': 'Date', 'direction': 'desc'}]
                        )
                    ])
                ], className="shadow-sm")
            ]
        )
    ])

def register_team_callbacks(app, data_service):
    """
    Register callbacks for the team statistics layout to handle game type filtering.

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
        print(f"=== TEAM RECENT GAMES STORE CALLBACK: Selector value changed to: {recent_games_value} ===")
        return recent_games_value

    @app.callback(
        [dash.dependencies.Output('team-stats-loading', 'children'),
         dash.dependencies.Output('team-leaderboards-loading', 'children'),
         dash.dependencies.Output('team-game-log-loading', 'children')],
        [dash.dependencies.Input('game-type-session-store', 'data'),
         dash.dependencies.Input('team-recent-games-store', 'data')]
    )
    def update_team_stats_by_game_type(game_type_data, recent_games_data):
        """Update team statistics based on selected game type."""
        from flask import session

        print(f"\n=== TEAM CALLBACK TRIGGERED ===")
        print(f"=== INPUTS: game_type_data={game_type_data}, recent_games_data={recent_games_data} ===")

        # Get team context from session
        team_id = session.get('team_id') if session.get('authenticated', False) else None
        is_coach = session.get('is_coach', False)

        # Get game type from callback parameter instead of session
        game_type = game_type_data if isinstance(game_type_data, str) else None
        if game_type_data and isinstance(game_type_data, dict):
            game_type = game_type_data.get('game_type')

        # Handle "All Games" selection - when active_tab is "all", game_type should be None
        if game_type == "all":
            game_type = None

        # Only default to Regular Season if game_type is explicitly undefined, not when it's None (All Games)
        # None means "All Games", empty string or False means no selection made
        if game_type == "" or game_type is False:
            game_type = 'R'

        print(f"=== PROCESSED: Team ID={team_id}, Coach={is_coach}, Game type={game_type} ===")
        print(f"=== Recent games data: {recent_games_data} ===")
        
        # Cache management: Track previous game type to detect changes
        previous_game_type = session.get('team_previous_game_type')
        logger = logging.getLogger(__name__)
        
        # Clear cache if game type has changed
        if previous_game_type != game_type:
            try:
                logger.info(f"Team layout: Game type changed from {previous_game_type} to {game_type}, clearing cache for team {team_id}")
                print(f"TEAM CALLBACK: Game type changed from {previous_game_type} to {game_type}, clearing cache")
                
                # Use optimized cache clearing strategy
                # Clear cache for the previous game type to ensure fresh data
                if previous_game_type is not None:
                    try:
                        clear_result = data_service.clear_games_cache_optimized(team_id=team_id, game_type=previous_game_type)
                        if clear_result['cleared']:
                            logger.debug(f"Team layout: Optimized cache clear for previous game type {previous_game_type} - "
                                       f"removed {clear_result['entries_removed']} entries, "
                                       f"freed {clear_result['memory_freed']:,.0f} bytes")
                            print(f"TEAM CALLBACK: Optimized cache clear for previous game type {previous_game_type} - "
                                  f"{clear_result['entries_removed']} entries, {clear_result['memory_freed']:,.0f}B freed")
                        else:
                            logger.debug(f"Team layout: Skipped cache clear for previous game type {previous_game_type} - {clear_result['reason']}")
                            print(f"TEAM CALLBACK: Skipped cache clear for previous game type - {clear_result['reason']}")
                    except Exception as prev_cache_error:
                        logger.warning(f"Team layout: Failed optimized cache clear for previous game type {previous_game_type}: {str(prev_cache_error)}")
                        print(f"TEAM CALLBACK: Warning - Failed optimized cache clear for previous game type: {str(prev_cache_error)}")
                        # Fallback to regular cache clearing
                        try:
                            data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
                            print(f"TEAM CALLBACK: Fallback cache clear successful for previous game type")
                        except Exception as fallback_error:
                            logger.warning(f"Team layout: Fallback cache clear also failed: {str(fallback_error)}")
                
                # Clear cache for the new game type to ensure consistency
                try:
                    clear_result = data_service.clear_games_cache_optimized(team_id=team_id, game_type=game_type)
                    if clear_result['cleared']:
                        logger.debug(f"Team layout: Optimized cache clear for current game type {game_type} - "
                                   f"removed {clear_result['entries_removed']} entries, "
                                   f"freed {clear_result['memory_freed']:,.0f} bytes")
                        print(f"TEAM CALLBACK: Optimized cache clear for current game type {game_type} - "
                              f"{clear_result['entries_removed']} entries, {clear_result['memory_freed']:,.0f}B freed")
                    else:
                        logger.debug(f"Team layout: Skipped cache clear for current game type {game_type} - {clear_result['reason']}")
                        print(f"TEAM CALLBACK: Skipped cache clear for current game type - {clear_result['reason']}")
                except Exception as curr_cache_error:
                    logger.warning(f"Team layout: Failed optimized cache clear for current game type {game_type}: {str(curr_cache_error)}")
                    print(f"TEAM CALLBACK: Warning - Failed optimized cache clear for current game type: {str(curr_cache_error)}")
                    # Fallback to regular cache clearing
                    try:
                        data_service.clear_games_cache(team_id=team_id, game_type=game_type)
                        print(f"TEAM CALLBACK: Fallback cache clear successful for current game type")
                    except Exception as fallback_error:
                        logger.warning(f"Team layout: Fallback cache clear also failed: {str(fallback_error)}")
                        # Continue execution - cache clearing failure shouldn't break the UI
                
                # Update session with new game type (do this even if cache clearing partially failed)
                session['team_previous_game_type'] = game_type
                logger.info(f"Team layout: Cache management completed successfully for team {team_id}")
                print(f"TEAM CALLBACK: Cache management completed for team {team_id}")
                
            except Exception as cache_error:
                logger.error(f"Team layout: Unexpected error in cache management for team {team_id}: {str(cache_error)}")
                print(f"TEAM CALLBACK: Error in cache management: {str(cache_error)}")
                
                # Add cache diagnostic information for debugging
                try:
                    cache_info = data_service.get_cache_info()
                    logger.debug(f"Team layout: Cache diagnostic info after error: {cache_info}")
                except Exception as diag_error:
                    logger.warning(f"Team layout: Failed to get cache diagnostics: {str(diag_error)}")
                
                # Continue execution - cache errors shouldn't break the UI
                session['team_previous_game_type'] = game_type
        
        # Cache performance monitoring - log cache metrics before data operations
        try:
            cache_info = data_service.get_cache_info()
            logger.info(f"Team layout: Cache performance metrics - Size: {cache_info.get('cache_size', 0)} entries, "
                       f"Memory: {cache_info.get('cache_memory_usage', 0):,.0f} bytes, "
                       f"Keys: {cache_info.get('cache_keys', [])}")
            print(f"TEAM CALLBACK: Cache metrics - {cache_info.get('cache_size', 0)} entries, "
                  f"{cache_info.get('cache_memory_usage', 0):,.0f} bytes")
        except Exception as metrics_error:
            logger.warning(f"Team layout: Failed to collect cache performance metrics: {str(metrics_error)}")
            print(f"TEAM CALLBACK: Warning - Failed to collect cache metrics: {str(metrics_error)}")
        else:
            logger.debug(f"Team layout: Game type unchanged ({game_type}), no cache clearing needed")
            print(f"TEAM CALLBACK: Game type unchanged ({game_type}), no cache clearing needed")
        
        # Get games with game type filtering
        games = data_service.get_games(team_id, game_type)
        games = data_service._filter_games_by_date(games, include_future=False)

        # Filter to recent games if selected
        num_recent_games = None
        stats_title = "Summary"
        if recent_games_data and recent_games_data != 'all':
            try:
                num_recent_games_requested = int(recent_games_data)

                # Sort games by date and get N most recent
                if not games.empty and 'Date' in games.columns:
                    games_copy = games.copy()
                    games_copy['DateSortable'] = pd.to_datetime(games_copy['Date'], errors='coerce')
                    games_sorted = games_copy.sort_values('DateSortable', ascending=False).reset_index(drop=True)

                    num_recent_games = min(num_recent_games_requested, len(games_sorted))

                    if num_recent_games > 0:
                        games = games_sorted.head(num_recent_games)
                        stats_title = f"Summary - Last {num_recent_games} Games"
                        print(f"TEAM CALLBACK: Filtered to last {num_recent_games} games")
            except (ValueError, TypeError) as e:
                print(f"WARNING: Could not parse recent_games_data: {e}")
                num_recent_games = None

        # Calculate team stats from filtered games
        if num_recent_games:
            # Recalculate stats for recent games only
            from layouts.recent_games_layout import _aggregate_recent_games_team_stats
            team_stats = _aggregate_recent_games_team_stats(games, data_service, team_id)
        else:
            # Use normal team stats calculation
            team_stats = data_service.calculate_team_stats(team_id, game_type)

        # Get leaderboards with game type filtering
        if num_recent_games:
            # Calculate leaderboards for recent games only
            game_ids = games['ID'].tolist() if 'ID' in games.columns and not games.empty else []
            if game_ids:
                players = data_service.get_players(team_id)
                # We'll recalculate leaderboards below using helper functions
                forwards_points_leaders = []
                defense_leaders = []
                goalies_leaders = []

                for _, player in players.iterrows():
                    player_id = data_service._get_player_id_from_series(player)
                    if player_id is None:
                        continue

                    position = player.get('Position', 'F')

                    if position == 'G':
                        from layouts.recent_games_layout import _calculate_goalie_stats_for_games
                        stats = _calculate_goalie_stats_for_games(player_id, game_ids, data_service, team_id)
                        goalies_leaders.append({'player': player.to_dict(), **stats})
                    else:
                        from layouts.recent_games_layout import _calculate_player_stats_for_games
                        stats = _calculate_player_stats_for_games(player_id, game_ids, data_service, team_id)
                        if position == 'F':
                            forwards_points_leaders.append({'player': player.to_dict(), **stats})
                        elif position == 'D':
                            defense_leaders.append({'player': player.to_dict(), **stats})

                # Sort leaderboards
                forwards_points_leaders = sorted(forwards_points_leaders, key=lambda x: (-x.get('points', 0), -x.get('goals', 0)))
                defense_leaders = sorted(defense_leaders, key=lambda x: (-x.get('plus_minus', 0), -x.get('points', 0)))
                goalies_leaders = sorted(goalies_leaders, key=lambda x: (-x.get('save_percentage', 0), -x.get('saves', 0)))

                forwards_sort_label = "Points"
                defense_sort_label = "Plus/Minus"
                goalies_sort_label = "Save Percentage"
            else:
                forwards_points_leaders = []
                defense_leaders = []
                goalies_leaders = []
                forwards_sort_label = "Points"
                defense_sort_label = "Plus/Minus"
                goalies_sort_label = "Save Percentage"
        else:
            # Normal leaderboards (not recent games filter)
            if is_coach:
                forwards_points_leaders = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id, game_type=game_type)
                defense_leaders = data_service.get_team_leaderboard(stat='plus_minus', position='D', team_id=team_id, game_type=game_type)
                goalies_leaders = data_service.get_team_leaderboard(stat='save_percentage', position='G', team_id=team_id, game_type=game_type)
                forwards_sort_label = "Points"
                defense_sort_label = "Plus/Minus"
                goalies_sort_label = "Save Percentage"
            else:
                forwards_points_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='F', team_id=team_id, game_type=game_type)
                defense_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='D', team_id=team_id, game_type=game_type)
                goalies_leaders = data_service.get_team_leaderboard(stat='jersey_number', position='G', team_id=team_id, game_type=game_type)
                forwards_sort_label = "Jersey Number"
                defense_sort_label = "Jersey Number"
                goalies_sort_label = "Jersey Number"
        
        # Create updated team stats component with 4-column layout
        team_stats_component = dbc.Card([
            dbc.CardHeader(html.H4(stats_title, className="card-title")),
            dbc.CardBody([
                dbc.Row([
                    # Record
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

                    # Goals
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
                                html.Span("Differential: ", className="fw-bold"),
                                html.Span(f"{team_stats['goals_for'] - team_stats['goals_against']:+d}")
                            ], className="mb-1"),
                        ])
                    ], md=3),

                    # Shots
                    dbc.Col([
                        html.H5("Shots"),
                        html.Div([
                            html.Div([
                                html.Span("Shots For: ", className="fw-bold"),
                                html.Span(f"{team_stats.get('shots_for', 0)}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Shots Against: ", className="fw-bold"),
                                html.Span(f"{team_stats.get('shots_against', 0)}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Differential: ", className="fw-bold"),
                                html.Span(f"{team_stats.get('shots_for', 0) - team_stats.get('shots_against', 0):+d}")
                            ], className="mb-1"),
                        ])
                    ], md=3),

                    # Penalties
                    dbc.Col([
                        html.H5("Penalties"),
                        html.Div([
                            html.Div([
                                html.Span("Penalties: ", className="fw-bold"),
                                html.Span(f"{team_stats.get('penalties', 0)}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Penalty Minutes: ", className="fw-bold"),
                                html.Span(f"{team_stats.get('penalty_minutes', 0)}")
                            ], className="mb-1"),
                        ])
                    ], md=3),
                ])
            ])
        ], className="mb-4 shadow-sm")
        
        # Create updated leaderboards component
        leaderboards_component = [
            dbc.Row([
                # Forwards leaderboard
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Forwards Leaderboard", className="card-title")),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id='forwards-leaderboard-table-filtered',
                                columns=[
                                    {'name': 'Player', 'id': 'Player', 'type': 'text'},
                                    {'name': 'G', 'id': 'Goals', 'type': 'numeric'},
                                    {'name': 'A', 'id': 'Assists', 'type': 'numeric'},
                                    {'name': 'P', 'id': 'Points', 'type': 'numeric'},
                                    # Only show plus/minus column for coaches
                                    *([{'name': '+/-', 'id': 'PlusMinus', 'type': 'numeric'}] if is_coach or not config.is_coaches_only_stat('plus_minus') else [])
                                ],
                                data=[{
                                    'Player': f"#{stats['player']['JerseyNumber']}",
                                    'Goals': stats['goals'],
                                    'Assists': stats['assists'],
                                    'Points': stats['points'],
                                    # Only include plus/minus data for coaches
                                    **({'PlusMinus': stats['plus_minus']} if is_coach or not config.is_coaches_only_stat('plus_minus') else {})
                                } for stats in forwards_points_leaders],
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'center',
                                    'padding': '10px',
                                    'minWidth': '80px'
                                },
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'Player'},
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
                                sort_mode='single',
                                sort_by=[{'column_id': 'Points', 'direction': 'desc'}] if is_coach else [{'column_id': 'Player', 'direction': 'asc'}]
                            )
                        ])
                    ], className="mb-4 shadow-sm")
                ], md=6),
                
                # Defense leaderboard
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Defense Leaderboard", className="card-title")),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id='defense-leaderboard-table-filtered',
                                columns=[
                                    {'name': 'Player', 'id': 'Player', 'type': 'text'},
                                    {'name': 'G', 'id': 'Goals', 'type': 'numeric'},
                                    {'name': 'A', 'id': 'Assists', 'type': 'numeric'},
                                    {'name': 'P', 'id': 'Points', 'type': 'numeric'},
                                    # Only show plus/minus column for coaches
                                    *([{'name': '+/-', 'id': 'PlusMinus', 'type': 'numeric'}] if is_coach or not config.is_coaches_only_stat('plus_minus') else [])
                                ],
                                data=[{
                                    'Player': f"#{stats['player']['JerseyNumber']}",
                                    'Goals': stats['goals'],
                                    'Assists': stats['assists'],
                                    'Points': stats['points'],
                                    # Only include plus/minus data for coaches
                                    **({'PlusMinus': stats['plus_minus']} if is_coach or not config.is_coaches_only_stat('plus_minus') else {})
                                } for stats in defense_leaders],
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'center',
                                    'padding': '10px',
                                    'minWidth': '80px'
                                },
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'Player'},
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
                                sort_mode='single',
                                sort_by=[{'column_id': 'PlusMinus', 'direction': 'desc'}] if is_coach and (is_coach or not config.is_coaches_only_stat('plus_minus')) else [{'column_id': 'Player', 'direction': 'asc'}]
                            )
                        ])
                    ], className="mb-4 shadow-sm")
                ], md=6)
            ]),
            
            # Goalies leaderboard - full width row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4(f"Goalies Leaderboard (Sorted by {goalies_sort_label})", className="card-title")),
                        dbc.CardBody([
                            html.Table([
                                html.Thead(
                                    html.Tr([
                                        html.Th("Player", className="text-start"),
                                        html.Th("GP", className="text-center"),
                                        html.Th("W", className="text-center"),
                                        html.Th("L", className="text-center"),
                                        html.Th("T", className="text-center"),
                                        html.Th("SV%", className="text-center"),
                                        html.Th("GAA", className="text-center"),
                                        html.Th("SO", className="text-center"),
                                        html.Th("SOG", className="text-center")
                                    ])
                                ),
                                html.Tbody([
                                    html.Tr([
                                        html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                                        html.Td(f"{stats['games_played']}", className="text-center"),
                                        html.Td(f"{stats['wins']}", className="text-center"),
                                        html.Td(f"{stats['losses']}", className="text-center"),
                                        html.Td(f"{stats['ties']}", className="text-center"),
                                        html.Td(f"{stats['save_percentage']:.3f}", className="text-center"),
                                        html.Td(f"{stats['gaa']:.2f}", className="text-center"),
                                        html.Td(f"{stats['shutouts']}", className="text-center"),
                                        html.Td(f"{stats['shots_against']}", className="text-center")
                                    ]) for stats in goalies_leaders
                                ])
                            ], className="table table-striped table-hover")
                        ])
                    ], className="mb-4 shadow-sm")
                ], md=12)
            ], className="mt-3") if goalies_leaders else html.Div()
        ]
        
        # Create updated game log component
        game_log_component = dbc.Card([
            dbc.CardHeader(html.H4("Game Log", className="card-title")),
            dbc.CardBody([
                dash_table.DataTable(
                    id='team-game-log-table-filtered',
                    columns=[
                        {'name': 'Date', 'id': 'Date'},
                        {'name': 'Opponent', 'id': 'Opponent'},
                        {'name': 'Location', 'id': 'Location'},
                        {'name': 'Result', 'id': 'Result'},
                        {'name': 'Score', 'id': 'Score'},
                        {'name': 'Game Type', 'id': 'GameType'}
                    ],
                    data=[{
                        'Date': game['Date'],
                        'Opponent': game['Opponent'],
                        'Location': game['Location'],
                        'Result': game['Result'],
                        'Score': f"{game['GoalsFor']} - {game['GoalsAgainst']}",
                        'GameType': config.get_game_type_name(game.get('GameType', 'E'))
                    } for _, game in games.iterrows()],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'padding': '10px',
                        'minWidth': '80px'
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        },
                        {
                            'if': {'filter_query': '{Result} = "W"'},
                            'backgroundColor': 'rgba(0, 255, 0, 0.1)'
                        },
                        {
                            'if': {'filter_query': '{Result} = "L"'},
                            'backgroundColor': 'rgba(255, 0, 0, 0.1)'
                        },
                        {
                            'if': {'filter_query': '{Result} = "T"'},
                            'backgroundColor': 'rgba(255, 255, 0, 0.1)'
                        }
                    ],
                    sort_action='native',
                    sort_mode='single',
                    sort_by=[{'column_id': 'Date', 'direction': 'desc'}]
                )
            ])
        ], className="shadow-sm")
        
        # Cache performance monitoring - log cache metrics after data operations
        try:
            post_cache_info = data_service.get_cache_info()
            performance_metrics = post_cache_info.get('cache_performance_metrics', {})
            logger.info(f"Team layout: Post-operation cache metrics - Size: {post_cache_info.get('cache_size', 0)} entries, "
                       f"Memory: {post_cache_info.get('cache_memory_usage', 0):,.0f} bytes, "
                       f"Efficiency: {performance_metrics.get('memory_efficiency', 0):.1f}%, "
                       f"Valid/Empty: {performance_metrics.get('valid_entries', 0)}/{performance_metrics.get('empty_entries', 0)}")
            print(f"TEAM CALLBACK: Post-operation cache - {post_cache_info.get('cache_size', 0)} entries, "
                  f"{post_cache_info.get('cache_memory_usage', 0):,.0f} bytes, "
                  f"{performance_metrics.get('memory_efficiency', 0):.1f}% efficiency")
        except Exception as post_metrics_error:
            logger.warning(f"Team layout: Failed to collect post-operation cache metrics: {str(post_metrics_error)}")
            print(f"TEAM CALLBACK: Warning - Failed to collect post-operation cache metrics: {str(post_metrics_error)}")

        print(f"=== TEAM CALLBACK RETURNING COMPONENTS ===")
        print(f"=== Stats title should show: {stats_title} ===")

        return team_stats_component, leaderboards_component, game_log_component
