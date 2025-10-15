"""
Integration components for progressive loading system.

This module provides integration between skeleton screens, lazy loading,
and progressive data updates for the hockey stats application.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, clientside_callback
import dash_bootstrap_components as dbc
from components.skeleton_loader import SkeletonLoader
from components.lazy_loader import LazyLoader, create_lazy_loading_setup
from components.progressive_components import ProgressivePlayerStats, ProgressiveTeamAnalytics
from services.progressive_data_service import get_progressive_data_service, TransitionManager
import json
import time


class ProgressiveLayoutIntegration:
    """
    Integrates progressive loading into existing layouts.
    
    Provides drop-in replacements for existing layout components
    that include skeleton screens, lazy loading, and progressive updates.
    """
    
    @staticmethod
    def enhance_player_layout(original_layout_func):
        """
        Enhance player layout with progressive loading.
        
        Args:
            original_layout_func: Original player layout function
            
        Returns:
            Enhanced layout function with progressive loading
        """
        def enhanced_layout(data_service, team_context=None):
            # Create progressive version
            return html.Div([
                # Global lazy loading setup
                create_lazy_loading_setup(),
                
                # Navigation (loads immediately)
                html.Div(id='nav-immediate'),
                
                # Title (loads immediately)
                html.H1("Player Statistics", className="text-center mt-4"),
                
                # Game type filter (loads immediately)
                html.Div(id='game-type-filter-immediate'),
                
                # Progressive player content
                ProgressivePlayerStats.create_component(),
                
                # Transition styles
                html.Style("""
                    .lazy-load-container {
                        transition: opacity 0.3s ease-in-out;
                    }
                    
                    .lazy-load-container.loading {
                        opacity: 0.7;
                    }
                    
                    .skeleton-to-content {
                        animation: skeletonFadeOut 0.3s ease-out;
                    }
                    
                    @keyframes skeletonFadeOut {
                        from { opacity: 1; }
                        to { opacity: 0; }
                    }
                    
                    .content-fade-in {
                        animation: contentFadeIn 0.5s ease-in;
                    }
                    
                    @keyframes contentFadeIn {
                        from { opacity: 0; transform: translateY(10px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                """)
            ])
        
        return enhanced_layout
    
    @staticmethod
    def enhance_team_layout(original_layout_func):
        """
        Enhance team layout with progressive loading.
        
        Args:
            original_layout_func: Original team layout function
            
        Returns:
            Enhanced layout function with progressive loading
        """
        def enhanced_layout(data_service, team_context=None):
            return html.Div([
                # Global lazy loading setup
                create_lazy_loading_setup(),
                
                # Navigation (loads immediately)
                html.Div(id='nav-immediate'),
                
                # Title (loads immediately)
                html.H1("Team Statistics", className="text-center mt-4"),
                
                # Game type filter (loads immediately)
                html.Div(id='game-type-filter-immediate'),
                
                # Progressive team content
                ProgressiveTeamAnalytics.create_component(),
                
                # Loading progress indicator
                html.Div([
                    dbc.Progress(
                        id='team-loading-progress',
                        value=0,
                        striped=True,
                        animated=True,
                        style={'display': 'none'},
                        className="mb-3"
                    )
                ])
            ])
        
        return enhanced_layout
    
    @staticmethod
    def enhance_game_layout(original_layout_func):
        """
        Enhance game layout with progressive loading.
        
        Args:
            original_layout_func: Original game layout function
            
        Returns:
            Enhanced layout function with progressive loading
        """
        def enhanced_layout(data_service, team_context=None):
            return html.Div([
                # Global lazy loading setup
                create_lazy_loading_setup(),
                
                # Navigation (loads immediately)
                html.Div(id='nav-immediate'),
                
                # Title (loads immediately)
                html.H1("Game Statistics", className="text-center mt-4"),
                
                # Game type filter (loads immediately)
                html.Div(id='game-type-filter-immediate'),
                
                # Game selection (loads immediately with skeleton)
                html.Div([
                    dbc.Card([
                        dbc.CardHeader([
                            SkeletonLoader.create_skeleton_line(
                                width="120px", 
                                height="1.5rem", 
                                margin_bottom="0"
                            )
                        ]),
                        dbc.CardBody([
                            SkeletonLoader.create_skeleton_line(width="200px"),
                            html.Div([
                                *[SkeletonLoader.create_skeleton_line(
                                    width="100%", 
                                    height="1.2rem"
                                ) for _ in range(3)]
                            ])
                        ])
                    ], className="mb-4 shadow-sm")
                ], id='game-selection-container'),
                
                # Progressive game content
                LazyLoader().create_lazy_container(
                    'game-summary-progressive',
                    SkeletonLoader.render_game_summary_skeleton(),
                    priority='high'
                ),
                
                # Player performance with scroll loading
                LazyLoader().create_scroll_loader(
                    'game-player-performance',
                    load_more_callback=None,
                    items_per_page=10
                )
            ])
        
        return enhanced_layout


class ProgressiveCallbackIntegration:
    """
    Integrates progressive loading callbacks with existing callback system.
    """
    
    @staticmethod
    def register_enhanced_callbacks(app, data_service):
        """Register all enhanced callbacks for progressive loading."""
        
        # Initialize progressive data service
        progressive_service = get_progressive_data_service(data_service)
        
        # Register component-specific callbacks
        ProgressivePlayerStats.register_callbacks(app, data_service)
        ProgressiveTeamAnalytics.register_callbacks(app, data_service)
        
        # Global loading state management
        @app.callback(
            Output('team-loading-progress', 'style'),
            Output('team-loading-progress', 'value'),
            Input('lazy-load-observer-trigger', 'data'),
            State('priority-queue-store', 'data')
        )
        def update_team_loading_progress(observer_data, queue_data):
            """Update team loading progress indicator."""
            if not queue_data:
                return {'display': 'none'}, 0
            
            total_components = (
                len(queue_data.get('high', [])) + 
                len(queue_data.get('medium', [])) + 
                len(queue_data.get('low', []))
            )
            loaded_count = queue_data.get('loaded_count', 0)
            
            if total_components == 0 or loaded_count >= total_components:
                return {'display': 'none'}, 100
            
            progress = (loaded_count / total_components) * 100
            return {'display': 'block'}, progress
        
        # Immediate content loading callbacks
        @app.callback(
            Output('nav-immediate', 'children'),
            Input('url', 'pathname')
        )
        def load_navigation_immediate(pathname):
            """Load navigation immediately."""
            from layouts.navigation import create_navigation
            return create_navigation()
        
        @app.callback(
            Output('game-type-filter-immediate', 'children'),
            Input('url', 'pathname')
        )
        def load_game_type_filter_immediate(pathname):
            """Load game type filter immediately."""
            from components.game_type_filter import create_game_type_filter_component, create_game_type_session_store
            return html.Div([
                create_game_type_filter_component(),
                create_game_type_session_store()
            ])
        
        # Enhanced game selection callback with progressive loading
        @app.callback(
            Output('game-selection-container', 'children'),
            Input('game-type-session-store', 'data'),
            prevent_initial_call=True
        )
        def load_game_selection_progressive(game_type_data):
            """Load game selection with progressive enhancement."""
            
            # Start with skeleton
            skeleton_content = dbc.Card([
                dbc.CardHeader([
                    SkeletonLoader.create_skeleton_line(
                        width="120px", 
                        height="1.5rem", 
                        margin_bottom="0"
                    )
                ]),
                dbc.CardBody([
                    SkeletonLoader.create_skeleton_line(width="200px"),
                    html.Div([
                        *[SkeletonLoader.create_skeleton_line(
                            width="100%", 
                            height="1.2rem"
                        ) for _ in range(3)]
                    ])
                ])
            ], className="mb-4 shadow-sm")
            
            # Queue actual content loading
            progressive_service.queue_data_update({
                'update_id': 'game_selection',
                'data_type': 'game_selection',
                'data': game_type_data,
                'priority': 1
            })
            
            return skeleton_content
        
        # Clientside callback for smooth transitions
        app.clientside_callback(
            """
            function(trigger_data) {
                // Handle smooth transitions between skeleton and content
                const containers = document.querySelectorAll('.lazy-load-container');
                
                containers.forEach(function(container) {
                    const skeletonElements = container.querySelectorAll('.skeleton');
                    const contentElements = container.querySelectorAll('.content-fade-in');
                    
                    if (skeletonElements.length > 0 && contentElements.length > 0) {
                        // Fade out skeleton
                        skeletonElements.forEach(function(skeleton) {
                            skeleton.classList.add('skeleton-to-content');
                        });
                        
                        // Fade in content after delay
                        setTimeout(function() {
                            skeletonElements.forEach(function(skeleton) {
                                skeleton.style.display = 'none';
                            });
                            
                            contentElements.forEach(function(content) {
                                content.style.display = 'block';
                                content.classList.add('content-fade-in');
                            });
                        }, 300);
                    }
                });
                
                return window.dash_clientside.no_update;
            }
            """,
            Output('lazy-load-observer-trigger', 'data', allow_duplicate=True),
            Input('lazy-load-observer-trigger', 'data'),
            prevent_initial_call=True
        )


class ProgressiveDataIntegration:
    """
    Integrates progressive data loading with existing data service.
    """
    
    @staticmethod
    def create_enhanced_data_service(original_data_service):
        """
        Create enhanced data service with progressive loading capabilities.
        
        Args:
            original_data_service: Original data service instance
            
        Returns:
            Enhanced data service with progressive loading
        """
        
        class EnhancedDataService:
            """Enhanced data service wrapper."""
            
            def __init__(self, base_service):
                self.base_service = base_service
                self.progressive_service = get_progressive_data_service(base_service)
            
            def __getattr__(self, name):
                """Delegate to base service for unknown attributes."""
                return getattr(self.base_service, name)
            
            def get_player_stats_progressive(self, player_id, team_id, game_type=None, component_id=None):
                """Get player stats with progressive loading."""
                if component_id:
                    # Load incrementally
                    self.progressive_service.load_data_incrementally(
                        component_id,
                        'player_stats',
                        {
                            'player_id': player_id,
                            'team_id': team_id,
                            'game_type': game_type
                        }
                    )
                    return None  # Data will be delivered via callbacks
                else:
                    # Load normally
                    return self.base_service.calculate_player_stats(player_id, team_id, game_type)
            
            def get_team_stats_progressive(self, team_id, game_type=None, component_id=None):
                """Get team stats with progressive loading."""
                if component_id:
                    # Load incrementally
                    self.progressive_service.load_data_incrementally(
                        component_id,
                        'team_stats',
                        {
                            'team_id': team_id,
                            'game_type': game_type
                        }
                    )
                    return None  # Data will be delivered via callbacks
                else:
                    # Load normally
                    return self.base_service.calculate_team_stats(team_id, game_type)
            
            def stream_live_updates(self, component_id, data_type, params, interval=5.0):
                """Stream live data updates to a component."""
                self.progressive_service.stream_data_updates(
                    component_id, data_type, params, interval
                )
        
        return EnhancedDataService(original_data_service)


def integrate_progressive_loading(app, data_service):
    """
    Main integration function to add progressive loading to the application.
    
    Args:
        app: Dash application instance
        data_service: Original data service
        
    Returns:
        Enhanced data service with progressive loading capabilities
    """
    
    # Create enhanced data service
    enhanced_data_service = ProgressiveDataIntegration.create_enhanced_data_service(data_service)
    
    # Register enhanced callbacks
    ProgressiveCallbackIntegration.register_enhanced_callbacks(app, enhanced_data_service)
    
    # Add global CSS for progressive loading
    app.index_string = app.index_string.replace(
        '</head>',
        '''
        <style>
            /* Progressive Loading Animations */
            .progressive-fade-in {
                animation: progressiveFadeIn 0.5s ease-in-out;
            }
            
            @keyframes progressiveFadeIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .progressive-slide-up {
                animation: progressiveSlideUp 0.4s ease-out;
            }
            
            @keyframes progressiveSlideUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .loading-shimmer {
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: shimmer 1.5s infinite;
            }
            
            @keyframes shimmer {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }
        </style>
        </head>'''
    )
    
    return enhanced_data_service