"""
Example of how to integrate progressive loading into the hockey stats application.

This example shows how to enhance existing layouts with progressive loading
capabilities including skeleton screens, lazy loading, and progressive data updates.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# Import progressive loading components
from components.progressive_integration import (
    ProgressiveLayoutIntegration, 
    integrate_progressive_loading
)
from components.skeleton_loader import SkeletonLoader
from components.lazy_loader import LazyLoader
from services.progressive_data_service import get_progressive_data_service


def create_enhanced_app_example(original_app, original_data_service):
    """
    Example of how to enhance an existing Dash app with progressive loading.
    
    Args:
        original_app: Existing Dash application
        original_data_service: Existing data service
        
    Returns:
        Enhanced app with progressive loading
    """
    
    # Integrate progressive loading
    enhanced_data_service = integrate_progressive_loading(original_app, original_data_service)
    
    # Example: Enhanced player layout
    def create_enhanced_player_layout(data_service, team_context=None):
        """Enhanced player layout with progressive loading."""
        
        return html.Div([
            # Immediate loading: Navigation and title
            html.Div(id='nav-container'),
            html.H1("Player Statistics", className="text-center mt-4"),
            
            # High priority: Player selection (loads with skeleton first)
            LazyLoader().create_lazy_container(
                'player-selection',
                SkeletonLoader.create_skeleton_card(
                    title_width="40%", 
                    lines=2, 
                    show_header=True
                ),
                priority='high'
            ),
            
            # Medium priority: Player info (loads after selection)
            LazyLoader().create_lazy_container(
                'player-info',
                SkeletonLoader.render_player_stats_skeleton(),
                priority='medium'
            ),
            
            # Low priority: Game log (loads last)
            LazyLoader().create_lazy_container(
                'player-game-log',
                SkeletonLoader.create_skeleton_table(rows=8, columns=6),
                priority='low'
            )
        ])
    
    # Example: Progressive data loading callback
    @original_app.callback(
        dash.dependencies.Output('lazy-content-player-info', 'children'),
        dash.dependencies.Input('lazy-load-trigger-player-info', 'data'),
        dash.dependencies.State('player-dropdown', 'value')
    )
    def load_player_info_progressive(trigger_data, jersey_number):
        """Load player info progressively when triggered."""
        
        if not trigger_data.get('trigger') or not jersey_number:
            return SkeletonLoader.render_player_stats_skeleton()
        
        # Get progressive data service
        progressive_service = get_progressive_data_service()
        
        # Start incremental loading
        progressive_service.load_data_incrementally(
            'player-info',
            'player_stats',
            {
                'jersey_number': jersey_number,
                'team_id': 'current_team'  # Get from session
            },
            chunk_size=50
        )
        
        # Return loading placeholder while data loads
        return SkeletonLoader.render_loading_placeholder(
            message="Loading player statistics..."
        )
    
    return original_app, enhanced_data_service


def example_skeleton_usage():
    """Example of using skeleton components."""
    
    # Basic skeleton card
    skeleton_card = SkeletonLoader.create_skeleton_card(
        title_width="60%",
        lines=3,
        show_header=True
    )
    
    # Player stats skeleton
    player_skeleton = SkeletonLoader.render_player_stats_skeleton()
    
    # Team analytics skeleton
    team_skeleton = SkeletonLoader.render_team_analytics_skeleton()
    
    # Game summary skeleton
    game_skeleton = SkeletonLoader.render_game_summary_skeleton()
    
    return html.Div([
        html.H2("Skeleton Examples"),
        
        html.H3("Basic Card Skeleton"),
        skeleton_card,
        
        html.H3("Player Stats Skeleton"),
        player_skeleton,
        
        html.H3("Team Analytics Skeleton"),
        team_skeleton,
        
        html.H3("Game Summary Skeleton"),
        game_skeleton
    ])


def example_lazy_loading_usage():
    """Example of using lazy loading components."""
    
    lazy_loader = LazyLoader()
    
    # Basic lazy container
    lazy_container = lazy_loader.create_lazy_container(
        'example-component',
        SkeletonLoader.create_skeleton_card(),
        priority='medium'
    )
    
    # Priority loader
    priority_loader = lazy_loader.create_priority_loader(
        high_priority_components=[
            {
                'id': 'critical-data',
                'component': html.Div("Critical data loads immediately")
            }
        ],
        medium_priority_components=[
            {
                'id': 'important-data',
                'skeleton': SkeletonLoader.create_skeleton_card()
            }
        ],
        low_priority_components=[
            {
                'id': 'optional-data',
                'skeleton': SkeletonLoader.create_skeleton_table()
            }
        ]
    )
    
    # Scroll loader
    scroll_loader = lazy_loader.create_scroll_loader(
        'infinite-scroll',
        load_more_callback=None,
        items_per_page=20
    )
    
    return html.Div([
        html.H2("Lazy Loading Examples"),
        
        html.H3("Basic Lazy Container"),
        lazy_container,
        
        html.H3("Priority Loader"),
        priority_loader,
        
        html.H3("Scroll Loader"),
        scroll_loader
    ])


def example_progressive_data_usage(data_service):
    """Example of using progressive data loading."""
    
    # Get progressive data service
    progressive_service = get_progressive_data_service(data_service)
    
    # Example: Subscribe to updates
    def handle_player_update(update_data):
        """Handle player data updates."""
        print(f"Received update: {update_data}")
    
    progressive_service.subscribe_to_updates('player-stats', handle_player_update)
    
    # Example: Load data incrementally
    progressive_service.load_data_incrementally(
        'player-game-log',
        'player_game_log',
        {
            'player_id': 'player_123',
            'team_id': 'team_456'
        },
        chunk_size=25
    )
    
    # Example: Stream live updates
    progressive_service.stream_data_updates(
        'live-stats',
        'team_stats',
        {
            'team_id': 'team_456'
        },
        interval=10.0  # Update every 10 seconds
    )
    
    return html.Div([
        html.H2("Progressive Data Loading"),
        html.P("Check console for update messages"),
        html.Div(id='progressive-data-container')
    ])


# Complete integration example
def integrate_progressive_loading_complete_example():
    """Complete example of integrating progressive loading."""
    
    # Create Dash app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Mock data service (replace with actual data service)
    class MockDataService:
        def get_players(self, team_id=None):
            return []
        
        def calculate_player_stats(self, player_id, team_id, game_type=None):
            return {'games_played': 10, 'goals': 5, 'assists': 3}
    
    data_service = MockDataService()
    
    # Integrate progressive loading
    enhanced_data_service = integrate_progressive_loading(app, data_service)
    
    # Create layout with progressive loading
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        
        # Examples
        example_skeleton_usage(),
        html.Hr(),
        example_lazy_loading_usage(),
        html.Hr(),
        example_progressive_data_usage(enhanced_data_service)
    ])
    
    return app, enhanced_data_service


if __name__ == '__main__':
    # Run the example
    app, enhanced_service = integrate_progressive_loading_complete_example()
    app.run_server(debug=True, port=8051)