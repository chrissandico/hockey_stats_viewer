"""
Performance Monitoring Layout

Integrates the performance dashboard into the main application layout
with proper authentication and access controls.
"""

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from flask import session

from components.performance_dashboard import create_performance_dashboard_layout
from services.auth_service import AuthService


def create_performance_layout(auth_service: AuthService):
    """
    Create the performance monitoring layout with authentication checks.
    
    Args:
        auth_service: Authentication service instance
    
    Returns:
        Dash layout component
    """
    
    return html.Div([
        # Authentication check
        dcc.Location(id='performance-url', refresh=False),
        
        # Main content
        html.Div(id='performance-content'),
        
        # Access denied message
        html.Div(id='performance-access-denied', style={'display': 'none'})
    ])


@callback(
    [Output('performance-content', 'children'),
     Output('performance-access-denied', 'style')],
    [Input('performance-url', 'pathname')],
    prevent_initial_call=False
)
def display_performance_dashboard(pathname):
    """
    Display performance dashboard only for authorized users (coaches).
    """
    
    try:
        # Check if user is authenticated and is a coach
        if 'team_name' not in session or 'is_coach' not in session:
            return [], {'display': 'block'}
        
        if not session.get('is_coach', False):
            return [], {'display': 'block'}
        
        # User is authorized, show the dashboard
        dashboard_layout = create_performance_dashboard_layout()
        
        return dashboard_layout, {'display': 'none'}
        
    except Exception as e:
        # On error, deny access
        return [], {'display': 'block'}


def create_access_denied_layout():
    """Create access denied layout for unauthorized users"""
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H4("Access Denied", className="alert-heading"),
                    html.P("You don't have permission to access the app performance dashboard."),
                    html.Hr(),
                    html.P("This feature is only available to coaches.", className="mb-0")
                ], color="warning")
            ], width=8, className="mx-auto")
        ], className="mt-5")
    ], fluid=True)


# Register the access denied layout callback
@callback(
    Output('performance-access-denied', 'children'),
    [Input('performance-access-denied', 'style')],
    prevent_initial_call=True
)
def show_access_denied(style):
    """Show access denied message when needed"""
    if style.get('display') == 'block':
        return create_access_denied_layout()
    return []


def register_performance_callbacks(app, auth_service: AuthService):
    """
    Register all performance monitoring callbacks with the Dash app.
    
    Args:
        app: Dash application instance
        auth_service: Authentication service instance
    """
    
    # The callbacks are already registered via the @callback decorators
    # This function is here for consistency with other layout modules
    # and can be used for any additional setup if needed
    pass


# Navigation integration
def get_performance_nav_item():
    """
    Get navigation item for performance dashboard.
    
    Returns:
        Navigation item component
    """
    
    return dbc.NavItem([
        dbc.NavLink(
            [
                html.I(className="fas fa-chart-line me-2"),
                "App Performance"
            ],
            href="/performance",
            id="performance-nav-link"
        )
    ])


@callback(
    Output('performance-nav-link', 'style'),
    [Input('performance-url', 'pathname')],
    prevent_initial_call=False
)
def show_performance_nav(pathname):
    """
    Show performance navigation only for coaches.
    """
    
    try:
        # Check if user is a coach
        if 'is_coach' in session and session.get('is_coach', False):
            return {'display': 'block'}
        else:
            return {'display': 'none'}
            
    except Exception:
        return {'display': 'none'}