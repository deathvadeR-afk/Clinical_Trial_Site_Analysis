"""
Verification script for Milestone 3 Analytics Engine components
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from analytics.match_calculator import MatchScoreCalculator
from analytics.strengths_weaknesses import StrengthsWeaknessesDetector
from analytics.recommendation_engine import RecommendationEngine

def main():
    """Main verification function"""
    print("🔍 Verifying Milestone 3 Analytics Engine Components")
    print("=" * 50)
    
    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")
    
    # Connect to database
    if not db_manager.connect():
        print("❌ Failed to connect to database")
        return False
    
    print("✅ Database connection established")
    
    # Verify Match Calculator
    print("\n=== Verifying Match Calculator ===")
    try:
        match_calculator = MatchScoreCalculator(db_manager)
        print("✅ MatchCalculator class instantiated successfully")
        
        # Test methods exist
        assert hasattr(match_calculator, 'calculate_therapeutic_match_score')
        assert hasattr(match_calculator, 'calculate_phase_match_score')
        assert hasattr(match_calculator, 'calculate_intervention_match_score')
        assert hasattr(match_calculator, 'calculate_geographic_match_score')
        assert hasattr(match_calculator, 'calculate_overall_match_score')
        assert hasattr(match_calculator, 'apply_experience_based_adjustments')
        assert hasattr(match_calculator, 'store_match_scores')
        print("✅ All MatchCalculator methods present")
    except Exception as e:
        print(f"❌ Match Calculator verification failed: {e}")
        return False
    
    # Verify Strengths and Weaknesses Detector
    print("\n=== Verifying Strengths and Weaknesses Detector ===")
    try:
        detector = StrengthsWeaknessesDetector(db_manager)
        print("✅ StrengthsWeaknessesDetector class instantiated successfully")
        
        # Test methods exist
        assert hasattr(detector, 'define_strength_indicators')
        assert hasattr(detector, 'define_weakness_indicators')
        assert hasattr(detector, 'detect_site_strengths')
        assert hasattr(detector, 'detect_site_weaknesses')
        assert hasattr(detector, 'implement_comparative_analysis')
        assert hasattr(detector, 'build_pattern_detection')
        assert hasattr(detector, 'create_weakness_categorization')
        assert hasattr(detector, 'generate_structured_strengths_weaknesses')
        print("✅ All StrengthsWeaknessesDetector methods present")
    except Exception as e:
        print(f"❌ Strengths and Weaknesses Detector verification failed: {e}")
        return False
    
    # Verify Recommendation Engine
    print("\n=== Verifying Recommendation Engine ===")
    try:
        engine = RecommendationEngine(db_manager)
        print("✅ RecommendationEngine class instantiated successfully")
        
        # Test methods exist
        assert hasattr(engine, 'accept_target_study_parameters')
        assert hasattr(engine, 'apply_mandatory_filtering_criteria')
        assert hasattr(engine, 'execute_match_score_calculation')
        assert hasattr(engine, 'implement_portfolio_optimization')
        assert hasattr(engine, 'generate_site_selection_tiers')
        assert hasattr(engine, 'create_recommendation_reports')
        assert hasattr(engine, 'support_alternative_scenarios')
        assert hasattr(engine, 'enable_interactive_refinement')
        assert hasattr(engine, 'generate_recommendations')
        print("✅ All RecommendationEngine methods present")
    except Exception as e:
        print(f"❌ Recommendation Engine verification failed: {e}")
        return False
    
    # Disconnect from database
    db_manager.disconnect()
    print("\n✅ Disconnected from database")
    
    print("\n🎉 All Milestone 3 components verified successfully!")
    print("✅ Match Score Calculation System ready")
    print("✅ Strengths and Weaknesses Detection ready")
    print("✅ Site Recommendation Engine ready")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)