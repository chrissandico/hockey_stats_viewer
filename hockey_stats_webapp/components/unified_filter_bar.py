from dash import html, dcc
import dash_bootstrap_components as dbc
from components.game_type_filter import create_game_type_session_store


def create_game_type_dropdown():
    """
    Create the game type dropdown component.

    Returns:
        html.Div: Game type dropdown with label and emoji indicators
    """
    return html.Div([
        html.Label("Game Type", className="form-label fw-bold mb-1"),
        dbc.Select(
            id="game-type-dropdown",
            options=[
                {'label': '⚪ All Games', 'value': 'all'},
                {'label': '🟠 Exhibition', 'value': 'E'},
                {'label': '🔵 Regular Season', 'value': 'R'},
                {'label': '🟣 Tournament', 'value': 'T'}
            ],
            value='R',  # Default to Regular Season
            className="form-select"
        )
    ])


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
                {'label': 'Last 2 Games', 'value': '2'},
                {'label': 'Last 3 Games', 'value': '3'},
                {'label': 'Last 5 Games', 'value': '5'},
                {'label': 'Last 10 Games', 'value': '10'}
            ],
            value='all',
            className="form-select"
        )
    ])


def create_unified_filter_bar(
    screen_specific_controls=None,
    recent_games_selector_id='recent-games-selector',
    recent_games_store_id='recent-games-store'
):
    """
    Create a unified filter bar with all dropdown-based controls in a single row.

    This component provides a clean, cohesive filtering interface with all controls
    as dropdowns. The layout adapts based on screen type:
    - Team Stats: 2 columns (Game Type, Recent Games)
    - Player Stats: 3 columns (Game Type, Player Selection, Recent Games)

    Args:
        screen_specific_controls (dash.html component, optional): Optional Dash component
            for the middle column (e.g., player selection dropdown for Player Stats).
            If None, uses 2-column layout (Team Stats).
        recent_games_selector_id (str): ID for the recent games dropdown selector.
            Default: 'recent-games-selector'
        recent_games_store_id (str): ID for the recent games session store.
            Default: 'recent-games-store'

    Returns:
        dbc.Card: A Bootstrap card component containing the unified filter bar

    Responsive Behavior:
        - Desktop (≥768px): Columns side-by-side with equal widths
        - Mobile (<576px): All controls stack vertically at full width
    """
    # Determine column configuration based on screen type
    if screen_specific_controls:
        # 3-column layout (Player Stats)
        col_width = 4
        columns = [
            dbc.Col([create_game_type_dropdown()], xs=12, md=col_width),
            dbc.Col([screen_specific_controls], xs=12, md=col_width),
            dbc.Col([create_recent_games_dropdown(recent_games_selector_id)], xs=12, md=col_width)
        ]
    else:
        # 2-column layout (Team Stats)
        col_width = 6
        columns = [
            dbc.Col([create_game_type_dropdown()], xs=12, md=col_width),
            dbc.Col([create_recent_games_dropdown(recent_games_selector_id)], xs=12, md=col_width)
        ]

    return dbc.Card([
        dbc.CardHeader([
            html.H5("Filters", className="mb-0")
        ]),
        dbc.CardBody([
            # Single row with adaptive columns
            dbc.Row(columns, className="g-3"),

            # Session stores (hidden components)
            create_game_type_session_store(),
            dcc.Store(id=recent_games_store_id, storage_type='session', data='all')
        ], className="pb-3")
    ], className="mb-4 shadow-sm")
