"""
Test script for Metrics Calculator
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from database.db_manager import DatabaseManager
from analytics.metrics_calculator import MetricsCalculator

def test_metrics_calculator():
    """Test the metrics calculator functionality"""
    print("Testing Metrics Calculator...")
    
    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")
    
    # Connect to database
    if not db_manager.connect():
        print("❌ Failed to connect to database")
        return False
    
    print("✅ Connected to database successfully")
    
    # Create tables
    if not db_manager.create_tables("database/schema.sql"):
        print("❌ Failed to create database tables")
        return False
    
    print("✅ Database tables created successfully")
    
    # Insert test data
    test_sites = [
        {
            'site_name': 'Test Hospital A',
            'city': 'New York',
            'state': 'NY',
            'country': 'United States',
            'institution_type': 'Hospital',
            'accreditation_status': 'Accredited'
        },
        {
            'site_name': 'Test University B',
            'city': 'Boston',
            'state': 'MA',
            'country': 'United States',
            'institution_type': 'University',
            'accreditation_status': 'Highly Accredited'
        }
    ]
    
    for site_data in test_sites:
        if db_manager.insert_data('sites_master', site_data):
            print(f"✅ Inserted test site: {site_data['site_name']}")
        else:
            print(f"❌ Failed to insert test site: {site_data['site_name']}")
    
    # Insert test trial participation data
    test_participation = [
        {
            'site_id': 1,
            'nct_id': 'NCT00000001',
            'role': 'Primary',
            'recruitment_status': 'Completed',
            'actual_enrollment': 100,
            'enrollment_start_date': '2020-01-01',
            'enrollment_end_date': '2021-01-01'
        },
        {
            'site_id': 1,
            'nct_id': 'NCT00000002',
            'role': 'Secondary',
            'recruitment_status': 'Completed',
            'actual_enrollment': 50,
            'enrollment_start_date': '2021-01-01',
            'enrollment_end_date': '2021-06-01'
        }
    ]
    
    for participation_data in test_participation:
        if db_manager.insert_data('site_trial_participation', participation_data):
            print(f"✅ Inserted test participation data for site {participation_data['site_id']}")
        else:
            print(f"❌ Failed to insert test participation data for site {participation_data['site_id']}")
    
    # Insert test investigators
    test_investigators = [
        {
            'full_name': 'Dr. John Smith',
            'normalized_name': 'dr. john smith',
            'affiliation_site_id': 1,
            'credentials': 'MD, PhD',
            'specialization': 'Oncology',
            'total_trials_count': 5,
            'active_trials_count': 2,
            'h_index': 25,
            'total_publications': 100,
            'recent_publications_count': 20
        },
        {
            'full_name': 'Dr. Jane Doe',
            'normalized_name': 'dr. jane doe',
            'affiliation_site_id': 1,
            'credentials': 'MD',
            'specialization': 'Cardiology',
            'total_trials_count': 3,
            'active_trials_count': 1,
            'h_index': 15,
            'total_publications': 50,
            'recent_publications_count': 10
        }
    ]
    
    for investigator_data in test_investigators:
        if db_manager.insert_data('investigators', investigator_data):
            print(f"✅ Inserted test investigator: {investigator_data['full_name']}")
        else:
            print(f"❌ Failed to insert test investigator: {investigator_data['full_name']}")
    
    # Initialize metrics calculator
    metrics_calculator = MetricsCalculator(db_manager)
    
    # Test aggregate_trial_participation_data
    print("\nTesting aggregate_trial_participation_data...")
    trial_data = metrics_calculator.aggregate_trial_participation_data(1)
    if trial_data:
        print("✅ aggregate_trial_participation_data test passed")
        print(f"   Total studies: {trial_data.get('total_studies', 0)}")
        print(f"   Completion ratio: {trial_data.get('completion_ratio', 0):.2f}")
    else:
        print("❌ aggregate_trial_participation_data test failed")
    
    # Test build_therapeutic_area_taxonomy
    print("\nTesting build_therapeutic_area_taxonomy...")
    taxonomy = metrics_calculator.build_therapeutic_area_taxonomy()
    if taxonomy is not None:  # Can be empty dict
        print("✅ build_therapeutic_area_taxonomy test passed")
        print(f"   Therapeutic areas found: {len(taxonomy)}")
    else:
        print("❌ build_therapeutic_area_taxonomy test failed")
    
    # Test calculate_temporal_metrics
    print("\nTesting calculate_temporal_metrics...")
    temporal_data = metrics_calculator.calculate_temporal_metrics(1)
    if temporal_data is not None:  # Can be empty dict
        print("✅ calculate_temporal_metrics test passed")
        print(f"   Years with data: {len(temporal_data)}")
    else:
        print("❌ calculate_temporal_metrics test failed")
    
    # Test aggregate_investigator_data
    print("\nTesting aggregate_investigator_data...")
    investigator_data = metrics_calculator.aggregate_investigator_data(1)
    if investigator_data:
        print("✅ aggregate_investigator_data test passed")
        print(f"   Total investigators: {investigator_data.get('total_investigators', 0)}")
        print(f"   Average h-index: {investigator_data.get('avg_h_index', 0):.2f}")
    else:
        print("❌ aggregate_investigator_data test failed")
    
    # Test create_site_capability_profiles
    print("\nTesting create_site_capability_profiles...")
    capability_profile = metrics_calculator.create_site_capability_profiles(1)
    if capability_profile:
        print("✅ create_site_capability_profiles test passed")
        print(f"   Site name: {capability_profile.get('site_name', 'Unknown')}")
    else:
        print("❌ create_site_capability_profiles test failed")
    
    # Test build_geographic_metadata
    print("\nTesting build_geographic_metadata...")
    geo_metadata = metrics_calculator.build_geographic_metadata()
    if geo_metadata is not None:  # Can be empty dict
        print("✅ build_geographic_metadata test passed")
        print(f"   Countries with sites: {len(geo_metadata.get('countries', {}))}")
    else:
        print("❌ build_geographic_metadata test failed")
    
    # Test populate_sites_master_table
    print("\nTesting populate_sites_master_table...")
    populate_result = metrics_calculator.populate_sites_master_table()
    if populate_result:
        print("✅ populate_sites_master_table test passed")
    else:
        print("❌ populate_sites_master_table test failed")
    
    # Disconnect from database
    db_manager.disconnect()
    print("✅ Disconnected from database")
    
    print("\n🎉 All Metrics Calculator tests completed!")
    return True

if __name__ == "__main__":
    success = test_metrics_calculator()
    if not success:
        sys.exit(1)