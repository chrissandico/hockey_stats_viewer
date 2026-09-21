from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from flask import session as flask_session
from utils import format_player_label
import config


def create_main_layout(team_context=None):
    """
    Create the dashboard home layout.  A dcc.Store fires once on load and
    triggers register_dashboard_callbacks to populate all five sections.
    """
    team_name = (team_context or {}).get('team_name', 'Your Team')
    return html.Div([
        dcc.Store(id='dashboard-trigger', data=True),
        dbc.Container([
            html.Div([
                html.H1(team_name, className="display-5 fw-bold mb-1"),
                html.P("Season Statistics", className="text-muted mb-3"),
            ], className="text-center pt-4 pb-2"),
            dcc.Loading(html.Div([
                html.Div(id='dashboard-kpi-row', className="mb-4"),
                html.Div(id='dashboard-form-row', className="text-center mb-4"),
                dbc.Row([
                    dbc.Col(html.Div(id='dashboard-last-game'), md=6, xs=12),
                    dbc.Col(html.Div(id='dashboard-top-performers'), md=6, xs=12),
                ], className="mb-4"),
                html.Div(id='dashboard-chart', style={'display': 'none'}),
            ])),
            dbc.Row([
                _quick_card("Players",   "Individual stats and game logs",    "/player"),
                _quick_card("Games",     "Results, period breakdowns, shots", "/game"),
                _quick_card("Team",      "Leaderboards and season trends",    "/team"),
                _quick_card("Opponents", "Head-to-head records by opponent",  "/opponent"),
            ], className="mb-4"),
        ], fluid=True),
    ])


def _top_performer_item(label, entry, stat_key, signed=False):
    name = format_player_label(entry['player'])
    value = entry.get(stat_key, 0)
    if signed:
        value = f"+{value}" if value >= 0 else str(value)
    return dbc.ListGroupItem([html.Strong(f"{label}: "), f"{name}  ({value})"])


def _quick_card(title, desc, href):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.H5(title, className="fw-bold"),
        html.P(desc, className="text-muted small"),
        dbc.Button(f"View {title}", href=href, color="primary", className="mt-2"),
    ])), md=3, className="mb-3")


def register_dashboard_callbacks(app, data_service):
    """
    Single callback that populates the five dashboard sections when the page
    loads.  Each data call is wrapped in its own try/except so a failure in
    one section does not blank the others.
    """

    @app.callback(
        Output('dashboard-kpi-row', 'children'),
        Output('dashboard-form-row', 'children'),
        Output('dashboard-last-game', 'children'),
        Output('dashboard-top-performers', 'children'),
        Output('dashboard-chart', 'children'),
        Input('dashboard-trigger', 'data'),
    )
    def populate_dashboard(_trigger):
        team_id = flask_session.get('team_id')
        if not team_id or not data_service:
            return [html.Div()] * 5

        # ── KPI tiles ─────────────────────────────────────────────────────────
        try:
            stats = data_service.calculate_team_stats(team_id)
            win_pct = f"{stats['win_percentage']:.0%}"
            kpi_row = dbc.Row([
                dbc.Col(html.Div([
                    html.Div(str(stats['wins']),         className="kpi-value"),
                    html.Div("Wins",                     className="kpi-label"),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(str(stats['losses']),       className="kpi-value"),
                    html.Div("Losses",                   className="kpi-label"),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(str(stats['ties']),         className="kpi-value"),
                    html.Div("Ties",                     className="kpi-label"),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(win_pct,                    className="kpi-value"),
                    html.Div("Win %",                    className="kpi-label"),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(str(stats['goals_for']),    className="kpi-value"),
                    html.Div("Goals For",                className="kpi-label"),
                ], className="kpi-tile"), xs=6, md=2),
                dbc.Col(html.Div([
                    html.Div(str(stats['goals_against']), className="kpi-value"),
                    html.Div("Goals Against",            className="kpi-label"),
                ], className="kpi-tile"), xs=6, md=2),
            ], className="g-2 justify-content-center")

            is_coach = flask_session.get('is_coach', False)
            if is_coach:
                try:
                    st_stats = data_service.calculate_special_teams_stats(team_id)
                    st_index = st_stats.get('combined_st_index', 100.0)
                    pp_pct = f"{st_stats.get('pp_percentage', 0.0):.1f}%"
                    pk_pct = f"{st_stats.get('pk_percentage', 100.0):.1f}%"

                    st_kpi = dbc.Row([
                        dbc.Col(html.Div([
                            html.Div(f"{st_index:.1f}%", className="kpi-value text-primary"),
                            html.Div("ST Index (PP% + PK%)", className="kpi-label"),
                        ], className="kpi-tile border-primary"), xs=12, md=4),
                        dbc.Col(html.Div([
                            html.Div(pp_pct, className="kpi-value text-success"),
                            html.Div("Power Play (PP%)", className="kpi-label"),
                        ], className="kpi-tile"), xs=6, md=4),
                        dbc.Col(html.Div([
                            html.Div(pk_pct, className="kpi-value text-danger"),
                            html.Div("Penalty Kill (PK%)", className="kpi-label"),
                        ], className="kpi-tile"), xs=6, md=4),
                    ], className="g-2 justify-content-center mt-2")

                    kpi_row = html.Div([kpi_row, st_kpi])
                except Exception as e:
                    pass
        except Exception:
            kpi_row = html.Div()

        # ── Fetch games once; shared by form-dots, last-game, and chart ───────
        games_df = None
        try:
            games_df = data_service.get_games(team_id)
        except Exception:
            pass

        if games_df is not None and not games_df.empty and 'Date' in games_df.columns:
            games_df = games_df.sort_values('Date', ascending=False).reset_index(drop=True)

        # ── Recent form dots ──────────────────────────────────────────────────
        try:
            if games_df is not None and not games_df.empty:
                recent = games_df.head(5)
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
            if games_df is not None and not games_df.empty:
                last = games_df.iloc[0]
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

                is_coach = flask_session.get('is_coach', False)
                mode = 'coach' if is_coach else 'parent'
                last_game_id = last.get('ID')

                from services.ai_summary_service import AISummaryService
                ai_summary_service = AISummaryService()
                ai_summary_text = ""
                try:
                    digest = data_service.get_game_summary_digest(last_game_id, team_id)
                    if digest:
                        ai_summary_text = ai_summary_service.generate_summary(digest, mode=mode)
                except Exception as e:
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
                        html.H6("🎙️ Game Analyst Recap", className="fw-bold text-primary mb-2") if is_coach else html.H6("🎙️ Highlights & Recap", className="fw-bold text-success mb-2"),
                        html.Div(summary_paragraphs if summary_paragraphs else "Summary unavailable.")
                    ], className="bg-light p-3 rounded border")
                ]), className="shadow-sm mb-3")
            else:
                last_game = html.Div()
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
                game_type=None,
            )
            skaters = [p for p in leaderboard if p.get('player', {}).get('Position') != 'G']

            if skaters:
                top_points = skaters[0]  # leaderboard is already sorted by points desc
                top_goals = max(skaters, key=lambda p: p.get('goals', 0))
                top_assists = max(skaters, key=lambda p: p.get('assists', 0))
                items.append(_top_performer_item('Goals', top_goals, 'goals'))
                items.append(_top_performer_item('Assists', top_assists, 'assists'))
                items.append(_top_performer_item('Points', top_points, 'points'))

                is_coach = flask_session.get('is_coach', False)
                if is_coach or not config.is_coaches_only_stat('plus_minus'):
                    defensemen = [p for p in skaters if p.get('player', {}).get('Position') == 'D']
                    if defensemen:
                        top_plus_minus = max(defensemen, key=lambda p: p.get('plus_minus', 0))
                        items.append(_top_performer_item(
                            'Plus/Minus (D)', top_plus_minus, 'plus_minus', signed=True
                        ))
                if is_coach:
                    top_corsi = max(skaters, key=lambda p: p.get('on_ice_shot_share_pct', 0.0))
                    if top_corsi and top_corsi.get('on_ice_shot_share_pct', 0.0) > 0:
                        c_val = f"{top_corsi.get('on_ice_shot_share_pct', 0.0):.1f}%"
                        c_name = format_player_label(top_corsi['player'])
                        items.append(dbc.ListGroupItem([
                            html.Strong("Shot Share Leader (Corsi): "),
                            f"{c_name}  ({c_val})"
                        ]))

            top_performers = dbc.Card(dbc.CardBody([
                html.H6("Top Performers", className="text-muted mb-2"),
                dbc.ListGroup(items, flush=True),
            ])) if items else html.Div()
        except Exception:
            top_performers = html.Div()

        # ── Goals trend chart removed as requested ─────────────────────────────
        season_chart = html.Div()

        return kpi_row, form_row, last_game, top_performers, season_chart
