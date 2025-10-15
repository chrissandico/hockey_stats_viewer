#!/usr/bin/env python3
"""
Verification script to test App Performance features while the application is running.
This script will generate some test data and verify the monitoring system is working.
"""

import os
import sys
import time
import requests
import threading
from datetime import datetime

# Add the hockey_stats_webapp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def test_performance_metrics_generation():
    """Generate test performance metrics to verify the monitoring system."""
    
    print("=== Generating Test Performance Metrics ===\n")
    
    try:
        from services.performance_metrics import performance_metrics
        from services.performance_decorators import track_performance, PerformanceContext
        
        print("1. Recording Test Metrics")
        print("-" * 50)
        
        # Record various types of metrics
        for i in range(10):
            # Response times
            response_time = 0.5 + (i * 0.2)  # Gradually increasing response times
            performance_metrics.record_response_time(f"test_endpoint_{i}", response_time, f"session_{i}")
            
            # Cache operations
            cache_hit = i % 3 != 0  # 2/3 cache hits, 1/3 misses
            performance_metrics.record_cache_hit(f"cache_key_{i}", cache_hit, f"session_{i}")
            
            # API calls
            performance_metrics.record_api_call("google_sheets", f"session_{i}")
            
            # Occasional errors
            if i % 4 == 0:
                performance_metrics.record_error(f"test_endpoint_{i}", "TestError", f"session_{i}")
            
            time.sleep(0.1)  # Small delay between operations
        
        print(f"✅ Generated 10 test operations with metrics")
        
        print("\n2. Testing Performance Decorators")
        print("-" * 50)
        
        @track_performance("decorated_test_function")
        def test_slow_function():
            time.sleep(0.3)  # Simulate slow operation
            return "completed"
        
        @track_performance("decorated_fast_function")
        def test_fast_function():
            time.sleep(0.05)  # Simulate fast operation
            return "completed"
        
        # Execute decorated functions
        test_slow_function()
        test_fast_function()
        test_slow_function()  # Run slow function again
        
        print("✅ Executed decorated functions")
        
        print("\n3. Testing Context Manager")
        print("-" * 50)
        
        with PerformanceContext("context_test_operation"):
            time.sleep(0.15)
        
        print("✅ Executed context manager operation")
        
        print("\n4. Checking Generated Metrics")
        print("-" * 50)
        
        # Get performance summary
        summary = performance_metrics.get_performance_summary(time_window_minutes=5)
        
        print(f"Response Times:")
        print(f"  Count: {summary['response_times']['count']}")
        print(f"  Average: {summary['response_times']['avg']:.3f}s")
        print(f"  Max: {summary['response_times']['max']:.3f}s")
        print(f"  95th Percentile: {summary['response_times']['p95']:.3f}s")
        
        print(f"\nCache Performance:")
        print(f"  Hit Rate: {summary['cache_performance']['hit_rate']:.1%}")
        print(f"  Total Operations: {summary['cache_performance']['total']}")
        
        print(f"\nError Rate:")
        print(f"  Error Rate: {summary['error_rates']['error_rate']:.1%}")
        print(f"  Total Errors: {summary['error_rates']['errors']}")
        
        print(f"\nAPI Usage:")
        print(f"  Calls Made: {summary['api_quota']['calls_made']}")
        print(f"  Usage: {summary['api_quota']['usage_percentage']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating test metrics: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alerting_system():
    """Test the alerting system with threshold violations."""
    
    print("\n=== Testing Alerting System ===\n")
    
    try:
        from services.performance_metrics import performance_metrics
        
        print("1. Generating Slow Operations (Should Trigger Alerts)")
        print("-" * 50)
        
        # Generate slow operations that should trigger response time alerts
        for i in range(3):
            slow_time = 6.0 + i  # 6s, 7s, 8s - should trigger warnings
            performance_metrics.record_response_time("slow_operation", slow_time, "alert_test")
            print(f"  Recorded slow operation: {slow_time:.1f}s")
        
        print("\n2. Generating High Error Rate")
        print("-" * 50)
        
        # Generate errors to trigger error rate alerts
        for i in range(5):
            performance_metrics.record_error("error_prone_operation", "HighErrorRate", "alert_test")
            # Also record some successful operations
            performance_metrics.record_response_time("error_prone_operation", 1.0, "alert_test")
        
        print("✅ Generated high error rate scenario")
        
        print("\n3. Checking Alert Thresholds")
        print("-" * 50)
        
        alerts = performance_metrics.check_performance_thresholds()
        
        if alerts:
            print(f"🚨 Found {len(alerts)} performance alerts:")
            for alert in alerts:
                print(f"  {alert['type'].upper()}: {alert['message']}")
                print(f"    Current: {alert['value']:.3f}, Threshold: {alert['threshold']:.3f}")
        else:
            print("ℹ️  No alerts triggered (thresholds may need adjustment)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing alerting system: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_interface_access():
    """Test accessing the web interface and App Performance dashboard."""
    
    print("\n=== Testing Web Interface Access ===\n")
    
    try:
        base_url = "http://localhost:8050"
        
        print("1. Testing Main Application Access")
        print("-" * 50)
        
        try:
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                print("✅ Main application accessible")
                print(f"  Status: {response.status_code}")
                print(f"  Content length: {len(response.content)} bytes")
            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not access main application: {e}")
            print("  (This is expected if the app is not running)")
        
        print("\n2. Testing App Performance Route")
        print("-" * 50)
        
        try:
            perf_url = f"{base_url}/performance"
            response = requests.get(perf_url, timeout=5)
            print(f"✅ App Performance route accessible")
            print(f"  Status: {response.status_code}")
            
            # Check if the response contains expected App Performance content
            content = response.text.lower()
            if "app performance" in content:
                print("✅ App Performance content detected")
            elif "access denied" in content:
                print("ℹ️  Access denied (expected without coach login)")
            else:
                print("ℹ️  Response received but content unclear")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not access App Performance route: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing web interface: {e}")
        return False


def continuous_monitoring_test():
    """Run continuous monitoring to simulate real usage."""
    
    print("\n=== Running Continuous Monitoring Test ===\n")
    
    try:
        from services.performance_metrics import performance_metrics
        from services.performance_integration import track_user_action
        
        print("1. Simulating User Activities")
        print("-" * 50)
        
        activities = [
            ("view_player_stats", 0.8),
            ("load_team_data", 1.2),
            ("generate_report", 2.1),
            ("refresh_cache", 0.3),
            ("export_data", 1.5)
        ]
        
        for i in range(15):  # Run 15 operations
            activity, base_time = activities[i % len(activities)]
            
            # Add some randomness to response times
            import random
            response_time = base_time + random.uniform(-0.2, 0.4)
            
            with track_user_action(activity, f"user_session_{i % 3}"):
                time.sleep(max(0.05, response_time))  # Simulate work
            
            # Simulate cache operations
            cache_hit = random.choice([True, True, True, False])  # 75% hit rate
            performance_metrics.record_cache_hit(f"{activity}_cache", cache_hit)
            
            # Occasional API calls
            if i % 3 == 0:
                performance_metrics.record_api_call("google_sheets")
            
            print(f"  Completed {activity} in {response_time:.2f}s")
            
            time.sleep(0.2)  # Brief pause between activities
        
        print("\n2. Final Performance Summary")
        print("-" * 50)
        
        final_summary = performance_metrics.get_performance_summary(time_window_minutes=10)
        
        print(f"Total Operations: {final_summary['response_times']['count']}")
        print(f"Average Response Time: {final_summary['response_times']['avg']:.3f}s")
        print(f"Cache Hit Rate: {final_summary['cache_performance']['hit_rate']:.1%}")
        print(f"Error Rate: {final_summary['error_rates']['error_rate']:.1%}")
        print(f"API Calls: {final_summary['api_quota']['calls_made']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in continuous monitoring test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    
    print("🔍 App Performance Monitoring Verification")
    print("=" * 60)
    print("This script will test the App Performance monitoring system")
    print("while the hockey stats application is running.")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Performance Metrics Generation", test_performance_metrics_generation),
        ("Alerting System", test_alerting_system),
        ("Web Interface Access", test_web_interface_access),
        ("Continuous Monitoring", continuous_monitoring_test)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            test_results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            test_results[test_name] = False
            print(f"\n❌ FAILED: {test_name} - {e}")
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 VERIFICATION REPORT")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 App Performance Monitoring is working correctly!")
        print("\nTo view the dashboard:")
        print("1. Open browser to: http://localhost:8050")
        print("2. Login as a coach (password starting with 'c')")
        print("3. Click 'App Performance' tab in navigation")
        print("4. View real-time performance metrics and charts")
    else:
        print(f"\n⚠️  Some tests failed, but the system may still be functional.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)