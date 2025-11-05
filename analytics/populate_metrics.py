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

        # Build therapeutic area taxonomy
        therapeutic_taxonomy = metrics_calculator.build_therapeutic_area_taxonomy()
        print(f"Built therapeutic area taxonomy with {len(therapeutic_taxonomy)} areas")
        
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
            
            # Determine therapeutic areas for this site based on trial participation
            therapeutic_areas = get_site_therapeutic_areas(db_manager, site_id, therapeutic_taxonomy)
            
            # Insert or update site metrics for each therapeutic area
            for therapeutic_area in therapeutic_areas:
                metrics_data = {
                    "site_id": site_id,
                    "therapeutic_area": therapeutic_area,
                    "total_studies": trial_data.get("total_studies", 0),
                    "completed_studies": trial_data.get("completed_studies", 0),
                    "terminated_studies": trial_data.get("terminated_studies", 0),
                    "withdrawn_studies": trial_data.get("withdrawn_studies", 0),
                    "avg_enrollment_duration_days": trial_data.get("avg_enrollment_duration_days", 0),
                    "completion_ratio": trial_data.get("completion_ratio", 0),
                    "recruitment_efficiency_score": trial_data.get("completion_ratio", 0),  # Simplified
                    "experience_index": trial_data.get("total_studies", 0),  # Simplified
                    "last_calculated": "2025-11-05",  # This should be datetime.now().isoformat() in production
                }
                
                # Check if metrics already exist for this site and therapeutic area
                existing_metrics = db_manager.query(
                    "SELECT metric_id FROM site_metrics WHERE site_id = ? AND therapeutic_area = ?",
                    (site_id, therapeutic_area)
                )
                
                if existing_metrics:
                    # Update existing metrics
                    metric_id = existing_metrics[0]["metric_id"]
                    set_clause = ", ".join([f"{key} = ?" for key in metrics_data.keys() if key not in ["site_id", "therapeutic_area"]])
                    values = [metrics_data[key] for key in metrics_data.keys() if key not in ["site_id", "therapeutic_area"]] + [site_id, therapeutic_area]
                    sql = f"UPDATE site_metrics SET {set_clause} WHERE site_id = ? AND therapeutic_area = ?"
                    success = db_manager.execute(sql, tuple(values))
                    if success:
                        print(f"  Updated metrics for {therapeutic_area}")
                    else:
                        print(f"  Failed to update metrics for {therapeutic_area}")
                else:
                    # Insert new metrics
                    success = db_manager.insert_data("site_metrics", metrics_data)
                    if success:
                        print(f"  Inserted metrics for {therapeutic_area}")
                    else:
                        print(f"  Failed to insert metrics for {therapeutic_area}")

        print("Metrics calculation completed successfully")
        return True

    except Exception as e:
        print(f"Error calculating metrics: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db_manager.disconnect()


def get_site_therapeutic_areas(db_manager, site_id, therapeutic_taxonomy):
    """
    Determine therapeutic areas for a specific site based on trial participation
    
    Args:
        db_manager: Database manager instance
        site_id: ID of the site
        therapeutic_taxonomy: Dictionary mapping therapeutic areas to conditions
        
    Returns:
        List of therapeutic areas for the site
    """
    # Get all conditions for trials this site participated in
    conditions_results = db_manager.query("""
        SELECT ct.conditions
        FROM site_trial_participation stp
        JOIN clinical_trials ct ON stp.nct_id = ct.nct_id
        WHERE stp.site_id = ? AND ct.conditions IS NOT NULL
    """, (site_id,))
    
    if not conditions_results:
        # If no conditions found, return "General" as fallback
        return ["General"]
    
    # Collect all conditions for this site
    site_conditions = []
    for row in conditions_results:
        try:
            conditions = eval(row["conditions"])  # This should be json.loads in production
            if isinstance(conditions, list):
                site_conditions.extend(conditions)
        except:
            continue
    
    # Determine therapeutic areas based on conditions
    site_therapeutic_areas = set()
    for condition in site_conditions:
        condition_lower = condition.lower()
        # Check each therapeutic area in the taxonomy
        for area, area_conditions in therapeutic_taxonomy.items():
            for area_condition in area_conditions:
                if area_condition.lower() in condition_lower or condition_lower in area_condition.lower():
                    site_therapeutic_areas.add(area)
                    break
    
    # If no therapeutic areas found, return "General"
    if not site_therapeutic_areas:
        return ["General"]
    
    return list(site_therapeutic_areas)


if __name__ == "__main__":
    success = populate_metrics()
    if success:
        print("Metrics populated successfully!")
    else:
        print("Failed to populate metrics!")