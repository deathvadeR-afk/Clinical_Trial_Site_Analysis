"""
Test script for ClinicalTrials.gov API integration
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion.clinicaltrials_api import ClinicalTrialsAPI

def test_api_connection():
    """Test the basic API connection and functionality"""
    print("Testing ClinicalTrials.gov API Integration")
    print("=" * 50)
    
    # Initialize the API client
    ct_api = ClinicalTrialsAPI()
    
    # Test 1: Basic retrieval without filters
    print("Test 1: Basic study retrieval...")
    result = ct_api.get_studies(page_size=10)
    
    if result:
        print("✓ Basic study retrieval test passed")
        studies = result.get('studies', [])
        print(f"  Retrieved {len(studies)} studies")
        
        if studies:
            first_study = studies[0]
            id_module = first_study['protocolSection']['identificationModule']
            nct_id = id_module['nctId']
            title = id_module.get('briefTitle', 'N/A')
            print(f"  First study: {nct_id} - {title}")
            
            # Test 2: Find the same study in the results
            print(f"\nTest 2: Finding study {nct_id} in results...")
            found_study = ct_api.find_study_in_results(nct_id, result)
            
            if found_study:
                print("✓ Study search test passed")
                print(f"  Found study {nct_id} in results")
            else:
                print("✗ Study search test failed")
    else:
        print("✗ Basic study retrieval test failed")
        return False
    
    # Test 3: Test with different page size
    print("\nTest 3: Retrieving studies with different page size...")
    result = ct_api.get_studies(page_size=5)
    
    if result:
        print("✓ Different page size test passed")
        studies = result.get('studies', [])
        print(f"  Retrieved {len(studies)} studies")
    else:
        print("✗ Different page size test failed")
    
    print("\n" + "=" * 50)
    print("API Integration Tests Complete!")
    return True

if __name__ == "__main__":
    test_api_connection()