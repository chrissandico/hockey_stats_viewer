import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from layouts.navigation import create_navigation

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
    
    # Create enhanced radio options with date, opponent, and result
    radio_options = [
        {'label': f"{game['Date']} vs {game['Opponent']} ({game['Result']} {game['GoalsFor']}-{game['GoalsAgainst']})", 'value': game['ID']} 
        for _, game in games.iterrows()
    ]
    
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
        
        # Game summary
        html.Div(id='game-summary-container', className="mb-4"),
        
        # Position filter for player stats
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
                html.Div(id='game-player-stats-container')
            ])
        ], className="mb-4 shadow-sm"),
        
        # Game timeline
        html.Div(id='game-timeline-container')
    ])

# Callbacks for game statistics
def register_game_callbacks(app, data_service):
    """
    Register callbacks for the game statistics layout.
    
    Args:
        app (dash.Dash): The Dash application
        data_service (DataService): The data service for retrieving game data
    """
    # Callback for game summary
    @app.callback(
        dash.dependencies.Output('game-summary-container', 'children'),
        [dash.dependencies.Input('game-dropdown', 'value')]
    )
    def update_game_summary(game_id):
        if game_id is None:
            return html.Div()
        
        # Get game summary
        summary = data_service.get_game_summary(game_id)
        if summary is None:
            return html.Div(dbc.Alert("Game not found", color="danger"))
        
        # Create game summary card
        game = summary['game']
        result_color = "success" if game['Result'] == 'W' else "danger" if game['Result'] == 'L' else "warning"
        
        return dbc.Card([
            dbc.CardHeader(html.H4(f"Game Summary: {game['Date']} vs {game['Opponent']}", className="card-title")),
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
                                html.Span(f"{game['Result']}", className=f"text-{result_color}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Score: ", className="fw-bold"),
                                html.Span(f"{game['GoalsFor']} - {game['GoalsAgainst']}")
                            ], className="mb-1"),
                        ])
                    ], md=4),
                    
                    # Shots and penalties
                    dbc.Col([
                        html.H5("Shots & Penalties"),
                        html.Div([
                            html.Div([
                                html.Span("Your Team Shots: ", className="fw-bold"),
                                html.Span(f"{summary['your_team_shots']}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Opponent Shots: ", className="fw-bold"),
                                html.Span(f"{summary['opponent_shots']}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Your Team PIM: ", className="fw-bold"),
                                html.Span(f"{summary['your_team_pim']}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Opponent PIM: ", className="fw-bold"),
                                html.Span(f"{summary['opponent_pim']}")
                            ], className="mb-1"),
                        ])
                    ], md=4),
                    
                    # Power play
                    dbc.Col([
                        html.H5("Power Play"),
                        html.Div([
                            html.Div([
                                html.Span("Your Team PP: ", className="fw-bold"),
                                html.Span(f"{summary['your_team_pp_goals']} / {summary['your_team_pp_opps']} ({summary['your_team_pp_pct']:.1%})")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Opponent PP: ", className="fw-bold"),
                                html.Span(f"{summary['opponent_pp_goals']} / {summary['opponent_pp_opps']} ({summary['opponent_pp_pct']:.1%})")
                            ], className="mb-1"),
                        ])
                    ], md=4),
                ])
            ])
        ], className="shadow-sm")
    
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
        
        # Determine position filter
        position = None
        if forwards_active:
            position = 'F'
        elif defense_active:
            position = 'D'
        elif goalies_active:
            position = 'G'
        
        # Get player stats for the game
        player_stats = data_service.get_game_player_stats(game_id, position)
        
        if not player_stats:
            return html.Div(dbc.Alert("No player statistics found", color="warning"))
        
        # Create player stats table
        if position == 'G':
            # Calculate goalie stats for the game
            goalie_game_stats = []
            for stats in player_stats:
                player_id = stats['player']['ID']
                
                # Get events for this game
                events = data_service.get_events()
                game_events = events[events['GameID'] == game_id]
                
                # Get all teams in events to determine which is your team
                team_counts = events['Team'].value_counts()
                your_team = team_counts.idxmax() if not team_counts.empty else None
                team_name = your_team if your_team is not None else 'your_team'
                
                # Calculate goals against
                goals_against_events = game_events[(game_events['IsGoal'] == True) & 
                                                 (game_events['Team'] != team_name)]
                goals_against = len(goals_against_events)
                
                # Calculate shots against - ensure we count both shots and goals as shots
                shots_events = game_events[(game_events['EventType'] == 'Shot') & 
                                         (game_events['Team'] != team_name)]
                
                # Also count goals as shots (if they're not already counted as shots)
                goals_as_shots = game_events[(game_events['IsGoal'] == True) & 
                                           (game_events['Team'] != team_name) &
                                           (game_events['EventType'] != 'Shot')]
                
                # Combine unique events
                shots_against = len(shots_events) + len(goals_as_shots)
                
                # Calculate saves
                saves = max(0, shots_against - goals_against)
                
                # Calculate save percentage
                save_percentage = saves / shots_against if shots_against > 0 else 0
                
                goalie_game_stats.append({
                    'player': stats['player'],
                    'shots_against': shots_against,
                    'saves': saves,
                    'goals_against': goals_against,
                    'save_percentage': save_percentage
                })
            
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
            # Skater stats table
            return html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Player", className="text-start"),
                        html.Th("Pos", className="text-center"),
                        html.Th("G", className="text-center"),
                        html.Th("A", className="text-center"),
                        html.Th("P", className="text-center"),
                        html.Th("+/-", className="text-center"),
                        html.Th("Shots", className="text-center"),
                        html.Th("PIM", className="text-center")
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                        html.Td(f"{stats['player']['Position']}", className="text-center"),
                        html.Td(f"{stats['goals']}", className="text-center"),
                        html.Td(f"{stats['assists']}", className="text-center"),
                        html.Td(f"{stats['points']}", className="text-center"),
                        html.Td(f"{stats['plus_minus']}", className="text-center"),
                        html.Td(f"{stats['shots']}", className="text-center"),
                        html.Td(f"{stats['penalty_minutes']}", className="text-center")
                    ]) for stats in player_stats
                ])
            ], className="table table-striped table-hover")
    
    # Callback for game timeline
    @app.callback(
        dash.dependencies.Output('game-timeline-container', 'children'),
        [dash.dependencies.Input('game-dropdown', 'value')]
    )
    def update_game_timeline(game_id):
        if game_id is None:
            return html.Div()
        
        # Get game timeline
        timeline = data_service.get_game_timeline(game_id)
        
        if not timeline:
            return html.Div(dbc.Alert("No timeline events found", color="warning"))
        
        # Create timeline card
        return dbc.Card([
            dbc.CardHeader(html.H4("Game Timeline", className="card-title")),
            dbc.CardBody([
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Period", className="text-center"),
                            html.Th("Event", className="text-center"),
                            html.Th("Team", className="text-center"),
                            html.Th("Player", className="text-start"),
                            html.Th("Details", className="text-start")
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(f"{event['Period']}", className="text-center"),
                            html.Td(f"{event['EventType']}", className="text-center"),
                            html.Td(f"{event['Team']}", className="text-center"),
                            html.Td(f"{event.get('PrimaryPlayerName', 'N/A')}", className="text-start"),
                            html.Td(
                                # Different details based on event type
                                (f"Goal{' (SH)' if event.get('IsShortHanded') else ''}, " +
                                 f"Assists: {event.get('AssistPlayer1Name', 'None')}, {event.get('AssistPlayer2Name', 'None')}")
                                if event['EventType'] == 'Goal' else
                                f"{event.get('PenaltyType', '')}, {event.get('PenaltyDuration', '')} min"
                                if event['EventType'] == 'Penalty' else
                                "",
                                className="text-start"
                            )
                        ]) for event in timeline
                    ])
                ], className="table table-striped table-hover")
            ])
        ], className="shadow-sm")
