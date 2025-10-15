"""
Lazy loading system for progressive data loading.

This module provides components and utilities for implementing lazy loading
of data and UI components based on user interaction and viewport visibility.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, clientside_callback, ClientsideFunction
import dash_bootstrap_components as dbc
from components.skeleton_loader import SkeletonLoader
import json


class LazyLoader:
    """
    Provides lazy loading functionality for components and data.
    
    Implements intersection observer pattern for scroll-based loading
    and priority-based loading for above-the-fold content.
    """
    
    def __init__(self, app=None):
        """Initialize the lazy loader with optional Dash app."""
        self.app = app
        self._registered_components = {}
        self._priority_queue = []
        
        if app:
            self._register_clientside_callbacks()
    
    def _register_clientside_callbacks(self):
        """Register clientside callbacks for intersection observer."""
        # Intersection Observer callback for lazy loading
        self.app.clientside_callback(
            """
            function(n_intervals) {
                // Initialize intersection observer if not already done
                if (!window.lazyLoadObserver) {
                    window.lazyLoadObserver = new IntersectionObserver(
                        function(entries) {
                            entries.forEach(function(entry) {
                                if (entry.isIntersecting) {
                                    const element = entry.target;
                                    const componentId = element.getAttribute('data-lazy-id');
                                    
                                    if (componentId && !element.classList.contains('lazy-loaded')) {
                                        element.classList.add('lazy-loaded');
                                        
                                        // Trigger loading by updating a hidden store
                                        const store = document.getElementById('lazy-load-trigger-' + componentId);
                                        if (store) {
                                            const currentData = JSON.parse(store.textContent || '{}');
                                            currentData.trigger = Date.now();
                                            store.textContent = JSON.stringify(currentData);
                                            
                                            // Dispatch change event
                                            const event = new Event('change', { bubbles: true });
                                            store.dispatchEvent(event);
                                        }
                                        
                                        // Stop observing this element
                                        window.lazyLoadObserver.unobserve(element);
                                    }
                                }
                            });
                        },
                        {
                            rootMargin: '50px', // Start loading 50px before element is visible
                            threshold: 0.1
                        }
                    );
                }
                
                // Observe all lazy-loadable elements
                const lazyElements = document.querySelectorAll('[data-lazy-id]:not(.lazy-loaded)');
                lazyElements.forEach(function(element) {
                    window.lazyLoadObserver.observe(element);
                });
                
                return window.dash_clientside.no_update;
            }
            """,
            Output('lazy-load-observer-trigger', 'data'),
            Input('lazy-load-interval', 'n_intervals')
        )
    
    def create_lazy_container(self, component_id, skeleton_component, priority="medium"):
        """
        Create a lazy loading container with skeleton placeholder.
        
        Args:
            component_id (str): Unique identifier for the component
            skeleton_component: Skeleton component to show while loading
            priority (str): Loading priority ('high', 'medium', 'low')
        
        Returns:
            html.Div: Lazy loading container
        """
        return html.Div([
            # Hidden store to trigger loading
            dcc.Store(
                id=f'lazy-load-trigger-{component_id}',
                data={'loaded': False, 'priority': priority}
            ),
            
            # Container that will be observed
            html.Div([
                # Initial skeleton content
                html.Div(
                    skeleton_component,
                    id=f'lazy-content-{component_id}',
                    style={'minHeight': '200px'}  # Prevent layout shift
                )
            ],
            id=f'lazy-container-{component_id}',
            **{
                'data-lazy-id': component_id,
                'data-priority': priority
            },
            className='lazy-load-container'
            )
        ])
    
    def create_priority_loader(self, high_priority_components, medium_priority_components=None, low_priority_components=None):
        """
        Create a priority-based loading system.
        
        Args:
            high_priority_components (list): Components to load immediately
            medium_priority_components (list): Components to load after high priority
            low_priority_components (list): Components to load last
        
        Returns:
            html.Div: Priority loading container
        """
        medium_priority_components = medium_priority_components or []
        low_priority_components = low_priority_components or []
        
        return html.Div([
            # Priority queue store
            dcc.Store(
                id='priority-queue-store',
                data={
                    'high': [comp['id'] for comp in high_priority_components],
                    'medium': [comp['id'] for comp in medium_priority_components],
                    'low': [comp['id'] for comp in low_priority_components],
                    'current_priority': 'high',
                    'loaded_count': 0
                }
            ),
            
            # Loading progress indicator
            html.Div(
                id='priority-loading-progress',
                style={'display': 'none'}
            ),
            
            # Component containers
            html.Div([
                # High priority components (load immediately)
                html.Div([
                    comp['component'] for comp in high_priority_components
                ], id='high-priority-container'),
                
                # Medium priority components (load after high)
                html.Div([
                    self.create_lazy_container(
                        comp['id'], 
                        comp.get('skeleton', SkeletonLoader.render_loading_placeholder()),
                        priority='medium'
                    ) for comp in medium_priority_components
                ], id='medium-priority-container'),
                
                # Low priority components (load last)
                html.Div([
                    self.create_lazy_container(
                        comp['id'], 
                        comp.get('skeleton', SkeletonLoader.render_loading_placeholder()),
                        priority='low'
                    ) for comp in low_priority_components
                ], id='low-priority-container')
            ])
        ])
    
    def create_scroll_loader(self, component_id, load_more_callback, items_per_page=10):
        """
        Create a scroll-based infinite loading component.
        
        Args:
            component_id (str): Unique identifier for the component
            load_more_callback: Function to call when more items are needed
            items_per_page (int): Number of items to load per request
        
        Returns:
            html.Div: Scroll loading container
        """
        return html.Div([
            # Content container
            html.Div(
                id=f'scroll-content-{component_id}',
                children=[]
            ),
            
            # Loading trigger (invisible element at bottom)
            html.Div(
                id=f'scroll-trigger-{component_id}',
                **{'data-lazy-id': f'scroll-{component_id}'},
                style={
                    'height': '1px',
                    'width': '100%',
                    'visibility': 'hidden'
                }
            ),
            
            # Loading indicator
            html.Div([
                SkeletonLoader.render_loading_placeholder(
                    message="Loading more items..."
                )
            ],
            id=f'scroll-loading-{component_id}',
            style={'display': 'none'}
            ),
            
            # Store for scroll state
            dcc.Store(
                id=f'scroll-state-{component_id}',
                data={
                    'page': 0,
                    'items_per_page': items_per_page,
                    'has_more': True,
                    'loading': False
                }
            )
        ], className='scroll-loader-container')
    
    def create_conditional_loader(self, component_id, condition_callback, skeleton_component):
        """
        Create a conditional loader that loads based on a condition.
        
        Args:
            component_id (str): Unique identifier for the component
            condition_callback: Function that returns True when component should load
            skeleton_component: Skeleton to show while waiting
        
        Returns:
            html.Div: Conditional loading container
        """
        return html.Div([
            # Condition store
            dcc.Store(
                id=f'condition-store-{component_id}',
                data={'should_load': False, 'checked': False}
            ),
            
            # Content container
            html.Div([
                skeleton_component
            ], id=f'conditional-content-{component_id}')
        ])
    
    @staticmethod
    def create_loading_boundary(children, loading_component=None, error_component=None):
        """
        Create a loading boundary that handles loading and error states.
        
        Args:
            children: Child components to wrap
            loading_component: Component to show while loading
            error_component: Component to show on error
        
        Returns:
            html.Div: Loading boundary container
        """
        if loading_component is None:
            loading_component = SkeletonLoader.render_loading_placeholder()
        
        if error_component is None:
            error_component = dbc.Alert(
                "An error occurred while loading this content.",
                color="warning",
                className="mb-3"
            )
        
        return html.Div([
            # Loading state store
            dcc.Store(
                id='loading-boundary-state',
                data={'loading': True, 'error': False, 'loaded': False}
            ),
            
            # Content container with conditional display
            html.Div(children, id='loading-boundary-content'),
            
            # Loading overlay
            html.Div(
                loading_component,
                id='loading-boundary-loading',
                className='loading-overlay'
            ),
            
            # Error overlay
            html.Div(
                error_component,
                id='loading-boundary-error',
                style={'display': 'none'}
            )
        ], className='loading-boundary')


class ProgressiveLoader:
    """
    Handles progressive loading of data with smooth transitions.
    """
    
    @staticmethod
    def create_progressive_table(table_id, initial_data=None, batch_size=20):
        """
        Create a table that loads data progressively.
        
        Args:
            table_id (str): Unique identifier for the table
            initial_data (list): Initial data to display
            batch_size (int): Number of rows to load per batch
        
        Returns:
            html.Div: Progressive table container
        """
        return html.Div([
            # Table container
            html.Div(
                id=f'progressive-table-{table_id}',
                children=[
                    SkeletonLoader.create_skeleton_table(rows=5, columns=4)
                ] if initial_data is None else []
            ),
            
            # Load more button
            html.Div([
                dbc.Button(
                    "Load More",
                    id=f'load-more-btn-{table_id}',
                    color="outline-primary",
                    className="mt-3",
                    style={'display': 'none'}
                )
            ], className='text-center'),
            
            # Progress store
            dcc.Store(
                id=f'progressive-table-state-{table_id}',
                data={
                    'loaded_rows': 0,
                    'batch_size': batch_size,
                    'total_rows': 0,
                    'loading': False
                }
            )
        ])
    
    @staticmethod
    def create_progressive_stats(stats_id, stat_categories):
        """
        Create stats that load progressively by category.
        
        Args:
            stats_id (str): Unique identifier for the stats
            stat_categories (list): List of stat categories to load
        
        Returns:
            html.Div: Progressive stats container
        """
        return html.Div([
            # Stats container
            html.Div(
                id=f'progressive-stats-{stats_id}',
                children=[
                    SkeletonLoader.create_skeleton_stats_grid()
                ]
            ),
            
            # Loading progress
            html.Div([
                dbc.Progress(
                    id=f'stats-progress-{stats_id}',
                    value=0,
                    striped=True,
                    animated=True,
                    className="mb-3",
                    style={'display': 'none'}
                )
            ]),
            
            # Stats state store
            dcc.Store(
                id=f'progressive-stats-state-{stats_id}',
                data={
                    'categories': stat_categories,
                    'loaded_categories': [],
                    'current_category': 0,
                    'loading': False
                }
            )
        ])


def register_lazy_loading_callbacks(app, data_service):
    """
    Register callbacks for lazy loading functionality.
    
    Args:
        app: Dash application instance
        data_service: Data service for fetching data
    """
    
    # Global lazy loading setup
    @app.callback(
        Output('lazy-load-observer-trigger', 'data', allow_duplicate=True),
        Input('url', 'pathname'),
        prevent_initial_call=True
    )
    def setup_lazy_loading(pathname):
        """Setup lazy loading when page loads."""
        return {'setup': True, 'timestamp': dash.callback_context.triggered[0]['value']}
    
    # Priority loading callback
    @app.callback(
        Output('priority-loading-progress', 'children'),
        Input('priority-queue-store', 'data')
    )
    def update_priority_progress(queue_data):
        """Update priority loading progress."""
        if not queue_data:
            return []
        
        total_components = len(queue_data.get('high', [])) + len(queue_data.get('medium', [])) + len(queue_data.get('low', []))
        loaded_count = queue_data.get('loaded_count', 0)
        
        if total_components == 0:
            return []
        
        progress_percent = (loaded_count / total_components) * 100
        
        return dbc.Progress(
            value=progress_percent,
            striped=True,
            animated=progress_percent < 100,
            className="mb-3"
        )


# Global lazy loading setup components
def create_lazy_loading_setup():
    """Create global lazy loading setup components."""
    return html.Div([
        # Interval for intersection observer setup
        dcc.Interval(
            id='lazy-load-interval',
            interval=1000,  # Check every second
            n_intervals=0,
            max_intervals=1  # Only run once
        ),
        
        # Store for observer trigger
        dcc.Store(id='lazy-load-observer-trigger', data={}),
        
        # Global loading state
        dcc.Store(id='global-loading-state', data={'components_loading': 0})
    ], style={'display': 'none'})