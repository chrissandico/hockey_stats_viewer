"""
Progressive loading components that integrate skeleton screens with lazy loading.

This module provides high-level components that combine skeleton screens
and lazy loading for specific parts of the hockey stats application.
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from components.skeleton_loader import SkeletonLoader
from components.lazy_loader import LazyLoader, ProgressiveLoader
import time


class ProgressivePlayerStats:
    """Progressive loading component for player statistics."""
    
    @staticmethod
    def create_component(player_id=None):
        """Create progressive player stats component."""
        return html.Div([
            # Above-the-fold: Player selection (loads immediately)
            html.Div(
                id='player-selection-immediate',
                children=[
                    SkeletonLoader.create_skeleton_card(
                        title_width="40%", 
                        lines=2, 
                        show_header=True
                    )
                ]
            ),
            
            # Below-the-fold: Player info (lazy loaded)
            LazyLoader().create_lazy_container(
                'player-info',
                SkeletonLoader.render_player_stats_skeleton(),
                priority='high'
            ),
            
            # Below-the-fold: Game log (lazy loaded with lower priority)
            LazyLoader().create_lazy_container(
                'player-game-log',
                SkeletonLoader.create_skeleton_card(
                    title_width="30%",
                    lines=1,
                    show_header=True
                ),
                priority='medium'
            )
        ])
    
    @staticmethod
    def register_callbacks(app, data_service):
        """Register callbacks for progressive player stats."""
        
        @app.callback(
            Output('lazy-content-player-info', 'children'),
            Input('lazy-load-trigger-player-info', 'data'),
            State('player-dropdown', 'value'),
            State('game-type-session-store', 'data'),
            prevent_initial_call=True
        )
        def load_player_info(trigger_data, jersey_number, game_type_data):
            """Load player info when triggered by intersection observer."""
            if not trigger_data.get('trigger') or not jersey_number:
                return SkeletonLoader.render_player_stats_skeleton()
            
            # Simulate loading delay for smooth transition
            time.sleep(0.1)
            
            # Get actual player info (reuse existing logic)
            from flask import session
            team_id = session.get('team_id') if session.get('authenticated', False) else None
            is_coach = session.get('is_coach', False)
            
            # Get game type
            game_type = game_type_data if isinstance(game_type_data, str) else None
            if game_type_data and isinstance(game_type_data, dict):
                game_type = game_type_data.get('game_type')
            if game_type == "all":
                game_type = None
            
            # Get player data
            team_players = data_service.get_players(team_id)
            matching_players = team_players[team_players['JerseyNumber'] == jersey_number]
            
            if matching_players.empty:
                return dbc.Alert("Player not found", color="danger")
            
            player = matching_players.iloc[0]
            player_id = data_service._get_player_id_from_series(player)
            
            if player_id is None:
                return dbc.Alert("Player ID not found", color="danger")
            
            # Calculate stats
            is_goalie = player['Position'] == 'G'
            if is_goalie:
                stats = data_service.calculate_goalie_stats(player_id, team_id, game_type)
            else:
                stats = data_service.calculate_player_stats(player_id, team_id, game_type)
            
            if stats is None:
                return dbc.Alert("Could not calculate player statistics", color="danger")
            
            # Return player info card (reuse existing layout logic)
            return dbc.Card([
                dbc.CardHeader(html.H4(f"#{player['JerseyNumber']}", className="card-title")),
                dbc.CardBody([
                    dbc.Row([
                        # Player details
                        dbc.Col([
                            html.H5("Player Details"),
                            html.P(f"Position: {player['Position']}"),
                        ], md=4),
                        
                        # Season stats
                        dbc.Col([
                            html.H5("Season Totals"),
                            html.Div([
                                html.Div([
                                    html.Span("Games Played: ", className="fw-bold"),
                                    html.Span(f"{stats['games_played']}")
                                ], className="mb-1"),
                                
                                # Position-specific stats
                                *([
                                    html.Div([
                                        html.Span("Wins: ", className="fw-bold"),
                                        html.Span(f"{stats['wins']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("GAA: ", className="fw-bold"),
                                        html.Span(f"{stats['gaa']:.2f}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Save %: ", className="fw-bold"),
                                        html.Span(f"{stats['save_percentage']:.3f}")
                                    ], className="mb-1"),
                                ] if is_goalie else [
                                    html.Div([
                                        html.Span("Goals: ", className="fw-bold"),
                                        html.Span(f"{stats['goals']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Assists: ", className="fw-bold"),
                                        html.Span(f"{stats['assists']}")
                                    ], className="mb-1"),
                                    html.Div([
                                        html.Span("Points: ", className="fw-bold"),
                                        html.Span(f"{stats['points']}")
                                    ], className="mb-1"),
                                ])
                            ])
                        ], md=4),
                        
                        # Additional stats
                        dbc.Col([
                            html.H5("Additional Stats"),
                            html.Div([
                                *([
                                    html.Div([
                                        html.Span("Shots Against: ", className="fw-bold"),
                                        html.Span(f"{stats['shots_against']}")
                                    ], className="mb-1"),
                                ] if is_goalie else [
                                    html.Div([
                                        html.Span("Penalty Minutes: ", className="fw-bold"),
                                        html.Span(f"{stats.get('penalty_minutes', 0)}")
                                    ], className="mb-1") if is_coach else html.Div()
                                ])
                            ])
                        ], md=4),
                    ])
                ])
            ], className="mb-4 shadow-sm")


class ProgressiveTeamAnalytics:
    """Progressive loading component for team analytics."""
    
    @staticmethod
    def create_component():
        """Create progressive team analytics component."""
        return LazyLoader().create_priority_loader(
            high_priority_components=[
                {
                    'id': 'team-summary',
                    'component': html.Div(id='team-summary-immediate')
                }
            ],
            medium_priority_components=[
                {
                    'id': 'team-leaderboards',
                    'skeleton': SkeletonLoader.render_team_analytics_skeleton()
                }
            ],
            low_priority_components=[
                {
                    'id': 'team-game-log',
                    'skeleton': SkeletonLoader.create_skeleton_card(
                        title_width="30%",
                        lines=1,
                        show_header=True
                    )
                }
            ]
        )
    
    @staticmethod
    def register_callbacks(app, data_service):
        """Register callbacks for progressive team analytics."""
        
        @app.callback(
            Output('team-summary-immediate', 'children'),
            Input('game-type-session-store', 'data')
        )
        def load_team_summary_immediate(game_type_data):
            """Load team summary immediately (high priority)."""
            from flask import session
            team_id = session.get('team_id') if session.get('authenticated', False) else None
            
            game_type = game_type_data if isinstance(game_type_data, str) else None
            if game_type_data and isinstance(game_type_data, dict):
                game_type = game_type_data.get('game_type')
            if game_type == "all":
                game_type = None
            
            team_stats = data_service.calculate_team_stats(team_id, game_type)
            
            return dbc.Card([
                dbc.CardHeader(html.H4("Summary", className="card-title")),
                dbc.CardBody([
                    dbc.Row([
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
                            ])
                        ], md=4),
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
                            ])
                        ], md=4),
                        dbc.Col([
                            html.H5("Percentages"),
                            html.Div([
                                html.Div([
                                    html.Span("Win %: ", className="fw-bold"),
                                    html.Span(f"{team_stats['win_percentage']:.3f}")
                                ], className="mb-1"),
                            ])
                        ], md=4),
                    ])
                ])
            ], className="mb-4 shadow-sm")


class ProgressiveGameSummary:
    """Progressive loading component for game summaries."""
    
    @staticmethod
    def create_component():
        """Create progressive game summary component."""
        return html.Div([
            # Game selection (immediate)
            html.Div(
                id='game-selection-immediate',
                children=[
                    SkeletonLoader.create_skeleton_card(
                        title_width="40%", 
                        lines=2, 
                        show_header=True
                    )
                ]
            ),
            
            # Game summary (lazy loaded)
            LazyLoader().create_lazy_container(
                'game-summary',
                SkeletonLoader.render_game_summary_skeleton(),
                priority='high'
            ),
            
            # Player performance (lazy loaded with scroll)
            LazyLoader().create_scroll_loader(
                'game-player-performance',
                load_more_callback=None,  # Will be set in callback
                items_per_page=10
            )
        ])


class ProgressiveDataLoader:
    """Handles progressive data loading with caching and prioritization."""
    
    def __init__(self, data_service):
        """Initialize with data service."""
        self.data_service = data_service
        self._cache = {}
        self._loading_queue = []
    
    def queue_data_load(self, data_type, params, priority='medium'):
        """Queue a data loading operation."""
        load_item = {
            'data_type': data_type,
            'params': params,
            'priority': priority,
            'timestamp': time.time()
        }
        
        # Insert based on priority
        if priority == 'high':
            self._loading_queue.insert(0, load_item)
        elif priority == 'medium':
            mid_point = len(self._loading_queue) // 2
            self._loading_queue.insert(mid_point, load_item)
        else:  # low priority
            self._loading_queue.append(load_item)
    
    def process_queue(self, max_items=3):
        """Process items from the loading queue."""
        processed = []
        
        for _ in range(min(max_items, len(self._loading_queue))):
            if not self._loading_queue:
                break
                
            item = self._loading_queue.pop(0)
            
            # Check cache first
            cache_key = f"{item['data_type']}_{hash(str(item['params']))}"
            if cache_key in self._cache:
                processed.append({
                    'item': item,
                    'data': self._cache[cache_key],
                    'from_cache': True
                })
                continue
            
            # Load data
            try:
                data = self._load_data(item['data_type'], item['params'])
                self._cache[cache_key] = data
                processed.append({
                    'item': item,
                    'data': data,
                    'from_cache': False
                })
            except Exception as e:
                processed.append({
                    'item': item,
                    'error': str(e),
                    'from_cache': False
                })
        
        return processed
    
    def _load_data(self, data_type, params):
        """Load data based on type and parameters."""
        if data_type == 'player_stats':
            return self.data_service.calculate_player_stats(**params)
        elif data_type == 'team_stats':
            return self.data_service.calculate_team_stats(**params)
        elif data_type == 'game_summary':
            return self.data_service.get_game_summary(**params)
        elif data_type == 'player_game_log':
            return self.data_service.get_player_game_log(**params)
        else:
            raise ValueError(f"Unknown data type: {data_type}")


def register_progressive_loading_callbacks(app, data_service):
    """Register all progressive loading callbacks."""
    
    # Register individual component callbacks
    ProgressivePlayerStats.register_callbacks(app, data_service)
    ProgressiveTeamAnalytics.register_callbacks(app, data_service)
    
    # Global progressive loading state
    @app.callback(
        Output('global-loading-state', 'data'),
        Input('lazy-load-observer-trigger', 'data'),
        State('global-loading-state', 'data')
    )
    def update_global_loading_state(observer_data, current_state):
        """Update global loading state based on lazy loading activity."""
        if not observer_data:
            return current_state
        
        # Update loading component count
        current_state = current_state or {'components_loading': 0}
        
        if observer_data.get('setup'):
            current_state['setup_complete'] = True
        
        return current_state