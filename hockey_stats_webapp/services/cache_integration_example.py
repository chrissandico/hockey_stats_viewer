"""
Example integration of the Enhanced Caching System

This script demonstrates how to integrate the new caching components
with the existing hockey stats application.
"""

import logging
from typing import Optional
from .enhanced_sheets_service import EnhancedSheetsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_enhanced_sheets_service(cache_config: Optional[dict] = None) -> EnhancedSheetsService:
    """
    Create an enhanced sheets service with optimized cache configuration.
    
    Args:
        cache_config: Optional cache configuration overrides
        
    Returns:
        Configured EnhancedSheetsService instance
    """
    
    # Default optimized configuration for hockey stats app
    default_config = {
        'l1_size_mb': 25,      # Increased L1 for frequently accessed data
        'l2_size_mb': 60,      # Larger L2 for session data
        'l3_size_mb': 120,     # Larger L3 for persistent storage
        'smart_cache_size_mb': 40,  # Smart cache for dependency tracking
        'background_workers': 4,     # More workers for better performance
        'enable_background_refresh': True
    }
    
    # Merge with provided config
    if cache_config:
        default_config.update(cache_config)
    
    try:
        service = EnhancedSheetsService(cache_config=default_config)
        logger.info("Enhanced sheets service created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create enhanced sheets service: {e}")
        raise


def migrate_from_legacy_service(legacy_service, enhanced_service: EnhancedSheetsService):
    """
    Migrate data from legacy SheetsService to EnhancedSheetsService.
    
    Args:
        legacy_service: Existing SheetsService instance
        enhanced_service: New EnhancedSheetsService instance
    """
    
    logger.info("Starting migration from legacy service")
    
    try:
        # Warm the enhanced cache with existing data if available
        if hasattr(legacy_service, 'cache') and legacy_service.cache:
            logger.info("Warming enhanced cache with legacy data")
            
            for key, data in legacy_service.cache.items():
                if data is not None:
                    # Store in enhanced cache with appropriate priority
                    priority = 1 if key in ['players', 'games', 'events'] else 2
                    enhanced_service.multi_level_cache.set(key, data, priority=priority)
                    enhanced_service.smart_cache.set(key, data)
            
            logger.info(f"Migrated {len(legacy_service.cache)} cache entries")
        
        # Perform initial data refresh to ensure consistency
        enhanced_service.refresh_all_data()
        
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise


def get_cache_performance_report(service: EnhancedSheetsService) -> dict:
    """
    Generate a comprehensive cache performance report.
    
    Args:
        service: EnhancedSheetsService instance
        
    Returns:
        Dictionary with performance metrics and recommendations
    """
    
    stats = service.get_comprehensive_stats()
    
    # Calculate performance metrics
    performance = stats['performance']
    hit_rate = performance['cache_hit_rate_percent']
    avg_response_time = performance['avg_response_time_ms']
    
    # Generate recommendations
    recommendations = []
    
    if hit_rate < 70:
        recommendations.append("Cache hit rate is low. Consider increasing cache sizes or adjusting TTL values.")
    
    if avg_response_time > 500:
        recommendations.append("Average response time is high. Consider optimizing data fetching or increasing L1 cache size.")
    
    if stats['multi_level_cache']['overall']['promotions'] < stats['multi_level_cache']['overall']['total_requests'] * 0.1:
        recommendations.append("Low cache promotion rate. Data access patterns may benefit from cache warming.")
    
    # Memory usage warnings
    for level in ['l1', 'l2']:
        if level in stats['multi_level_cache'] and stats['multi_level_cache'][level]['usage_percent'] > 90:
            recommendations.append(f"Cache level {level.upper()} is near capacity. Consider increasing size.")
    
    return {
        'summary': {
            'cache_hit_rate_percent': hit_rate,
            'avg_response_time_ms': avg_response_time,
            'total_requests': performance['total_requests'],
            'api_calls_saved': performance['cache_hits']
        },
        'detailed_stats': stats,
        'recommendations': recommendations,
        'health_status': 'good' if hit_rate > 80 and avg_response_time < 300 else 'needs_attention'
    }


# Example usage and integration patterns
if __name__ == "__main__":
    
    # Example 1: Basic setup
    logger.info("Example 1: Basic enhanced service setup")
    
    try:
        service = create_enhanced_sheets_service()
        
        # Test basic functionality
        players = service.get_players()
        games = service.get_games()
        
        logger.info(f"Loaded {len(players)} players and {len(games)} games")
        
        # Get performance stats
        stats = service.get_comprehensive_stats()
        logger.info(f"Cache hit rate: {stats['performance']['cache_hit_rate_percent']:.1f}%")
        
    except Exception as e:
        logger.error(f"Example 1 failed: {e}")
    
    # Example 2: Custom cache configuration
    logger.info("Example 2: Custom cache configuration")
    
    try:
        custom_config = {
            'l1_size_mb': 30,
            'l2_size_mb': 80,
            'l3_size_mb': 150,
            'background_workers': 6
        }
        
        service = create_enhanced_sheets_service(custom_config)
        
        # Warm cache proactively
        service.smart_cache.warm_cache(['players', 'games'])
        
        logger.info("Custom configuration applied successfully")
        
    except Exception as e:
        logger.error(f"Example 2 failed: {e}")
    
    # Example 3: Performance monitoring
    logger.info("Example 3: Performance monitoring")
    
    try:
        service = create_enhanced_sheets_service()
        
        # Simulate some usage
        for i in range(10):
            players = service.get_players()
            games = service.get_games()
        
        # Generate performance report
        report = get_cache_performance_report(service)
        
        logger.info(f"Performance Report:")
        logger.info(f"  Health Status: {report['health_status']}")
        logger.info(f"  Cache Hit Rate: {report['summary']['cache_hit_rate_percent']:.1f}%")
        logger.info(f"  Avg Response Time: {report['summary']['avg_response_time_ms']:.1f}ms")
        logger.info(f"  API Calls Saved: {report['summary']['api_calls_saved']}")
        
        if report['recommendations']:
            logger.info("Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"  - {rec}")
        
    except Exception as e:
        logger.error(f"Example 3 failed: {e}")