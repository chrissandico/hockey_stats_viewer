import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from layouts.navigation import create_navigation
from components.period_breakdown import create_period_breakdown_component
from components.game_type_filter import create_game_type_badge
import config

def create_game_layout(data_service, team_context=None):
    """
    Create the game statistics layout.
    
    Args:
        data_service (DataService): The data service for retrieving game data
        team_context (dict, optional): Team context containing team_id and team_name
        
    Returns:
        dash.html.Div: The game statistics layout
    """
    # Get team-filtered games for the dropdown
    team_id = team_context['team_id'] if team_context else None
    games = data_service.get_games(team_id)
    
    # Filter to only show completed games (past dates)
    games = data_service._filter_games_by_date(games, include_future=False)
    
    # Create enhanced radio options with date, opponent, result, and game type
    radio_options = []
    for _, game in games.iterrows():
        try:
            # Safely access Result column with fallback
            result = game.get('Result', 'Unknown')
            goals_for = game.get('GoalsFor', 0)
            goals_against = game.get('GoalsAgainst', 0)
            game_type = game.get('GameType', 'E')
            game_type_name = config.get_game_type_name(game_type)
            
            label = f"{game['Date']} vs {game['Opponent']} ({result} {goals_for}-{goals_against}) - {game_type_name}"
            radio_options.append({'label': label, 'value': game['ID']})
        except Exception as e:
            # Fallback to basic label if there's any error
            print(f"Error creating game label for game {game.get('ID', 'Unknown')}: {e}")
            label = f"{game.get('Date', 'Unknown')} vs {game.get('Opponent', 'Unknown')}"
            radio_options.append({'label': label, 'value': game.get('ID', 'Unknown')})
    
    # Sort by date (ascending order)
    radio_options.sort(key=lambda x: games[games['ID'] == x['value']]['Date'].iloc[0], reverse=False)
    
    return html.Div([
        # Navigation bar
        create_navigation(),
        
        # Title
        html.H1("Game Statistics", className="text-center mt-4"),
        
        # Game selection
        dbc.Card([
            dbc.CardHeader(html.H4("Select Game", className="card-title")),
            dbc.CardBody([
                html.P("Choose a game:"),
                dbc.RadioItems(
                    id='game-dropdown',
                    options=radio_options,
                    className="mb-3",
                    inline=False
                ),
            ])
        ], className="mb-4 shadow-sm"),
        
        # Game summary with loading
        dcc.Loading(
            id="game-summary-loading",
            type="default",
            color="#00205b",
            children=[
                html.Div(id='game-summary-container', className="mb-4")
            ]
        ),
        
        # Position filter for player stats with loading
        dbc.Card([
            dbc.CardHeader(html.H4("Player Performance", className="card-title")),
            dbc.CardBody([
                html.P("Filter by position:"),
                dbc.ButtonGroup([
                    dbc.Button("All", id="btn-all", color="primary", outline=True, active=True, className="me-1"),
                    dbc.Button("Forwards", id="btn-forwards", color="primary", outline=True, className="me-1"),
                    dbc.Button("Defense", id="btn-defense", color="primary", outline=True, className="me-1"),
                    dbc.Button("Goalies", id="btn-goalies", color="primary", outline=True)
                ], className="mb-3"),
                dcc.Loading(
                    id="game-player-stats-loading",
                    type="default",
                    color="#00205b",
                    children=[
                        html.Div(id='game-player-stats-container')
                    ]
                )
            ])
        ], className="mb-4 shadow-sm")
    ])

# Callbacks for game statistics
def register_game_callbacks(app, data_service, team_context=None):
    """
    Register callbacks for the game statistics layout.
    
    Args:
        app (dash.Dash): The Dash application
        data_service (DataService): The data service for retrieving game data
        team_context (dict, optional): Team context containing team_id and team_name
    """
    # Extract team_id from context for use in callbacks
    team_id = team_context['team_id'] if team_context else None
    # Callback for game summary
    @app.callback(
        dash.dependencies.Output('game-summary-container', 'children'),
        [dash.dependencies.Input('game-dropdown', 'value')]
    )
    def update_game_summary(game_id):
        if game_id is None:
            return html.Div()
        
        # Get team context from session (import here to avoid circular imports)
        from flask import session
        
        # Get team_id and coach status from session for proper filtering
        session_team_id = None
        is_coach = False
        if session.get('authenticated', False):
            session_team_id = session.get('team_id')
            is_coach = session.get('is_coach', False)
        
        # Use session team_id if available, otherwise fall back to passed team_id
        effective_team_id = session_team_id if session_team_id else team_id
        
        # Get game summary - pass effective_team_id for consistency
        summary = data_service.get_game_summary(game_id, effective_team_id)
        if summary is None:
            return html.Div(dbc.Alert("Game not found", color="danger"))
        
        # Get period breakdown data
        period_data = data_service.get_period_breakdown(game_id, effective_team_id)
        
        # Create game summary card
        game = summary['game']
        # Safely access Result column with fallback
        result = game.get('Result', 'Unknown')
        result_color = "success" if result == 'W' else "danger" if result == 'L' else "warning"
        
        # Get game type for badge
        game_type = game.get('GameType', 'E')
        
        # Create the main game summary components
        game_summary_components = [
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H4(f"Game Summary: {game['Date']} vs {game['Opponent']}", className="card-title d-inline-block me-2"),
                        create_game_type_badge(game_type)
                    ], className="d-flex align-items-center")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        # Game details
                        dbc.Col([
                            html.H5("Game Details"),
                            html.Div([
                                html.Div([
                                    html.Span("Date: ", className="fw-bold"),
                                    html.Span(f"{game['Date']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Opponent: ", className="fw-bold"),
                                    html.Span(f"{game['Opponent']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Location: ", className="fw-bold"),
                                    html.Span(f"{game['Location']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Result: ", className="fw-bold"),
                                    html.Span(f"{result}", className=f"text-{result_color}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Score: ", className="fw-bold"),
                                    html.Span(f"{game['GoalsFor']} - {game['GoalsAgainst']}")
                                ], className="mb-1"),
                            ])
                        ], md=6),
                        
                        # Shots and penalties
                        dbc.Col([
                            html.H5("Shots & Penalties"),
                            html.Div([
                                # Always show shots
                                html.Div([
                                    html.Span("Your Team Shots: ", className="fw-bold"),
                                    html.Span(f"{summary['your_team_shots']}")
                                ], className="mb-1"),
                                html.Div([
                                    html.Span("Opponent Shots: ", className="fw-bold"),
                                    html.Span(f"{summary['opponent_shots']}")
                                ], className="mb-1"),
                                
                                # Only show PIM for coaches
                                *([
                                    html.Div([
                                        html.Span("Your Team PIM: ", className="fw-bold"),
                                        html.Span(f"{summary['your_team_pim']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Opponent PIM: ", className="fw-bold"),
                                        html.Span(f"{summary['opponent_pim']}")
                                    ], className="mb-1"),
                                ] if is_coach or not config.is_coaches_only_stat('your_team_pim') else []),
                            ])
                        ], md=6),
                    ])
                ])
            ], className="shadow-sm")
        ]
        
        # Add period breakdown component if data is available
        if period_data:
            period_breakdown_component = create_period_breakdown_component(
                period_data, 
                title="Period Breakdown", 
                show_title=True
            )
            game_summary_components.append(period_breakdown_component)
        
        return html.Div(game_summary_components)
    
    # Callback for position filter buttons
    @app.callback(
        [dash.dependencies.Output('btn-all', 'active'),
         dash.dependencies.Output('btn-forwards', 'active'),
         dash.dependencies.Output('btn-defense', 'active'),
         dash.dependencies.Output('btn-goalies', 'active')],
        [dash.dependencies.Input('btn-all', 'n_clicks'),
         dash.dependencies.Input('btn-forwards', 'n_clicks'),
         dash.dependencies.Input('btn-defense', 'n_clicks'),
         dash.dependencies.Input('btn-goalies', 'n_clicks')]
    )
    def update_position_filter(all_clicks, forwards_clicks, defense_clicks, goalies_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return True, False, False, False
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'btn-all':
            return True, False, False, False
        elif button_id == 'btn-forwards':
            return False, True, False, False
        elif button_id == 'btn-defense':
            return False, False, True, False
        elif button_id == 'btn-goalies':
            return False, False, False, True
        
        return True, False, False, False
    
    # Callback for player stats
    @app.callback(
        dash.dependencies.Output('game-player-stats-container', 'children'),
        [dash.dependencies.Input('game-dropdown', 'value'),
         dash.dependencies.Input('btn-all', 'active'),
         dash.dependencies.Input('btn-forwards', 'active'),
         dash.dependencies.Input('btn-defense', 'active'),
         dash.dependencies.Input('btn-goalies', 'active')]
    )
    def update_player_stats(game_id, all_active, forwards_active, defense_active, goalies_active):
        if game_id is None:
            return html.Div()
        
        # Get team context from session (import here to avoid circular imports)
        from flask import session
        
        # Get team_id and coach status from session for proper filtering
        session_team_id = None
        is_coach = False
        if session.get('authenticated', False):
            session_team_id = session.get('team_id')
            is_coach = session.get('is_coach', False)
        
        # Use session team_id if available, otherwise fall back to passed team_id
        effective_team_id = session_team_id if session_team_id else team_id
        
        # Determine position filter
        position = None
        if forwards_active:
            position = 'F'
        elif defense_active:
            position = 'D'
        elif goalies_active:
            position = 'G'
        
        # Get player stats for the game - pass effective_team_id to filter only logged-in team players
        player_stats = data_service.get_game_player_stats(game_id, position, effective_team_id)
        
        if not player_stats:
            return html.Div(dbc.Alert("No player statistics found", color="warning"))
        
        # Create player stats table
        if position == 'G':
            # Use the existing goalie game stats calculation from data service
            goalie_game_stats = []
            for stats in player_stats:
                player_id = stats['player']['ID']
                
                # Use the data service method which has proper team identifier mapping
                goalie_stats = data_service.calculate_goalie_game_stats(player_id, game_id, effective_team_id)
                if goalie_stats:
                    goalie_game_stats.append(goalie_stats)
            
            # Goalie stats table
            return html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Goalie", className="text-start"),
                        html.Th("Shots Against", className="text-center"),
                        html.Th("Saves", className="text-center"),
                        html.Th("Goals Against", className="text-center"),
                        html.Th("Save %", className="text-center")
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                        html.Td(f"{stats['shots_against']}", className="text-center"),
                        html.Td(f"{stats['saves']}", className="text-center"),
                        html.Td(f"{stats['goals_against']}", className="text-center"),
                        html.Td(f"{stats['save_percentage']:.3f}", className="text-center")
                    ]) for stats in goalie_game_stats
                ])
            ], className="table table-striped table-hover")
        else:
            # Skater stats table - conditionally include coaches-only columns
            header_cells = [
                html.Th("Player", className="text-start"),
                html.Th("Pos", className="text-center"),
                html.Th("G", className="text-center"),
                html.Th("A", className="text-center"),
                html.Th("P", className="text-center"),
            ]
            
            # Only add coaches-only columns if user is a coach
            if is_coach or not config.is_coaches_only_stat('plus_minus'):
                header_cells.append(html.Th("+/-", className="text-center"))
            
            if is_coach or not config.is_coaches_only_stat('PIM'):
                header_cells.append(html.Th("PIM", className="text-center"))
            
            # Create rows with conditional cells
            rows = []
            for stats in player_stats:
                row_cells = [
                    html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                    html.Td(f"{stats['player']['Position']}", className="text-center"),
                    html.Td(f"{stats['goals']}", className="text-center"),
                    html.Td(f"{stats['assists']}", className="text-center"),
                    html.Td(f"{stats['points']}", className="text-center"),
                ]
                
                # Only add coaches-only cells if user is a coach
                if is_coach or not config.is_coaches_only_stat('plus_minus'):
                    row_cells.append(html.Td(f"{stats['plus_minus']}", className="text-center"))
                
                if is_coach or not config.is_coaches_only_stat('PIM'):
                    row_cells.append(html.Td(f"{stats['penalty_minutes']}", className="text-center"))
                
                rows.append(html.Tr(row_cells))
            
            return html.Table([
                html.Thead(html.Tr(header_cells)),
                html.Tbody(rows)
            ], className="table table-striped table-hover")
