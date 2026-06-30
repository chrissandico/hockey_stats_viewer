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
