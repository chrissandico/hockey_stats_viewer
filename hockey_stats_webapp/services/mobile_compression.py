"""
Mobile Data Compression and Optimization Service

This service provides data compression, lightweight data formats, and mobile-specific
optimizations to reduce bandwidth usage and improve performance on mobile devices.
"""

import gzip
import json
import base64
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MobileCompressionService:
    """
    Service for compressing and optimizing data for mobile clients.
    Provides lightweight data formats and response compression.
    """
    
    def __init__(self):
        """Initialize the mobile compression service."""
        self.compression_enabled = True
        self.lightweight_mode = False
        
        # Define field mappings for lightweight mode
        self.lightweight_field_mappings = {
            'players': {
                'essential': ['ID', 'Name', 'JerseyNumber', 'Position'],
                'optional': ['Team', 'Height', 'Weight', 'Birthdate']
            },
            'games': {
                'essential': ['ID', 'Date', 'Opponent', 'HomeAway', 'Result'],
                'optional': ['GameType', 'Location', 'StartTime', 'Notes']
            },
            'events': {
                'essential': ['GameID', 'PlayerID', 'EventType', 'Period', 'Time'],
                'optional': ['Team', 'IsGoal', 'IsPowerPlay', 'IsShortHanded', 'Description']
            },
            'stats': {
                'essential': ['player_id', 'goals', 'assists', 'points', 'games_played'],
                'optional': ['plus_minus', 'penalty_minutes', 'shots', 'shot_percentage']
            }
        }
        
        # Define compression thresholds (in bytes)
        self.compression_threshold = 1024  # Compress responses larger than 1KB
        self.max_response_size = 50 * 1024  # 50KB max response size
    
    def enable_lightweight_mode(self, enabled: bool = True):
        """
        Enable or disable lightweight mode for mobile clients.
        
        Args:
            enabled (bool): Whether to enable lightweight mode
        """
        self.lightweight_mode = enabled
        logger.info(f"Lightweight mode {'enabled' if enabled else 'disabled'}")
    
    def compress_response(self, data: Union[str, bytes, Dict, List]) -> Dict[str, Any]:
        """
        Compress response data for transmission.
        
        Args:
            data: Data to compress (string, bytes, dict, or list)
            
        Returns:
            Dict containing compressed data and metadata
        """
        try:
            # Convert data to JSON string if it's not already a string
            if isinstance(data, (dict, list)):
                json_str = json.dumps(data, separators=(',', ':'))
            elif isinstance(data, bytes):
                json_str = data.decode('utf-8')
            else:
                json_str = str(data)
            
            original_size = len(json_str.encode('utf-8'))
            
            # Only compress if data is larger than threshold
            if original_size < self.compression_threshold:
                return {
                    'data': data,
                    'compressed': False,
                    'original_size': original_size,
                    'compressed_size': original_size,
                    'compression_ratio': 1.0
                }
            
            # Compress the data
            compressed_bytes = gzip.compress(json_str.encode('utf-8'))
            compressed_size = len(compressed_bytes)
            
            # Encode compressed data as base64 for JSON transmission
            compressed_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
            
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
            
            logger.info(f"Compressed data: {original_size} -> {compressed_size} bytes "
                       f"(ratio: {compression_ratio:.2f}x)")
            
            return {
                'data': compressed_b64,
                'compressed': True,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'encoding': 'gzip+base64'
            }
            
        except Exception as e:
            logger.error(f"Error compressing response: {e}")
            # Return uncompressed data on error
            return {
                'data': data,
                'compressed': False,
                'error': str(e)
            }
    
    def decompress_response(self, compressed_response: Dict[str, Any]) -> Any:
        """
        Decompress a compressed response.
        
        Args:
            compressed_response: Compressed response dictionary
            
        Returns:
            Decompressed data
        """
        try:
            if not compressed_response.get('compressed', False):
                return compressed_response['data']
            
            # Decode base64 and decompress
            compressed_b64 = compressed_response['data']
            compressed_bytes = base64.b64decode(compressed_b64)
            decompressed_str = gzip.decompress(compressed_bytes).decode('utf-8')
            
            # Parse JSON if it looks like JSON
            try:
                return json.loads(decompressed_str)
            except json.JSONDecodeError:
                return decompressed_str
                
        except Exception as e:
            logger.error(f"Error decompressing response: {e}")
            return compressed_response.get('data')
    
    def create_lightweight_dataframe(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        Create a lightweight version of a DataFrame for mobile clients.
        
        Args:
            df: Original DataFrame
            data_type: Type of data ('players', 'games', 'events', 'stats')
            
        Returns:
            Lightweight DataFrame with reduced columns
        """
        if not self.lightweight_mode or data_type not in self.lightweight_field_mappings:
            return df
        
        try:
            field_mapping = self.lightweight_field_mappings[data_type]
            essential_fields = field_mapping['essential']
            
            # Get available essential fields
            available_fields = [field for field in essential_fields if field in df.columns]
            
            if not available_fields:
                logger.warning(f"No essential fields found for {data_type}, returning original DataFrame")
                return df
            
            # Create lightweight DataFrame with only essential fields
            lightweight_df = df[available_fields].copy()
            
            logger.info(f"Created lightweight {data_type} DataFrame: "
                       f"{len(df.columns)} -> {len(lightweight_df.columns)} columns")
            
            return lightweight_df
            
        except Exception as e:
            logger.error(f"Error creating lightweight DataFrame for {data_type}: {e}")
            return df
    
    def optimize_player_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize player statistics for mobile transmission.
        
        Args:
            stats: Player statistics dictionary
            
        Returns:
            Optimized statistics dictionary
        """
        if not self.lightweight_mode:
            return stats
        
        try:
            essential_stats = {}
            field_mapping = self.lightweight_field_mappings.get('stats', {})
            essential_fields = field_mapping.get('essential', [])
            
            # Copy essential fields
            for field in essential_fields:
                if field in stats:
                    essential_stats[field] = stats[field]
            
            # Add computed fields that are commonly needed
            if 'goals' in stats and 'assists' in stats:
                essential_stats['points'] = stats.get('goals', 0) + stats.get('assists', 0)
            
            # Round floating point numbers to reduce precision
            for key, value in essential_stats.items():
                if isinstance(value, float):
                    essential_stats[key] = round(value, 3)
            
            logger.debug(f"Optimized player stats: {len(stats)} -> {len(essential_stats)} fields")
            
            return essential_stats
            
        except Exception as e:
            logger.error(f"Error optimizing player stats: {e}")
            return stats
    
    def create_paginated_response(self, data: List[Dict], page: int = 1, 
                                page_size: int = 20) -> Dict[str, Any]:
        """
        Create a paginated response for large datasets.
        
        Args:
            data: List of data items
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Paginated response dictionary
        """
        try:
            total_items = len(data)
            total_pages = (total_items + page_size - 1) // page_size
            
            # Validate page number
            page = max(1, min(page, total_pages)) if total_pages > 0 else 1
            
            # Calculate slice indices
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_items)
            
            # Get page data
            page_data = data[start_idx:end_idx]
            
            return {
                'data': page_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_items': total_items,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_previous': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating paginated response: {e}")
            return {
                'data': data,
                'pagination': {
                    'page': 1,
                    'page_size': len(data),
                    'total_items': len(data),
                    'total_pages': 1,
                    'has_next': False,
                    'has_previous': False
                },
                'error': str(e)
            }
    
    def optimize_image_data(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize image data for mobile clients.
        
        Args:
            image_data: Image data dictionary
            
        Returns:
            Optimized image data
        """
        try:
            optimized = image_data.copy()
            
            # Add lazy loading attributes
            optimized['lazy'] = True
            optimized['loading'] = 'lazy'
            
            # Add responsive image attributes
            if 'src' in optimized:
                # Create placeholder for lazy loading
                optimized['placeholder'] = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PC9zdmc+'
                
                # Add srcset for responsive images if not present
                if 'srcset' not in optimized:
                    base_src = optimized['src']
                    optimized['srcset'] = f"{base_src} 1x"
            
            # Add mobile-optimized dimensions
            if self.lightweight_mode:
                optimized['max_width'] = '100%'
                optimized['height'] = 'auto'
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing image data: {e}")
            return image_data
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """
        Get compression statistics and performance metrics.
        
        Returns:
            Dictionary with compression statistics
        """
        return {
            'compression_enabled': self.compression_enabled,
            'lightweight_mode': self.lightweight_mode,
            'compression_threshold': self.compression_threshold,
            'max_response_size': self.max_response_size,
            'supported_encodings': ['gzip', 'base64'],
            'field_mappings': self.lightweight_field_mappings
        }
    
    def estimate_bandwidth_savings(self, original_size: int, compressed_size: int) -> Dict[str, Any]:
        """
        Estimate bandwidth savings from compression.
        
        Args:
            original_size: Original data size in bytes
            compressed_size: Compressed data size in bytes
            
        Returns:
            Dictionary with bandwidth savings estimates
        """
        try:
            savings_bytes = original_size - compressed_size
            savings_percentage = (savings_bytes / original_size * 100) if original_size > 0 else 0
            
            # Estimate data usage for different connection types
            connection_estimates = {
                '3G': {
                    'original_time': original_size / (1.5 * 1024 * 1024 / 8),  # 1.5 Mbps
                    'compressed_time': compressed_size / (1.5 * 1024 * 1024 / 8)
                },
                '4G': {
                    'original_time': original_size / (10 * 1024 * 1024 / 8),  # 10 Mbps
                    'compressed_time': compressed_size / (10 * 1024 * 1024 / 8)
                },
                'WiFi': {
                    'original_time': original_size / (50 * 1024 * 1024 / 8),  # 50 Mbps
                    'compressed_time': compressed_size / (50 * 1024 * 1024 / 8)
                }
            }
            
            return {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'savings_bytes': savings_bytes,
                'savings_percentage': round(savings_percentage, 2),
                'compression_ratio': round(original_size / compressed_size, 2) if compressed_size > 0 else 1.0,
                'connection_estimates': connection_estimates
            }
            
        except Exception as e:
            logger.error(f"Error estimating bandwidth savings: {e}")
            return {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'error': str(e)
            }