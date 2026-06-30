from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from flask import session as flask_session
from utils import format_player_label


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
            dcc.Loading(html.Div(id='dashboard-kpi-row', className="mb-4")),
            html.Div(id='dashboard-form-row', className="text-center mb-4"),
            dbc.Row([
                dbc.Col(dcc.Loading(html.Div(id='dashboard-last-game')), md=5),
                dbc.Col(dcc.Loading(html.Div(id='dashboard-top-performers')), md=7),
            ], className="mb-4"),
            dcc.Loading(html.Div(id='dashboard-chart', className="mb-4")),
            dbc.Row([
                _quick_card("Players",   "Individual stats and game logs",    "/player"),
                _quick_card("Games",     "Results, period breakdowns, shots", "/game"),
                _quick_card("Team",      "Leaderboards and season trends",    "/team"),
                _quick_card("Opponents", "Head-to-head records by opponent",  "/opponent"),
            ], className="mb-4"),
        ], fluid=True),
    ])


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

        # ── Last game card ────────────────────────────────────────────────────
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
                last_game = dbc.Card(dbc.CardBody([
                    html.H6("Last Game", className="text-muted mb-2"),
                    html.H4(str(last.get('Opponent', 'Unknown')), className="mb-1"),
                    html.H3(
                        f"{last.get('GoalsFor', 0)} — {last.get('GoalsAgainst', 0)}",
                        className="fw-bold mb-2",
                    ),
                    dbc.Badge(badge_text, color=badge_color, className="me-2"),
                    html.Span(str(last.get('Date', '')), className="text-muted small"),
                ]))
            else:
                last_game = html.Div()
        except Exception:
            last_game = html.Div()

        # ── Top performers ────────────────────────────────────────────────────
        try:
            items = []
            for stat_key, label in [('goals', 'Goals'), ('assists', 'Assists'), ('points', 'Points')]:
                try:
                    leaders = data_service.get_team_leaderboard(
                        stat=stat_key,
                        position=None,
                        limit=1,
                        team_id=team_id,
                        game_type=None,
                    )
                    if leaders:
                        top = leaders[0]
                        name = format_player_label(top['player'])
                        value = top.get(stat_key, 0)
                        items.append(dbc.ListGroupItem(
                            [html.Strong(f"{label}: "), f"{name}  ({value})"]
                        ))
                except Exception:
                    pass

            top_performers = dbc.Card(dbc.CardBody([
                html.H6("Top Performers", className="text-muted mb-2"),
                dbc.ListGroup(items, flush=True),
            ])) if items else html.Div()
        except Exception:
            top_performers = html.Div()

        # ── Season goals trend chart ──────────────────────────────────────────
        try:
            if games_df is not None and not games_df.empty and 'Date' in games_df.columns:
                import pandas as pd
                chart_df = games_df.copy()
                chart_df['_sort_date'] = pd.to_datetime(chart_df['Date'], errors='coerce')
                chart_df = chart_df.sort_values('_sort_date').dropna(subset=['_sort_date'])

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=chart_df['Date'],
                    y=chart_df['GoalsFor'],
                    name='Goals For',
                    mode='lines+markers',
                    line=dict(color='#00843d'),
                ))
                fig.add_trace(go.Scatter(
                    x=chart_df['Date'],
                    y=chart_df['GoalsAgainst'],
                    name='Goals Against',
                    mode='lines+markers',
                    line=dict(color='#c8102e'),
                ))
                fig.update_layout(
                    height=260,
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    margin=dict(l=40, r=20, t=30, b=40),
                    xaxis_title='Game Date',
                    yaxis_title='Goals',
                )
                season_chart = dcc.Graph(figure=fig, config={'displayModeBar': False})
            else:
                season_chart = html.Div()
        except Exception:
            season_chart = html.Div()

        return kpi_row, form_row, last_game, top_performers, season_chart
