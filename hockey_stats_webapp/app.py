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
from layouts.main_layout import create_main_layout, register_dashboard_callbacks
from layouts.player_layout import create_player_layout, register_player_callbacks
from layouts.team_layout import create_team_layout
from layouts.game_layout import create_game_layout, register_game_callbacks
from layouts.opponent_layout import create_opponent_layout, register_opponent_callbacks
from layouts.navigation import create_navigation, register_navigation_callbacks
from layouts.shell import create_shell_header, create_shell_footer, register_shell_callbacks

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap",
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

# Configure Flask server for sessions
server = app.server
server.secret_key = os.environ.get('SECRET_KEY', 'hockey-stats-secret-key')

# Initialize services with error handling
print("=== STARTUP: Initializing services ===")
try:
    sheets_service = SheetsService()
    auth_service = AuthService(sheets_service)  # Pass sheets_service for team-based auth
    data_service = DataService(sheets_service, force_refresh=True)  # Force refresh data on startup
    
    # Verify DataService initialization
    print("=== STARTUP: Verifying DataService initialization ===")
    print(f"DataService instance created: {data_service}")
    print(f"DataService has cache busting attributes: {hasattr(data_service, '_players_cache')}")
    
    services_initialized = True
    
except Exception as e:
    print(f"ERROR: Failed to initialize services: {e}")
    print("This may be expected in local development without credentials.")
    print("On Render, credentials should be available via environment variables.")
    
    # Create dummy services for local development
    sheets_service = None
    auth_service = None
    data_service = None
    services_initialized = False

# Test goalie detection with error handling (only if services are initialized)
print("=== STARTUP: Testing goalie detection ===")
if services_initialized and data_service is not None:
    try:
        players = data_service.get_players()
        print(f"Players data loaded: {len(players)} players")
        
        if not players.empty:
            print(f"Player columns: {players.columns.tolist()}")
            
            # Check for goalies
            if 'Position' in players.columns:
                goalies = players[players['Position'] == 'G']
                print(f"Found {len(goalies)} goalies in player data")
                
                if not goalies.empty:
                    goalie = goalies.iloc[0]
                    
                    # Try different possible ID column names
                    goalie_id = None
                    possible_id_columns = ['ID', 'PlayerID', 'id', 'player_id']
                    
                    for col_name in possible_id_columns:
                        if col_name in goalie.index:
                            try:
                                goalie_id = goalie[col_name]
                                print(f"Goalie found using column '{col_name}': ID={goalie_id}")
                                break
                            except Exception as e:
                                print(f"Failed to access column '{col_name}': {e}")
                                continue
                    
                    if goalie_id is not None:
                        jersey_number = goalie.get('JerseyNumber', 'Unknown')
                        print(f"Goalie details: ID={goalie_id}, Jersey={jersey_number}")
                        
                        # Test goalie stats calculation with error handling
                        print("=== STARTUP: Testing goalie stats calculation ===")
                        try:
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
                                print("WARNING: Failed to calculate goalie stats during startup verification")
                        except Exception as e:
                            print(f"ERROR calculating goalie stats: {e}")
                    else:
                        print("ERROR: Could not find valid ID column for goalie")
                else:
                    print("WARNING: No goalies found in player data")
            else:
                print("ERROR: No 'Position' column found in players data")
        else:
            print("WARNING: Players data is empty")
            
    except Exception as e:
        print(f"ERROR during goalie detection test: {e}")
        import traceback
        traceback.print_exc()
        print("CONTINUING STARTUP despite goalie detection error...")
else:
    print("Skipping goalie detection test - services not initialized")

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
        'team_name': team_name,
        'is_coach': session.get('is_coach', False),
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
    html.Div(id='shell-header-container'),
    dcc.Loading(
        id="main-loading",
        type="default",
        color="#0042bb",
        children=[html.Div(id='page-content')],
        style={"minHeight": "200px"}
    ),
    html.Div(id='shell-footer-container'),
], className="nhl-app")

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
    elif pathname == '/opponent':
        team_context = get_team_context()
        return create_opponent_layout(data_service, team_context)
    else:
        team_context = get_team_context()
        return create_main_layout(team_context)

# Shell callback — renders persistent header/footer outside page-content
@app.callback(
    Output('shell-header-container', 'children'),
    Output('shell-footer-container', 'children'),
    Input('url', 'pathname')
)
def update_shell(pathname):
    if pathname == '/login' or not validate_team_session():
        return [], []
    return create_shell_header(get_team_context()), create_shell_footer()

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
            ], className="shadow", style={
                "backgroundColor": "rgba(255, 255, 255, 0.95)",
                "backdropFilter": "blur(10px)"
            })
        ], className="d-flex justify-content-center align-items-center login-container", 
           style={"minHeight": "100vh"})
    ], style={
        "backgroundImage": "url('/assets/theshift.jpg')",
        "backgroundSize": "cover",
        "backgroundPosition": "center",
        "backgroundRepeat": "no-repeat",
        "backgroundAttachment": "fixed",
        "minHeight": "100vh",
        "width": "100%"
    })

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
    
    # Check if services are available
    if not services_initialized or sheets_service is None or auth_service is None:
        print("Services not initialized - cannot authenticate (missing credentials)")
        return dash.no_update, "Authentication service unavailable. This typically occurs when credentials are missing in local development."
    
    try:
        # Force refresh teams data to get the latest passwords from Google Sheets
        print("Forcing refresh of teams data to get latest passwords...")
        sheets_service.get_teams(force_refresh=True)
        
        print(f"Attempting to verify password: {password}")
        team_info = auth_service.verify_password(password)
        print(f"Auth service returned: {team_info}")
        
        if team_info:
            # Store authentication and team information in session
            session['authenticated'] = True
            session['team_id'] = team_info['team_id']
            session['team_name'] = team_info['team_name']
            session['is_coach'] = team_info.get('is_coach', False)  # Store coach flag
            print(f"User authenticated for team: {team_info['team_name']} (ID: {team_info['team_id']}, Coach: {session['is_coach']})")
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
# Always register callbacks, but handle the case where services aren't initialized
register_shell_callbacks(app)
register_player_callbacks(app, data_service)

if services_initialized:
    # Register dashboard callbacks for the home page live stats
    register_dashboard_callbacks(app, data_service)

    # Register game callbacks - use the fixed version from game_layout.py
    # Note: We pass None for team_context since it will be retrieved dynamically from session
    register_game_callbacks(app, data_service, team_context=None)

    # Register team callbacks for game type filtering
    from layouts.team_layout import register_team_callbacks
    register_team_callbacks(app, data_service)

    # Register opponent callbacks
    register_opponent_callbacks(app, data_service)

    # Register game type filter callbacks
    from components.game_type_filter import register_game_type_filter_callbacks
    register_game_type_filter_callbacks(app, data_service)

    print("=== STARTUP: All callbacks registered successfully ===")
else:
    print("=== STARTUP: Core callbacks registered, but data-dependent callbacks skipped due to service initialization failure ===")
    print("This is expected in local development without credentials.")


# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)
