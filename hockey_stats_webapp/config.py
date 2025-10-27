"""Global configuration settings for the hockey stats webapp."""

# List of stats that are only visible to coaches
COACHES_ONLY_STATS = [
    'plus_minus',       # Player plus/minus rating
    'penalty_minutes',  # Player penalty minutes
    'PIM',              # Penalty minutes (abbreviation used in some views)
    'your_team_pim',    # Team penalty minutes in game summary
    'opponent_pim'      # Opponent penalty minutes in game summary
]

# Game type constants
GAME_TYPES = {
    'E': {
        'name': 'Exhibition',
        'color': '#FF9800',  # Orange
        'badge_class': 'warning'
    },
    'R': {
        'name': 'Regular Season',
        'color': '#2196F3',  # Blue
        'badge_class': 'primary'
    },
    'T': {
        'name': 'Tournament',
        'color': '#9C27B0',  # Purple
        'badge_class': 'secondary'
    }
}

# Default game type
DEFAULT_GAME_TYPE = 'E'

def is_coaches_only_stat(stat_name):
    """
    Check if a statistic is only visible to coaches.
    
    Args:
        stat_name (str): The name of the statistic
        
    Returns:
        bool: True if the stat is coaches-only, False otherwise
    """
    return stat_name in COACHES_ONLY_STATS

def get_game_type_name(game_type_code):
    """
    Get the display name for a game type code.
    
    Args:
        game_type_code (str): The game type code (E, R, T)
        
    Returns:
        str: The display name for the game type
    """
    if not game_type_code or game_type_code not in GAME_TYPES:
        game_type_code = DEFAULT_GAME_TYPE
    return GAME_TYPES[game_type_code]['name']

def get_game_type_color(game_type_code):
    """
    Get the color for a game type code.
    
    Args:
        game_type_code (str): The game type code (E, R, T)
        
    Returns:
        str: The hex color code for the game type
    """
    if not game_type_code or game_type_code not in GAME_TYPES:
        game_type_code = DEFAULT_GAME_TYPE
    return GAME_TYPES[game_type_code]['color']

def get_game_type_badge_class(game_type_code):
    """
    Get the Bootstrap badge class for a game type code.
    
    Args:
        game_type_code (str): The game type code (E, R, T)
        
    Returns:
        str: The Bootstrap badge class for the game type
    """
    if not game_type_code or game_type_code not in GAME_TYPES:
        game_type_code = DEFAULT_GAME_TYPE
    return GAME_TYPES[game_type_code]['badge_class']

def get_all_game_types():
    """
    Get all available game types.
    
    Returns:
        dict: Dictionary of all game types with their properties
    """
    return GAME_TYPES.copy()

def is_valid_game_type(game_type_code):
    """
    Check if a game type code is valid.
    
    Args:
        game_type_code (str): The game type code to validate
        
    Returns:
        bool: True if the game type code is valid, False otherwise
    """
    return game_type_code in GAME_TYPES

# Team identifier mappings for events data
TEAM_IDENTIFIER_MAPPINGS = {
    # Known team identifiers and their canonical forms
    'starsu11a': 'starsu11a',
    'waxersu12select': 'waxersu12select', 
    'test_team': 'test_team',
    
    # Special handling for generic identifier
    'your_team': 'auto_detect',  # Will auto-detect from events
}

# Primary team identifier (used as fallback)
PRIMARY_TEAM_IDENTIFIER = 'starsu11a'

def get_team_identifier_mapping(team_id):
    """
    Get the mapped team identifier for events data.
    
    Args:
        team_id (str): The team identifier to map
        
    Returns:
        str: The mapped team identifier, or None if auto-detect needed
    """
    return TEAM_IDENTIFIER_MAPPINGS.get(team_id)

def get_primary_team_identifier():
    """
    Get the primary team identifier used as fallback.
    
    Returns:
        str: The primary team identifier
    """
    return PRIMARY_TEAM_IDENTIFIER
