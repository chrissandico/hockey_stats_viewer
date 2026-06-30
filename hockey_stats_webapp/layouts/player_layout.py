import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import logging
from components.game_type_filter import create_game_type_filter_component, create_game_type_session_store
from components.unified_filter_bar import create_unified_filter_bar
import config

def create_player_layout(data_service, team_context=None):
    """
    Create the player statistics layout.
    
    Args:
        data_service (DataService): The data service for retrieving player data
        team_context (dict, optional): Team context containing team_id and team_name
        
    Returns:
        dash.html.Div: The player statistics layout
    """
    # Handle case where data service is not available
    if data_service is None:
        radio_options = []
    else:
        # Get team-filtered players for the dropdown
        team_id = team_context['team_id'] if team_context else None
        players = data_service.get_players(team_id)
        
        # Create enhanced radio options with jersey number and position
        radio_options = [
            {'label': f"#{row['JerseyNumber']} - {row['Position']}", 'value': row['JerseyNumber']} 
            for _, row in players.iterrows()
        ]
        
        # Sort by jersey number (ascending order)
        radio_options.sort(key=lambda x: x['value'])

        # Create player dropdown options with placeholder
        player_dropdown_options = [
            {'label': '-- Select Player --', 'value': '', 'disabled': True},
            *radio_options
        ]

    return html.Div([
        # Title
        html.H1("Player Statistics", className="text-center mt-4"),

        # Unified filter bar
        create_unified_filter_bar(
            screen_specific_controls=html.Div([
                html.Label("Player", className="form-label fw-bold mb-1"),
                dbc.Select(
                    id='player-dropdown',
                    options=player_dropdown_options,
                    value='',
                    className="form-select"
                )
            ]),
            recent_games_selector_id='player-recent-games-selector',
            recent_games_store_id='player-recent-games-store'
        ),
        
        # Progress indicator for data loading
        html.Div(id='player-progress-container', style={'display': 'none'}),
        
        # Player info and season stats with loading
        dcc.Loading(
            id="player-info-loading",
            type="default",
            color="#00205b",
            children=[
                html.Div(id='player-info-container', className="mb-4")
            ]
        ),
        
        # Game log with loading
        dcc.Loading(
            id="player-game-log-loading",
            type="default",
            color="#00205b",
            children=[
                html.Div(id='player-game-log-container')
            ]
        )
    ])

# Callback to update player info and stats
def register_player_callbacks(app, data_service):
    """
    Register callbacks for the player statistics layout.
    
    Args:
        app (dash.Dash): The Dash application
        data_service (DataService): The data service for retrieving player data
    """
    @app.callback(
        dash.dependencies.Output('player-recent-games-store', 'data'),
        [dash.dependencies.Input('player-recent-games-selector', 'value')]
    )
    def update_recent_games_store(recent_games_value):
        """Store the selected recent games count."""
        print(f"=== PLAYER RECENT GAMES STORE CALLBACK: Selector value changed to: {recent_games_value} ===")
        return recent_games_value

    @app.callback(
        [dash.dependencies.Output('player-info-container', 'children'),
         dash.dependencies.Output('player-game-log-container', 'children')],
        [dash.dependencies.Input('player-dropdown', 'value'),
         dash.dependencies.Input('game-type-session-store', 'data'),
         dash.dependencies.Input('player-recent-games-store', 'data')]
    )
    def update_player_info(jersey_number, game_type_data, recent_games_data):
        # Debug logging for callback inputs
        print(f"=== PLAYER CALLBACK TRIGGERED ===")
        print(f"=== INPUTS: jersey_number={jersey_number}, game_type_data={game_type_data}, recent_games_data={recent_games_data} ===")

        # Check if data service is available
        if data_service is None:
            print("DataService is None - services not initialized (missing credentials)")
            if jersey_number is not None:
                return (
                    html.Div(dbc.Alert([
                        html.H5("Service Unavailable", className="alert-heading"),
                        html.P("Player statistics are not available because the application could not connect to the data source."),
                        html.P("This typically occurs when credentials are missing in local development.", className="mb-0")
                    ], color="warning")),
                    html.Div()
                )
            return html.Div(), html.Div()
        
        # Get team context from session
        from flask import session
        team_id = session.get('team_id') if session.get('authenticated', False) else None
        is_coach = session.get('is_coach', False)
        
        # Get game type from callback parameter instead of session
        game_type = game_type_data if isinstance(game_type_data, str) else None
        if game_type_data and isinstance(game_type_data, dict):
            game_type = game_type_data.get('game_type')
        
        # Handle "All Games" selection - when active_tab is "all", game_type should be None
        if game_type == "all":
            game_type = None

        print(f"=== PROCESSED: Jersey={jersey_number}, Team ID={team_id}, Coach={is_coach}, Game type={game_type} ===")
        print(f"=== Recent games data: {recent_games_data} ===")

        # Cache management: Track previous state to detect changes
        previous_game_type = session.get('player_previous_game_type')
        previous_jersey_number = session.get('player_previous_jersey_number')
        logger = logging.getLogger(__name__)
        
        # Clear cache if game type or player selection has changed
        cache_cleared = False
        if previous_game_type != game_type or previous_jersey_number != jersey_number:
            try:
                logger.info(f"Player layout: State changed - game type: {previous_game_type} -> {game_type}, player: {previous_jersey_number} -> {jersey_number}, clearing cache for team {team_id}")
                print(f"PLAYER CALLBACK: State changed - game type: {previous_game_type} -> {game_type}, player: {previous_jersey_number} -> {jersey_number}, clearing cache")
                
                # Use optimized cache clearing strategy
                # Clear cache for the previous game type to ensure fresh data
                if previous_game_type is not None:
                    try:
                        clear_result = data_service.clear_games_cache_optimized(team_id=team_id, game_type=previous_game_type)
                        if clear_result['cleared']:
                            logger.debug(f"Player layout: Optimized cache clear for previous game type {previous_game_type} - "
                                       f"removed {clear_result['entries_removed']} entries, "
                                       f"freed {clear_result['memory_freed']:,.0f} bytes")
                            print(f"PLAYER CALLBACK: Optimized cache clear for previous game type {previous_game_type} - "
                                  f"{clear_result['entries_removed']} entries, {clear_result['memory_freed']:,.0f}B freed")
                        else:
                            logger.debug(f"Player layout: Skipped cache clear for previous game type {previous_game_type} - {clear_result['reason']}")
                            print(f"PLAYER CALLBACK: Skipped cache clear for previous game type - {clear_result['reason']}")
                    except Exception as prev_cache_error:
                        logger.warning(f"Player layout: Failed optimized cache clear for previous game type {previous_game_type}: {str(prev_cache_error)}")
                        print(f"PLAYER CALLBACK: Warning - Failed optimized cache clear for previous game type: {str(prev_cache_error)}")
                        # Fallback to regular cache clearing
                        try:
                            data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
                            print(f"PLAYER CALLBACK: Fallback cache clear successful for previous game type")
                        except Exception as fallback_error:
                            logger.warning(f"Player layout: Fallback cache clear also failed: {str(fallback_error)}")
                
                # Clear cache for the new game type to ensure consistency
                try:
                    clear_result = data_service.clear_games_cache_optimized(team_id=team_id, game_type=game_type)
                    if clear_result['cleared']:
                        logger.debug(f"Player layout: Optimized cache clear for current game type {game_type} - "
                                   f"removed {clear_result['entries_removed']} entries, "
                                   f"freed {clear_result['memory_freed']:,.0f} bytes")
                        print(f"PLAYER CALLBACK: Optimized cache clear for current game type {game_type} - "
                              f"{clear_result['entries_removed']} entries, {clear_result['memory_freed']:,.0f}B freed")
                        cache_cleared = True
                    else:
                        logger.debug(f"Player layout: Skipped cache clear for current game type {game_type} - {clear_result['reason']}")
                        print(f"PLAYER CALLBACK: Skipped cache clear for current game type - {clear_result['reason']}")
                        cache_cleared = False
                except Exception as curr_cache_error:
                    logger.warning(f"Player layout: Failed optimized cache clear for current game type {game_type}: {str(curr_cache_error)}")
                    print(f"PLAYER CALLBACK: Warning - Failed optimized cache clear for current game type: {str(curr_cache_error)}")
                    # Fallback to regular cache clearing
                    try:
                        data_service.clear_games_cache(team_id=team_id, game_type=game_type)
                        print(f"PLAYER CALLBACK: Fallback cache clear successful for current game type")
                        cache_cleared = True
                    except Exception as fallback_error:
                        logger.warning(f"Player layout: Fallback cache clear also failed: {str(fallback_error)}")
                        cache_cleared = False
                        # Continue execution - cache clearing failure shouldn't break the UI
                
                # Update session with new state (do this even if cache clearing partially failed)
                session['player_previous_game_type'] = game_type
                session['player_previous_jersey_number'] = jersey_number
                logger.info(f"Player layout: Cache management completed successfully for team {team_id}")
                print(f"PLAYER CALLBACK: Cache management completed for team {team_id}")
                
            except Exception as cache_error:
                logger.error(f"Player layout: Unexpected error in cache management for team {team_id}: {str(cache_error)}")
                print(f"PLAYER CALLBACK: Error in cache management: {str(cache_error)}")
                
                # Add cache diagnostic information for debugging
                try:
                    cache_info = data_service.get_cache_info()
                    logger.debug(f"Player layout: Cache diagnostic info after error: {cache_info}")
                except Exception as diag_error:
                    logger.warning(f"Player layout: Failed to get cache diagnostics: {str(diag_error)}")
                
                # Continue execution - cache errors shouldn't break the UI
                session['player_previous_game_type'] = game_type
                session['player_previous_jersey_number'] = jersey_number
        
        # Cache performance monitoring - log cache metrics before data operations
        try:
            cache_info = data_service.get_cache_info()
            logger.info(f"Player layout: Cache performance metrics - Size: {cache_info.get('cache_size', 0)} entries, "
                       f"Memory: {cache_info.get('cache_memory_usage', 0):,.0f} bytes, "
                       f"Keys: {cache_info.get('cache_keys', [])}")
            print(f"PLAYER CALLBACK: Cache metrics - {cache_info.get('cache_size', 0)} entries, "
                  f"{cache_info.get('cache_memory_usage', 0):,.0f} bytes")
        except Exception as metrics_error:
            logger.warning(f"Player layout: Failed to collect cache performance metrics: {str(metrics_error)}")
            print(f"PLAYER CALLBACK: Warning - Failed to collect cache metrics: {str(metrics_error)}")
        
        print(f"\n=== CALLBACK: update_player_info called with jersey_number={jersey_number} ===")
        print(f"DataService instance in callback: {data_service}")
        print(f"Coach status: {is_coach}")
        print(f"Game type from session: {game_type}")

        if not jersey_number or jersey_number == '':
            print("No jersey number selected, returning empty divs")
            return html.Div(), html.Div()
        
        # Get player by jersey number - filter by team to ensure we get the right player
        print(f"Getting player with jersey number: {jersey_number} (type: {type(jersey_number)}) for team: {team_id}")

        # Get team-filtered players first
        team_players = data_service.get_players(team_id)

        # Convert jersey_number to int for comparison (dbc.Select returns strings)
        try:
            jersey_number_int = int(jersey_number)
        except (ValueError, TypeError):
            print(f"ERROR: Invalid jersey number format: {jersey_number}")
            return html.Div(dbc.Alert("Invalid player selection", color="danger")), html.Div()

        matching_players = team_players[team_players['JerseyNumber'] == jersey_number_int]

        if matching_players.empty:
            print(f"ERROR: Player with jersey number {jersey_number_int} not found for team {team_id}!")
            print(f"Available players: {team_players['JerseyNumber'].tolist()}")
            return html.Div(dbc.Alert("Player not found", color="danger")), html.Div()
        
        player = matching_players.iloc[0]
        
        # Use centralized helper method for column detection
        player_id = data_service._get_player_id_from_series(player)
        if player_id is None:
            print(f"ERROR: No player ID found using centralized method")
            return html.Div(dbc.Alert("Player ID not found", color="danger")), html.Div()
        
        print(f"Found player: ID={player_id}, Position={player['Position']}")
        
        # Check if player is a goalie and calculate appropriate stats
        is_goalie = player['Position'] == 'G'
        print(f"Player position: {player['Position']}, Is goalie: {is_goalie}")
        
        if is_goalie:
            print(f"=== CALLBACK: Calculating goalie stats for player ID: {player_id} with team_id: {team_id} ===")
            
            # Debug: Check game roster for goalie
            print("Getting game roster...")
            game_roster = data_service.get_game_roster()
            goalie_roster = game_roster[game_roster['PlayerID'] == player_id]
            print(f"DEBUG: Goalie roster entries: {len(goalie_roster)}")
            
            # Debug: Check games for goalie
            print("Getting player games...")
            goalie_games = data_service.get_player_games(player_id, team_id)
            print(f"DEBUG: Goalie games count: {len(goalie_games)}")
            if not goalie_games.empty:
                print(f"DEBUG: First game data: {goalie_games.iloc[0].to_dict()}")
            else:
                print("WARNING: No games found for goalie!")
            
            # Calculate goalie stats
            print("Calculating goalie stats...")
            try:
                stats = data_service.calculate_goalie_stats(player_id, team_id, game_type)
                print(f"DEBUG: Goalie stats calculated: {stats}")
                
                # Verify stats values
                if stats:
                    print(f"Goalie stats verification:")
                    print(f"  Games Played: {stats['games_played']}")
                    print(f"  Wins: {stats['wins']}")
                    print(f"  Shutouts: {stats['shutouts']}")
                    print(f"  Goals Against: {stats['goals_against']}")
                    print(f"  Shots Against: {stats['shots_against']}")
                    print(f"  Saves: {stats['saves']}")
                    print(f"  Save Percentage: {stats['save_percentage']:.3f}")
                else:
                    print("ERROR: calculate_goalie_stats returned None!")
            except Exception as e:
                print(f"EXCEPTION in calculate_goalie_stats: {str(e)}")
                import traceback
                traceback.print_exc()
                stats = None
            
            # Debug: Check game log for goalie
            print("Getting player game log...")
            game_log = data_service.get_player_game_log(player_id, team_id)
            print(f"DEBUG: Goalie game log entries: {len(game_log)}")
            if game_log:
                print(f"DEBUG: First game log entry: {game_log[0]}")
        else:
            print(f"Calculating player stats for player ID: {player_id} with team_id: {team_id}")
            stats = data_service.calculate_player_stats(player_id, team_id, game_type)
            
        if stats is None:
            return html.Div(dbc.Alert("Could not calculate player statistics", color="danger")), html.Div()

        # Get player game log with game type filtering
        game_log = data_service.get_player_game_log(player_id, team_id, game_type)
        print(f"DEBUG: Player game log BEFORE filtering: {len(game_log)} entries (filtered by game_type: {game_type})")

        # Filter to recent games if selected
        num_recent_games = None
        stats_title = "Season Totals"
        if recent_games_data and recent_games_data != 'all':
            try:
                # Extract number from "Last N Games" format (e.g., "Last 5 Games" → split()[1] = "5")
                num_recent_games_requested = int(recent_games_data.split()[1]) if isinstance(recent_games_data, str) else recent_games_data
                print(f"DEBUG: Recent games requested: {num_recent_games_requested}")

                # Limit to available games
                num_recent_games = min(num_recent_games_requested, len(game_log))
                print(f"DEBUG: Actual recent games to show: {num_recent_games} (min of {num_recent_games_requested} and {len(game_log)})")

                if num_recent_games > 0:
                    # Game log is already sorted by date (most recent first)
                    game_log = game_log[:num_recent_games]
                    stats_title = f"Last {num_recent_games} Games"
                    print(f"DEBUG: Filtered game log to last {num_recent_games} games - game_log now has {len(game_log)} entries")

                    # Recalculate stats based on recent games only
                    recent_game_ids = [g['game']['ID'] for g in game_log]
                    print(f"DEBUG: Recalculating stats for recent game IDs: {recent_game_ids}")

                    # Import helper function from recent_games_layout
                    if is_goalie:
                        from layouts.recent_games_layout import _calculate_goalie_stats_for_games
                        stats = _calculate_goalie_stats_for_games(player_id, recent_game_ids, data_service, team_id)
                    else:
                        from layouts.recent_games_layout import _calculate_player_stats_for_games
                        stats = _calculate_player_stats_for_games(player_id, recent_game_ids, data_service, team_id)

                    print(f"DEBUG: Recalculated stats for recent {num_recent_games} games: {stats}")
                else:
                    print(f"DEBUG: num_recent_games is 0, skipping filtering")
            except (ValueError, TypeError) as e:
                print(f"WARNING: Could not parse recent_games_data: {e}")
                num_recent_games = None
        else:
            print(f"DEBUG: No recent games filtering - recent_games_data={recent_games_data}")

        print(f"DEBUG: Final game_log length AFTER filtering: {len(game_log)} entries")

        # Create player info card
        player_info = dbc.Card([
            dbc.CardHeader(html.H4(f"#{player['JerseyNumber']}", className="card-title")),
            dbc.CardBody([
                # Debug info removed for production
                
                dbc.Row([
                    # Player details
                    dbc.Col([
                        html.H5("Player Details"),
                        html.P(f"Position: {player['Position']}"),
                    ], md=4),
                    
                    # Season stats - different display for goalies vs skaters
                    dbc.Col([
                        html.H5(stats_title),
                        html.Div([
                            # Conditional stats based on position
                            *([
                                # Goalie specific stats
                                html.Div([
                                    html.Span("Wins: ", className="fw-bold"),
                                    html.Span(f"{stats['wins']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Shutouts: ", className="fw-bold"),
                                    html.Span(f"{stats['shutouts']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("GAA: ", className="fw-bold"),
                                    html.Span(f"{stats['gaa']:.2f}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Save %: ", className="fw-bold"),
                                    html.Span(f"{stats['save_percentage']:.3f}")
                                ], className="mb-1"),
                            ] if player['Position'] == 'G' else [
                                # Skater specific stats
                                html.Div([
                                    html.Span("Goals: ", className="fw-bold"),
                                    html.Span(f"{stats['goals']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Assists: ", className="fw-bold"),
                                    html.Span(f"{stats['assists']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Points: ", className="fw-bold"),
                                    html.Span(f"{stats['points']}")
                                ], className="mb-1"),
                                # Only show plus/minus for coaches
                                *([html.Div([
                                    html.Span("Plus/Minus: ", className="fw-bold"),
                                    html.Span(f"{stats['plus_minus']}")
                                ], className="mb-1")] if is_coach or not config.is_coaches_only_stat('plus_minus') else []),
                            ])
                        ])
                    ], md=4),
                    
                    # Additional stats - different for goalies vs skaters
                    dbc.Col([
                        html.H5("Additional Stats"),
                        html.Div([
                            *([
                                # Goalie additional stats
                                html.Div([
                                    html.Span("Shots Against: ", className="fw-bold"),
                                    html.Span(f"{stats['shots_against']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Saves: ", className="fw-bold"),
                                    html.Span(f"{stats['saves']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Goals Against: ", className="fw-bold"),
                                    html.Span(f"{stats['goals_against']}")
                                ], className="mb-1"),
                            ] if player['Position'] == 'G' else [
                                # Skater additional stats - only show PIM for coaches
                                *([html.Div([
                                    html.Span("Penalty Minutes: ", className="fw-bold"),
                                    html.Span(f"{stats['penalty_minutes']}")
                                ], className="mb-1")] if is_coach or not config.is_coaches_only_stat('penalty_minutes') else []),
                            ])
                        ])
                    ], md=4),
                ])
            ])
        ], className="mb-4 shadow-sm")

        # Create game log table
        if game_log:
            # Convert game log to DataFrame for the table
            game_log_data = []
            for game_stats in game_log:
                # Different game log data for goalies vs skaters
                if player['Position'] == 'G':
                    print(f"DEBUG: Processing goalie game stats: {game_stats}")
                    game_log_entry = {
                        'Date': game_stats['game']['Date'],
                        'Game Type': config.get_game_type_name(game_stats['game'].get('GameType', 'E')),
                        'Opponent': game_stats['game']['Opponent'],
                        'Result': game_stats['result'],
                        'SA': game_stats['shots_against'],
                        'SV': game_stats['saves'],
                        'GA': game_stats['goals_against'],
                        'SV%': f"{game_stats['save_percentage']:.3f}",
                        'SO': 'Yes' if game_stats['shutout'] else 'No'
                    }
                    print(f"DEBUG: Created game log entry: {game_log_entry}")
                    game_log_data.append(game_log_entry)
                else:
                    # Skater game log - conditionally include coaches-only stats
                    entry = {
                        'Date': game_stats['game']['Date'],
                        'Game Type': config.get_game_type_name(game_stats['game'].get('GameType', 'E')),
                        'Opponent': game_stats['game']['Opponent'],
                        'Result': game_stats['game']['Result'],
                        'Goals': game_stats['goals'],
                        'Assists': game_stats['assists'],
                        'Points': game_stats['points'],
                    }
                    
                    # Only add coaches-only stats if user is a coach
                    if is_coach or not config.is_coaches_only_stat('plus_minus'):
                        entry['+/-'] = game_stats['plus_minus']
                    
                    if is_coach or not config.is_coaches_only_stat('PIM'):
                        entry['PIM'] = game_stats['penalty_minutes']
                    
                    game_log_data.append(entry)
            
            game_log_df = pd.DataFrame(game_log_data)
                
            # Different columns for goalies vs skaters
            if player['Position'] == 'G':
                columns = [
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Game Type', 'id': 'Game Type'},
                    {'name': 'Opponent', 'id': 'Opponent'},
                    {'name': 'Result', 'id': 'Result'},
                    {'name': 'Shots Against', 'id': 'SA'},
                    {'name': 'Saves', 'id': 'SV'},
                    {'name': 'Goals Against', 'id': 'GA'},
                    {'name': 'Save %', 'id': 'SV%'},
                    {'name': 'Shutout', 'id': 'SO'}
                ]
            else:
                # Skater columns - conditionally include coaches-only columns
                columns = [
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Game Type', 'id': 'Game Type'},
                    {'name': 'Opponent', 'id': 'Opponent'},
                    {'name': 'Result', 'id': 'Result'},
                    {'name': 'Goals', 'id': 'Goals'},
                    {'name': 'Assists', 'id': 'Assists'},
                    {'name': 'Points', 'id': 'Points'},
                ]
                
                # Only add coaches-only columns if user is a coach
                if is_coach or not config.is_coaches_only_stat('plus_minus'):
                    columns.append({'name': '+/-', 'id': '+/-'})
                
                if is_coach or not config.is_coaches_only_stat('PIM'):
                    columns.append({'name': 'PIM', 'id': 'PIM'})
                
            game_log_card = dbc.Card([
                dbc.CardHeader(html.H4("Game Log", className="card-title")),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='game-log-table',
                        columns=columns,
                        data=game_log_df.to_dict('records'),
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
                            }
                        ]
                    )
                    ])
            ], className="shadow-sm")
        else:
            game_log_card = dbc.Card([
                dbc.CardHeader(html.H4("Game Log", className="card-title")),
                dbc.CardBody([
                    html.P("No games found for this player.")
                ])
            ], className="shadow-sm")
        
        # Cache performance monitoring - log cache metrics after data operations
        try:
            post_cache_info = data_service.get_cache_info()
            performance_metrics = post_cache_info.get('cache_performance_metrics', {})
            logger.info(f"Player layout: Post-operation cache metrics - Size: {post_cache_info.get('cache_size', 0)} entries, "
                       f"Memory: {post_cache_info.get('cache_memory_usage', 0):,.0f} bytes, "
                       f"Efficiency: {performance_metrics.get('memory_efficiency', 0):.1f}%, "
                       f"Valid/Empty: {performance_metrics.get('valid_entries', 0)}/{performance_metrics.get('empty_entries', 0)}")
            print(f"PLAYER CALLBACK: Post-operation cache - {post_cache_info.get('cache_size', 0)} entries, "
                  f"{post_cache_info.get('cache_memory_usage', 0):,.0f} bytes, "
                  f"{performance_metrics.get('memory_efficiency', 0):.1f}% efficiency")
        except Exception as post_metrics_error:
            logger.warning(f"Player layout: Failed to collect post-operation cache metrics: {str(post_metrics_error)}")
            print(f"PLAYER CALLBACK: Warning - Failed to collect post-operation cache metrics: {str(post_metrics_error)}")

        print(f"=== PLAYER CALLBACK COMPLETE: Returning player_info and game_log_card with {len(game_log)} game entries ===\n")
        return player_info, game_log_card
