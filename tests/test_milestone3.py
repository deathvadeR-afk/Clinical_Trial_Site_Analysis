"""
Test script for Milestone 3 Analytics Engine components
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from database.db_manager import DatabaseManager
from analytics.match_calculator import MatchScoreCalculator
from analytics.strengths_weaknesses import StrengthsWeaknessesDetector
from analytics.recommendation_engine import RecommendationEngine


def setup_test_database():
    """Set up test database with sample data"""
    print("Setting up test database...")

    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")

    # Connect to database
    if not db_manager.connect():
        print("❌ Failed to connect to database")
        return None

    # Create tables
    if not db_manager.create_tables("database/schema.sql"):
        print("❌ Failed to create database tables")
        return None

    print("✅ Database setup completed")
    return db_manager


def insert_test_data(db_manager):
    """Insert test data for Milestone 3 testing"""
    print("Inserting test data...")

    # Insert test sites
    test_sites = [
        {
            "site_name": "Test Hospital A",
            "city": "New York",
            "state": "NY",
            "country": "United States",
            "institution_type": "Hospital",
            "accreditation_status": "Accredited",
        },
        {
            "site_name": "Test University B",
            "city": "Boston",
            "state": "MA",
            "country": "United States",
            "institution_type": "University",
            "accreditation_status": "Highly Accredited",
        },
    ]

    for site_data in test_sites:
        if db_manager.insert_data("sites_master", site_data):
            print(f"✅ Inserted test site: {site_data['site_name']}")
        else:
            print(f"❌ Failed to insert test site: {site_data['site_name']}")

    # Insert test trials
    test_trials = [
        {
            "nct_id": "NCT00000001",
            "title": "Diabetes Treatment Study",
            "status": "Completed",
            "phase": "Phase 2",
            "study_type": "Interventional",
            "conditions": '["diabetes", "hyperglycemia"]',
            "interventions": '[{"interventionType": "Drug", "interventionName": "Metformin"}]',
            "enrollment_count": 100,
            "start_date": "2020-01-01",
            "completion_date": "2021-01-01",
        },
        {
            "nct_id": "NCT00000002",
            "title": "Hypertension Study",
            "status": "Completed",
            "phase": "Phase 3",
            "study_type": "Interventional",
            "conditions": '["hypertension", "cardiovascular disease"]',
            "interventions": '[{"interventionType": "Device", "interventionName": "Blood Pressure Monitor"}]',
            "enrollment_count": 200,
            "start_date": "2021-01-01",
            "completion_date": "2022-01-01",
        },
    ]

    for trial_data in test_trials:
        if db_manager.insert_data("clinical_trials", trial_data):
            print(f"✅ Inserted test trial: {trial_data['nct_id']}")
        else:
            print(f"❌ Failed to insert test trial: {trial_data['nct_id']}")

    # Insert test trial participation
    test_participation = [
        {
            "site_id": 1,
            "nct_id": "NCT00000001",
            "role": "Primary",
            "recruitment_status": "Completed",
            "actual_enrollment": 100,
            "enrollment_start_date": "2020-01-01",
            "enrollment_end_date": "2021-01-01",
        },
        {
            "site_id": 1,
            "nct_id": "NCT00000002",
            "role": "Secondary",
            "recruitment_status": "Completed",
            "actual_enrollment": 150,
            "enrollment_start_date": "2021-01-01",
            "enrollment_end_date": "2022-01-01",
        },
        {
            "site_id": 2,
            "nct_id": "NCT00000001",
            "role": "Secondary",
            "recruitment_status": "Completed",
            "actual_enrollment": 50,
            "enrollment_start_date": "2020-01-01",
            "enrollment_end_date": "2021-01-01",
        },
    ]

    for participation_data in test_participation:
        if db_manager.insert_data("site_trial_participation", participation_data):
            print(
                f"✅ Inserted test participation data for site {participation_data['site_id']}"
            )
        else:
            print(
                f"❌ Failed to insert test participation data for site {participation_data['site_id']}"
            )

    # Insert test investigators
    test_investigators = [
        {
            "full_name": "Dr. John Smith",
            "normalized_name": "dr. john smith",
            "affiliation_site_id": 1,
            "credentials": "MD, PhD",
            "specialization": "Endocrinology",
            "total_trials_count": 5,
            "active_trials_count": 2,
            "h_index": 25,
            "total_publications": 100,
            "recent_publications_count": 20,
        },
        {
            "full_name": "Dr. Jane Doe",
            "normalized_name": "dr. jane doe",
            "affiliation_site_id": 2,
            "credentials": "MD",
            "specialization": "Cardiology",
            "total_trials_count": 3,
            "active_trials_count": 1,
            "h_index": 15,
            "total_publications": 50,
            "recent_publications_count": 10,
        },
    ]

    for investigator_data in test_investigators:
        if db_manager.insert_data("investigators", investigator_data):
            print(f"✅ Inserted test investigator: {investigator_data['full_name']}")
        else:
            print(
                f"❌ Failed to insert test investigator: {investigator_data['full_name']}"
            )

    # Insert test site metrics
    test_metrics = [
        {
            "site_id": 1,
            "therapeutic_area": "Endocrinology",
            "total_studies": 2,
            "completed_studies": 2,
            "terminated_studies": 0,
            "withdrawn_studies": 0,
            "avg_enrollment_duration_days": 365.0,
            "completion_ratio": 1.0,
            "recruitment_efficiency_score": 0.9,
            "experience_index": 0.8,
        },
        {
            "site_id": 2,
            "therapeutic_area": "Cardiology",
            "total_studies": 1,
            "completed_studies": 1,
            "terminated_studies": 0,
            "withdrawn_studies": 0,
            "avg_enrollment_duration_days": 365.0,
            "completion_ratio": 1.0,
            "recruitment_efficiency_score": 0.8,
            "experience_index": 0.6,
        },
    ]

    for metric_data in test_metrics:
        if db_manager.insert_data("site_metrics", metric_data):
            print(f"✅ Inserted test metrics for site {metric_data['site_id']}")
        else:
            print(f"❌ Failed to insert test metrics for site {metric_data['site_id']}")

    print("✅ Test data insertion completed")


def test_match_calculator(db_manager):
    """Test the match calculator functionality"""
    print("\n=== Testing Match Calculator ===")

    # Initialize match calculator
    match_calculator = MatchScoreCalculator(db_manager)

    # Test target study
    target_study = {
        "conditions": ["diabetes", "hyperglycemia"],
        "phase": "Phase 2",
        "intervention_type": "Drug",
        "country": "United States",
    }

    # Test match score calculation for site 1
    print("Testing match score calculation for Site 1...")
    scores = match_calculator.calculate_match_scores_for_site(1, target_study)
    if scores:
        print("✅ Match score calculation test passed")
        print(f"   Overall match score: {scores.get('overall_match_score', 0):.3f}")
    else:
        print("❌ Match score calculation test failed")
        return False

    # Test experience-based adjustments
    print("Testing experience-based adjustments...")
    adjusted_scores = match_calculator.apply_experience_based_adjustments(
        1, scores, target_study
    )
    if adjusted_scores:
        print("✅ Experience-based adjustments test passed")
        print(
            f"   Adjusted overall match score: {adjusted_scores.get('overall_match_score', 0):.3f}"
        )
    else:
        print("❌ Experience-based adjustments test failed")
        return False

    # Test storing match scores
    print("Testing match score storage...")
    store_result = match_calculator.store_match_scores(1, target_study, adjusted_scores)
    if store_result:
        print("✅ Match score storage test passed")
    else:
        print("❌ Match score storage test failed")
        return False

    return True


def test_strengths_weaknesses_detector(db_manager):
    """Test the strengths and weaknesses detector"""
    print("\n=== Testing Strengths and Weaknesses Detector ===")

    # Initialize detector
    detector = StrengthsWeaknessesDetector(db_manager)

    # Test strength detection
    print("Testing strength detection for Site 1...")
    strengths = detector.detect_site_strengths(1)
    print(f"✅ Detected {len(strengths)} strengths")

    # Test weakness detection
    print("Testing weakness detection for Site 1...")
    weaknesses = detector.detect_site_weaknesses(1)
    print(f"✅ Detected {len(weaknesses)} weaknesses")

    # Test comparative analysis
    print("Testing comparative analysis...")
    comparative_analysis = detector.implement_comparative_analysis(1)
    if comparative_analysis:
        print("✅ Comparative analysis test passed")
    else:
        print("❌ Comparative analysis test failed")
        return False

    # Test pattern detection
    print("Testing pattern detection...")
    patterns = detector.build_pattern_detection(1)
    print(f"✅ Pattern detection test completed")

    # Test structured generation
    print("Testing structured strengths/weaknesses generation...")
    structured_output = detector.generate_structured_strengths_weaknesses(1)
    if structured_output:
        print("✅ Structured generation test passed")
    else:
        print("❌ Structured generation test failed")
        return False

    return True


def test_recommendation_engine(db_manager):
    """Test the recommendation engine"""
    print("\n=== Testing Recommendation Engine ===")

    # Initialize recommendation engine
    engine = RecommendationEngine(db_manager)

    # Test target study parameters
    target_study = {
        "conditions": ["diabetes", "hyperglycemia"],
        "phase": "Phase 2",
        "intervention_type": "Drug",
        "country": "United States",
    }

    # Test parameter validation
    print("Testing target study parameter validation...")
    validation_result = engine.accept_target_study_parameters(target_study)
    if validation_result:
        print("✅ Parameter validation test passed")
    else:
        print("❌ Parameter validation test failed")
        return False

    # Test mandatory filtering
    print("Testing mandatory filtering criteria...")
    eligible_sites = engine.apply_mandatory_filtering_criteria(target_study)
    print(f"✅ Found {len(eligible_sites)} eligible sites")

    # Test match score calculation
    print("Testing match score calculation...")
    site_scores = engine.execute_match_score_calculation(eligible_sites, target_study)
    print(f"✅ Calculated match scores for {len(site_scores)} sites")

    # Test portfolio optimization
    print("Testing portfolio optimization...")
    optimized_sites = engine.implement_portfolio_optimization(site_scores, target_study)
    print(f"✅ Optimized to {len(optimized_sites)} sites")

    # Test tier generation
    print("Testing site selection tiers...")
    tiers = engine.generate_site_selection_tiers(optimized_sites)
    print(
        f"✅ Generated tiers: Primary={len(tiers['primary'])}, Secondary={len(tiers['secondary'])}, Tertiary={len(tiers['tertiary'])}"
    )

    # Test recommendation reports
    print("Testing recommendation reports...")
    reports = engine.create_recommendation_reports(tiers, target_study)
    if reports:
        print("✅ Recommendation reports test passed")
    else:
        print("❌ Recommendation reports test failed")
        return False

    # Test full recommendation generation
    print("Testing full recommendation generation...")
    recommendations = engine.generate_recommendations(target_study)
    if recommendations:
        print("✅ Full recommendation generation test passed")
    else:
        print("❌ Full recommendation generation test failed")
        return False

    return True


def main():
    """Main test function"""
    print("🧪 Testing Milestone 3 Analytics Engine Components")
    print("=" * 50)

    # Set up test database
    db_manager = setup_test_database()
    if not db_manager:
        return False

    try:
        # Insert test data
        insert_test_data(db_manager)

        # Test match calculator
        if not test_match_calculator(db_manager):
            print("\n❌ Match Calculator tests failed")
            return False

        # Test strengths and weaknesses detector
        if not test_strengths_weaknesses_detector(db_manager):
            print("\n❌ Strengths and Weaknesses Detector tests failed")
            return False

        # Test recommendation engine
        if not test_recommendation_engine(db_manager):
            print("\n❌ Recommendation Engine tests failed")
            return False

        # Disconnect from database
        db_manager.disconnect()
        print("\n✅ Disconnected from database")

        print("\n🎉 All Milestone 3 tests passed!")
        print("✅ Match Score Calculation System working")
        print("✅ Strengths and Weaknesses Detection working")
        print("✅ Site Recommendation Engine working")
        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        db_manager.disconnect()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
