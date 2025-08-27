import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from layouts.navigation import create_navigation

def create_player_layout(data_service):
    """
    Create the player statistics layout.
    
    Args:
        data_service (DataService): The data service for retrieving player data
        
    Returns:
        dash.html.Div: The player statistics layout
    """
    # Get all players for the dropdown
    players = data_service.get_players()
    
    # Create enhanced radio options with jersey number and position
    radio_options = [
        {'label': f"#{row['JerseyNumber']} - {row['Position']}", 'value': row['JerseyNumber']} 
        for _, row in players.iterrows()
    ]
    
    # Sort by jersey number (ascending order)
    radio_options.sort(key=lambda x: x['value'])
    
    return html.Div([
        # Navigation bar
        create_navigation(),
        
        # Title
        html.H1("Player Statistics", className="text-center mt-4"),
        
        # Player selection
        dbc.Card([
            dbc.CardHeader(html.H4("Select Player", className="card-title")),
            dbc.CardBody([
                html.P("Choose a player by jersey number:"),
                dbc.RadioItems(
                    id='player-dropdown',
                    options=radio_options,
                    className="mb-3",
                    inline=False
                ),
            ])
        ], className="mb-4 shadow-sm"),
        
        # Player info and season stats
        html.Div(id='player-info-container', className="mb-4"),
        
        # Game log
        html.Div(id='player-game-log-container')
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
        [dash.dependencies.Output('player-info-container', 'children'),
         dash.dependencies.Output('player-game-log-container', 'children')],
        [dash.dependencies.Input('player-dropdown', 'value')]
    )
    def update_player_info(jersey_number):
        if jersey_number is None:
            return html.Div(), html.Div()
        
        # Get player by jersey number
        player = data_service.get_player_by_jersey(jersey_number)
        if player is None:
            return html.Div(dbc.Alert("Player not found", color="danger")), html.Div()
        
        # Calculate player stats
        stats = data_service.calculate_player_stats(player['ID'])
        if stats is None:
            return html.Div(dbc.Alert("Could not calculate player statistics", color="danger")), html.Div()
        
        # Create player info card
        player_info = dbc.Card([
            dbc.CardHeader(html.H4(f"#{player['JerseyNumber']}", className="card-title")),
            dbc.CardBody([
                dbc.Row([
                    # Player details
                    dbc.Col([
                        html.H5("Player Details"),
                        html.P(f"Position: {player['Position']}"),
                    ], md=4),
                    
                    # Season stats
                    dbc.Col([
                        html.H5("Season Totals"),
                        html.Div([
                            html.Div([
                                html.Span("Games Played: ", className="fw-bold"),
                                html.Span(f"{stats['games_played']}")
                            ], className="mb-1"),
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
                            html.Div([
                                html.Span("Plus/Minus: ", className="fw-bold"),
                                html.Span(f"{stats['plus_minus']}")
                            ], className="mb-1"),
                        ])
                    ], md=4),
                    
                    # Additional stats
                    dbc.Col([
                        html.H5("Additional Stats"),
                        html.Div([
                            html.Div([
                                html.Span("Shots: ", className="fw-bold"),
                                html.Span(f"{stats['shots']}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Penalty Minutes: ", className="fw-bold"),
                                html.Span(f"{stats['penalty_minutes']}")
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Goals per Game: ", className="fw-bold"),
                                html.Span(f"{stats['goals_per_game']:.2f}")
                            ], className="mb-1"),
                        ])
                    ], md=4),
                ])
            ])
        ], className="mb-4 shadow-sm")
        
        # Get player game log
        game_log = data_service.get_player_game_log(player['ID'])
        
        # Create game log table
        if game_log:
            # Convert game log to DataFrame for the table
            game_log_data = []
            for game_stats in game_log:
                game_log_data.append({
                    'Date': game_stats['game']['Date'],
                    'Opponent': game_stats['game']['Opponent'],
                    'Result': game_stats['game']['Result'],
                    'Goals': game_stats['goals'],
                    'Assists': game_stats['assists'],
                    'Points': game_stats['points'],
                    '+/-': game_stats['plus_minus'],
                    'Shots': game_stats['shots'],
                    'PIM': game_stats['penalty_minutes']
                })
            
            game_log_df = pd.DataFrame(game_log_data)
            
            game_log_card = dbc.Card([
                dbc.CardHeader(html.H4("Game Log", className="card-title")),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='game-log-table',
                        columns=[
                            {'name': 'Date', 'id': 'Date'},
                            {'name': 'Opponent', 'id': 'Opponent'},
                            {'name': 'Result', 'id': 'Result'},
                            {'name': 'Goals', 'id': 'Goals'},
                            {'name': 'Assists', 'id': 'Assists'},
                            {'name': 'Points', 'id': 'Points'},
                            {'name': '+/-', 'id': '+/-'},
                            {'name': 'Shots', 'id': 'Shots'},
                            {'name': 'PIM', 'id': 'PIM'}
                        ],
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
        
        return player_info, game_log_card
