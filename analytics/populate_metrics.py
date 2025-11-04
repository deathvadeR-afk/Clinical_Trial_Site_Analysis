"""
Script to populate metrics data in the database
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from analytics.metrics_calculator import MetricsCalculator


def populate_metrics():
    """Populate metrics data in the database"""
    print("Populating metrics data...")

    # Initialize database manager
    db_manager = DatabaseManager("clinical_trials.db")
    if not db_manager.connect():
        print("Failed to connect to database")
        return False

    try:
        # Initialize metrics calculator
        metrics_calculator = MetricsCalculator(db_manager)

        # Get all sites
        site_results = db_manager.query("SELECT site_id FROM sites_master")

        if not site_results:
            print("No sites found to calculate metrics for")
            return False

        # Calculate metrics for each site
        for row in site_results:
            site_id = row["site_id"]
            print(f"Calculating metrics for site {site_id}...")

            # Aggregate trial participation data
            trial_data = metrics_calculator.aggregate_trial_participation_data(site_id)
            print(f"  Trial data: {trial_data}")

            # Calculate temporal metrics
            temporal_data = metrics_calculator.calculate_temporal_metrics(site_id)
            print(f"  Temporal data: {temporal_data}")

            # Aggregate investigator data
            investigator_data = metrics_calculator.aggregate_investigator_data(site_id)
            print(f"  Investigator data: {investigator_data}")

            # Create capability profile
            capability_profile = metrics_calculator.create_site_capability_profiles(
                site_id
            )
            print(f"  Capability profile created")

        print("Metrics calculation completed successfully")
        return True

    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return False
    finally:
        db_manager.disconnect()


if __name__ == "__main__":
    success = populate_metrics()
    if success:
        print("Metrics populated successfully!")
    else:
        print("Failed to populate metrics!")
