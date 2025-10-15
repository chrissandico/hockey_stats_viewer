"""
Test script for the Enhanced Caching System

This script tests the core functionality of the enhanced caching components
to ensure they work correctly together.
"""

import sys
import os
import time
import pandas as pd
from datetime import datetime, timedelta

# Add the hockey_stats_webapp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

try:
    from services.smart_cache_manager import SmartCacheManager, CacheEntry
    from services.multi_level_cache import MultiLevelCache
    from services.background_cache_refresh import BackgroundCacheRefresh
    print("✓ Successfully imported all caching components")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_smart_cache_manager():
    """Test SmartCacheManager functionality."""
    print("\n=== Testing SmartCacheManager ===")
    
    try:
        # Initialize cache manager
        cache = SmartCacheManager(max_memory_mb=10, default_ttl=60)
        
        # Test basic set/get operations
        test_data = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
        
        success = cache.set('test_data', test_data, dependencies={'players'})
        assert success, "Failed to set cache entry"
        print("✓ Cache set operation successful")
        
        retrieved_data = cache.get('test_data')
        assert retrieved_data is not None, "Failed to retrieve cache entry"
        assert len(retrieved_data) == 3, "Retrieved data has incorrect length"
        print("✓ Cache get operation successful")
        
        # Test cache invalidation
        cache.invalidate_by_dependency('players')
        invalidated_data = cache.get('test_data')
        assert invalidated_data is None, "Cache entry should be invalidated"
        print("✓ Cache invalidation successful")
        
        # Test cache statistics
        stats = cache.get_stats()
        assert 'entries' in stats, "Stats missing entries count"
        assert 'hit_rate_percent' in stats, "Stats missing hit rate"
        print("✓ Cache statistics working")
        
        print("✓ SmartCacheManager tests passed")
        return True
        
    except Exception as e:
        print(f"✗ SmartCacheManager test failed: {e}")
        return False


def test_multi_level_cache():
    """Test MultiLevelCache functionality."""
    print("\n=== Testing MultiLevelCache ===")
    
    try:
        # Initialize multi-level cache
        cache = MultiLevelCache(l1_size_mb=5, l2_size_mb=10, l3_size_mb=15)
        
        # Test data storage and retrieval
        test_data = pd.DataFrame({'id': [1, 2], 'value': ['X', 'Y']})
        
        # Store in L1 (high priority)
        success = cache.set('l1_data', test_data, priority=1)
        assert success, "Failed to store in L1 cache"
        print("✓ L1 cache storage successful")
        
        # Retrieve from cache
        retrieved = cache.get('l1_data')
        assert retrieved is not None, "Failed to retrieve from cache"
        assert len(retrieved) == 2, "Retrieved data incorrect"
        print("✓ Multi-level cache retrieval successful")
        
        # Test cache level statistics
        stats = cache.get_comprehensive_stats()
        assert 'overall' in stats, "Missing overall stats"
        assert 'l1' in stats, "Missing L1 stats"
        assert 'l2' in stats, "Missing L2 stats"
        print("✓ Multi-level cache statistics working")
        
        # Test cache invalidation
        cache.invalidate('l1_data')
        invalidated = cache.get('l1_data')
        assert invalidated is None, "Cache entry should be invalidated"
        print("✓ Multi-level cache invalidation successful")
        
        print("✓ MultiLevelCache tests passed")
        return True
        
    except Exception as e:
        print(f"✗ MultiLevelCache test failed: {e}")
        return False


def test_background_cache_refresh():
    """Test BackgroundCacheRefresh functionality."""
    print("\n=== Testing BackgroundCacheRefresh ===")
    
    try:
        # Initialize background refresh
        refresh_manager = BackgroundCacheRefresh(max_workers=2, refresh_interval=5)
        
        # Test data for refresh function
        refresh_call_count = 0
        
        def mock_refresh_function():
            nonlocal refresh_call_count
            refresh_call_count += 1
            return pd.DataFrame({'id': [refresh_call_count], 'timestamp': [datetime.now()]})
        
        # Register refresh task
        success = refresh_manager.register_refresh_task(
            'test_refresh', 
            mock_refresh_function, 
            priority=1, 
            refresh_interval=2
        )
        assert success, "Failed to register refresh task"
        print("✓ Refresh task registration successful")
        
        # Test access pattern recording
        refresh_manager.record_cache_access('test_refresh')
        refresh_manager.record_cache_access('test_refresh')
        print("✓ Access pattern recording successful")
        
        # Test manual refresh
        refresh_manager.force_refresh_all()
        assert refresh_call_count > 0, "Refresh function should have been called"
        print("✓ Manual refresh successful")
        
        # Test statistics
        stats = refresh_manager.get_refresh_stats()
        assert 'tasks' in stats, "Missing task stats"
        assert 'refreshes' in stats, "Missing refresh stats"
        print("✓ Background refresh statistics working")
        
        # Cleanup
        refresh_manager.unregister_refresh_task('test_refresh')
        print("✓ Task unregistration successful")
        
        print("✓ BackgroundCacheRefresh tests passed")
        return True
        
    except Exception as e:
        print(f"✗ BackgroundCacheRefresh test failed: {e}")
        return False


def test_cache_integration():
    """Test integration between all caching components."""
    print("\n=== Testing Cache Integration ===")
    
    try:
        # Initialize all components
        smart_cache = SmartCacheManager(max_memory_mb=5)
        multi_cache = MultiLevelCache(l1_size_mb=3, l2_size_mb=5, l3_size_mb=8)
        
        refresh_call_count = 0
        
        def refresh_function():
            nonlocal refresh_call_count
            refresh_call_count += 1
            return pd.DataFrame({'refresh_id': [refresh_call_count], 'data': [f'refresh_{refresh_call_count}']})
        
        background_refresh = BackgroundCacheRefresh(max_workers=1)
        background_refresh.register_refresh_task('integration_test', refresh_function)
        
        # Test data flow between components
        test_data = pd.DataFrame({'integration': [1, 2, 3]})
        
        # Store in smart cache
        smart_cache.set('integration_data', test_data)
        
        # Retrieve and store in multi-level cache
        retrieved = smart_cache.get('integration_data')
        multi_cache.set('integration_data', retrieved, priority=1)
        
        # Verify data consistency
        ml_retrieved = multi_cache.get('integration_data')
        assert ml_retrieved is not None, "Data not found in multi-level cache"
        assert len(ml_retrieved) == 3, "Data integrity issue"
        print("✓ Cache integration data flow successful")
        
        # Test coordinated invalidation
        smart_cache.invalidate('integration_data')
        multi_cache.invalidate('integration_data')
        
        assert smart_cache.get('integration_data') is None, "Smart cache not invalidated"
        assert multi_cache.get('integration_data') is None, "Multi-level cache not invalidated"
        print("✓ Coordinated cache invalidation successful")
        
        print("✓ Cache integration tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Cache integration test failed: {e}")
        return False


def run_performance_benchmark():
    """Run a simple performance benchmark."""
    print("\n=== Performance Benchmark ===")
    
    try:
        cache = MultiLevelCache(l1_size_mb=10, l2_size_mb=20, l3_size_mb=30)
        
        # Generate test data
        test_data = pd.DataFrame({
            'id': range(1000),
            'value': [f'value_{i}' for i in range(1000)]
        })
        
        # Benchmark cache operations
        start_time = time.time()
        
        # Store data
        for i in range(10):
            cache.set(f'benchmark_data_{i}', test_data, priority=1)
        
        store_time = time.time() - start_time
        
        # Retrieve data
        start_time = time.time()
        
        for i in range(10):
            retrieved = cache.get(f'benchmark_data_{i}')
            assert retrieved is not None, f"Failed to retrieve benchmark_data_{i}"
        
        retrieve_time = time.time() - start_time
        
        print(f"✓ Performance Benchmark Results:")
        print(f"  Store 10 datasets: {store_time:.3f}s ({store_time/10:.3f}s per operation)")
        print(f"  Retrieve 10 datasets: {retrieve_time:.3f}s ({retrieve_time/10:.3f}s per operation)")
        
        # Cache statistics
        stats = cache.get_comprehensive_stats()
        print(f"  Cache hit rate: {stats['overall']['hit_rate_percent']:.1f}%")
        print(f"  L1 usage: {stats['l1']['usage_percent']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance benchmark failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Enhanced Caching System Test Suite")
    print("=" * 50)
    
    tests = [
        test_smart_cache_manager,
        test_multi_level_cache,
        test_background_cache_refresh,
        test_cache_integration,
        run_performance_benchmark
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced caching system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)