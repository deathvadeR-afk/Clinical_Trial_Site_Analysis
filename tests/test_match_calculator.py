"""
Test script for Match Score Calculator
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analytics.match_calculator import MatchScoreCalculator
from database.db_manager import DatabaseManager


def test_match_calculator():
    """Test the match score calculator functionality"""
    print("Testing Match Score Calculator")
    print("=" * 30)

    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")

    # Connect to database
    if db_manager.connect():
        print("✓ Database connection successful")

        # Create tables
        if db_manager.create_tables("database/schema.sql"):
            print("✓ Database tables created successfully")

            # Initialize match score calculator
            match_calculator = MatchScoreCalculator(db_manager)
            print("✓ Match score calculator initialized")

            # Test 1: Calculate therapeutic match score
            print("\nTest 1: Calculating therapeutic match score...")
            site_conditions = ["diabetes", "hypertension", "cardiovascular disease"]
            target_conditions = ["diabetes", "obesity"]

            therapeutic_score = match_calculator.calculate_therapeutic_match_score(
                site_conditions, target_conditions
            )
            print(f"✓ Therapeutic match score: {therapeutic_score:.3f}")

            # Test 2: Calculate phase match score
            print("\nTest 2: Calculating phase match score...")
            site_phases = ["Phase 2", "Phase 3"]
            target_phase = "Phase 2"

            phase_score = match_calculator.calculate_phase_match_score(
                site_phases, target_phase
            )
            print(f"✓ Phase match score: {phase_score:.3f}")

            # Test 3: Calculate intervention match score
            print("\nTest 3: Calculating intervention match score...")
            site_interventions = ["Drug", "Device"]
            target_intervention = "Drug"

            intervention_score = match_calculator.calculate_intervention_match_score(
                site_interventions, target_intervention
            )
            print(f"✓ Intervention match score: {intervention_score:.3f}")

            # Test 4: Calculate geographic match score
            print("\nTest 4: Calculating geographic match score...")
            site_country = "United States"
            target_country = "United States"

            geographic_score = match_calculator.calculate_geographic_match_score(
                site_country, target_country
            )
            print(f"✓ Geographic match score: {geographic_score:.3f}")

            # Test 5: Calculate overall match score
            print("\nTest 5: Calculating overall match score...")
            overall_score = match_calculator.calculate_overall_match_score(
                therapeutic_score, phase_score, intervention_score, geographic_score
            )
            print(f"✓ Overall match score: {overall_score:.3f}")

            # Test 6: Insert a test site and calculate match scores for it
            print("\nTest 6: Calculating match scores for a site in database...")
            test_site = {
                "site_name": "Test Medical Center",
                "normalized_name": "test medical center",
                "city": "Boston",
                "state": "MA",
                "country": "United States",
                "institution_type": "Academic",
                "accreditation_status": "Active",
            }

            if db_manager.insert_data("sites_master", test_site):
                print("✓ Test site inserted successfully")

                # Get the site ID
                results = db_manager.query(
                    "SELECT site_id FROM sites_master WHERE site_name = ?",
                    ("Test Medical Center",),
                )
                if results:
                    site_id = results[0]["site_id"]

                    # Define target study
                    target_study = {
                        "conditions": ["diabetes", "hypertension"],
                        "phase": "Phase 2",
                        "intervention_type": "Drug",
                        "country": "United States",
                    }

                    # Calculate match scores
                    scores = match_calculator.calculate_match_scores_for_site(
                        site_id, target_study
                    )
                    if scores:
                        print("✓ Match scores calculated successfully")
                        print(f"  Therapeutic: {scores['therapeutic_match_score']:.3f}")
                        print(f"  Phase: {scores['phase_match_score']:.3f}")
                        print(
                            f"  Intervention: {scores['intervention_match_score']:.3f}"
                        )
                        print(f"  Geographic: {scores['geographic_match_score']:.3f}")
                        print(f"  Overall: {scores['overall_match_score']:.3f}")
                    else:
                        print("✗ Failed to calculate match scores")
                else:
                    print("✗ Failed to retrieve site ID")
            else:
                print("✗ Failed to insert test site")

        else:
            print("✗ Failed to create database tables")

        # Disconnect
        db_manager.disconnect()
        print("\n✓ Database disconnected")
    else:
        print("✗ Database connection failed")
        return False

    print("\n" + "=" * 30)
    print("Match Score Calculator Tests Complete!")
    return True


if __name__ == "__main__":
    test_match_calculator()
