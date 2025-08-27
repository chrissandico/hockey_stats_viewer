import os
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask import session

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
sheets_service = SheetsService()
auth_service = AuthService()
data_service = DataService(sheets_service, force_refresh=True)  # Force refresh data on startup

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
    # Check if user is authenticated
    if not session.get('authenticated', False) and pathname != '/login':
        return create_login_layout()
    
    # Display the appropriate page based on the URL
    if pathname == '/login':
        return create_login_layout()
    elif pathname == '/player':
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
