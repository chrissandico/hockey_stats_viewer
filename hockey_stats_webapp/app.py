import os
import dash
import sys
import importlib
from dash import html, dcc
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
    external_stylesheets=[dbc.themes.BOOTSTRAP],
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
auth_service = AuthService()
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

# Define the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Define the main callback for navigation
@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')]
)
def display_page(pathname):
    # TESTING: Bypass authentication for testing
    print(f"DEBUG: Bypassing authentication for testing - allowing access to {pathname}")
    
    # Force authentication for testing
    session['authenticated'] = True
    
    # Always redirect to player page for testing
    if pathname == '/' or pathname == '/login':
        print("DEBUG: Redirecting to player page for testing")
        return create_player_layout(data_service)
    
    # Display the appropriate page based on the URL
    if pathname == '/player':
        return create_player_layout(data_service)
    elif pathname == '/team':
        return create_team_layout(data_service)
    elif pathname == '/game':
        return create_game_layout(data_service)
    else:
        return create_main_layout()

# Create login layout
def create_login_layout():
    return html.Div([
        html.H1("Hockey Stats App - Login", className="text-center mt-4"),
        html.Div([
            dbc.Card(
                dbc.CardBody([
                    html.H4("Team Login", className="card-title text-center"),
                    dbc.Input(id="password-input", type="password", placeholder="Enter team password"),
                    html.Div(id="login-error", className="text-danger mt-2"),
                    dbc.Button("Login", id="login-button", color="primary", className="mt-3 w-100")
                ]),
                className="shadow-sm"
            )
        ], className="d-flex justify-content-center align-items-center", style={"height": "50vh"})
    ])

# Define login callback
@app.callback(
    [dash.dependencies.Output('url', 'pathname'),
     dash.dependencies.Output('login-error', 'children')],
    [dash.dependencies.Input('login-button', 'n_clicks')],
    [dash.dependencies.State('password-input', 'value')]
)
def login(n_clicks, password):
    if n_clicks is None:
        return dash.no_update, dash.no_update
    
    if auth_service.verify_password(password):
        session['authenticated'] = True
        return '/', ''
    else:
        return dash.no_update, "Incorrect password. Please try again."

# Define logout callback
@app.callback(
    dash.dependencies.Output('url', 'pathname', allow_duplicate=True),
    [dash.dependencies.Input('logout-button', 'n_clicks')],
    prevent_initial_call=True
)
def logout(n_clicks):
    if n_clicks is None:
        return dash.no_update
    
    session['authenticated'] = False
    return '/login'

# Register callbacks for navigation, player and game views
register_navigation_callbacks(app)
register_player_callbacks(app, data_service)
register_game_callbacks(app, data_service)

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)
