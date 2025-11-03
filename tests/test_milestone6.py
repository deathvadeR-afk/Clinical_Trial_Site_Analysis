#!/usr/bin/env python3
"""
Test script for Milestone 6 components
Tests performance optimization, pipeline automation, and monitoring features
"""
import sys
import os
import json
import tempfile

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from utils.cache_manager import CacheManager
from database.db_manager import DatabaseManager
from pipeline.automated_pipeline import AutomatedPipeline
from pipeline.monitor_data_quality import DataQualityMonitor
from pipeline.notification_system import NotificationSystem

def test_cache_manager():
    """Test the cache manager functionality"""
    print("Testing Cache Manager...")
    
    # Create cache manager
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_manager = CacheManager(cache_dir=temp_dir, default_ttl=10)
        
        # Test set and get
        test_data = {"name": "Test Site", "score": 0.85}
        cache_manager.set("test_key", test_data)
        
        retrieved_data = cache_manager.get("test_key")
        assert retrieved_data == test_data, f"Expected {test_data}, got {retrieved_data}"
        
        # Test delete
        cache_manager.delete("test_key")
        deleted_data = cache_manager.get("test_key")
        assert deleted_data is None, f"Expected None, got {deleted_data}"
        
        print("✓ Cache Manager tests passed")
        return True

def test_database_caching():
    """Test database caching functionality"""
    print("Testing Database Caching...")
    
    # Create database manager
    db_manager = DatabaseManager()
    
    # Test connection
    assert db_manager.connect(), "Failed to connect to database"
    
    # Test cached query
    result1 = db_manager.query("SELECT COUNT(*) as count FROM sites_master", use_cache=True, cache_key="site_count_test")
    assert len(result1) > 0, "Failed to execute cached query"
    
    # Test cache hit
    result2 = db_manager.query("SELECT COUNT(*) as count FROM sites_master", use_cache=True, cache_key="site_count_test")
    assert result1 == result2, "Cache hit failed"
    
    db_manager.disconnect()
    print("✓ Database Caching tests passed")
    return True

def test_automated_pipeline():
    """Test automated pipeline functionality"""
    print("Testing Automated Pipeline...")
    
    # Create pipeline
    pipeline = AutomatedPipeline()
    
    # Test connection
    assert pipeline.connect_database(), "Failed to connect to database"
    
    # Test last update time retrieval
    last_update = pipeline.get_last_update_time()
    # This should not raise an exception
    
    pipeline.disconnect_database()
    print("✓ Automated Pipeline tests passed")
    return True

def test_data_quality_monitoring():
    """Test data quality monitoring functionality"""
    print("Testing Data Quality Monitoring...")
    
    # Create monitor
    monitor = DataQualityMonitor()
    
    # Test connection
    assert monitor.connect_database(), "Failed to connect to database"
    
    # Test completeness check
    completeness = monitor.check_completeness()
    assert isinstance(completeness, dict), "Completeness check should return a dictionary"
    
    # Test recency check
    recency = monitor.check_recency()
    assert isinstance(recency, dict), "Recency check should return a dictionary"
    
    # Test consistency check
    consistency = monitor.check_consistency()
    assert isinstance(consistency, dict), "Consistency check should return a dictionary"
    
    # Test report generation
    report = monitor.generate_quality_report()
    assert isinstance(report, dict), "Quality report should be a dictionary"
    assert 'generated_at' in report, "Report should have generated_at field"
    
    monitor.disconnect_database()
    print("✓ Data Quality Monitoring tests passed")
    return True

def test_notification_system():
    """Test notification system functionality"""
    print("Testing Notification System...")
    
    # Create notification system
    notification_system = NotificationSystem()
    
    # Test config loading
    config = notification_system.config
    assert isinstance(config, dict), "Config should be a dictionary"
    
    # Test that notifications are disabled by default
    assert not notification_system.notifications_enabled, "Notifications should be disabled by default"
    
    print("✓ Notification System tests passed")
    return True

def main():
    """Main test function"""
    print("Running Milestone 6 Component Tests")
    print("=" * 40)
    
    tests = [
        test_cache_manager,
        test_database_caching,
        test_automated_pipeline,
        test_data_quality_monitoring,
        test_notification_system
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Milestone 6 tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)