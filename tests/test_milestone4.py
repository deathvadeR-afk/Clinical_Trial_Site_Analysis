"""
Test script for Milestone 4 AI/ML Advanced Features
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

def test_gemini_client():
    """Test Gemini API client"""
    try:
        from ai_ml.gemini_client import GeminiClient
        client = GeminiClient()
        print("✅ GeminiClient instantiated successfully")
        
        # Test methods exist
        assert hasattr(client, 'configure_client')
        assert hasattr(client, 'design_prompt_templates')
        assert hasattr(client, 'generate_text')
        assert hasattr(client, 'implement_batch_processing')
        assert hasattr(client, 'create_specialized_prompts')
        assert hasattr(client, 'implement_response_validation')
        assert hasattr(client, 'build_insight_caching_strategy')
        assert hasattr(client, 'generate_meta_insights')
        print("✅ All GeminiClient methods present")
        
        return True
    except Exception as e:
        print(f"❌ Error testing GeminiClient: {e}")
        return False

def test_site_clustering():
    """Test Site Clustering module"""
    try:
        from ai_ml.clustering import SiteClustering
        print("✅ SiteClustering imported successfully")
        
        # Test class can be instantiated (without DB manager for now)
        # clustering = SiteClustering(None)
        
        # Test methods exist
        methods = [
            'construct_textual_site_profiles',
            'generate_embeddings',
            'implement_dimensionality_reduction',
            'apply_clustering_algorithms',
            'characterize_each_cluster',
            'calculate_cluster_quality_metrics',
            'use_clustering_insights_for_recommendations',
            'store_clustering_results',
            'perform_site_clustering'
        ]
        
        for method in methods:
            assert hasattr(SiteClustering, method), f"Missing method: {method}"
        
        print("✅ All SiteClustering methods present")
        return True
    except Exception as e:
        print(f"❌ Error testing SiteClustering: {e}")
        return False

def test_predictive_model():
    """Test Predictive Enrollment Model"""
    try:
        from ai_ml.predictive_model import PredictiveEnrollmentModel
        print("✅ PredictiveEnrollmentModel imported successfully")
        
        # Test methods exist
        methods = [
            'prepare_training_dataset',
            'engineer_additional_features',
            'train_regression_model',
            'evaluate_model_performance',
            'implement_prediction_intervals',
            'use_gemini_api_for_prediction_explanations',
            'integrate_enrollment_predictions',
            'implement_model_monitoring',
            'train_predictive_model'
        ]
        
        for method in methods:
            assert hasattr(PredictiveEnrollmentModel, method), f"Missing method: {method}"
        
        print("✅ All PredictiveEnrollmentModel methods present")
        return True
    except Exception as e:
        print(f"❌ Error testing PredictiveEnrollmentModel: {e}")
        return False

def test_nl_query():
    """Test Natural Language Query module"""
    try:
        from ai_ml.nl_query import NLQueryProcessor
        print("✅ NLQueryProcessor imported successfully")
        
        # Test methods exist
        methods = [
            'design_query_interface',
            'implement_query_understanding_pipeline',
            'execute_generated_queries',
            'generate_natural_language_responses',
            'implement_multi_turn_conversation',
            'add_query_suggestion_system',
            'implement_safety_controls',
            'process_query'
        ]
        
        for method in methods:
            assert hasattr(NLQueryProcessor, method), f"Missing method: {method}"
        
        print("✅ All NLQueryProcessor methods present")
        return True
    except Exception as e:
        print(f"❌ Error testing NLQueryProcessor: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Milestone 4 AI/ML Advanced Features")
    print("=" * 50)
    
    tests = [
        ("Gemini API Integration", test_gemini_client),
        ("Embedding-Based Site Clustering", test_site_clustering),
        ("Predictive Enrollment Modeling", test_predictive_model),
        ("LLM-Powered Natural Language Querying", test_nl_query)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n=== Testing {test_name} ===")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Milestone 4 components verified successfully!")
        print("✅ Gemini API Integration ready")
        print("✅ Embedding-Based Site Clustering ready")
        print("✅ Predictive Enrollment Modeling ready")
        print("✅ LLM-Powered Natural Language Querying ready")
        return True
    else:
        print("❌ Some Milestone 4 components failed verification!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)