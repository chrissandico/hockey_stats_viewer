import dash
from dash import html, Input, Output, callback
import dash_bootstrap_components as dbc
from flask import session

def create_navigation():
    """
    Create a consistent navigation bar for all pages.
    
    Returns:
        dash.html.Div: The navigation bar component
    """
    return dbc.Navbar(
        dbc.Container([
            # Brand/logo
            dbc.NavbarBrand("Hockey Stats", className="ms-2"),
            
            # Toggle button for mobile view
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            
            # Navigation links in a collapsible container
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Home", href="/", active="exact")),
                    dbc.NavItem(dbc.NavLink("Player Stats", href="/player", active="exact")),
                    dbc.NavItem(dbc.NavLink("Team Stats", href="/team", active="exact")),
                    dbc.NavItem(dbc.NavLink("Game Stats", href="/game", active="exact")),
                    # Coach-only links
                    html.Div(id="app-performance-nav-item", style={"display": "none"})
                ], className="me-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
                is_open=False,
            ),
            
            # Logout button
            dbc.NavItem(dbc.Button("Logout", id="logout-button", color="light", className="ms-2")),
        ]),
        color="primary",
        dark=True,
        className="mb-4",
        sticky="top",  # Make the navbar stick to the top when scrolling
    )

@callback(
    [Output('app-performance-nav-item', 'children'),
     Output('app-performance-nav-item', 'style')],
    [Input('url', 'pathname')],
    prevent_initial_call=False
)
def show_app_performance_nav(pathname):
    """Show App Performance navigation only for coaches."""
    try:
        # Check if user is a coach
        if 'is_coach' in session and session.get('is_coach', False):
            nav_item = dbc.NavItem(dbc.NavLink([
                html.I(className="fas fa-chart-line me-2"),
                "App Performance"
            ], href="/performance", active="exact"))
            return nav_item, {'display': 'block'}
        else:
            return [], {'display': 'none'}
    except Exception:
        return [], {'display': 'none'}

def register_navigation_callbacks(app):
    """
    Register callbacks for the navigation bar.
    
    Args:
        app (dash.Dash): The Dash application
    """
    @app.callback(
        dash.dependencies.Output("navbar-collapse", "is_open"),
        [dash.dependencies.Input("navbar-toggler", "n_clicks")],
        [dash.dependencies.State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open
