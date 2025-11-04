"""
Test script for Database Manager
"""

import sys
import os
import unittest

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from database.db_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test cases for Database Manager"""

    def test_database_manager(self):
        """Test the database manager functionality"""
        print("Testing Database Manager")
        print("=" * 30)

        # Initialize database manager
        db_manager = DatabaseManager("test_clinical_trials.db")

        # Test 1: Database connection
        print("Test 1: Database connection...")
        self.assertTrue(db_manager.connect(), "Database connection should be successful")

        try:
            # Test 2: Create tables
            print("\nTest 2: Creating database tables...")
            self.assertTrue(db_manager.create_tables("database/schema.sql"), "Database tables should be created successfully")

            # Test 3: Insert data
            print("\nTest 3: Inserting test data...")
            test_site = {
                "site_name": "Test Medical Center",
                "normalized_name": "test medical center",
                "city": "Boston",
                "state": "MA",
                "country": "USA",
                "institution_type": "Academic",
                "accreditation_status": "Active",
            }

            self.assertTrue(db_manager.insert_data("sites_master", test_site), "Data insertion should be successful")

            # Test 4: Query data
            print("\nTest 4: Querying test data...")
            results = db_manager.query(
                "SELECT * FROM sites_master WHERE site_name = ?",
                ("Test Medical Center",),
            )
            self.assertIsNotNone(results, "Data query should not return None")
            self.assertGreater(len(results), 0, "Should retrieve at least one record")
            print(f"  Retrieved {len(results)} record(s)")

        finally:
            # Disconnect
            db_manager.disconnect()
            print("\n✓ Database disconnected")

        print("\n" + "=" * 30)
        print("Database Manager Tests Complete!")


if __name__ == "__main__":
    unittest.main()