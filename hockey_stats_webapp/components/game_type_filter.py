import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from config import get_all_game_types, get_game_type_name, get_game_type_badge_class, DEFAULT_GAME_TYPE

def create_game_type_filter_component(selected_game_type=None, show_all_option=True):
    """
    Create a reusable game type filter component.
    
    Args:
        selected_game_type (str, optional): Currently selected game type. Defaults to Exhibition.
        show_all_option (bool): Whether to show an "All Games" option. Defaults to True.
        
    Returns:
        dash.html.Div: The game type filter component
    """
    # Get all available game types
    game_types = get_all_game_types()
    
    # Set default selection
    if selected_game_type is None:
        selected_game_type = DEFAULT_GAME_TYPE
    
    # Create tab options
    tab_options = []
    
    # Add "All Games" option if requested
    if show_all_option:
        tab_options.append(
            dbc.Tab(
                label="All Games",
                tab_id="all",
                active_tab_style={"backgroundColor": "#6c757d", "color": "white"},
                tab_style={"backgroundColor": "#f8f9fa", "color": "#6c757d"}
            )
        )
    
    # Add game type tabs
    for game_type_code, game_type_info in game_types.items():
        tab_options.append(
            dbc.Tab(
                label=game_type_info['name'],
                tab_id=game_type_code,
                active_tab_style={"backgroundColor": game_type_info['color'], "color": "white"},
                tab_style={"backgroundColor": "#f8f9fa", "color": game_type_info['color']}
            )
        )
    
    # Determine active tab
    if show_all_option and selected_game_type is None:
        active_tab = "all"
    else:
        active_tab = selected_game_type or DEFAULT_GAME_TYPE
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-filter me-2"),
                "Filter by Game Type"
            ], className="card-title mb-0")
        ]),
        dbc.CardBody([
            dbc.Tabs(
                tab_options,
                id="game-type-filter-tabs",
                active_tab=active_tab,
                className="mb-3"
            ),
            html.Div(id="game-type-filter-info", className="text-muted small")
        ])
    ], className="mb-4 shadow-sm")

def create_game_type_badge(game_type_code):
    """
    Create a colored badge for a game type.
    
    Args:
        game_type_code (str): The game type code (E, R, T)
        
    Returns:
        dash_bootstrap_components.Badge: The game type badge
    """
    game_type_name = get_game_type_name(game_type_code)
    badge_class = get_game_type_badge_class(game_type_code)
    
    return dbc.Badge(
        game_type_name,
        color=badge_class,
        className="me-1"
    )

def register_game_type_filter_callbacks(app, data_service):
    """
    Register callbacks for the game type filter component.
    
    Args:
        app (dash.Dash): The Dash application
        data_service (DataService): The data service for retrieving game data
    """
    @app.callback(
        dash.dependencies.Output('game-type-filter-info', 'children'),
        [dash.dependencies.Input('game-type-filter-tabs', 'active_tab')]
    )
    def update_game_type_info(active_tab):
        """Update the info text based on the selected game type."""
        if active_tab == "all":
            return "Showing statistics for all game types combined."
        elif active_tab in get_all_game_types():
            game_type_name = get_game_type_name(active_tab)
            return f"Showing statistics for {game_type_name} games only."
        else:
            return ""
    
    @app.callback(
        dash.dependencies.Output('game-type-session-store', 'data'),
        [dash.dependencies.Input('game-type-filter-tabs', 'active_tab')],
        prevent_initial_call=True
    )
    def update_game_type_session(active_tab):
        """Update the game type selection in the session."""
        # Set the game type in the session
        if active_tab == "all":
            data_service._set_game_type_in_session(None)
        else:
            data_service._set_game_type_in_session(active_tab)
        
        return active_tab

def create_game_type_session_store():
    """
    Create a hidden div to store game type selection in the session.
    
    Returns:
        dash.dcc.Store: The session store component
    """
    return dcc.Store(id='game-type-session-store', storage_type='session')
