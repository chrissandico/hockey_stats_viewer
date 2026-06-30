import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
def create_main_layout(team_context=None):
    """
    Create the main layout for the application.
    
    Args:
        team_context (dict, optional): Team context containing team_id and team_name
    
    Returns:
        dash.html.Div: The main layout
    """
    # Get team name for display
    team_name = team_context['team_name'] if team_context else "Hockey Stats"
    
    return html.Div([
        # Main content container
        dbc.Container([
            # Welcome message with team name
            html.H1(f"Welcome to {team_name}", className="text-center mt-4"),
            html.P("Select a view from the navigation bar above to get started.", className="text-center"),
            
            # Dashboard cards
            dbc.Row([
                # Player Stats Card
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.H4("Player Statistics", className="text-center")),
                        dbc.CardBody([
                            html.P("View detailed statistics for individual players."),
                            dbc.Button("Go to Player Stats", href="/player", color="primary", className="w-100")
                        ])
                    ], className="mb-4 shadow-sm"),
                    md=4
                ),
                
                # Team Stats Card
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.H4("Team Statistics", className="text-center")),
                        dbc.CardBody([
                            html.P("View team performance metrics and player rankings."),
                            dbc.Button("Go to Team Stats", href="/team", color="primary", className="w-100")
                        ])
                    ], className="mb-4 shadow-sm"),
                    md=4
                ),
                
                # Game Stats Card
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.H4("Game Statistics", className="text-center")),
                        dbc.CardBody([
                            html.P("View detailed information about specific games."),
                            dbc.Button("Go to Game Stats", href="/game", color="primary", className="w-100")
                        ])
                    ], className="mb-4 shadow-sm"),
                    md=4
                ),
            ], className="mt-4"),
            
            # Footer
            html.Footer([
                html.Hr(),
                html.P("Hockey Stats Web Application", className="text-center text-muted")
            ], className="mt-5")
        ], className="mb-5")
    ])
