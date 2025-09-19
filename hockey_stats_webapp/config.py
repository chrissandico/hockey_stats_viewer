"""Global configuration settings for the hockey stats webapp."""

# List of stats that are only visible to coaches
COACHES_ONLY_STATS = [
    'plus_minus',       # Player plus/minus rating
    'penalty_minutes',  # Player penalty minutes
    'PIM',              # Penalty minutes (abbreviation used in some views)
    'your_team_pim',    # Team penalty minutes in game summary
    'opponent_pim'      # Opponent penalty minutes in game summary
]

def is_coaches_only_stat(stat_name):
    """
    Check if a statistic is only visible to coaches.
    
    Args:
        stat_name (str): The name of the statistic
        
    Returns:
        bool: True if the stat is coaches-only, False otherwise
    """
    return stat_name in COACHES_ONLY_STATS
