"""
Team layout - Deprecated.
Leaderboards have been migrated to main_layout.py (Dashboard).
"""

def create_team_layout(data_service, team_context=None):
    from layouts.main_layout import create_main_layout
    return create_main_layout(team_context)

def register_team_callbacks(app, data_service):
    pass
