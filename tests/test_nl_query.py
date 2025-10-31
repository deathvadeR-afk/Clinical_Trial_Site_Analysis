"""
Test script for NL Query Module
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

def test_nl_query_import():
    """Test that the NL query module can be imported without errors"""
    try:
        from ai_ml.nl_query import NLQueryProcessor
        print("✅ NLQueryProcessor imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing NLQueryProcessor: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing NL Query Module Import")
    print("=" * 35)
    
    if test_nl_query_import():
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)