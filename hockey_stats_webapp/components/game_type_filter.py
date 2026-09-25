import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from config import get_game_type_name, get_game_type_badge_class


def create_game_type_badge(game_type_code):
    """
    Create a colored badge for a game type.
    
    Args:
        game_type_code (str): The game type code (E, R, T, P)
        
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
    """No-op callback registration for backwards compatibility."""
    pass


def create_game_type_session_store():
    """No-op store for backwards compatibility."""
    return html.Div(style={'display': 'none'})
