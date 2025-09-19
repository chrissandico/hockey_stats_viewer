import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from layouts.navigation import create_navigation
import config

def create_team_layout(data_service, team_context=None):
    """
    Create the team statistics layout.
    
    Args:
        data_service (DataService): The data service for retrieving team data
        team_context (dict, optional): Team context containing team_id and team_name
        
    Returns:
        dash.html.Div: The team statistics layout
    """
    # Get team ID and coach status from session context like player layout does
    from flask import session
    team_id = session.get('team_id') if session.get('authenticated', False) else None
    is_coach = session.get('is_coach', False)
    
    print(f"\n=== TEAM LAYOUT: Using team_id from session: {team_id} ===")
    print(f"TEAM LAYOUT: Coach status: {is_coach}")
    
    # Calculate team stats with team filtering
    team_stats = data_service.calculate_team_stats(team_id)
    print(f"TEAM LAYOUT: Team stats calculated: {team_stats}")
    
    # Get games for the game log with team filtering and date filtering (only completed games)
    games = data_service.get_games(team_id)
    games = data_service._filter_games_by_date(games, include_future=False)
    print(f"TEAM LAYOUT: Games retrieved: {len(games)} games (filtered to completed games only)")
    
    # Get leaderboards with team filtering - use different sorting for defense based on coach status
    forwards_points_leaders = data_service.get_team_leaderboard(stat='points', position='F', team_id=team_id)  # Team forwards sorted by points
    
    # For defense, use plus_minus for coaches, points for non-coaches
    defense_sort_stat = 'plus_minus' if is_coach else 'points'
    defense_leaders = data_service.get_team_leaderboard(stat=defense_sort_stat, position='D', team_id=team_id)
    defense_sort_label = "Plus/Minus" if is_coach else "Points"
    
    
    return html.Div([
        # Navigation bar
        create_navigation(),
        
        # Title
        html.H1("Team Statistics", className="text-center mt-4"),
        
        # Team season summary with loading
        dcc.Loading(
            id="team-stats-loading",
            type="default",
            color="#00205b",
            children=[
                dbc.Card([
                    dbc.CardHeader(html.H4("Season Summary", className="card-title")),
                    dbc.CardBody([
                        dbc.Row([
                            # Record
                            dbc.Col([
                                html.H5("Record"),
                                html.Div([
                                    html.Div([
                                        html.Span("Games Played: ", className="fw-bold"),
                                        html.Span(f"{team_stats['games_played']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Wins: ", className="fw-bold"),
                                        html.Span(f"{team_stats['wins']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Losses: ", className="fw-bold"),
                                        html.Span(f"{team_stats['losses']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Ties: ", className="fw-bold"),
                                        html.Span(f"{team_stats['ties']}")
                                    ], className="mb-1"),
                                ])
                            ], md=4),
                            
                            # Goals
                            dbc.Col([
                                html.H5("Goals"),
                                html.Div([
                                    html.Div([
                                        html.Span("Goals For: ", className="fw-bold"),
                                        html.Span(f"{team_stats['goals_for']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Goals Against: ", className="fw-bold"),
                                        html.Span(f"{team_stats['goals_against']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Goal Differential: ", className="fw-bold"),
                                        html.Span(f"{team_stats['goals_for'] - team_stats['goals_against']}")
                                    ], className="mb-1"),
                                ])
                            ], md=4),
                            
                            # Percentages
                            dbc.Col([
                                html.H5("Percentages"),
                                html.Div([
                                    html.Div([
                                        html.Span("Win Percentage: ", className="fw-bold"),
                                        html.Span(f"{team_stats['win_percentage']:.3f}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Goals For per Game: ", className="fw-bold"),
                                        html.Span(f"{team_stats['goals_for'] / team_stats['games_played']:.2f}" if team_stats['games_played'] > 0 else "0.00")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Goals Against per Game: ", className="fw-bold"),
                                        html.Span(f"{team_stats['goals_against'] / team_stats['games_played']:.2f}" if team_stats['games_played'] > 0 else "0.00")
                                    ], className="mb-1"),
                                ])
                            ], md=4),
                        ])
                    ])
                ], className="mb-4 shadow-sm")
            ]
        ),
        
        # Leaderboards with loading
        dcc.Loading(
            id="team-leaderboards-loading",
            type="default",
            color="#00205b",
            children=[
                dbc.Row([
                    # Forwards leaderboard
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H4("Forwards Leaderboard (Sorted by Points)", className="card-title")),
                            dbc.CardBody([
                                html.Table([
                                    html.Thead(
                                        html.Tr([
                                            html.Th("Player", className="text-start"),
                                            html.Th("G", className="text-center"),
                                            html.Th("A", className="text-center"),
                                            html.Th("P", className="text-center"),
                                            # Only show plus/minus column for coaches
                                            *([html.Th("+/-", className="text-center")] if is_coach or not config.is_coaches_only_stat('plus_minus') else [])
                                        ])
                                    ),
                                    html.Tbody([
                                        html.Tr([
                                            html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                                            html.Td(f"{stats['goals']}", className="text-center"),
                                            html.Td(f"{stats['assists']}", className="text-center"),
                                            html.Td(f"{stats['points']}", className="text-center"),
                                            # Only show plus/minus cell for coaches
                                            *([html.Td(f"{stats['plus_minus']}", className="text-center")] if is_coach or not config.is_coaches_only_stat('plus_minus') else [])
                                        ]) for stats in forwards_points_leaders
                                    ])
                                ], className="table table-striped table-hover")
                            ])
                        ], className="mb-4 shadow-sm")
                    ], md=6),
                    
                    # Defense leaderboard
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H4(f"Defense Leaderboard (Sorted by {defense_sort_label})", className="card-title")),
                            dbc.CardBody([
                                html.Table([
                                    html.Thead(
                                        html.Tr([
                                            html.Th("Player", className="text-start"),
                                            html.Th("G", className="text-center"),
                                            html.Th("A", className="text-center"),
                                            html.Th("P", className="text-center"),
                                            # Only show plus/minus column for coaches
                                            *([html.Th("+/-", className="text-center")] if is_coach or not config.is_coaches_only_stat('plus_minus') else [])
                                        ])
                                    ),
                                    html.Tbody([
                                        html.Tr([
                                            html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                                            html.Td(f"{stats['goals']}", className="text-center"),
                                            html.Td(f"{stats['assists']}", className="text-center"),
                                            html.Td(f"{stats['points']}", className="text-center"),
                                            # Only show plus/minus cell for coaches
                                            *([html.Td(f"{stats['plus_minus']}", className="text-center")] if is_coach or not config.is_coaches_only_stat('plus_minus') else [])
                                        ]) for stats in defense_leaders
                                    ])
                                ], className="table table-striped table-hover")
                            ])
                        ], className="mb-4 shadow-sm")
                    ], md=6)
                ])
            ]
        ),
        
        # Game log with loading
        dcc.Loading(
            id="team-game-log-loading",
            type="default",
            color="#00205b",
            children=[
                dbc.Card([
                    dbc.CardHeader(html.H4("Game Log", className="card-title")),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='team-game-log-table',
                            columns=[
                                {'name': 'Date', 'id': 'Date'},
                                {'name': 'Opponent', 'id': 'Opponent'},
                                {'name': 'Location', 'id': 'Location'},
                                {'name': 'Result', 'id': 'Result'},
                                {'name': 'Score', 'id': 'Score'}
                            ],
                            data=[{
                                'Date': game['Date'],
                                'Opponent': game['Opponent'],
                                'Location': game['Location'],
                                'Result': game['Result'],
                                'Score': f"{game['GoalsFor']} - {game['GoalsAgainst']}"
                            } for _, game in games.iterrows()],
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'center',
                                'padding': '10px',
                                'minWidth': '80px'
                            },
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                },
                                {
                                    'if': {'filter_query': '{Result} = "W"'},
                                    'backgroundColor': 'rgba(0, 255, 0, 0.1)'
                                },
                                {
                                    'if': {'filter_query': '{Result} = "L"'},
                                    'backgroundColor': 'rgba(255, 0, 0, 0.1)'
                                },
                                {
                                    'if': {'filter_query': '{Result} = "T"'},
                                    'backgroundColor': 'rgba(255, 255, 0, 0.1)'
                                }
                            ],
                            sort_action='native',
                            sort_mode='single',
                            sort_by=[{'column_id': 'Date', 'direction': 'desc'}]
                        )
                    ])
                ], className="shadow-sm")
            ]
        )
    ])
