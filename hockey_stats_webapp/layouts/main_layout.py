from dash import html, dcc, Output, Input, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from flask import session as flask_session
from utils import format_player_label, resolve_game_type
import config


def create_main_layout(team_context=None):
    """
    Create the dashboard home layout with game type filtering (defaults to Regular Season).
    Includes Forwards, Defense, and Goalie leaderboards directly on the main screen.
    """
    team_name = (team_context or {}).get('team_name', 'Your Team')
    return html.Div([
        dcc.Store(id='dashboard-trigger', data=True),
        dbc.Container([
            html.Div([
                html.H1(team_name, className="display-5 fw-bold mb-1"),
                html.P("Season Dashboard & Analytics", className="text-muted mb-3"),
            ], className="text-center pt-4 pb-2"),

            dcc.Loading(html.Div([
                html.Div(id='dashboard-kpi-row', className="mb-4"),
                html.Div(id='dashboard-form-row', className="text-center mb-4"),
                dbc.Row([
                    dbc.Col(html.Div(id='dashboard-last-game'), md=6, xs=12),
                    dbc.Col(html.Div(id='dashboard-top-performers'), md=6, xs=12),
                ], className="mb-4"),
                html.Div(id='dashboard-chart', style={'display': 'none'}),

                # Position Leaderboards section
                html.Div([
                    html.H3("Team Leaderboards", className="fw-bold mb-3"),
                    dbc.Tabs([
                        dbc.Tab(label="All", tab_id="all",
                                label_style={"fontWeight": "600", "fontSize": "15px"},
                                active_label_style={"fontWeight": "700", "fontSize": "15px", "color": "#0042bb"}),
                        dbc.Tab(label="Forwards", tab_id="forwards",
                                label_style={"fontWeight": "600", "fontSize": "15px"},
                                active_label_style={"fontWeight": "700", "fontSize": "15px", "color": "#0042bb"}),
                        dbc.Tab(label="Defense",  tab_id="defense",
                                label_style={"fontWeight": "600", "fontSize": "15px"},
                                active_label_style={"fontWeight": "700", "fontSize": "15px", "color": "#0042bb"}),
                        dbc.Tab(label="Goalies",  tab_id="goalies",
                                label_style={"fontWeight": "600", "fontSize": "15px"},
                                active_label_style={"fontWeight": "700", "fontSize": "15px", "color": "#0042bb"}),
                    ], id='dashboard-position-tabs', active_tab="all", className="mb-3 border-bottom border-2"),
                    html.Div(id='dashboard-leaderboards-container', className="mb-4"),
                ]),
            ])),

            dbc.Row([
                _quick_card("Players", "Individual stats and game logs", "/player"),
                _quick_card("Game Log", "Results, period breakdowns, shots", "/game"),
                _quick_card("vs. Opponents Performance", "Head-to-head records by opponent", "/opponent"),
            ], className="mb-4"),
        ], fluid=True),
    ])


def _top_performer_item(label, entries, stat_key, signed=False, is_pct=False):
    if not entries:
        return None
    if not isinstance(entries, list):
        entries = [entries]

    player_lis = []
    for entry in entries:
        name = format_player_label(entry['player'])
        value = entry.get(stat_key, 0)
        if is_pct:
            val_str = f"{value:.1f}%"
        elif signed:
            val_str = f"+{value}" if value >= 0 else str(value)
        else:
            val_str = str(value)
        player_lis.append(html.Li(f"{name} ({val_str})"))

    return dbc.ListGroupItem([
        html.Div(html.Strong(f"{label}:"), className="fw-bold mb-1"),
        html.Ol(player_lis, className="mb-0 ps-3 small text-muted")
    ])


def _quick_card(title, desc, href):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.H5(title, className="fw-bold"),
        html.P(desc, className="text-muted small"),
        dbc.Button(f"View {title}", href=href, color="primary", className="mt-2"),
    ])), md=4, className="mb-3")


def register_dashboard_callbacks(app, data_service):
    """
    Populates the dashboard sections when the page loads, game type filter changes,
    or position tabs are selected.
    """

    @app.callback(
        Output('dashboard-kpi-row', 'children'),
        Output('dashboard-form-row', 'children'),
        Output('dashboard-last-game', 'children'),
        Output('dashboard-top-performers', 'children'),
        Output('dashboard-chart', 'children'),
        Output('dashboard-leaderboards-container', 'children'),
        [Input('dashboard-trigger', 'data'),
         Input('dashboard-position-tabs', 'active_tab'),
         Input('global-refresh-btn', 'n_clicks')]
    )
    def populate_dashboard(_trigger, active_tab, refresh_clicks):
        team_id = flask_session.get('team_id')
        if not team_id or not data_service:
            return [html.Div()] * 6

        triggered_id = None
        if callback_context.triggered:
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]

        force_summary_refresh = False
        if triggered_id == 'global-refresh-btn':
            data_service.force_refresh_all_data()
            force_summary_refresh = True

        if not active_tab:
            active_tab = "all"

        # Show all games (Regular Season, Tournament, Playoffs)
        game_type = None

        is_coach = flask_session.get('is_coach', False)

        # ── KPI tiles ─────────────────────────────────────────────────────────
        try:
            stats = data_service.calculate_team_stats(team_id, game_type=game_type)
            win_pct = f"{stats['win_percentage']:.0%}"

            # Calculate sub-breakdowns by game type (R = Regular, T = Tournament, P = Playoffs)
            r_stats = data_service.calculate_team_stats(team_id, game_type='R')
            t_stats = data_service.calculate_team_stats(team_id, game_type='T')
            p_stats = data_service.calculate_team_stats(team_id, game_type='P')

            r_win_pct = f"{r_stats['win_percentage']:.0%}" if r_stats['games_played'] > 0 else "N/A"
            t_win_pct = f"{t_stats['win_percentage']:.0%}" if t_stats['games_played'] > 0 else "N/A"
            p_win_pct = f"{p_stats['win_percentage']:.0%}" if p_stats['games_played'] > 0 else "N/A"

            wins_sub = f"R: {r_stats['wins']} · T: {t_stats['wins']} · P: {p_stats['wins']}"
            losses_sub = f"R: {r_stats['losses']} · T: {t_stats['losses']} · P: {p_stats['losses']}"
            ties_sub = f"R: {r_stats['ties']} · T: {t_stats['ties']} · P: {p_stats['ties']}"
            win_pct_sub = f"R: {r_win_pct} · T: {t_win_pct} · P: {p_win_pct}"
            gf_sub = f"R: {r_stats['goals_for']} · T: {t_stats['goals_for']} · P: {p_stats['goals_for']}"
            ga_sub = f"R: {r_stats['goals_against']} · T: {t_stats['goals_against']} · P: {p_stats['goals_against']}"

            sub_style = {"fontSize": "0.75rem", "color": "#6c757d", "marginTop": "2px"}

            kpi_row = dbc.Row([
                dbc.Col(html.Div([
                    html.Div(str(stats['wins']), className="kpi-value"),
                    html.Div("Wins", className="kpi-label"),
                    html.Div(wins_sub, style=sub_style),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(str(stats['losses']), className="kpi-value"),
                    html.Div("Losses", className="kpi-label"),
                    html.Div(losses_sub, style=sub_style),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(str(stats['ties']), className="kpi-value"),
                    html.Div("Ties", className="kpi-label"),
                    html.Div(ties_sub, style=sub_style),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(win_pct, className="kpi-value"),
                    html.Div("Win %", className="kpi-label"),
                    html.Div(win_pct_sub, style=sub_style),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(str(stats['goals_for']), className="kpi-value"),
                    html.Div("Goals For", className="kpi-label"),
                    html.Div(gf_sub, style=sub_style),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(str(stats['goals_against']), className="kpi-value"),
                    html.Div("Goals Against", className="kpi-label"),
                    html.Div(ga_sub, style=sub_style),
                ], className="kpi-tile"), xs=6, md=2),
            ], className="g-2 justify-content-center")

            if is_coach:
                try:
                    st_stats = data_service.calculate_special_teams_stats(team_id, game_type=game_type)
                    pp_opps = st_stats.get('pp_opportunities', 0)
                    pk_opps = st_stats.get('pk_opportunities', 0)

                    pp_pct = f"{st_stats.get('pp_percentage', 0.0):.1f}%" if pp_opps > 0 else "N/A"
                    pk_pct = f"{st_stats.get('pk_percentage', 0.0):.1f}%" if pk_opps > 0 else "N/A"

                    if pp_opps > 0 and pk_opps > 0:
                        st_index_display = f"{st_stats.get('combined_st_index', 100.0):.1f}%"
                    elif pp_opps > 0:
                        st_index_display = f"{st_stats.get('pp_percentage', 0.0):.1f}% (PP)"
                    elif pk_opps > 0:
                        st_index_display = f"{st_stats.get('pk_percentage', 0.0):.1f}% (PK)"
                    else:
                        st_index_display = "N/A"

                    # Special teams sub-breakdowns
                    r_st = data_service.calculate_special_teams_stats(team_id, game_type='R')
                    t_st = data_service.calculate_special_teams_stats(team_id, game_type='T')
                    p_st = data_service.calculate_special_teams_stats(team_id, game_type='P')

                    r_pp = f"{r_st.get('pp_percentage', 0.0):.1f}%" if r_st.get('pp_opportunities', 0) > 0 else "N/A"
                    t_pp = f"{t_st.get('pp_percentage', 0.0):.1f}%" if t_st.get('pp_opportunities', 0) > 0 else "N/A"
                    p_pp = f"{p_st.get('pp_percentage', 0.0):.1f}%" if p_st.get('pp_opportunities', 0) > 0 else "N/A"

                    r_pk = f"{r_st.get('pk_percentage', 0.0):.1f}%" if r_st.get('pk_opportunities', 0) > 0 else "N/A"
                    t_pk = f"{t_st.get('pk_percentage', 0.0):.1f}%" if t_st.get('pk_opportunities', 0) > 0 else "N/A"
                    p_pk = f"{p_st.get('pk_percentage', 0.0):.1f}%" if p_st.get('pk_opportunities', 0) > 0 else "N/A"

                    def format_st_index(st):
                        if st.get('pp_opportunities', 0) > 0 or st.get('pk_opportunities', 0) > 0:
                            return f"{st.get('combined_st_index', 0.0):.1f}%"
                        return "N/A"

                    st_index_sub = f"R: {format_st_index(r_st)} · T: {format_st_index(t_st)} · P: {format_st_index(p_st)}"
                    pp_sub = f"R: {r_pp} · T: {t_pp} · P: {p_pp}"
                    pk_sub = f"R: {r_pk} · T: {t_pk} · P: {p_pk}"

                    st_kpi = dbc.Row([
                        dbc.Col(html.Div([
                            html.Div(st_index_display, className="kpi-value text-primary"),
                            html.Div("ST Index (PP% + PK%)", className="kpi-label"),
                            html.Div(st_index_sub, style=sub_style),
                        ], className="kpi-tile border-primary"), xs=12, md=4),
                        dbc.Col(html.Div([
                            html.Div(pp_pct, className="kpi-value text-success"),
                            html.Div(f"Power Play (PP%) {f'({st_stats.get(\"pp_goals\", 0)}/{pp_opps} PPG)' if pp_opps > 0 else ''}", className="kpi-label"),
                            html.Div(pp_sub, style=sub_style),
                        ], className="kpi-tile"), xs=6, md=4),
                        dbc.Col(html.Div([
                            html.Div(pk_pct, className="kpi-value text-danger"),
                            html.Div(f"Penalty Kill (PK%) {f'({st_stats.get(\"pk_successes\", 0)}/{pk_opps} Kills)' if pk_opps > 0 else ''}", className="kpi-label"),
                            html.Div(pk_sub, style=sub_style),
                        ], className="kpi-tile"), xs=6, md=4),
                    ], className="g-2 justify-content-center mt-2")

                    kpi_row = html.Div([kpi_row, st_kpi])
                except Exception:
                    pass
        except Exception:
            kpi_row = html.Div()

        # ── Fetch games once; filter to completed games for Last Game & Form ─
        games_df = None
        completed_games = None
        try:
            games_df = data_service.get_games(team_id, game_type=game_type)
            if games_df is not None and not games_df.empty:
                completed_games = data_service._filter_games_by_date(games_df, include_future=False)
                if completed_games is not None and not completed_games.empty and 'Date' in completed_games.columns:
                    completed_games = completed_games.sort_values('Date', ascending=False).reset_index(drop=True)
        except Exception:
            pass

        # ── Recent form dots ──────────────────────────────────────────────────
        try:
            if completed_games is not None and not completed_games.empty:
                recent = completed_games.head(5)
                dots = []
                for _, row in recent.iterrows():
                    result = str(row.get('Result', '')).upper()
                    if 'W' in result:
                        css = 'form-dot-W'
                        letter = 'W'
                    elif 'L' in result:
                        css = 'form-dot-L'
                        letter = 'L'
                    else:
                        css = 'form-dot-T'
                        letter = 'T'
                    dots.append(html.Span(letter, className=f"form-dot {css} me-1"))
                form_row = html.Div([
                    html.Span("Recent form: ", className="text-muted me-2"),
                    *dots,
                ])
            else:
                form_row = html.Div()
        except Exception:
            form_row = html.Div()

        # ── Last game card with AI Summary ───────────────────────────────────
        try:
            if completed_games is not None and not completed_games.empty:
                last = completed_games.iloc[0]
                result = str(last.get('Result', '')).upper()
                if 'W' in result:
                    badge_color = 'success'
                    badge_text = 'W'
                elif 'L' in result:
                    badge_color = 'danger'
                    badge_text = 'L'
                else:
                    badge_color = 'secondary'
                    badge_text = 'T'

                mode = 'coach' if is_coach else 'parent'
                last_game_id = last.get('ID')

                from services.ai_summary_service import AISummaryService
                ai_summary_service = AISummaryService()
                ai_summary_text = ""
                try:
                    digest = data_service.get_game_summary_digest(last_game_id, team_id)
                    if digest:
                        ai_summary_text = ai_summary_service.generate_summary(digest, mode=mode, force_refresh=force_summary_refresh)
                except Exception:
                    pass

                summary_paragraphs = [html.P(p.strip(), className="small text-dark mb-2") for p in ai_summary_text.split('\n\n') if p.strip()]

                last_game = dbc.Card(dbc.CardBody([
                    html.Div([
                        html.H6("Last Game", className="text-muted mb-0 d-inline-block"),
                        dbc.Badge("AI Game Summary", color="primary" if is_coach else "success", className="float-end small")
                    ], className="d-flex justify-content-between align-items-center mb-2"),
                    html.H4(f"vs {last.get('Opponent', 'Unknown')}", className="mb-1"),
                    html.H3(
                        f"{last.get('GoalsFor', 0)} — {last.get('GoalsAgainst', 0)}",
                        className="fw-bold mb-2",
                    ),
                    html.Div([
                        dbc.Badge(badge_text, color=badge_color, className="me-2"),
                        html.Span(str(last.get('Date', '')), className="fw-semibold"),
                    ], className="mb-3 border-bottom pb-2"),
                    html.Div([
                        html.Div([
                            html.H6("🎙️ Game Analyst Recap", className="fw-bold text-primary mb-0 d-inline-block") if is_coach else html.H6("🎙️ Highlights & Recap", className="fw-bold text-success mb-0 d-inline-block"),
                        ], className="d-flex justify-content-between align-items-center mb-2"),
                        html.Div(summary_paragraphs if summary_paragraphs else "Summary unavailable.")
                    ], className="bg-light p-3 rounded border")
                ]), className="shadow-sm mb-3")
            else:
                last_game = dbc.Card(dbc.CardBody([
                    html.Div([
                        html.H6("Last Game", className="text-muted mb-0 d-inline-block"),
                        dbc.Badge("PRE-SEASON", color="secondary", className="float-end small")
                    ], className="d-flex justify-content-between align-items-center mb-2"),
                    html.H5("No Completed Regular Season Games", className="mb-1 text-muted"),
                    html.P("Game stats and AI summaries will be displayed here once the regular season begins.", className="small text-muted mb-0")
                ]), className="shadow-sm mb-3")
        except Exception:
            last_game = html.Div()

        # ── Top performers ────────────────────────────────────────────────────
        try:
            items = []
            leaderboard = data_service.get_team_leaderboard(
                stat='points',
                position=None,
                limit=None,
                team_id=team_id,
                game_type=game_type,
            )
            skaters = [p for p in leaderboard if p.get('player', {}).get('Position') != 'G']

            if skaters:
                top_goals = sorted(skaters, key=lambda p: (p.get('goals', 0), p.get('points', 0)), reverse=True)[:3]
                top_assists = sorted(skaters, key=lambda p: (p.get('assists', 0), p.get('points', 0)), reverse=True)[:3]
                top_points = sorted(skaters, key=lambda p: (p.get('points', 0), p.get('goals', 0)), reverse=True)[:3]

                if top_goals:
                    items.append(_top_performer_item('Goals', top_goals, 'goals'))
                if top_assists:
                    items.append(_top_performer_item('Assists', top_assists, 'assists'))
                if top_points:
                    items.append(_top_performer_item('Points', top_points, 'points'))

                if is_coach or not config.is_coaches_only_stat('plus_minus'):
                    defensemen = [p for p in skaters if p.get('player', {}).get('Position') == 'D']
                    if defensemen:
                        top_plus_minus = sorted(defensemen, key=lambda p: (p.get('plus_minus', 0), p.get('points', 0)), reverse=True)[:3]
                        if top_plus_minus:
                            items.append(_top_performer_item(
                                'Plus/Minus (D)', top_plus_minus, 'plus_minus', signed=True
                            ))
                if is_coach:
                    corsi_skaters = [p for p in skaters if p.get('on_ice_shot_share_pct', 0.0) > 0]
                    if corsi_skaters:
                        top_corsi = sorted(corsi_skaters, key=lambda p: p.get('on_ice_shot_share_pct', 0.0), reverse=True)[:3]
                        if top_corsi:
                            items.append(_top_performer_item(
                                'Shot Share Leaders (Corsi)', top_corsi, 'on_ice_shot_share_pct', is_pct=True
                            ))

            top_performers = dbc.Card(dbc.CardBody([
                html.H6("Top Performers (All-time)", className="text-muted mb-2"),
                dbc.ListGroup(items, flush=True),
            ])) if items else html.Div()
        except Exception:
            top_performers = html.Div()

        # ── Position Leaderboard ───────────────────────────────────────────────
        try:
            if active_tab == "goalies":
                goalies_leaders = data_service.get_team_leaderboard(
                    stat='save_percentage' if is_coach else 'jersey_number',
                    position='G',
                    team_id=team_id,
                    game_type=game_type
                )
                table_columns = [
                    {'name': 'Player', 'id': 'Player', 'type': 'text'},
                    {'name': 'GP', 'id': 'GP', 'type': 'numeric'},
                    {'name': 'W', 'id': 'W', 'type': 'numeric'},
                    {'name': 'L', 'id': 'L', 'type': 'numeric'},
                    {'name': 'SV%', 'id': 'SV%', 'type': 'numeric'},
                    {'name': 'GAA', 'id': 'GAA', 'type': 'numeric'},
                ]
                table_data = [{
                    'Player': format_player_label(stats['player']),
                    'GP': stats['games_played'],
                    'W': stats['wins'],
                    'L': stats['losses'],
                    'SV%': f"{stats['save_percentage']:.3f}",
                    'GAA': f"{stats['gaa']:.2f}",
                } for stats in goalies_leaders]
                tab_title_text = "Goalies"
            else:
                if active_tab == "all":
                    pos_code = 'all'
                    tab_title_text = "All Players"
                elif active_tab == "forwards":
                    pos_code = 'F'
                    tab_title_text = "Forwards"
                else:
                    pos_code = 'D'
                    tab_title_text = "Defense"

                if is_coach:
                    if active_tab == "defense":
                        stat_sort = 'plus_minus'
                    else:
                        stat_sort = 'points'
                else:
                    stat_sort = 'jersey_number'

                pos_leaders = data_service.get_team_leaderboard(
                    stat=stat_sort,
                    position=pos_code,
                    team_id=team_id,
                    game_type=game_type
                )
                table_columns = [
                    {'name': 'Player', 'id': 'Player', 'type': 'text'},
                    *([{'name': 'Pos', 'id': 'Position', 'type': 'text'}] if active_tab == "all" else []),
                    {'name': 'G', 'id': 'Goals', 'type': 'numeric'},
                    {'name': 'A', 'id': 'Assists', 'type': 'numeric'},
                    {'name': 'P', 'id': 'Points', 'type': 'numeric'},
                    *([
                        {'name': '+/-', 'id': 'PlusMinus', 'type': 'numeric'},
                        {'name': 'SF', 'id': 'SF', 'type': 'numeric'},
                        {'name': 'SA', 'id': 'SA', 'type': 'numeric'},
                        {'name': 'SF%', 'id': 'SFPct', 'type': 'numeric'}
                    ] if is_coach else [])
                ]
                table_data = [{
                    'Player': format_player_label(stats['player']),
                    **({'Position': stats['player'].get('Position', '')} if active_tab == "all" else {}),
                    'Goals': stats['goals'],
                    'Assists': stats['assists'],
                    'Points': stats['points'],
                    **({
                        'PlusMinus': stats['plus_minus'],
                        'SF': stats.get('on_ice_shots_for', 0),
                        'SA': stats.get('on_ice_shots_against', 0),
                        'SFPct': f"{stats.get('on_ice_shot_share_pct', 0.0):.1f}%"
                    } if is_coach else {})
                } for stats in pos_leaders]

            if not table_data:
                leaderboard_body = html.P(
                    f"No {tab_title_text.lower()} found.",
                    className="text-muted text-center py-3"
                )
            else:
                table_component = dash_table.DataTable(
                    id='dashboard-position-leaderboard-table',
                    columns=table_columns,
                    data=table_data,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'padding': '12px 8px',
                        'minWidth': '55px',
                        'fontSize': '14px',
                        'fontFamily': 'inherit',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': 'Player'}, 'textAlign': 'left', 'minWidth': '120px'},
                        {'if': {'column_id': 'Position'}, 'minWidth': '50px'},
                    ],
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'fontSize': '14px',
                        'height': '46px',
                        'cursor': 'pointer',
                        'userSelect': 'none',
                        'padding': '10px 6px',
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
                    ],
                    sort_action='native',
                    sort_mode='single',
                )

                # Add SF% explanation if coach mode is active and not on goalies tab
                sf_explanation = []
                if is_coach and active_tab != "goalies":
                    sf_explanation.append(
                        html.Div([
                            html.Div([
                                html.Span("📊 About SF% (Shot Share %): ", className="fw-bold text-dark"),
                                "Calculated as ",
                                html.Code("SF / (SF + SA) × 100%", className="bg-white text-dark px-2 py-0.5 rounded border border-1 fw-bold"),
                                "."
                            ], className="mb-1"),
                            html.Div([
                                "SF% measures the percentage of total on-ice shot attempts taken by your team vs. opponent while this player is on the ice. ",
                                html.Span("A value above 50% indicates your team controlled play and generated more shot opportunities than they allowed.", className="fw-semibold text-primary")
                            ], className="text-muted small")
                        ], className="mt-3 p-3 rounded bg-light border border-1")
                    )

                leaderboard_body = html.Div([
                    html.Div(
                        "💡 Tap column headers to sort table",
                        className="text-muted small text-end mb-2 fw-semibold",
                        style={'fontSize': '12px'}
                    ),
                    table_component,
                    *sf_explanation
                ])

            leaderboard_card = dbc.Card([
                dbc.CardHeader(html.H5(f"Roster Leaderboard — {tab_title_text}", className="card-title mb-0")),
                dbc.CardBody([leaderboard_body])
            ], className="mb-4 shadow-sm")

        except Exception as e:
            leaderboard_card = html.Div(f"Error loading leaderboards: {str(e)}", className="text-danger")

        season_chart = html.Div()

        return kpi_row, form_row, last_game, top_performers, season_chart, leaderboard_card
