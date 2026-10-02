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
    Deprecated filter bar widget.
    """
    return html.Div(style={'display': 'none'})
