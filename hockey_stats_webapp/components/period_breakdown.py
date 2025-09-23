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
    Create a period-by-period scoring breakdown component.
    
    Args:
        period_data (dict): Dictionary containing period breakdown data with structure:
            {
                'your_team': {
                    'name': 'Team Name',
                    'periods': [goals_p1, goals_p2, goals_p3],
                    'total': total_goals
                },
                'opponent': {
                    'name': 'Opponent Name', 
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
