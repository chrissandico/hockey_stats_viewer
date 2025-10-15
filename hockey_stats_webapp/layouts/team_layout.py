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
                            ], md=4),
                            
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
                            ], md=4),
                            
                            # Percentages
                            dbc.Col([
                                html.H5("Percentages"),
                                html.Div([
                                    html.Div([
                                        html.Span("Win Percentage: ", className="fw-bold"),
                                        html.Span(f"{team_stats['win_percentage']:.3f}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Goals For per Game: ", className="fw-bold"),
                                        html.Span(f"{team_stats['goals_for'] / team_stats['games_played']:.2f}" if team_stats['games_played'] > 0 else "0.00")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Goals Against per Game: ", className="fw-bold"),
                                        html.Span(f"{team_stats['goals_against'] / team_stats['games_played']:.2f}" if team_stats['games_played'] > 0 else "0.00")
                                    ], className="mb-1"),
                                ])
                            ], md=4),
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
        [dash.dependencies.Output('team-stats-loading', 'children'),
         dash.dependencies.Output('team-leaderboards-loading', 'children'),
         dash.dependencies.Output('team-game-log-loading', 'children')],
        [dash.dependencies.Input('game-type-session-store', 'data')]
    )
    def update_team_stats_by_game_type(game_type_data):
        """Update team statistics based on selected game type."""
        from flask import session
        
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
        
        print(f"\n=== TEAM CALLBACK: update_team_stats_by_game_type called with game_type_data={game_type_data} ===")
        print(f"Team ID: {team_id}, Coach status: {is_coach}, Game type: {game_type}")
        
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
        
        # Calculate team stats with game type filtering
        team_stats = data_service.calculate_team_stats(team_id, game_type)
        
        # Get games with game type filtering
        games = data_service.get_games(team_id, game_type)
        games = data_service._filter_games_by_date(games, include_future=False)
        
        # Get leaderboards with game type filtering
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
        
        # Create updated team stats component
        team_stats_component = dbc.Card([
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
                    ], md=4),
                    
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
                    ], md=4),
                    
                    # Percentages
                    dbc.Col([
                        html.H5("Percentages"),
                        html.Div([
                            html.Div([
                                html.Span("Win Percentage: ", className="fw-bold"),
                                html.Span(f"{team_stats['win_percentage']:.3f}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Goals For per Game: ", className="fw-bold"),
                                html.Span(f"{team_stats['goals_for'] / team_stats['games_played']:.2f}" if team_stats['games_played'] > 0 else "0.00")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Goals Against per Game: ", className="fw-bold"),
                                html.Span(f"{team_stats['goals_against'] / team_stats['games_played']:.2f}" if team_stats['games_played'] > 0 else "0.00")
                            ], className="mb-1"),
                        ])
                    ], md=4),
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
        
        return team_stats_component, leaderboards_component, game_log_component
