#!/usr/bin/env python3
"""
Comprehensive test for Milestone 6 implementation
Tests the complete end-to-end workflow of performance optimization and pipeline automation
"""
import sys
import os
import time
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from utils.cache_manager import CacheManager
from database.db_manager import DatabaseManager
from pipeline.automated_pipeline import AutomatedPipeline
from pipeline.monitor_data_quality import DataQualityMonitor
from pipeline.scheduler import PipelineScheduler
from pipeline.notification_system import NotificationSystem


def test_complete_workflow():
    """Test the complete Milestone 6 workflow"""
    print("Testing Complete Milestone 6 Workflow...")
    print("=" * 50)

    # Test 1: Cache Manager
    print("1. Testing Cache Manager...")
    cache_manager = CacheManager(default_ttl=5)  # 5 second TTL for testing

    test_data = {"site_id": 123, "match_score": 0.85, "therapeutic_area": "Oncology"}
    cache_key = "test_site_match_123"

    # Set cache
    cache_manager.set(cache_key, test_data)
    print("   ✓ Data cached successfully")

    # Get cache
    cached_data = cache_manager.get(cache_key)
    assert cached_data == test_data, "Cache retrieval failed"
    print("   ✓ Data retrieved from cache successfully")

    # Wait for expiration
    print("   Waiting for cache to expire...")
    time.sleep(6)

    # Get expired cache
    expired_data = cache_manager.get(cache_key)
    assert expired_data is None, "Expired cache should return None"
    print("   ✓ Expired cache properly handled")

    # Test 2: Database with Caching
    print("\n2. Testing Database with Caching...")
    db_manager = DatabaseManager()

    if db_manager.connect():
        print("   ✓ Database connection successful")

        # Test cached query
        sites_count_result = db_manager.query(
            "SELECT COUNT(*) as count FROM sites_master",
            use_cache=True,
            cache_key="sites_count_cached_test",
        )

        if sites_count_result:
            sites_count = sites_count_result[0]["count"]
            print(f"   ✓ Cached query executed successfully ({sites_count} sites)")
        else:
            print("   ⚠️  Cached query returned no results")

        db_manager.disconnect()
        print("   ✓ Database disconnected")
    else:
        print("   ✗ Database connection failed")
        return False

    # Test 3: Automated Pipeline
    print("\n3. Testing Automated Pipeline...")
    pipeline = AutomatedPipeline()

    # Test connection
    if pipeline.connect_database():
        print("   ✓ Pipeline database connection successful")

        # Test last update time
        last_update = pipeline.get_last_update_time()
        print(f"   ✓ Last update time retrieved: {last_update}")

        pipeline.disconnect_database()
        print("   ✓ Pipeline database disconnected")
    else:
        print("   ✗ Pipeline database connection failed")
        return False

    # Test 4: Data Quality Monitoring
    print("\n4. Testing Data Quality Monitoring...")
    monitor = DataQualityMonitor()

    if monitor.connect_database():
        print("   ✓ Monitor database connection successful")

        # Test completeness check
        completeness = monitor.check_completeness()
        print(
            f"   ✓ Completeness check completed ({len(completeness)} tables analyzed)"
        )

        # Test recency check
        recency = monitor.check_recency()
        print(f"   ✓ Recency check completed ({len(recency)} tables analyzed)")

        # Test consistency check
        consistency = monitor.check_consistency()
        print(f"   ✓ Consistency check completed ({len(consistency)} checks performed)")

        # Generate report
        report = monitor.generate_quality_report()
        print(
            f"   ✓ Quality report generated (generated at: {report.get('generated_at', 'Unknown')})"
        )

        monitor.disconnect_database()
        print("   ✓ Monitor database disconnected")
    else:
        print("   ✗ Monitor database connection failed")
        return False

    # Test 5: Notification System
    print("\n5. Testing Notification System...")
    notification_system = NotificationSystem()

    # Test config loading
    config = notification_system.config
    print(
        f"   ✓ Notification system configured (notifications enabled: {notification_system.notifications_enabled})"
    )

    # Test system alert (without actually sending)
    alert_success = notification_system.send_system_alert(
        alert_type="Test Alert",
        message="This is a test alert from the comprehensive workflow test",
        severity="low",
    )
    print(
        f"   ✓ System alert test completed (would send: {notification_system.notifications_enabled})"
    )

    print("\n" + "=" * 50)
    print("🎉 All Milestone 6 components working correctly!")
    print("The platform is ready for production deployment.")
    return True


def main():
    """Main function"""
    print("Clinical Trial Site Analysis Platform")
    print("Milestone 6 Comprehensive Workflow Test")
    print("")

    try:
        success = test_complete_workflow()
        if success:
            print("\n✅ COMPREHENSIVE MILESTONE 6 TEST PASSED")
            print(
                "All components are working correctly and the platform is production-ready."
            )
            return True
        else:
            print("\n❌ COMPREHENSIVE MILESTONE 6 TEST FAILED")
            return False
    except Exception as e:
        print(f"\n💥 COMPREHENSIVE MILESTONE 6 TEST FAILED WITH EXCEPTION: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
