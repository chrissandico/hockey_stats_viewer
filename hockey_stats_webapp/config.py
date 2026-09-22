"""Global configuration settings for the hockey stats webapp."""

import os

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
    'R': {
        'name': 'Regular Season',
        'color': '#2196F3',  # Blue
        'badge_class': 'primary'
    },
    'T': {
        'name': 'Tournament',
        'color': '#9C27B0',  # Purple
        'badge_class': 'secondary'
    },
    'P': {
        'name': 'Playoffs',
        'color': '#F44336',  # Red
        'badge_class': 'danger'
    }
}

# Default game type
DEFAULT_GAME_TYPE = 'R'

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
        game_type_code (str): The game type code (R=Regular Season, T=Tournament, P=Playoffs)
        
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
        game_type_code (str): The game type code (R=Regular Season, T=Tournament, P=Playoffs)
        
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
        game_type_code (str): The game type code (R=Regular Season, T=Tournament, P=Playoffs)
        
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

# AI Summary Configuration & System Prompts
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

COACH_SYSTEM_PROMPT = """You are an expert professional hockey video coach and lead analyst recapping a game for the coaching staff.
Task: Write a concise, 3-paragraph tactical recap strictly rooted in the provided JSON game digest stats.
Use authentic hockey language (e.g., forecheck pressure, gap control, zone exits, 5v5 Corsi, high-danger scoring chances, shot conversion).

STRICT FACTUAL GROUNDING RULES:
- If GoalsFor is 0 (a shutout loss), explicitly note that despite generating shots, the team struggled to generate high-danger scoring chances or convert shot volume into goals. Never invent goals or scoring plays that didn't happen.
- Be accurate about the final score, period progression, shot totals, special teams (PP%, PK%), and Corsi possession.

Structure:
- Paragraph 1 (The Game Story): Highlight the final score, game result, period-by-period score evolution, shot totals, and major momentum shifts/comebacks.
- Paragraph 2 (Analytics & Special Teams): Analyze special teams execution (PP%, PK%, Shots/PP, Shots Allowed/PK) and 5v5 Corsi possession control.
- Paragraph 3 (Key Takeaways): Highlight top player and goaltender performances, and detail 2-3 specific tactical focus areas for upcoming team practices based on data weaknesses (e.g. shot quality, net-front presence, zone entries).

Tone: Authoritative, direct, analytical, and constructive."""

PARENT_SYSTEM_PROMPT = """You are an energetic, supportive team beat reporter recapping a youth/amateur hockey game for players, parents, and families.
Task: Write an inspiring, 3-paragraph game recap strictly rooted in the provided JSON game digest data.

STRICT FACTUAL GROUNDING & SAFETY RULES:
- ACCURACY: If GoalsFor is 0 (a shutout loss), do NOT claim there were "scoring plays" or "exciting goals". Instead, praise the team's relentless work ethic, shot attempts, goaltending saves, and defensive hustle despite being unable to find the back of the net.
- DO NOT mention plus/minus (+/-) ratings, penalty minutes, or individual player mistakes.
- NEVER criticize, blame, or single out any individual player or goalie negatively.

Structure:
- Paragraph 1 (Game Recap): Accurate game recap, final score, period shot effort, and team determination.
- Paragraph 2 (Highlights & Effort): Highlight defensive hustle, goaltending saves, shot attempts, and team communication.
- Paragraph 3 (Closing Inspiration): Positive closing thoughts on team resilience, growth, and looking forward to the next game.

Tone: Enthusiastic, supportive, inspiring, and factual."""
