"""
Real-time Performance Monitoring Dashboard

Provides a comprehensive dashboard for monitoring application performance,
including response times, error rates, cache performance, and API quota usage.
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any, List

from services.performance_metrics import performance_metrics


def create_performance_dashboard_layout():
    """Create the performance dashboard layout"""
    
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("App Performance Monitoring Dashboard", className="text-center mb-4"),
                html.P("Real-time application performance metrics and monitoring", 
                      className="text-center text-muted mb-4")
            ])
        ]),
        
        # Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Response Time", className="card-title"),
                        html.H2(id="avg-response-time", children="--", className="text-primary"),
                        html.P("Average (last 10 min)", className="card-text text-muted")
                    ])
                ], className="mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Error Rate", className="card-title"),
                        html.H2(id="error-rate", children="--", className="text-danger"),
                        html.P("Errors (last 10 min)", className="card-text text-muted")
                    ])
                ], className="mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Cache Hit Rate", className="card-title"),
                        html.H2(id="cache-hit-rate", children="--", className="text-success"),
                        html.P("Cache efficiency", className="card-text text-muted")
                    ])
                ], className="mb-3")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("API Quota", className="card-title"),
                        html.H2(id="api-quota-usage", children="--", className="text-warning"),
                        html.P("Google Sheets API", className="card-text text-muted")
                    ])
                ], className="mb-3")
            ], width=3)
        ]),
        
        # Charts Row 1
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Response Time Trends"),
                    dbc.CardBody([
                        dcc.Graph(id="response-time-chart")
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Error Rate Over Time"),
                    dbc.CardBody([
                        dcc.Graph(id="error-rate-chart")
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Charts Row 2
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Cache Performance"),
                    dbc.CardBody([
                        dcc.Graph(id="cache-performance-chart")
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("API Usage Monitoring"),
                    dbc.CardBody([
                        dcc.Graph(id="api-usage-chart")
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Performance Alerts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("App Performance Alerts"),
                    dbc.CardBody([
                        html.Div(id="performance-alerts")
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Detailed Metrics Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Detailed App Performance Metrics"),
                    dbc.CardBody([
                        html.Div(id="detailed-metrics-table")
                    ])
                ])
            ])
        ]),
        
        # Auto-refresh interval
        dcc.Interval(
            id='performance-dashboard-interval',
            interval=5*1000,  # Update every 5 seconds
            n_intervals=0
        )
        
    ], fluid=True)


@callback(
    [Output('avg-response-time', 'children'),
     Output('error-rate', 'children'),
     Output('cache-hit-rate', 'children'),
     Output('api-quota-usage', 'children')],
    [Input('performance-dashboard-interval', 'n_intervals')]
)
def update_summary_cards(n_intervals):
    """Update the summary cards with current metrics"""
    
    try:
        # Get performance summary
        summary = performance_metrics.get_performance_summary(time_window_minutes=10)
        
        # Response time
        avg_response_time = summary['response_times']['avg']
        response_time_text = f"{avg_response_time:.2f}s" if avg_response_time > 0 else "--"
        
        # Error rate
        error_rate = summary['error_rates']['error_rate']
        error_rate_text = f"{error_rate:.1%}" if error_rate >= 0 else "--"
        
        # Cache hit rate
        cache_hit_rate = summary['cache_performance']['hit_rate']
        cache_hit_text = f"{cache_hit_rate:.1%}" if cache_hit_rate >= 0 else "--"
        
        # API quota usage
        api_quota = summary['api_quota']['usage_percentage']
        api_quota_text = f"{api_quota:.1f}%"
        
        return response_time_text, error_rate_text, cache_hit_text, api_quota_text
        
    except Exception as e:
        return "--", "--", "--", "--"


@callback(
    Output('response-time-chart', 'figure'),
    [Input('performance-dashboard-interval', 'n_intervals')]
)
def update_response_time_chart(n_intervals):
    """Update response time trend chart"""
    
    try:
        # Get response time data for the last hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # Extract response time metrics
        response_times = []
        timestamps = []
        
        with performance_metrics._lock:
            for metric in performance_metrics._metrics['response_time']:
                if metric.timestamp >= cutoff_time:
                    response_times.append(metric.value)
                    timestamps.append(metric.timestamp)
        
        if not response_times:
            # Empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(
                title="Response Time Trends (Last Hour)",
                xaxis_title="Time",
                yaxis_title="Response Time (seconds)"
            )
            return fig
        
        # Create DataFrame for easier plotting
        df = pd.DataFrame({
            'timestamp': timestamps,
            'response_time': response_times
        })
        
        # Group by 5-minute intervals and calculate average
        df['time_bucket'] = df['timestamp'].dt.floor('5min')
        grouped = df.groupby('time_bucket')['response_time'].agg(['mean', 'max', 'min']).reset_index()
        
        # Create the chart
        fig = go.Figure()
        
        # Add average line
        fig.add_trace(go.Scatter(
            x=grouped['time_bucket'],
            y=grouped['mean'],
            mode='lines+markers',
            name='Average',
            line=dict(color='blue', width=2)
        ))
        
        # Add max/min area
        fig.add_trace(go.Scatter(
            x=grouped['time_bucket'],
            y=grouped['max'],
            mode='lines',
            name='Max',
            line=dict(color='lightblue', width=1),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=grouped['time_bucket'],
            y=grouped['min'],
            mode='lines',
            name='Min-Max Range',
            line=dict(color='lightblue', width=1),
            fill='tonexty',
            fillcolor='rgba(173, 216, 230, 0.3)'
        ))
        
        fig.update_layout(
            title="Response Time Trends (Last Hour)",
            xaxis_title="Time",
            yaxis_title="Response Time (seconds)",
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        # Return empty chart on error
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig


@callback(
    Output('error-rate-chart', 'figure'),
    [Input('performance-dashboard-interval', 'n_intervals')]
)
def update_error_rate_chart(n_intervals):
    """Update error rate chart"""
    
    try:
        # Get error data for the last hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # Extract error metrics
        errors = []
        timestamps = []
        
        with performance_metrics._lock:
            for metric in performance_metrics._metrics['errors']:
                if metric.timestamp >= cutoff_time:
                    errors.append(1)
                    timestamps.append(metric.timestamp)
        
        if not errors:
            # Empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No errors in the last hour",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(
                title="Error Rate (Last Hour)",
                xaxis_title="Time",
                yaxis_title="Errors per 5-minute window"
            )
            return fig
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'error_count': errors
        })
        
        # Group by 5-minute intervals
        df['time_bucket'] = df['timestamp'].dt.floor('5min')
        grouped = df.groupby('time_bucket')['error_count'].sum().reset_index()
        
        # Create bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=grouped['time_bucket'],
            y=grouped['error_count'],
            name='Errors',
            marker_color='red'
        ))
        
        fig.update_layout(
            title="Error Rate (Last Hour)",
            xaxis_title="Time",
            yaxis_title="Errors per 5-minute window"
        )
        
        return fig
        
    except Exception as e:
        # Return empty chart on error
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig


@callback(
    Output('cache-performance-chart', 'figure'),
    [Input('performance-dashboard-interval', 'n_intervals')]
)
def update_cache_performance_chart(n_intervals):
    """Update cache performance pie chart"""
    
    try:
        cache_stats = performance_metrics.get_cache_hit_rate(time_window_minutes=60)
        
        if cache_stats['total'] == 0:
            # Empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No cache activity",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title="Cache Performance (Last Hour)")
            return fig
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['Cache Hits', 'Cache Misses'],
            values=[cache_stats['hits'], cache_stats['misses']],
            hole=0.3,
            marker_colors=['green', 'red']
        )])
        
        fig.update_layout(
            title=f"Cache Performance (Last Hour)<br>Hit Rate: {cache_stats['hit_rate']:.1%}",
            annotations=[dict(text=f"{cache_stats['hit_rate']:.1%}", x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        return fig
        
    except Exception as e:
        # Return empty chart on error
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig


@callback(
    Output('api-usage-chart', 'figure'),
    [Input('performance-dashboard-interval', 'n_intervals')]
)
def update_api_usage_chart(n_intervals):
    """Update API usage gauge chart"""
    
    try:
        api_quota = performance_metrics.get_api_quota_usage()
        
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = api_quota['usage_percentage'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "API Quota Usage"},
            delta = {'reference': 80},  # Warning threshold
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            annotations=[
                dict(
                    text=f"Calls: {api_quota['calls_made']}/{api_quota['quota_limit']}",
                    x=0.5, y=0.1, showarrow=False
                )
            ]
        )
        
        return fig
        
    except Exception as e:
        # Return empty chart on error
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig


@callback(
    Output('performance-alerts', 'children'),
    [Input('performance-dashboard-interval', 'n_intervals')]
)
def update_performance_alerts(n_intervals):
    """Update performance alerts"""
    
    try:
        alerts = performance_metrics.check_performance_thresholds()
        
        if not alerts:
            return dbc.Alert(
                "All performance metrics are within normal thresholds.",
                color="success",
                className="mb-0"
            )
        
        alert_components = []
        for alert in alerts:
            color = "danger" if alert['type'] == 'critical' else "warning"
            
            alert_components.append(
                dbc.Alert([
                    html.H5(f"{alert['type'].title()} Alert", className="alert-heading"),
                    html.P(alert['message']),
                    html.Hr(),
                    html.P(f"Current: {alert['value']:.3f} | Threshold: {alert['threshold']:.3f}", 
                          className="mb-0")
                ], color=color, className="mb-2")
            )
        
        return alert_components
        
    except Exception as e:
        return dbc.Alert(
            f"Error loading alerts: {str(e)}",
            color="danger"
        )


@callback(
    Output('detailed-metrics-table', 'children'),
    [Input('performance-dashboard-interval', 'n_intervals')]
)
def update_detailed_metrics_table(n_intervals):
    """Update detailed metrics table"""
    
    try:
        summary = performance_metrics.get_performance_summary(time_window_minutes=60)
        
        # Create table rows
        table_rows = [
            html.Tr([
                html.Td("Response Time - Average"),
                html.Td(f"{summary['response_times']['avg']:.3f}s"),
                html.Td("Last 60 minutes")
            ]),
            html.Tr([
                html.Td("Response Time - 95th Percentile"),
                html.Td(f"{summary['response_times']['p95']:.3f}s"),
                html.Td("Last 60 minutes")
            ]),
            html.Tr([
                html.Td("Response Time - Maximum"),
                html.Td(f"{summary['response_times']['max']:.3f}s"),
                html.Td("Last 60 minutes")
            ]),
            html.Tr([
                html.Td("Error Rate"),
                html.Td(f"{summary['error_rates']['error_rate']:.2%}"),
                html.Td("Last 60 minutes")
            ]),
            html.Tr([
                html.Td("Cache Hit Rate"),
                html.Td(f"{summary['cache_performance']['hit_rate']:.2%}"),
                html.Td("Last 60 minutes")
            ]),
            html.Tr([
                html.Td("API Quota Usage"),
                html.Td(f"{summary['api_quota']['usage_percentage']:.1f}%"),
                html.Td("Current window")
            ]),
            html.Tr([
                html.Td("Total Requests"),
                html.Td(f"{summary['response_times']['count']}"),
                html.Td("Last 60 minutes")
            ])
        ]
        
        return dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("Metric"),
                    html.Th("Value"),
                    html.Th("Time Window")
                ])
            ]),
            html.Tbody(table_rows)
        ], striped=True, bordered=True, hover=True)
        
    except Exception as e:
        return dbc.Alert(
            f"Error loading detailed metrics: {str(e)}",
            color="danger"
        )