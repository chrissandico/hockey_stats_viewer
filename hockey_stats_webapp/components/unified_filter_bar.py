from dash import html, dcc
import dash_bootstrap_components as dbc
from components.game_type_filter import create_game_type_filter_component, create_game_type_session_store


def create_unified_filter_bar(
    screen_specific_controls=None,
    recent_games_selector_id='recent-games-selector',
    recent_games_store_id='recent-games-store'
):
    """
    Create a unified filter bar that combines game type filter, optional screen-specific
    controls (like player selection), and recent games selector into a single compact card.

    This component provides a consistent, mobile-responsive filtering interface across
    different screens (Team Stats, Player Stats, etc.).

    Args:
        screen_specific_controls (dash.html component, optional): Optional Dash component
            to display in the left column (e.g., player selection RadioItems for Player Stats).
            If None, the recent games selector will take full width.
        recent_games_selector_id (str): ID for the recent games dropdown selector.
            Default: 'recent-games-selector'
        recent_games_store_id (str): ID for the recent games session store.
            Default: 'recent-games-store'

    Returns:
        dbc.Card: A Bootstrap card component containing the unified filter bar

    Layout Structure:
        - Row 1: Game type tabs (Exhibition, Regular Season, Tournament, All Games) - full width
        - Row 2: Screen-specific controls (left, md=8) + Recent games dropdown (right, md=4)

    Responsive Behavior:
        - Desktop (≥768px): Two columns side-by-side in Row 2
        - Mobile (<768px): All controls stack vertically at full width
    """
    # Build the second row with conditional column layout
    second_row_cols = []

    # Add screen-specific controls column if provided
    if screen_specific_controls:
        second_row_cols.append(
            dbc.Col([
                screen_specific_controls
            ], xs=12, md=8)
        )

    # Add recent games selector column (full width if no screen-specific controls)
    second_row_cols.append(
        dbc.Col([
            html.Label("Recent Games:", className="fw-bold mb-2"),
            dbc.Select(
                id=recent_games_selector_id,
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
        ], xs=12, md=4 if screen_specific_controls else 12)
    )

    return dbc.Card([
        dbc.CardHeader(html.H4("Filters", className="card-title mb-0")),
        dbc.CardBody([
            # Row 1: Game type filter tabs (full width)
            dbc.Row([
                dbc.Col([
                    create_game_type_filter_component()
                ], width=12)
            ], className="mb-3"),

            # Row 2: Screen-specific controls + Recent games dropdown
            dbc.Row(second_row_cols),

            # Session stores (hidden components)
            create_game_type_session_store(),
            dcc.Store(id=recent_games_store_id, storage_type='session', data='all')
        ])
    ], className="mb-4 shadow-sm")
