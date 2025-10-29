"""
Test script for PubMed API integration
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion.pubmed_api import PubMedAPI

def test_pubmed_api():
    """Test the PubMed API integration"""
    print("Testing PubMed API Integration")
    print("=" * 50)
    
    # Initialize the API client
    pubmed_api = PubMedAPI()
    
    # Test 1: Basic author search
    print("Test 1: Searching for publications by author...")
    result = pubmed_api.search_authors("Smith J", date_range=("2020/01/01", "2023/12/31"))
    
    if result:
        print("✓ Author search test passed")
        if "esearchresult" in result:
            id_list = result["esearchresult"].get("idlist", [])
            print(f"  Found {len(id_list)} publications")
            
            # Test 2: Get details for first few publications
            if id_list:
                print(f"\nTest 2: Getting details for first {min(3, len(id_list))} publications...")
                details = pubmed_api.get_publication_details(id_list[:3])
                
                if details:
                    print("✓ Publication details retrieval test passed")
                    print(f"  Retrieved details for publications")
                else:
                    print("✗ Publication details retrieval test failed")
            else:
                print("  No publications found for detail retrieval")
        else:
            print("  Unexpected response format")
    else:
        print("✗ Author search test failed")
        return False
    
    # Test 3: Search with affiliation
    print("\nTest 3: Searching for publications by author with affiliation...")
    result = pubmed_api.search_authors("Johnson M", affiliation="Harvard")
    
    if result:
        print("✓ Author search with affiliation test passed")
        if "esearchresult" in result:
            id_list = result["esearchresult"].get("idlist", [])
            print(f"  Found {len(id_list)} publications")
        else:
            print("  Unexpected response format")
    else:
        print("✗ Author search with affiliation test failed")
    
    print("\n" + "=" * 50)
    print("PubMed API Integration Tests Complete!")
    return True

if __name__ == "__main__":
    test_pubmed_api()