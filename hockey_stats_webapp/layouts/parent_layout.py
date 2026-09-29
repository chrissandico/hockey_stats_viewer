import logging
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from utils import format_player_label
import config

logger = logging.getLogger(__name__)


def create_parent_layout(data_service, team_context=None):
    """
    Create a single-page parent view with high-level team summary stats at the top
    and the specific child's individual stats and game log at the bottom.

    Args:
        data_service (DataService): The data service for retrieving player and team data
        team_context (dict, optional): Context with team_id, team_name, jersey_number, player_id, child_name

    Returns:
        dash.html.Div: The parent layout
    """
    tc = team_context or {}
    team_id = tc.get('team_id')
    team_name = tc.get('team_name', 'Your Team')
    jersey_number_str = str(tc.get('jersey_number', '')).strip()
    player_id_ctx = str(tc.get('player_id', '')).strip()
    child_name_ctx = str(tc.get('child_name', '')).strip()

    if not data_service or not team_id:
        return dbc.Container([
            dbc.Alert([
                html.H5("Service Unavailable", className="alert-heading"),
                html.P("Statistics are currently unavailable."),
            ], color="warning", className="mt-4")
        ], fluid=True)

    # ---------------------------------------------------------------------------
    # 1. TOP SECTION: High-Level Team Summary
    # ---------------------------------------------------------------------------
    team_summary_content = _build_team_summary_section(data_service, team_id)

    # ---------------------------------------------------------------------------
    # 2. BOTTOM SECTION: Child's Individual Stats & Game Log
    # ---------------------------------------------------------------------------
    child_section_content = _build_child_section(
        data_service, team_id, jersey_number_str, player_id_ctx, child_name_ctx
    )

    return html.Div([
        dbc.Container([
            # Team Title Header
            html.Div([
                html.H1(f"{team_name}", className="display-6 fw-bold mb-1"),
                html.P("Parent Portal & Player Analytics", className="text-muted mb-3"),
            ], className="text-center pt-4 pb-2"),

            # High-level Team Stats Card
            team_summary_content,

            html.Hr(className="my-4"),

            # Child's Individual Section
            child_section_content,

            html.Div(className="py-3")
        ], fluid=True)
    ])


def _build_team_summary_section(data_service, team_id):
    """Build the high-level team stats summary section."""
    try:
        t_stats = data_service.calculate_team_stats(team_id)
    except Exception as e:
        logger.error(f"Parent Layout: Error calculating team stats: {e}")
        t_stats = None

    if not t_stats:
        return dbc.Alert("Team statistics could not be calculated.", color="warning")

    gp = t_stats.get('games_played', 0)
    record = t_stats.get('record', {})
    if isinstance(record, dict):
        wins = record.get('wins', 0)
        losses = record.get('losses', 0)
        ties = record.get('ties', 0)
        win_pct = record.get('win_pct', 0.0)
    else:
        wins = t_stats.get('wins', 0)
        losses = t_stats.get('losses', 0)
        ties = t_stats.get('ties', 0)
        win_pct = t_stats.get('win_percentage', 0.0)

    gf = t_stats.get('goals_for', 0)
    ga = t_stats.get('goals_against', 0)
    diff = t_stats.get('goal_differential', gf - ga)
    diff_str = f"+{diff}" if diff > 0 else str(diff)

    # Special teams
    st_summary = ""
    try:
        st = data_service.calculate_special_teams_stats(team_id)
        if st:
            pp = st.get('pp_percentage', 0.0)
            pk = st.get('pk_percentage', 0.0)
            st_summary = f" | PP: {pp:.1f}% | PK: {pk:.1f}%"
    except Exception:
        pass

    team_kpi_cards = [
        dbc.Col([
            html.Div([
                html.Div(f"{wins}-{losses}-{ties}", className="kpi-value text-primary"),
                html.Div("RECORD (W-L-T)", className="kpi-label"),
            ], className="kpi-tile text-center")
        ], xs=6, sm=4, md=2),
        dbc.Col([
            html.Div([
                html.Div(f"{win_pct:.1f}%", className="kpi-value"),
                html.Div("WIN %", className="kpi-label"),
            ], className="kpi-tile text-center")
        ], xs=6, sm=4, md=2),
        dbc.Col([
            html.Div([
                html.Div(str(gp), className="kpi-value"),
                html.Div("GAMES PLAYED", className="kpi-label"),
            ], className="kpi-tile text-center")
        ], xs=6, sm=4, md=2),
        dbc.Col([
            html.Div([
                html.Div(f"{gf} / {ga}", className="kpi-value"),
                html.Div("GOALS (FOR / AGST)", className="kpi-label"),
            ], className="kpi-tile text-center")
        ], xs=6, sm=4, md=3),
        dbc.Col([
            html.Div([
                html.Div(diff_str, className="kpi-value text-success" if diff > 0 else "kpi-value"),
                html.Div("GOAL DIFFERENTIAL", className="kpi-label"),
            ], className="kpi-tile text-center")
        ], xs=6, sm=4, md=3),
    ]

    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="fas fa-users-cog me-2 text-primary"),
                "Team Overview"
            ], className="card-title mb-0")
        ]),
        dbc.CardBody([
            dbc.Row(team_kpi_cards, className="g-3 mb-2"),
            if_st_text := (html.P(f"Special Teams{st_summary}", className="text-muted small text-center mb-0") if st_summary else None)
        ]),
    ], className="shadow-sm mb-4 border-0")


def _build_child_section(data_service, team_id, jersey_number_str, player_id_ctx, child_name_ctx):
    """Build the child player individual stats & game log section."""
    players_df = data_service.get_players(team_id)
    if players_df is None or players_df.empty:
        return dbc.Alert("No player data found for this team.", color="warning")

    target_player = None

    # Match by PlayerID if provided
    if player_id_ctx:
        for _, r in players_df.iterrows():
            pid = data_service._get_player_id_from_series(r)
            if pid and str(pid).strip().lower() == player_id_ctx.lower():
                target_player = r
                break

    # Match by JerseyNumber if not found by PlayerID
    if target_player is None and jersey_number_str:
        try:
            j_num = int(jersey_number_str)
            m = players_df[players_df['JerseyNumber'] == j_num]
            if not m.empty:
                target_player = m.iloc[0]
        except (ValueError, TypeError):
            m = players_df[players_df['JerseyNumber'].astype(str).str.strip() == jersey_number_str]
            if not m.empty:
                target_player = m.iloc[0]

    # Fallback: check if child_name matches
    if target_player is None and child_name_ctx:
        for _, r in players_df.iterrows():
            lbl = format_player_label(r)
            if child_name_ctx.lower() in lbl.lower():
                target_player = r
                break

    if target_player is None:
        return dbc.Alert(
            f"Child player profile (Jersey #{jersey_number_str or player_id_ctx}) was not found in the team roster.",
            color="danger"
        )

    player_id = data_service._get_player_id_from_series(target_player)
    position = str(target_player.get('Position', 'F') or 'F').upper()
    is_goalie = position == 'G'
    display_name = format_player_label(target_player)

    # Calculate stats
    try:
        if is_goalie:
            stats = data_service.calculate_goalie_stats(player_id, team_id)
        else:
            stats = data_service.calculate_player_stats(player_id, team_id)
    except Exception as e:
        logger.error(f"Parent Layout: Error calculating stats for player {player_id}: {e}")
        stats = None

    if not stats:
        return dbc.Alert("Could not calculate individual player statistics.", color="warning")

    # KPI Tiles
    if is_goalie:
        sv_pct = stats.get('save_percentage', 0.0)
        gaa = stats.get('gaa', 0.0)
        kpi_tiles = [
            html.Div([
                html.Div(str(stats.get('wins', 0)), className="kpi-value text-success"),
                html.Div("WINS", className="kpi-label"),
            ], className="kpi-tile"),
            html.Div([
                html.Div(str(stats.get('shutouts', 0)), className="kpi-value"),
                html.Div("SHUTOUTS", className="kpi-label"),
            ], className="kpi-tile"),
            html.Div([
                html.Div(f"{sv_pct:.3f}", className="kpi-value text-primary"),
                html.Div("SAVE % (SV%)", className="kpi-label"),
            ], className="kpi-tile"),
            html.Div([
                html.Div(f"{gaa:.2f}", className="kpi-value"),
                html.Div("GAA", className="kpi-label"),
            ], className="kpi-tile"),
        ]
    else:
        kpi_tiles = [
            html.Div([
                html.Div(str(stats.get('goals', 0)), className="kpi-value text-success"),
                html.Div("GOALS", className="kpi-label"),
            ], className="kpi-tile"),
            html.Div([
                html.Div(str(stats.get('assists', 0)), className="kpi-value text-primary"),
                html.Div("ASSISTS", className="kpi-label"),
            ], className="kpi-tile"),
            html.Div([
                html.Div(str(stats.get('points', 0)), className="kpi-value text-warning"),
                html.Div("POINTS", className="kpi-label"),
            ], className="kpi-tile"),
            html.Div([
                html.Div(str(stats.get('shots', 0)), className="kpi-value"),
                html.Div("SHOTS", className="kpi-label"),
            ], className="kpi-tile"),
        ]
        if not config.is_coaches_only_stat('plus_minus'):
            kpi_tiles.append(html.Div([
                html.Div(str(stats.get('plus_minus', 0)), className="kpi-value"),
                html.Div("+/-", className="kpi-label"),
            ], className="kpi-tile"))

    player_card = dbc.Card([
        dbc.CardHeader([
            html.H3([
                html.I(className="fas fa-user-circle me-2 text-primary"),
                f"{display_name}"
            ], className="card-title mb-0 d-inline-block"),
            dbc.Badge(f"Position: {position}", color="secondary", className="float-end fs-6 mt-1")
        ]),
        dbc.CardBody([
            html.Div(kpi_tiles, className="d-flex flex-wrap gap-3 my-2"),
        ]),
    ], className="shadow-sm mb-4 border-0")

    # Game Log
    game_log_data = data_service.get_player_game_log(player_id, team_id)
    game_log_card = _build_game_log_card(game_log_data, is_goalie)

    return html.Div([
        player_card,
        game_log_card
    ])


def _build_game_log_card(game_log, is_goalie):
    """Build game log table and chart for skater or goalie."""
    if not game_log:
        return dbc.Card([
            dbc.CardHeader(html.H4("Game Log", className="card-title mb-0")),
            dbc.CardBody(html.P("No game log records available.", className="text-muted text-center py-3")),
        ], className="shadow-sm border-0")

    table_rows = []
    for g in game_log:
        game_info = g.get('game', {})
        if is_goalie:
            table_rows.append({
                'Date': game_info.get('Date', ''),
                'Game Type': config.get_game_type_name(game_info.get('GameType', 'R')),
                'Opponent': game_info.get('Opponent', ''),
                'Result': g.get('result', ''),
                'SA': g.get('shots_against', 0),
                'SV': g.get('saves', 0),
                'GA': g.get('goals_against', 0),
                'SV%': f"{g.get('save_percentage', 0.0):.3f}",
                'SO': 'Yes' if g.get('shutout', False) else 'No',
            })
        else:
            entry = {
                'Date': game_info.get('Date', ''),
                'Game Type': config.get_game_type_name(game_info.get('GameType', 'R')),
                'Opponent': game_info.get('Opponent', ''),
                'Result': game_info.get('Result', ''),
                'Goals': g.get('goals', 0),
                'Assists': g.get('assists', 0),
                'Points': g.get('points', 0),
            }
            if not config.is_coaches_only_stat('plus_minus'):
                entry['+/-'] = g.get('plus_minus', 0)
            if not config.is_coaches_only_stat('PIM'):
                entry['PIM'] = g.get('penalty_minutes', 0)
            table_rows.append(entry)

    df_log = pd.DataFrame(table_rows)
    dates = [r['Date'] for r in table_rows]

    # Chart
    if is_goalie:
        sv_pcts = [float(r['SV%']) for r in table_rows]
        fig = go.Figure(go.Scatter(
            x=dates, y=sv_pcts,
            mode='lines+markers',
            line=dict(color='#0042bb', width=2),
            marker=dict(size=8)
        ))
        fig.update_layout(
            title="Save Percentage Trend",
            height=220,
            margin=dict(l=40, r=20, t=40, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white',
            yaxis=dict(tickformat='.3f'),
        )
    else:
        goals = [r['Goals'] for r in table_rows]
        assists = [r['Assists'] for r in table_rows]
        points = [r['Points'] for r in table_rows]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dates, y=goals, name='Goals', marker_color='#00843d'))
        fig.add_trace(go.Bar(x=dates, y=assists, name='Assists', marker_color='#0042bb'))
        fig.add_trace(go.Bar(x=dates, y=points, name='Points', marker_color='#eca200'))
        fig.update_layout(
            barmode='group',
            height=220,
            margin=dict(l=40, r=20, t=20, b=40),
            legend=dict(orientation='h', y=-0.3),
            plot_bgcolor='white',
            paper_bgcolor='white',
        )

    # Columns
    if is_goalie:
        cols = [
            {'name': 'Date', 'id': 'Date'},
            {'name': 'Game Type', 'id': 'Game Type'},
            {'name': 'Opponent', 'id': 'Opponent'},
            {'name': 'Result', 'id': 'Result'},
            {'name': 'Shots Against', 'id': 'SA'},
            {'name': 'Saves', 'id': 'SV'},
            {'name': 'Goals Against', 'id': 'GA'},
            {'name': 'Save %', 'id': 'SV%'},
            {'name': 'Shutout', 'id': 'SO'},
        ]
    else:
        cols = [
            {'name': 'Date', 'id': 'Date'},
            {'name': 'Game Type', 'id': 'Game Type'},
            {'name': 'Opponent', 'id': 'Opponent'},
            {'name': 'Result', 'id': 'Result'},
            {'name': 'Goals', 'id': 'Goals'},
            {'name': 'Assists', 'id': 'Assists'},
            {'name': 'Points', 'id': 'Points'},
        ]
        if not config.is_coaches_only_stat('plus_minus'):
            cols.append({'name': '+/-', 'id': '+/-'})
        if not config.is_coaches_only_stat('PIM'):
            cols.append({'name': 'PIM', 'id': 'PIM'})

    log_table = dash_table.DataTable(
        data=df_log.to_dict('records'),
        columns=cols,
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'color': '#212529',
            'borderBottom': '2px solid #dee2e6'
        },
        style_cell={
            'textAlign': 'center',
            'padding': '10px 12px',
            'fontFamily': 'Inter, sans-serif',
            'fontSize': '14px'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#fcfcfc'}
        ]
    )

    return dbc.Card([
        dbc.CardHeader(html.H4("Individual Game Log", className="card-title mb-0")),
        dbc.CardBody([
            dcc.Graph(figure=fig, config={'displayModeBar': False}, className="mb-4"),
            log_table
        ])
    ], className="shadow-sm border-0")
