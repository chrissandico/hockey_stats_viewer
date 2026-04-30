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
            dbc.NavbarBrand("⬡ Hockey Stats", className="nhl-navbar-brand"),

            # Toggle button for mobile view
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),

            # Navigation links
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Home", href="/", active="exact")),
                    dbc.NavItem(dbc.NavLink("Player Stats", href="/player", active="exact")),
                    dbc.NavItem(dbc.NavLink("Team Stats", href="/team", active="exact")),
                    dbc.NavItem(dbc.NavLink("Game Stats", href="/game", active="exact")),
                    dbc.NavItem(dbc.NavLink("Opponent Stats", href="/opponent", active="exact")),
                ], className="me-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
                is_open=False,
            ),

            # Logout button
            dbc.NavItem(dbc.Button("Logout", id="logout-button", className="nhl-navbar-logout ms-2")),
        ], fluid=True),
        dark=True,
        className="nhl-navbar mb-0",
        sticky="top",
    )

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
