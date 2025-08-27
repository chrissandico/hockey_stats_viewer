import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from layouts.navigation import create_navigation

def create_team_layout(data_service):
    """
    Create the team statistics layout.
    
    Args:
        data_service (DataService): The data service for retrieving team data
        
    Returns:
        dash.html.Div: The team statistics layout
    """
    # Calculate team stats
    team_stats = data_service.calculate_team_stats()
    
    # Get games for the game log
    games = data_service.get_games()
    
    # Get leaderboards
    forwards_points_leaders = data_service.get_team_leaderboard(stat='points', position='F', limit=5)
    defense_points_leaders = data_service.get_team_leaderboard(stat='points', position='D', limit=5)
    
    # Get goalies
    players = data_service.get_players()
    goalies = players[players['Position'] == 'G']
    goalie_stats = []
    for _, goalie in goalies.iterrows():
        stats = data_service.calculate_goalie_stats(goalie['ID'])
        if stats:
            goalie_stats.append(stats)
    
    # Sort goalies by save percentage
    goalie_stats.sort(key=lambda x: x['save_percentage'], reverse=True)
    
    return html.Div([
        # Navigation bar
        create_navigation(),
        
        # Title
        html.H1("Team Statistics", className="text-center mt-4"),
        
        # Team season summary
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
                            html.Div([
                                html.Span("Points: ", className="fw-bold"),
                                html.Span(f"{team_stats['points']}")
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
                                html.Span("Points Percentage: ", className="fw-bold"),
                                html.Span(f"{team_stats['points'] / (team_stats['games_played'] * 2):.3f}" if team_stats['games_played'] > 0 else "0.000")
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
        ], className="mb-4 shadow-sm"),
        
        # Leaderboards
        dbc.Row([
            # Forwards leaderboard
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Forwards Leaderboard", className="card-title")),
                    dbc.CardBody([
                        html.Table([
                            html.Thead(
                                html.Tr([
                                    html.Th("Player", className="text-start"),
                                    html.Th("G", className="text-center"),
                                    html.Th("A", className="text-center"),
                                    html.Th("P", className="text-center"),
                                    html.Th("+/-", className="text-center")
                                ])
                            ),
                            html.Tbody([
                                html.Tr([
                                    html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                                    html.Td(f"{stats['goals']}", className="text-center"),
                                    html.Td(f"{stats['assists']}", className="text-center"),
                                    html.Td(f"{stats['points']}", className="text-center"),
                                    html.Td(f"{stats['plus_minus']}", className="text-center")
                                ]) for stats in forwards_points_leaders
                            ])
                        ], className="table table-striped table-hover")
                    ])
                ], className="mb-4 shadow-sm")
            ], md=6),
            
            # Defense leaderboard
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Defense Leaderboard", className="card-title")),
                    dbc.CardBody([
                        html.Table([
                            html.Thead(
                                html.Tr([
                                    html.Th("Player", className="text-start"),
                                    html.Th("G", className="text-center"),
                                    html.Th("A", className="text-center"),
                                    html.Th("P", className="text-center"),
                                    html.Th("+/-", className="text-center")
                                ])
                            ),
                            html.Tbody([
                                html.Tr([
                                    html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                                    html.Td(f"{stats['goals']}", className="text-center"),
                                    html.Td(f"{stats['assists']}", className="text-center"),
                                    html.Td(f"{stats['points']}", className="text-center"),
                                    html.Td(f"{stats['plus_minus']}", className="text-center")
                                ]) for stats in defense_points_leaders
                            ])
                        ], className="table table-striped table-hover")
                    ])
                ], className="mb-4 shadow-sm")
            ], md=6)
        ]),
        
        # Goalie stats
        dbc.Card([
            dbc.CardHeader(html.H4("Goalie Statistics", className="card-title")),
            dbc.CardBody([
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Goalie", className="text-start"),
                            html.Th("GP", className="text-center"),
                            html.Th("W", className="text-center"),
                            html.Th("SO", className="text-center"),
                            html.Th("GAA", className="text-center"),
                            html.Th("SV%", className="text-center")
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(f"#{stats['player']['JerseyNumber']}", className="text-start"),
                            html.Td(f"{stats['games_played']}", className="text-center"),
                            html.Td(f"{stats['wins']}", className="text-center"),
                            html.Td(f"{stats['shutouts']}", className="text-center"),
                            html.Td(f"{stats['gaa']:.2f}", className="text-center"),
                            html.Td(f"{stats['save_percentage']:.3f}", className="text-center")
                        ]) for stats in goalie_stats
                    ])
                ], className="table table-striped table-hover")
            ])
        ], className="mb-4 shadow-sm"),
        
        # Game log
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
    ])
