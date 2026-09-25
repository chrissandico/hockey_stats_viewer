from dash import html, dcc
import dash_bootstrap_components as dbc


def create_recent_games_dropdown(selector_id):
    """
    Create the recent games dropdown component.

    Args:
        selector_id (str): ID for the dropdown selector

    Returns:
        html.Div: Recent games dropdown with label
    """
    return html.Div([
        html.Label("Recent Games", className="form-label fw-bold mb-1"),
        dbc.Select(
            id=selector_id,
            options=[
                {'label': 'All Games', 'value': 'all'},
                {'label': 'Last 2 Games', 'value': 'Last 2 Games'},
                {'label': 'Last 3 Games', 'value': 'Last 3 Games'},
                {'label': 'Last 5 Games', 'value': 'Last 5 Games'},
                {'label': 'Last 10 Games', 'value': 'Last 10 Games'}
            ],
            value='all',
            className="form-select"
        )
    ])


def create_unified_filter_bar(
    screen_specific_controls=None,
    recent_games_selector_id='recent-games-selector',
    recent_games_store_id='recent-games-store',
    show_recent_games=False
):
    """
    Create a unified filter bar for controls (Player selection, Opponent selection, Refresh button).
    """
    columns = []
    if screen_specific_controls and show_recent_games:
        columns = [
            dbc.Col([screen_specific_controls], xs=12, md=6),
            dbc.Col([create_recent_games_dropdown(recent_games_selector_id)], xs=12, md=6)
        ]
        extra_stores = [dcc.Store(id=recent_games_store_id, storage_type='session', data='all')]
    elif screen_specific_controls:
        columns = [
            dbc.Col([screen_specific_controls], xs=12, md=12)
        ]
        extra_stores = []
    elif show_recent_games:
        columns = [
            dbc.Col([create_recent_games_dropdown(recent_games_selector_id)], xs=12, md=12)
        ]
        extra_stores = [dcc.Store(id=recent_games_store_id, storage_type='session', data='all')]
    else:
        columns = [
            dbc.Col([
                html.Span("Showing all games (Regular Season, Tournament, Playoffs).", className="text-muted small")
            ], xs=12, md=12)
        ]
        extra_stores = []

    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.H5("Filters & Actions", className="mb-0 d-inline-block fw-bold"),
                dbc.Button([
                    html.I(className="fas fa-sync-alt me-1"),
                    "Refresh Data"
                ], id="global-refresh-btn", color="outline-primary", size="sm", className="float-end")
            ], className="d-flex justify-content-between align-items-center")
        ]),
        dbc.CardBody([
            dbc.Row(columns, className="g-3"),
            *extra_stores
        ], className="pb-3")
    ], className="mb-4 shadow-sm")
