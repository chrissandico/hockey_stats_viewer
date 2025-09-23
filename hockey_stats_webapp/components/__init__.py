"""
Components package for the Hockey Stats Web App.

This package contains reusable UI components that can be used across different layouts.
"""

from .period_breakdown import (
    create_period_breakdown_component,
    create_period_breakdown_table_only,
    create_compact_period_breakdown
)

__all__ = [
    'create_period_breakdown_component',
    'create_period_breakdown_table_only', 
    'create_compact_period_breakdown'
]
