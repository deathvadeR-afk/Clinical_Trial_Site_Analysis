"""
Test script for Data Validator
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion.data_validator import DataValidator
from database.db_manager import DatabaseManager


def test_data_validator():
    """Test the data validator functionality"""
    print("Testing Data Validator")
    print("=" * 22)

    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")

    # Connect to database
    if db_manager.connect():
        print("✓ Database connection successful")

        # Create tables
        if db_manager.create_tables("database/schema.sql"):
            print("✓ Database tables created successfully")

            # Initialize data validator
            data_validator = DataValidator(db_manager)
            print("✓ Data validator initialized")

            # Test 1: Validate complete clinical trial data
            print("\nTest 1: Validating complete clinical trial data...")
            complete_trial = {
                "nct_id": "NCT00000001",
                "title": "Sample Clinical Trial",
                "status": "Recruiting",
                "start_date": "2023-01-01",
                "completion_date": "2025-12-31",
            }

            validation_result = data_validator.validate_clinical_trial(complete_trial)
            if validation_result["is_valid"]:
                print("✓ Complete clinical trial validation passed")
                print(
                    f"  Completeness score: {validation_result['completeness_score']:.2f}"
                )
            else:
                print("✗ Complete clinical trial validation failed")
                print(f"  Errors: {validation_result['errors']}")

            # Test 2: Validate incomplete clinical trial data
            print("\nTest 2: Validating incomplete clinical trial data...")
            incomplete_trial = {
                "title": "Sample Clinical Trial",
                "status": "Recruiting",
                # Missing nct_id
            }

            validation_result = data_validator.validate_clinical_trial(incomplete_trial)
            if not validation_result["is_valid"]:
                print("✓ Incomplete clinical trial validation correctly failed")
                print(f"  Errors: {validation_result['errors']}")
            else:
                print("✗ Incomplete clinical trial validation should have failed")

            # Test 3: Validate site data
            print("\nTest 3: Validating site data...")
            complete_site = {
                "site_name": "Sample Medical Center",
                "city": "Boston",
                "country": "United States",
            }

            validation_result = data_validator.validate_site(complete_site)
            if validation_result["is_valid"]:
                print("✓ Site validation passed")
                print(
                    f"  Completeness score: {validation_result['completeness_score']:.2f}"
                )
            else:
                print("✗ Site validation failed")
                print(f"  Errors: {validation_result['errors']}")

            # Test 4: Validate investigator data
            print("\nTest 4: Validating investigator data...")
            complete_investigator = {
                "full_name": "Dr. Jane Smith",
                "h_index": 15,
                "total_publications": 50,
            }

            validation_result = data_validator.validate_investigator(
                complete_investigator
            )
            if validation_result["is_valid"]:
                print("✓ Investigator validation passed")
                print(
                    f"  Completeness score: {validation_result['completeness_score']:.2f}"
                )
            else:
                print("✗ Investigator validation failed")
                print(f"  Errors: {validation_result['errors']}")

            # Test 5: Generate quality report
            print("\nTest 5: Generating quality report...")
            quality_report = data_validator.generate_quality_report()
            if quality_report:
                print("✓ Quality report generated successfully")
                print(
                    f"  Tables: {list(quality_report.get('total_records', {}).keys())}"
                )
            else:
                print("✗ Quality report generation failed")

        else:
            print("✗ Failed to create database tables")

        # Disconnect
        db_manager.disconnect()
        print("\n✓ Database disconnected")
    else:
        print("✗ Database connection failed")
        return False

    print("\n" + "=" * 22)
    print("Data Validator Tests Complete!")
    return True


if __name__ == "__main__":
    test_data_validator()
