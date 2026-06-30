from dash import html, Output, Input
import dash_bootstrap_components as dbc


def create_shell_header(team_context=None):
    tc = team_context or {}
    team_name = tc.get('team_name', 'Hockey Stats')
    is_coach  = tc.get('is_coach', False)
    coach_badge = dbc.Badge("COACH", color="warning", className="ms-2") if is_coach else html.Span()

    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand(
                [html.Span("⬡ ", style={"color": "#eca200"}), team_name, coach_badge],
                href="/", className="fw-bold text-white d-flex align-items-center gap-1"
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse([
                dbc.Nav([
                    dbc.NavLink("Dashboard", href="/",         active="exact"),
                    dbc.NavLink("Players",   href="/player",   active="exact"),
                    dbc.NavLink("Games",     href="/game",     active="exact"),
                    dbc.NavLink("Team",      href="/team",     active="exact"),
                    dbc.NavLink("Opponents", href="/opponent", active="exact"),
                ], navbar=True, className="me-auto"),
                dbc.Button("Logout", id="logout-button", size="sm",
                           color="outline-light", className="ms-3"),
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
