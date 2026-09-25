def format_player_label(player):
    """Return 'PS #12' format. Accepts pd.Series or dict."""
    try:
        first = str(player.get('FirstName') or '').strip()
        last  = str(player.get('LastName')  or '').strip()
        jersey = player['JerseyNumber']
        if first and last:
            return f"{first[0]}{last[0]} #{jersey}"
    except (KeyError, TypeError):
        pass
    return f"#{player.get('JerseyNumber', '?')}"


def resolve_game_type(game_type_data):
    """
    Resolve game type code from session store or dropdown value.
    Returns:
        - 'R' for Regular Season (default if None/unrecognized)
        - 'T' for Tournament
        - 'P' for Playoffs
        - None for 'all' (All Games)
    """
    if game_type_data == 'all':
        return None
    if isinstance(game_type_data, str) and game_type_data in ['R', 'T', 'P']:
        return game_type_data
    if isinstance(game_type_data, dict):
        val = game_type_data.get('game_type')
        if val == 'all':
            return None
        if val in ['R', 'T', 'P']:
            return val
    return 'R'

