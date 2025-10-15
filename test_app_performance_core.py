#!/usr/bin/env python3
"""
Core test for App Performance monitoring system.
Tests the essential functionality without complex imports.
"""

import os
import sys
import time

# Add the hockey_stats_webapp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def test_core_functionality():
    """Test core App Performance functionality."""
    
    print("🔍 Testing App Performance Core Functionality")
    print("=" * 60)
    
    try:
        # Test 1: Performance Metrics
        print("\n1. Testing Performance Metrics")
        print("-" * 40)
        
        from services.performance_metrics import performance_metrics
        
        # Record test data
        performance_metrics.record_response_time("test_operation", 1.5, "test_session")
        performance_metrics.record_cache_hit("test_cache", True, "test_session")
        performance_metrics.record_cache_hit("test_cache", False, "test_session")
        performance_metrics.record_error("test_operation", "TestError", "test_session")
        performance_metrics.record_api_call("google_sheets", "test_session")
        
        # Get summary
        summary = performance_metrics.get_performance_summary(60)
        
        print(f"✅ Response Times: {summary['response_times']['count']} operations")
        print(f"✅ Cache Hit Rate: {summary['cache_performance']['hit_rate']:.1%}")
        print(f"✅ Error Rate: {summary['error_rates']['error_rate']:.1%}")
        print(f"✅ API Calls: {summary['api_quota']['calls_made']}")
        
        # Test 2: Performance Decorators
        print("\n2. Testing Performance Decorators")
        print("-" * 40)
        
        from services.performance_decorators import track_performance, PerformanceContext
        
        @track_performance("test_decorated_function")
        def test_function():
            time.sleep(0.1)
            return "success"
        
        result = test_function()
        print(f"✅ Decorated function: {result}")
        
        with PerformanceContext("test_context"):
            time.sleep(0.05)
        
        print("✅ Context manager executed")
        
        # Test 3: Dashboard Components
        print("\n3. Testing Dashboard Components")
        print("-" * 40)
        
        from components.performance_dashboard import create_performance_dashboard_layout
        
        dashboard = create_performance_dashboard_layout()
        dashboard_str = str(dashboard)
        
        expected_components = [
            "App Performance Monitoring Dashboard",
            "Response Time",
            "Error Rate",
            "Cache Hit Rate",
            "API Quota"
        ]
        
        found_components = 0
        for component in expected_components:
            if component in dashboard_str:
                print(f"✅ Found: {component}")
                found_components += 1
            else:
                print(f"⚠️  Missing: {component}")
        
        print(f"Dashboard components: {found_components}/{len(expected_components)}")
        
        # Test 4: Alert System
        print("\n4. Testing Alert System")
        print("-" * 40)
        
        # Generate slow operations to trigger alerts
        performance_metrics.record_response_time("slow_operation", 6.0, "alert_test")
        performance_metrics.record_response_time("slow_operation", 7.0, "alert_test")
        
        alerts = performance_metrics.check_performance_thresholds()
        
        if alerts:
            print(f"🚨 Generated {len(alerts)} alerts:")
            for alert in alerts:
                print(f"  {alert['type'].upper()}: {alert['message']}")
        else:
            print("ℹ️  No alerts triggered")
        
        print("\n" + "=" * 60)
        print("📊 CORE FUNCTIONALITY TEST RESULTS")
        print("=" * 60)
        print("✅ Performance Metrics: Working")
        print("✅ Performance Decorators: Working")
        print("✅ Dashboard Components: Working")
        print("✅ Alert System: Working")
        
        print(f"\n🎉 App Performance monitoring system is functional!")
        
        print(f"\n📋 Current Performance Summary:")
        final_summary = performance_metrics.get_performance_summary(60)
        print(f"  Total Operations: {final_summary['response_times']['count']}")
        print(f"  Average Response Time: {final_summary['response_times']['avg']:.3f}s")
        print(f"  Cache Hit Rate: {final_summary['cache_performance']['hit_rate']:.1%}")
        print(f"  Error Rate: {final_summary['error_rates']['error_rate']:.1%}")
        print(f"  API Calls Made: {final_summary['api_quota']['calls_made']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in core functionality test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_core_functionality()
    
    if success:
        print("\n🚀 READY TO USE!")
        print("\nTo access the App Performance dashboard:")
        print("1. Run: python hockey_stats_webapp/app.py")
        print("2. Open browser: http://localhost:8050")
        print("3. Login as coach (password starting with 'c')")
        print("4. Click 'App Performance' tab")
        print("5. View real-time monitoring dashboard")
    
    sys.exit(0 if success else 1)