"""
Test script for Gemini Client
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")


def test_gemini_client_import():
    """Test that the Gemini client can be imported without errors"""
    try:
        from ai_ml.gemini_client import GeminiClient

        print("✅ GeminiClient imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing GeminiClient: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 Testing Gemini Client Import")
    print("=" * 40)

    if test_gemini_client_import():
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
