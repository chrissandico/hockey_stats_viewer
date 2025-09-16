import os
import dash
import sys
import importlib
from dash import html, dcc, Output, Input, State, callback
import dash_bootstrap_components as dbc
from flask import session

# Force reload of modules to avoid caching issues
print("=== STARTUP: Forcing module reloads to avoid caching ===")
if 'services.data_service' in sys.modules:
    importlib.reload(sys.modules['services.data_service'])
if 'services.sheets_service' in sys.modules:
    importlib.reload(sys.modules['services.sheets_service'])
if 'layouts.player_layout' in sys.modules:
    importlib.reload(sys.modules['layouts.player_layout'])

# Import services and components
from services.sheets_service import SheetsService
from services.auth_service import AuthService
from services.data_service import DataService

# Import layouts
from layouts.main_layout import create_main_layout
from layouts.player_layout import create_player_layout, register_player_callbacks
from layouts.team_layout import create_team_layout
from layouts.game_layout import create_game_layout, register_game_callbacks
from layouts.navigation import create_navigation, register_navigation_callbacks

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

# Configure Flask server for sessions
server = app.server
server.secret_key = os.environ.get('SECRET_KEY', 'hockey-stats-secret-key')

# Initialize services
print("=== STARTUP: Initializing services ===")
sheets_service = SheetsService()
auth_service = AuthService(sheets_service)  # Pass sheets_service for team-based auth
data_service = DataService(sheets_service, force_refresh=True)  # Force refresh data on startup

# Verify DataService initialization
print("=== STARTUP: Verifying DataService initialization ===")
print(f"DataService instance created: {data_service}")
print(f"DataService has cache busting attributes: {hasattr(data_service, '_players_cache')}")

# Test goalie detection
print("=== STARTUP: Testing goalie detection ===")
players = data_service.get_players()
goalies = players[players['Position'] == 'G']
print(f"Found {len(goalies)} goalies in player data")
if not goalies.empty:
    goalie = goalies.iloc[0]
    goalie_id = goalie['ID']
    jersey_number = goalie.get('JerseyNumber', 'Unknown')
    print(f"Goalie found: ID={goalie_id}, Jersey={jersey_number}")
    
    # Test goalie stats calculation
    print("=== STARTUP: Testing goalie stats calculation ===")
    goalie_stats = data_service.calculate_goalie_stats(goalie_id)
    if goalie_stats:
        print(f"Goalie stats calculated successfully:")
        print(f"  Games Played: {goalie_stats['games_played']}")
        print(f"  Wins: {goalie_stats['wins']}")
        print(f"  Shutouts: {goalie_stats['shutouts']}")
        print(f"  Goals Against: {goalie_stats['goals_against']}")
        print(f"  Shots Against: {goalie_stats['shots_against']}")
        print(f"  Saves: {goalie_stats['saves']}")
        print(f"  Save Percentage: {goalie_stats['save_percentage']:.3f}")
    else:
        print("ERROR: Failed to calculate goalie stats during startup verification!")
else:
    print("WARNING: No goalies found during startup verification!")

# Helper functions for team context
def get_team_context():
    """Get team context from session."""
    if not session.get('authenticated', False):
        return None
    
    team_id = session.get('team_id')
    team_name = session.get('team_name')
    
    if not team_id or not team_name:
        print("ERROR: Authenticated session missing team context")
        return None
    
    return {
        'team_id': team_id,
        'team_name': team_name
    }

def validate_team_session():
    """Validate that the session has proper team context."""
    if not session.get('authenticated', False):
        return False
    
    team_context = get_team_context()
    if not team_context:
        # Clear invalid session
        session['authenticated'] = False
        session.pop('team_id', None)
        session.pop('team_name', None)
        print("WARNING: Invalid team session cleared")
        return False
    
    return True

# Define the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Loading(
        id="main-loading",
        type="default",
        color="#00205b",
        children=[
            html.Div(id='page-content')
        ],
        style={"minHeight": "200px"}
    )
])

# Define the main callback for navigation
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    # Check if user is authenticated and has valid team session
    if not validate_team_session() and pathname != '/login':
        return create_login_layout()
    
    # Display the appropriate page based on the URL
    if pathname == '/login':
        return create_login_layout()
    elif pathname == '/player':
        team_context = get_team_context()
        return create_player_layout(data_service, team_context)
    elif pathname == '/team':
        team_context = get_team_context()
        return create_team_layout(data_service, team_context)
    elif pathname == '/game':
        team_context = get_team_context()
        return create_game_layout(data_service, team_context)
    else:
        team_context = get_team_context()
        return create_main_layout(team_context)

# Create login layout
def create_login_layout():
    return html.Div([
        # Login card
        html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.H4([
                        html.I(className="fas fa-users me-2"),
                        "Team Access"
                    ], className="card-title text-center mb-0")
                ]),
                dbc.CardBody([
                    # Password input group with toggle
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-key")),
                        dbc.Input(
                            id="password-input", 
                            type="password", 
                            placeholder="Enter team access code"
                        ),
                        dbc.Button(
                            html.I(id="password-toggle-icon", className="fas fa-eye"),
                            id="password-toggle",
                            color="outline-secondary",
                            className="password-toggle-btn"
                        )
                    ], className="mb-3"),
                    
                    html.Div(id="login-error", className="text-danger mb-2"),
                    
                    dbc.Button([
                        html.I(className="fas fa-sign-in-alt me-2"),
                        "Login"
                    ], id="login-button", color="primary", className="w-100")
                ])
            ], className="shadow")
        ], className="d-flex justify-content-center align-items-center login-container", 
           style={"minHeight": "60vh"})
    ])

# Define login callback
@app.callback(
    [Output('url', 'pathname'),
     Output('login-error', 'children')],
    Input('login-button', 'n_clicks'),
    State('password-input', 'value')
)
def login(n_clicks, password):
    print(f"=== LOGIN CALLBACK TRIGGERED ===")
    print(f"n_clicks: {n_clicks}")
    print(f"password: {password}")
    
    if n_clicks is None:
        print("n_clicks is None, returning no_update")
        return dash.no_update, dash.no_update
    
    try:
        print(f"Attempting to verify password: {password}")
        team_info = auth_service.verify_password(password)
        print(f"Auth service returned: {team_info}")
        
        if team_info:
            # Store authentication and team information in session
            session['authenticated'] = True
            session['team_id'] = team_info['team_id']
            session['team_name'] = team_info['team_name']
            print(f"User authenticated for team: {team_info['team_name']} (ID: {team_info['team_id']})")
            return '/', ''
        else:
            print("Authentication failed - incorrect password")
            return dash.no_update, "Incorrect password. Please try again."
    except Exception as e:
        print(f"ERROR in login callback: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update, f"Login error: {str(e)}"

# Define password toggle callback
@app.callback(
    [Output('password-input', 'type'),
     Output('password-toggle-icon', 'className')],
    Input('password-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_password_visibility(n_clicks):
    if n_clicks is None:
        return dash.no_update, dash.no_update
    
    # Toggle between password and text type
    if n_clicks % 2 == 1:
        # Show password
        return 'text', 'fas fa-eye-slash'
    else:
        # Hide password
        return 'password', 'fas fa-eye'

# Define logout callback
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def logout(n_clicks):
    if n_clicks is None:
        return dash.no_update
    
    # Clear all session data
    session['authenticated'] = False
    session.pop('team_id', None)
    session.pop('team_name', None)
    print("User logged out - session cleared")
    return '/login'

# Register callbacks for navigation, player and game views
register_navigation_callbacks(app)
register_player_callbacks(app, data_service)

# Register game callbacks with team context support
# Note: We need to handle team context dynamically in the callbacks since it's session-based
def register_game_callbacks_with_context():
    """Register game callbacks with dynamic team context support."""
    
    # Import here to avoid circular imports
    import dash
    from dash import Output, Input
    
    # Callback for game summary
    @app.callback(
        Output('game-summary-container', 'children'),
        [Input('game-dropdown', 'value')]
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
        # Safely access Result column with fallback
        result = game.get('Result', 'Unknown')
        result_color = "success" if result == 'W' else "danger" if result == 'L' else "warning"
        
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
                                html.Span(f"{result}", className=f"text-{result_color}")
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
        [Output('btn-all', 'active'),
         Output('btn-forwards', 'active'),
         Output('btn-defense', 'active'),
         Output('btn-goalies', 'active')],
        [Input('btn-all', 'n_clicks'),
         Input('btn-forwards', 'n_clicks'),
         Input('btn-defense', 'n_clicks'),
         Input('btn-goalies', 'n_clicks')]
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
    
    # Callback for player stats with team context
    @app.callback(
        Output('game-player-stats-container', 'children'),
        [Input('game-dropdown', 'value'),
         Input('btn-all', 'active'),
         Input('btn-forwards', 'active'),
         Input('btn-defense', 'active'),
         Input('btn-goalies', 'active')]
    )
    def update_player_stats(game_id, all_active, forwards_active, defense_active, goalies_active):
        if game_id is None:
            return html.Div()
        
        # Get team context from session
        team_context = get_team_context()
        team_id = team_context['team_id'] if team_context else None
        
        # Determine position filter
        position = None
        if forwards_active:
            position = 'F'
        elif defense_active:
            position = 'D'
        elif goalies_active:
            position = 'G'
        
        # Get player stats for the game - pass team_id to filter only logged-in team players
        player_stats = data_service.get_game_player_stats(game_id, position, team_id)
        
        if not player_stats:
            return html.Div(dbc.Alert("No player statistics found", color="warning"))
        
        # Create player stats table
        if position == 'G':
            # Use the existing goalie stats calculation from data service
            goalie_game_stats = []
            for stats in player_stats:
                # Use the calculate_goalie_game_stats method for proper calculation
                goalie_stats = data_service.calculate_goalie_game_stats(stats['player']['ID'], game_id, team_id)
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

# Register the game callbacks with context support
register_game_callbacks_with_context()

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)
