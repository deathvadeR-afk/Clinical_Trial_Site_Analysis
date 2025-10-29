"""
Test script for Data Processor
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion.data_processor import DataProcessor
from database.db_manager import DatabaseManager

def test_data_processor():
    """Test the data processor functionality"""
    print("Testing Data Processor")
    print("=" * 25)
    
    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")
    
    # Connect to database
    if db_manager.connect():
        print("✓ Database connection successful")
        
        # Create tables
        if db_manager.create_tables("database/schema.sql"):
            print("✓ Database tables created successfully")
            
            # Initialize data processor
            data_processor = DataProcessor(db_manager)
            print("✓ Data processor initialized")
            
            # Create sample study data
            sample_study = {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT00000001",
                        "briefTitle": "Sample Clinical Trial"
                    },
                    "statusModule": {
                        "overallStatus": "Recruiting",
                        "startDateStruct": {"date": "2023-01-01"},
                        "completionDateStruct": {"date": "2025-12-31"}
                    },
                    "designModule": {
                        "studyType": "Interventional",
                        "phases": ["Phase 2"],
                        "designInfo": {
                            "enrollmentInfo": {"count": 100}
                        }
                    },
                    "conditionsModule": {
                        "conditions": ["Diabetes Mellitus"]
                    },
                    "armsInterventionsModule": {
                        "interventions": [
                            {"type": "Drug", "name": "Sample Drug"}
                        ]
                    },
                    "sponsorCollaboratorsModule": {
                        "leadSponsor": {
                            "name": "Sample Institution",
                            "class": "OTHER"
                        },
                        "responsibleParty": {
                            "investigatorFullName": "Dr. Jane Smith",
                            "investigatorAffiliation": "Sample Institution"
                        }
                    },
                    "contactsLocationsModule": {
                        "locations": [
                            {
                                "facility": "Sample Medical Center",
                                "city": "Boston",
                                "zip": "02101",
                                "country": "United States"
                            }
                        ]
                    }
                }
            }
            
            # Test 1: Process clinical trial data
            print("\nTest 1: Processing clinical trial data...")
            if data_processor.process_clinical_trial_data(sample_study):
                print("✓ Clinical trial data processing successful")
                
                # Verify data was inserted
                results = db_manager.query("SELECT * FROM clinical_trials WHERE nct_id = ?", ("NCT00000001",))
                if results:
                    print("✓ Clinical trial data verified in database")
                else:
                    print("✗ Clinical trial data not found in database")
            else:
                print("✗ Clinical trial data processing failed")
            
            # Test 2: Process site data
            print("\nTest 2: Processing site data...")
            if data_processor.process_site_data(sample_study):
                print("✓ Site data processing successful")
                
                # Verify data was inserted
                results = db_manager.query("SELECT * FROM sites_master WHERE site_name = ?", ("Sample Medical Center",))
                if results:
                    print("✓ Site data verified in database")
                else:
                    print("✗ Site data not found in database")
            else:
                print("✗ Site data processing failed")
            
            # Test 3: Process investigator data
            print("\nTest 3: Processing investigator data...")
            if data_processor.process_investigator_data(sample_study):
                print("✓ Investigator data processing successful")
                
                # Verify data was inserted
                results = db_manager.query("SELECT * FROM investigators WHERE full_name = ?", ("Dr. Jane Smith",))
                if results:
                    print("✓ Investigator data verified in database")
                else:
                    print("✗ Investigator data not found in database")
            else:
                print("✗ Investigator data processing failed")
            
        else:
            print("✗ Failed to create database tables")
        
        # Disconnect
        db_manager.disconnect()
        print("\n✓ Database disconnected")
    else:
        print("✗ Database connection failed")
        return False
    
    print("\n" + "=" * 25)
    print("Data Processor Tests Complete!")
    return True

if __name__ == "__main__":
    test_data_processor()