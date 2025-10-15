"""
Skeleton screen components for progressive loading.

This module provides reusable skeleton components that match the structure
of actual content to provide smooth loading experiences.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


class SkeletonLoader:
    """
    Provides skeleton screen components for various parts of the application.
    
    Skeleton screens show placeholder content while actual data is loading,
    improving perceived performance and user experience.
    """
    
    @staticmethod
    def create_skeleton_line(width="100%", height="1rem", margin_bottom="0.5rem"):
        """Create a skeleton line placeholder."""
        return html.Div(
            className="skeleton skeleton-text",
            style={
                'width': width,
                'height': height,
                'marginBottom': margin_bottom,
                'borderRadius': '4px'
            }
        )
    
    @staticmethod
    def create_skeleton_card(title_width="60%", lines=3, show_header=True):
        """Create a skeleton card with header and content lines."""
        content = []
        
        if show_header:
            content.append(
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width=title_width, 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ])
            )
        
        # Content lines
        body_content = []
        for i in range(lines):
            width = "100%" if i < lines - 1 else "80%"  # Last line shorter
            body_content.append(
                SkeletonLoader.create_skeleton_line(width=width)
            )
        
        content.append(dbc.CardBody(body_content))
        
        return dbc.Card(content, className="mb-4 shadow-sm")
    
    @staticmethod
    def create_skeleton_table(rows=5, columns=4):
        """Create a skeleton table placeholder."""
        # Header row
        header_cells = [
            html.Th(
                SkeletonLoader.create_skeleton_line(
                    width="80px", 
                    height="1rem", 
                    margin_bottom="0"
                ),
                className="text-center"
            ) for _ in range(columns)
        ]
        
        # Data rows
        data_rows = []
        for _ in range(rows):
            cells = [
                html.Td(
                    SkeletonLoader.create_skeleton_line(
                        width="60px", 
                        height="0.875rem", 
                        margin_bottom="0"
                    ),
                    className="text-center"
                ) for _ in range(columns)
            ]
            data_rows.append(html.Tr(cells))
        
        return html.Table([
            html.Thead(html.Tr(header_cells)),
            html.Tbody(data_rows)
        ], className="table table-striped table-hover")
    
    @staticmethod
    def create_skeleton_stats_grid(columns=3, stats_per_column=4):
        """Create a skeleton stats grid (like team summary)."""
        cols = []
        
        for _ in range(columns):
            stats = []
            # Column title
            stats.append(
                html.H5(
                    SkeletonLoader.create_skeleton_line(
                        width="120px", 
                        height="1.25rem", 
                        margin_bottom="0.5rem"
                    )
                )
            )
            
            # Stats lines
            for _ in range(stats_per_column):
                stats.append(
                    html.Div([
                        SkeletonLoader.create_skeleton_line(width="100%", height="1rem")
                    ], className="mb-1")
                )
            
            cols.append(dbc.Col(stats, md=4))
        
        return dbc.Row(cols)
    
    @staticmethod
    def render_player_stats_skeleton():
        """Render skeleton for player statistics page."""
        return html.Div([
            # Player selection skeleton
            SkeletonLoader.create_skeleton_card(
                title_width="40%", 
                lines=2, 
                show_header=True
            ),
            
            # Player info skeleton
            dbc.Card([
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width="150px", 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ]),
                dbc.CardBody([
                    dbc.Row([
                        # Player details column
                        dbc.Col([
                            html.H5(
                                SkeletonLoader.create_skeleton_line(
                                    width="120px", 
                                    height="1.25rem", 
                                    margin_bottom="0.5rem"
                                )
                            ),
                            SkeletonLoader.create_skeleton_line(width="100%"),
                        ], md=4),
                        
                        # Season stats column
                        dbc.Col([
                            html.H5(
                                SkeletonLoader.create_skeleton_line(
                                    width="120px", 
                                    height="1.25rem", 
                                    margin_bottom="0.5rem"
                                )
                            ),
                            *[SkeletonLoader.create_skeleton_line(width="100%") for _ in range(4)]
                        ], md=4),
                        
                        # Additional stats column
                        dbc.Col([
                            html.H5(
                                SkeletonLoader.create_skeleton_line(
                                    width="120px", 
                                    height="1.25rem", 
                                    margin_bottom="0.5rem"
                                )
                            ),
                            *[SkeletonLoader.create_skeleton_line(width="100%") for _ in range(2)]
                        ], md=4),
                    ])
                ])
            ], className="mb-4 shadow-sm"),
            
            # Game log skeleton
            dbc.Card([
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width="100px", 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ]),
                dbc.CardBody([
                    SkeletonLoader.create_skeleton_table(rows=8, columns=6)
                ])
            ], className="shadow-sm")
        ])
    
    @staticmethod
    def render_team_analytics_skeleton():
        """Render skeleton for team analytics page."""
        return html.Div([
            # Team summary skeleton
            dbc.Card([
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width="100px", 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ]),
                dbc.CardBody([
                    SkeletonLoader.create_skeleton_stats_grid(columns=3, stats_per_column=4)
                ])
            ], className="mb-4 shadow-sm"),
            
            # Leaderboards skeleton
            dbc.Row([
                # Forwards leaderboard
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            SkeletonLoader.create_skeleton_line(
                                width="180px", 
                                height="1.5rem", 
                                margin_bottom="0"
                            )
                        ]),
                        dbc.CardBody([
                            SkeletonLoader.create_skeleton_table(rows=6, columns=5)
                        ])
                    ], className="mb-4 shadow-sm")
                ], md=6),
                
                # Defense leaderboard
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            SkeletonLoader.create_skeleton_line(
                                width="180px", 
                                height="1.5rem", 
                                margin_bottom="0"
                            )
                        ]),
                        dbc.CardBody([
                            SkeletonLoader.create_skeleton_table(rows=6, columns=5)
                        ])
                    ], className="mb-4 shadow-sm")
                ], md=6)
            ]),
            
            # Goalies leaderboard skeleton
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            SkeletonLoader.create_skeleton_line(
                                width="200px", 
                                height="1.5rem", 
                                margin_bottom="0"
                            )
                        ]),
                        dbc.CardBody([
                            SkeletonLoader.create_skeleton_table(rows=3, columns=9)
                        ])
                    ], className="mb-4 shadow-sm")
                ], md=12)
            ]),
            
            # Game log skeleton
            dbc.Card([
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width="100px", 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ]),
                dbc.CardBody([
                    SkeletonLoader.create_skeleton_table(rows=10, columns=5)
                ])
            ], className="shadow-sm")
        ])
    
    @staticmethod
    def render_game_summary_skeleton():
        """Render skeleton for game summary page."""
        return html.Div([
            # Game selection skeleton
            SkeletonLoader.create_skeleton_card(
                title_width="40%", 
                lines=2, 
                show_header=True
            ),
            
            # Game summary skeleton
            dbc.Card([
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width="300px", 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ]),
                dbc.CardBody([
                    dbc.Row([
                        # Game details column
                        dbc.Col([
                            html.H5(
                                SkeletonLoader.create_skeleton_line(
                                    width="120px", 
                                    height="1.25rem", 
                                    margin_bottom="0.5rem"
                                )
                            ),
                            *[SkeletonLoader.create_skeleton_line(width="100%") for _ in range(5)]
                        ], md=6),
                        
                        # Shots & penalties column
                        dbc.Col([
                            html.H5(
                                SkeletonLoader.create_skeleton_line(
                                    width="150px", 
                                    height="1.25rem", 
                                    margin_bottom="0.5rem"
                                )
                            ),
                            *[SkeletonLoader.create_skeleton_line(width="100%") for _ in range(4)]
                        ], md=6),
                    ])
                ])
            ], className="mb-4 shadow-sm"),
            
            # Period breakdown skeleton
            dbc.Card([
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width="150px", 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ]),
                dbc.CardBody([
                    SkeletonLoader.create_skeleton_table(rows=4, columns=4)
                ])
            ], className="mb-4 shadow-sm"),
            
            # Player performance skeleton
            dbc.Card([
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width="180px", 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ]),
                dbc.CardBody([
                    # Position filter buttons skeleton
                    html.Div([
                        *[SkeletonLoader.create_skeleton_line(
                            width="80px", 
                            height="38px", 
                            margin_bottom="0.5rem"
                        ) for _ in range(4)]
                    ], className="mb-3 d-flex gap-2"),
                    
                    # Player stats table skeleton
                    SkeletonLoader.create_skeleton_table(rows=8, columns=6)
                ])
            ], className="shadow-sm")
        ])
    
    @staticmethod
    def render_navigation_skeleton():
        """Render skeleton for navigation bar."""
        return html.Nav([
            html.Div([
                # Brand skeleton
                SkeletonLoader.create_skeleton_line(
                    width="150px", 
                    height="1.5rem", 
                    margin_bottom="0"
                ),
                
                # Navigation links skeleton
                html.Div([
                    *[SkeletonLoader.create_skeleton_line(
                        width="80px", 
                        height="1rem", 
                        margin_bottom="0"
                    ) for _ in range(4)]
                ], className="d-flex gap-3")
            ], className="container-fluid d-flex justify-content-between align-items-center")
        ], className="navbar navbar-expand-lg navbar-dark bg-primary")
    
    @staticmethod
    def render_loading_placeholder(component_type="general", message="Loading..."):
        """
        Render a loading placeholder with optional message.
        
        Args:
            component_type (str): Type of component being loaded
            message (str): Loading message to display
        """
        return html.Div([
            html.Div([
                html.Div(className="hockey-puck-loader"),
                html.Div(message, className="loading-text")
            ], className="text-center")
        ], className="loading-overlay")