"""
Period Breakdown Component

A reusable component for displaying period-by-period scoring breakdown in hockey games.
This component can be used across different layouts to show consistent period scoring data.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd


def create_period_breakdown_component(period_data, title="Period Breakdown", show_title=True):
    """
    Create a period-by-period scoring and shots breakdown component.
    
    Args:
        period_data (dict): Dictionary containing period breakdown data with structure:
            {
                'your_team': {
                    'name': 'Team Name',
                    'goals': [goals_p1, goals_p2, goals_p3],
                    'shots': [shots_p1, shots_p2, shots_p3],
                    'total_goals': total_goals,
                    'total_shots': total_shots,
                    # Backward compatibility fields
                    'periods': [goals_p1, goals_p2, goals_p3],
                    'total': total_goals
                },
                'opponent': {
                    'name': 'Opponent Name', 
                    'goals': [goals_p1, goals_p2, goals_p3],
                    'shots': [shots_p1, shots_p2, shots_p3],
                    'total_goals': total_goals,
                    'total_shots': total_shots,
                    # Backward compatibility fields
                    'periods': [goals_p1, goals_p2, goals_p3],
                    'total': total_goals
                }
            }
        title (str): Title for the component
        show_title (bool): Whether to show the title header
        
    Returns:
        dash.html.Div: The period breakdown component
    """
    if not period_data or 'your_team' not in period_data or 'opponent' not in period_data:
        return html.Div(
            dbc.Alert("No period breakdown data available", color="warning"),
            className="mb-3"
        )
    
    # Extract team data
    your_team = period_data['your_team']
    opponent = period_data['opponent']
    
    # Check if we have the new shots data format
    has_shots_data = ('shots' in your_team and 'shots' in opponent and 
                     'total_shots' in your_team and 'total_shots' in opponent)
    
    if has_shots_data:
        # Create enhanced table with goals and shots
        header_row = html.Tr([
            html.Th("Team", className="text-start", style={"width": "25%"}),
            html.Th("1st", className="text-center", style={"width": "15%"}),
            html.Th("2nd", className="text-center", style={"width": "15%"}),
            html.Th("3rd", className="text-center", style={"width": "15%"}),
            html.Th("Total", className="text-center", style={"width": "15%"}),
            html.Th("SOG", className="text-center", style={"width": "15%"})
        ])
        
        # Create team rows with goals and shots
        your_team_row = html.Tr([
            html.Td(your_team['name'], className="text-start fw-bold"),
            html.Td(f"{your_team['goals'][0]} ({your_team['shots'][0]})", className="text-center"),
            html.Td(f"{your_team['goals'][1]} ({your_team['shots'][1]})", className="text-center"),
            html.Td(f"{your_team['goals'][2]} ({your_team['shots'][2]})", className="text-center"),
            html.Td(str(your_team['total_goals']), className="text-center fw-bold"),
            html.Td(str(your_team['total_shots']), className="text-center fw-bold")
        ])
        
        opponent_row = html.Tr([
            html.Td(opponent['name'], className="text-start fw-bold"),
            html.Td(f"{opponent['goals'][0]} ({opponent['shots'][0]})", className="text-center"),
            html.Td(f"{opponent['goals'][1]} ({opponent['shots'][1]})", className="text-center"),
            html.Td(f"{opponent['goals'][2]} ({opponent['shots'][2]})", className="text-center"),
            html.Td(str(opponent['total_goals']), className="text-center fw-bold"),
            html.Td(str(opponent['total_shots']), className="text-center fw-bold")
        ])
        
        # Create the table without legend
        table = html.Table([
            html.Thead(header_row, className="table-dark"),
            html.Tbody([your_team_row, opponent_row])
        ], className="table table-striped table-hover mb-0")
        
    else:
        # Fallback to original format for backward compatibility
        header_row = html.Tr([
            html.Th("Team", className="text-start", style={"width": "40%"}),
            html.Th("1", className="text-center", style={"width": "15%"}),
            html.Th("2", className="text-center", style={"width": "15%"}),
            html.Th("3", className="text-center", style={"width": "15%"}),
            html.Th("T", className="text-center", style={"width": "15%"})
        ])
        
        # Use backward compatibility fields
        your_team_periods = your_team.get('periods', [0, 0, 0])
        your_team_total = your_team.get('total', 0)
        opponent_periods = opponent.get('periods', [0, 0, 0])
        opponent_total = opponent.get('total', 0)
        
        your_team_row = html.Tr([
            html.Td(your_team['name'], className="text-start fw-bold"),
            html.Td(str(your_team_periods[0]), className="text-center"),
            html.Td(str(your_team_periods[1]), className="text-center"),
            html.Td(str(your_team_periods[2]), className="text-center"),
            html.Td(str(your_team_total), className="text-center fw-bold")
        ])
        
        opponent_row = html.Tr([
            html.Td(opponent['name'], className="text-start fw-bold"),
            html.Td(str(opponent_periods[0]), className="text-center"),
            html.Td(str(opponent_periods[1]), className="text-center"),
            html.Td(str(opponent_periods[2]), className="text-center"),
            html.Td(str(opponent_total), className="text-center fw-bold")
        ])
        
        # Create the table
        table = html.Table([
            html.Thead(header_row, className="table-dark"),
            html.Tbody([your_team_row, opponent_row])
        ], className="table table-striped table-hover mb-0")
    
    # Create the component with optional title
    component_children = []
    
    if show_title:
        component_children.append(
            dbc.CardHeader(
                html.H5(title, className="card-title mb-0")
            )
        )
    
    component_children.append(
        dbc.CardBody([
            table
        ], className="p-3")
    )
    
    return dbc.Card(
        component_children,
        className="shadow-sm mb-3"
    )


def create_period_breakdown_table_only(period_data):
    """
    Create just the period breakdown table without card wrapper.
    Useful for embedding in existing cards or layouts.
    
    Args:
        period_data (dict): Dictionary containing period breakdown data
        
    Returns:
        dash.html.Table: The period breakdown table
    """
    if not period_data or 'your_team' not in period_data or 'opponent' not in period_data:
        return html.Div(
            dbc.Alert("No period breakdown data available", color="warning", className="mb-0"),
        )
    
    # Extract team data
    your_team = period_data['your_team']
    opponent = period_data['opponent']
    
    # Create the table header
    header_row = html.Tr([
        html.Th("Team", className="text-start", style={"width": "40%"}),
        html.Th("1", className="text-center", style={"width": "15%"}),
        html.Th("2", className="text-center", style={"width": "15%"}),
        html.Th("3", className="text-center", style={"width": "15%"}),
        html.Th("T", className="text-center", style={"width": "15%"})
    ])
    
    # Create team rows
    your_team_row = html.Tr([
        html.Td(your_team['name'], className="text-start fw-bold"),
        html.Td(str(your_team['periods'][0]), className="text-center"),
        html.Td(str(your_team['periods'][1]), className="text-center"),
        html.Td(str(your_team['periods'][2]), className="text-center"),
        html.Td(str(your_team['total']), className="text-center fw-bold")
    ])
    
    opponent_row = html.Tr([
        html.Td(opponent['name'], className="text-start fw-bold"),
        html.Td(str(opponent['periods'][0]), className="text-center"),
        html.Td(str(opponent['periods'][1]), className="text-center"),
        html.Td(str(opponent['periods'][2]), className="text-center"),
        html.Td(str(opponent['total']), className="text-center fw-bold")
    ])
    
    # Create and return the table
    return html.Table([
        html.Thead(header_row, className="table-dark"),
        html.Tbody([your_team_row, opponent_row])
    ], className="table table-striped table-hover mb-0")


def create_compact_period_breakdown(period_data):
    """
    Create a compact version of the period breakdown for smaller spaces.
    
    Args:
        period_data (dict): Dictionary containing period breakdown data
        
    Returns:
        dash.html.Div: The compact period breakdown component
    """
    if not period_data or 'your_team' not in period_data or 'opponent' not in period_data:
        return html.Div(
            dbc.Alert("No data available", color="warning", className="mb-0 small"),
        )
    
    # Extract team data
    your_team = period_data['your_team']
    opponent = period_data['opponent']
    
    # Create compact display
    return html.Div([
        html.Div([
            html.Span(f"{your_team['name']}: ", className="fw-bold small"),
            html.Span(f"{your_team['periods'][0]}-{your_team['periods'][1]}-{your_team['periods'][2]} ({your_team['total']})", className="small")
        ], className="mb-1"),
        html.Div([
            html.Span(f"{opponent['name']}: ", className="fw-bold small"),
            html.Span(f"{opponent['periods'][0]}-{opponent['periods'][1]}-{opponent['periods'][2]} ({opponent['total']})", className="small")
        ])
    ], className="p-2 bg-light rounded")
