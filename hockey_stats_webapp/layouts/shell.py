from dash import html, Output, Input
import dash_bootstrap_components as dbc


def create_shell_header(team_context=None):
    tc = team_context or {}
    team_name = tc.get('team_name', 'Hockey Stats')
    is_coach  = tc.get('is_coach', False)
    is_parent = tc.get('is_parent', False)
    jersey_number = tc.get('jersey_number')
    child_name = tc.get('child_name')

    if is_coach:
        badge = dbc.Badge("COACH", color="warning", className="ms-2")
    elif is_parent:
        badge_text = f"PARENT #{jersey_number}" if jersey_number else "PARENT"
        badge = dbc.Badge(badge_text, color="info", className="ms-2")
    else:
        badge = html.Span()

    # For parent users, hide navigation links to other pages
    nav_links = []
    if not is_parent:
        nav_links = [
            dbc.Nav([
                dbc.NavLink("Dashboard",                 href="/",         active="exact"),
                dbc.NavLink("Players",                   href="/player",   active="exact"),
                dbc.NavLink("Game Log",                  href="/game",     active="exact"),
                dbc.NavLink("vs. Opponents Performance", href="/opponent", active="exact"),
            ], navbar=True, className="me-auto")
        ]

    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand(
                [html.Span("⬡ ", style={"color": "#eca200"}), team_name, badge],
                href="/", className="fw-bold text-white d-flex align-items-center gap-1"
            ),
            dbc.NavbarToggler(id="navbar-toggler") if not is_parent else html.Div(),
            dbc.Collapse([
                *nav_links,
                html.Div([
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="global-refresh-btn", size="sm", color="outline-light", className="me-2"),
                    dbc.Button("Logout", id="logout-button", size="sm", color="outline-light"),
                ], className="d-flex align-items-center ms-auto" if is_parent else "d-flex align-items-center ms-3"),
            ], id="navbar-collapse", navbar=True),
        ], fluid=True),
        dark=True, color="black", sticky="top", className="nhl-navbar mb-0",
    )


def create_shell_footer():
    return html.Footer([
        html.P("Hockey Stats Viewer", className="mb-0"),
        html.P("Built with Dash + Plotly", className="small mb-0",
               style={"color": "rgba(255,255,255,0.5)"}),
    ], className="nhl-footer")


def register_shell_callbacks(app):
    @app.callback(
        Output("navbar-collapse", "is_open"),
        Input("navbar-toggler", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_navbar(n):
        return bool(n and n % 2 == 1)
