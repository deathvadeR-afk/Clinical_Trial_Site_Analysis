"""
Test script for Database Manager
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager

def test_database_manager():
    """Test the database manager functionality"""
    print("Testing Database Manager")
    print("=" * 30)
    
    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")
    
    # Test 1: Database connection
    print("Test 1: Database connection...")
    if db_manager.connect():
        print("✓ Database connection successful")
        
        # Test 2: Create tables
        print("\nTest 2: Creating database tables...")
        if db_manager.create_tables("database/schema.sql"):
            print("✓ Database tables created successfully")
            
            # Test 3: Insert data
            print("\nTest 3: Inserting test data...")
            test_site = {
                "site_name": "Test Medical Center",
                "normalized_name": "test medical center",
                "city": "Boston",
                "state": "MA",
                "country": "USA",
                "institution_type": "Academic",
                "accreditation_status": "Active"
            }
            
            if db_manager.insert_data("sites_master", test_site):
                print("✓ Data insertion successful")
                
                # Test 4: Query data
                print("\nTest 4: Querying test data...")
                results = db_manager.query("SELECT * FROM sites_master WHERE site_name = ?", ("Test Medical Center",))
                if results:
                    print("✓ Data query successful")
                    print(f"  Retrieved {len(results)} record(s)")
                else:
                    print("✗ Data query failed")
            else:
                print("✗ Data insertion failed")
        else:
            print("✗ Failed to create database tables")
        
        # Disconnect
        db_manager.disconnect()
        print("\n✓ Database disconnected")
    else:
        print("✗ Database connection failed")
        return False
    
    print("\n" + "=" * 30)
    print("Database Manager Tests Complete!")
    return True

if __name__ == "__main__":
    test_database_manager()