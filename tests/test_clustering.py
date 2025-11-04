"""
Test script for Site Clustering Module
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")


def test_clustering_import():
    """Test that the clustering module can be imported without errors"""
    try:
        from ai_ml.clustering import SiteClustering

        print("SiteClustering imported successfully")
        return True
    except Exception as e:
        print(f"Error importing SiteClustering: {e}")
        return False


def main():
    """Main test function"""
    print("Testing Site Clustering Module Import")
    print("=" * 45)

    if test_clustering_import():
        print("\nAll tests passed!")
        return True
    else:
        print("\nSome tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
