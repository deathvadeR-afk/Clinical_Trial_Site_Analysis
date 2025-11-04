"""
Test script to verify database creation and connection
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager


def test_database():
    """Test database creation and connection"""
    print("Testing database creation and connection...")

    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")

    # Connect to database
    if not db_manager.connect():
        print("Failed to connect to database")
        return False

    print("Connected to database successfully")

    # Create tables
    if not db_manager.create_tables("database/schema.sql"):
        print("Failed to create database tables")
        return False

    print("Database tables created successfully")

    # Test inserting data
    test_data = {
        "site_name": "Test Site",
        "city": "Test City",
        "country": "Test Country",
        "institution_type": "Hospital",
        "accreditation_status": "Active",
    }

    if db_manager.insert_data("sites_master", test_data):
        print("Data insertion successful")
    else:
        print("Data insertion failed")
        return False

    # Test querying data
    results = db_manager.query(
        "SELECT * FROM sites_master WHERE site_name = ?", ("Test Site",)
    )
    if results:
        print("Data querying successful")
        print(f"Retrieved {len(results)} records")
    else:
        print("Data querying failed")
        return False

    # Disconnect
    db_manager.disconnect()
    print("Disconnected from database")

    print("\nAll database tests passed!")
    return True


if __name__ == "__main__":
    success = test_database()
    if not success:
        sys.exit(1)
