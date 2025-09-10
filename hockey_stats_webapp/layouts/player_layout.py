import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from layouts.navigation import create_navigation

def create_player_layout(data_service, team_context=None):
    """
    Create the player statistics layout.
    
    Args:
        data_service (DataService): The data service for retrieving player data
        team_context (dict, optional): Team context containing team_id and team_name
        
    Returns:
        dash.html.Div: The player statistics layout
    """
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
        [dash.dependencies.Output('player-info-container', 'children'),
         dash.dependencies.Output('player-game-log-container', 'children')],
        [dash.dependencies.Input('player-dropdown', 'value')]
    )
    def update_player_info(jersey_number):
        # Get team context from session
        from flask import session
        team_id = session.get('team_id') if session.get('authenticated', False) else None
        print(f"\n=== CALLBACK: update_player_info called with jersey_number={jersey_number} ===")
        print(f"DataService instance in callback: {data_service}")
        
        if jersey_number is None:
            print("No jersey number selected, returning empty divs")
            return html.Div(), html.Div()
        
        # Get player by jersey number
        print(f"Getting player with jersey number: {jersey_number}")
        player = data_service.get_player_by_jersey(jersey_number)
        if player is None:
            print(f"ERROR: Player with jersey number {jersey_number} not found!")
            return html.Div(dbc.Alert("Player not found", color="danger")), html.Div()
        
        print(f"Found player: ID={player['ID']}, Position={player['Position']}")
        
        # Check if player is a goalie and calculate appropriate stats
        is_goalie = player['Position'] == 'G'
        print(f"Player position: {player['Position']}, Is goalie: {is_goalie}")
        
        if is_goalie:
            print(f"=== CALLBACK: Calculating goalie stats for player ID: {player['ID']} with team_id: {team_id} ===")
            
            # Debug: Check game roster for goalie
            print("Getting game roster...")
            game_roster = data_service.get_game_roster()
            goalie_roster = game_roster[game_roster['PlayerID'] == player['ID']]
            print(f"DEBUG: Goalie roster entries: {len(goalie_roster)}")
            
            # Debug: Check games for goalie
            print("Getting player games...")
            goalie_games = data_service.get_player_games(player['ID'], team_id)
            print(f"DEBUG: Goalie games count: {len(goalie_games)}")
            if not goalie_games.empty:
                print(f"DEBUG: First game data: {goalie_games.iloc[0].to_dict()}")
            else:
                print("WARNING: No games found for goalie!")
            
            # Calculate goalie stats
            print("Calculating goalie stats...")
            try:
                stats = data_service.calculate_goalie_stats(player['ID'], team_id)
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
            game_log = data_service.get_player_game_log(player['ID'], team_id)
            print(f"DEBUG: Goalie game log entries: {len(game_log)}")
            if game_log:
                print(f"DEBUG: First game log entry: {game_log[0]}")
        else:
            print(f"Calculating player stats for player ID: {player['ID']} with team_id: {team_id}")
            stats = data_service.calculate_player_stats(player['ID'], team_id)
            
        if stats is None:
            return html.Div(dbc.Alert("Could not calculate player statistics", color="danger")), html.Div()
        
        # Create player info card with debug info
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
                        html.H5("Season Totals"),
                        html.Div([
                            # Common stat for both player types
                            html.Div([
                                html.Span("Games Played: ", className="fw-bold"),
                                html.Span(f"{stats['games_played']}")
                            ], className="mb-1"),
                            
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
                                html.Div([
                                    html.Span("Plus/Minus: ", className="fw-bold"),
                                    html.Span(f"{stats['plus_minus']}")
                                ], className="mb-1"),
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
                                # Skater additional stats
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
                        ])
                    ], md=4),
                ])
            ])
        ], className="mb-4 shadow-sm")
        
        # Get player game log
        game_log = data_service.get_player_game_log(player['ID'], team_id)
        print(f"DEBUG: Player game log entries: {len(game_log)}")
        
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
                
            # Different columns for goalies vs skaters
            if player['Position'] == 'G':
                columns = [
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Opponent', 'id': 'Opponent'},
                    {'name': 'Result', 'id': 'Result'},
                    {'name': 'Shots Against', 'id': 'SA'},
                    {'name': 'Saves', 'id': 'SV'},
                    {'name': 'Goals Against', 'id': 'GA'},
                    {'name': 'Save %', 'id': 'SV%'},
                    {'name': 'Shutout', 'id': 'SO'}
                ]
            else:
                columns = [
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Opponent', 'id': 'Opponent'},
                    {'name': 'Result', 'id': 'Result'},
                    {'name': 'Goals', 'id': 'Goals'},
                    {'name': 'Assists', 'id': 'Assists'},
                    {'name': 'Points', 'id': 'Points'},
                    {'name': '+/-', 'id': '+/-'},
                    {'name': 'Shots', 'id': 'Shots'},
                    {'name': 'PIM', 'id': 'PIM'}
                ]
                
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
        
        return player_info, game_log_card
