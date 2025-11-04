"""
Metrics Calculator for Clinical Trial Site Analysis Platform
Handles calculation of site performance metrics and data quality scores
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "metrics_calculator.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculator for determining site performance metrics and data quality scores"""

    def __init__(self, db_manager):
        """
        Initialize the metrics calculator

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def aggregate_trial_participation_data(self, site_id: int) -> Dict[str, Any]:
        """
        Aggregate trial participation data for a specific site

        Args:
            site_id: ID of the site to aggregate data for

        Returns:
            Dictionary with aggregated trial participation data
        """
        try:
            # Get all trial participation records for this site
            participation_results = self.db_manager.query(
                "SELECT * FROM site_trial_participation WHERE site_id = ?", (site_id,)
            )

            if not participation_results:
                logger.info(f"No trial participation data found for site {site_id}")
                return {}

            # Initialize aggregation variables
            total_studies = len(participation_results)
            completed_studies = 0
            terminated_studies = 0
            withdrawn_studies = 0
            total_enrollment = 0
            enrollment_durations = []

            # Process each participation record
            for row in participation_results:
                status = row["recruitment_status"]
                actual_enrollment = row["actual_enrollment"] or 0
                start_date = row["enrollment_start_date"]
                end_date = row["enrollment_end_date"]

                # Count study statuses
                if status:
                    if "completed" in status.lower():
                        completed_studies += 1
                    elif "terminated" in status.lower():
                        terminated_studies += 1
                    elif "withdrawn" in status.lower():
                        withdrawn_studies += 1

                # Sum enrollment
                total_enrollment += actual_enrollment

                # Calculate enrollment duration if dates are available
                if start_date and end_date:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        duration_days = (end_dt - start_dt).days
                        enrollment_durations.append(duration_days)
                    except ValueError:
                        pass  # Invalid date format

            # Calculate averages
            avg_enrollment = (
                total_enrollment / total_studies if total_studies > 0 else 0
            )
            avg_enrollment_duration = (
                sum(enrollment_durations) / len(enrollment_durations)
                if enrollment_durations
                else 0
            )

            # Calculate completion ratio
            completion_ratio = (
                completed_studies / total_studies if total_studies > 0 else 0
            )

            aggregated_data = {
                "total_studies": total_studies,
                "completed_studies": completed_studies,
                "terminated_studies": terminated_studies,
                "withdrawn_studies": withdrawn_studies,
                "total_enrollment": total_enrollment,
                "avg_enrollment": avg_enrollment,
                "avg_enrollment_duration_days": avg_enrollment_duration,
                "completion_ratio": completion_ratio,
            }

            logger.info(f"Aggregated trial participation data for site {site_id}")
            return aggregated_data

        except Exception as e:
            logger.error(
                f"Error aggregating trial participation data for site {site_id}: {e}"
            )
            return {}

    def build_therapeutic_area_taxonomy(self) -> Dict[str, List[str]]:
        """
        Build therapeutic area taxonomy mapping from clinical trial conditions

        Returns:
            Dictionary mapping therapeutic areas to related conditions
        """
        try:
            # Get all unique conditions from clinical trials
            condition_results = self.db_manager.query(
                "SELECT DISTINCT conditions FROM clinical_trials WHERE conditions IS NOT NULL"
            )

            if not condition_results:
                logger.warning("No conditions found in clinical trials")
                return {}

            # Parse conditions and build taxonomy
            therapeutic_areas = defaultdict(list)

            for row in condition_results:
                conditions_json = row["conditions"]
                try:
                    conditions = json.loads(conditions_json)
                    for condition in conditions:
                        # Simple categorization based on common therapeutic areas
                        condition_lower = condition.lower()
                        if any(
                            keyword in condition_lower
                            for keyword in ["cancer", "tumor", "carcinoma", "sarcoma"]
                        ):
                            therapeutic_areas["Oncology"].append(condition)
                        elif any(
                            keyword in condition_lower
                            for keyword in ["diabetes", "glucose", "insulin"]
                        ):
                            therapeutic_areas["Endocrinology"].append(condition)
                        elif any(
                            keyword in condition_lower
                            for keyword in [
                                "heart",
                                "cardiac",
                                "cardiovascular",
                                "hypertension",
                            ]
                        ):
                            therapeutic_areas["Cardiology"].append(condition)
                        elif any(
                            keyword in condition_lower
                            for keyword in [
                                "infect",
                                "virus",
                                "bacteria",
                                "viral",
                                "bacterial",
                            ]
                        ):
                            therapeutic_areas["Infectious Disease"].append(condition)
                        elif any(
                            keyword in condition_lower
                            for keyword in ["mental", "depression", "anxiety", "psych"]
                        ):
                            therapeutic_areas["Psychiatry"].append(condition)
                        elif any(
                            keyword in condition_lower
                            for keyword in ["neuro", "brain", "parkinson", "alzheimer"]
                        ):
                            therapeutic_areas["Neurology"].append(condition)
                        else:
                            therapeutic_areas["Other"].append(condition)
                except json.JSONDecodeError:
                    continue  # Skip invalid JSON

            # Remove duplicates and sort
            for area in therapeutic_areas:
                therapeutic_areas[area] = sorted(list(set(therapeutic_areas[area])))

            logger.info(
                f"Built therapeutic area taxonomy with {len(therapeutic_areas)} areas"
            )
            return dict(therapeutic_areas)

        except Exception as e:
            logger.error(f"Error building therapeutic area taxonomy: {e}")
            return {}

    def calculate_temporal_metrics(self, site_id: int) -> Dict[str, Any]:
        """
        Calculate temporal metrics for a specific site

        Args:
            site_id: ID of the site to calculate metrics for

        Returns:
            Dictionary with temporal metrics
        """
        try:
            # Get trial participation data with dates
            participation_results = self.db_manager.query(
                """
                SELECT strp.enrollment_start_date, strp.enrollment_end_date, strp.actual_enrollment,
                       ct.phase, ct.conditions
                FROM site_trial_participation strp
                JOIN clinical_trials ct ON strp.nct_id = ct.nct_id
                WHERE strp.site_id = ? AND strp.enrollment_start_date IS NOT NULL
                """,
                (site_id,),
            )

            if not participation_results:
                logger.info(f"No temporal data found for site {site_id}")
                return {}

            # Initialize temporal metrics
            yearly_metrics: Dict[int, Dict[str, Any]] = defaultdict(
                lambda: {
                    "studies_count": 0,
                    "total_enrollment": 0,
                    "phase_distribution": {},
                }
            )

            # Process each participation record
            for row in participation_results:
                start_date = row["enrollment_start_date"]
                actual_enrollment = row["actual_enrollment"] or 0
                phase = row["phase"] or "Unknown"

                # Extract year from start date
                try:
                    year = datetime.strptime(start_date, "%Y-%m-%d").year
                    yearly_metrics[year]["studies_count"] += 1
                    yearly_metrics[year]["total_enrollment"] += actual_enrollment
                    if phase not in yearly_metrics[year]["phase_distribution"]:
                        yearly_metrics[year]["phase_distribution"][phase] = 0
                    yearly_metrics[year]["phase_distribution"][phase] += 1
                except ValueError:
                    continue  # Invalid date format

            # Convert to regular dict and calculate averages
            temporal_metrics = {}
            for year, metrics in yearly_metrics.items():
                metrics["avg_enrollment_per_study"] = (
                    metrics["total_enrollment"] / metrics["studies_count"]
                    if metrics["studies_count"] > 0
                    else 0
                )
                temporal_metrics[year] = dict(metrics)
                # Convert phase_distribution to regular dict
                temporal_metrics[year]["phase_distribution"] = dict(
                    metrics["phase_distribution"]
                )

            logger.info(f"Calculated temporal metrics for site {site_id}")
            return temporal_metrics

        except Exception as e:
            logger.error(f"Error calculating temporal metrics for site {site_id}: {e}")
            return {}

    def aggregate_investigator_data(self, site_id: int) -> Dict[str, Any]:
        """
        Aggregate investigator data for a specific site

        Args:
            site_id: ID of the site to aggregate investigator data for

        Returns:
            Dictionary with aggregated investigator data
        """
        try:
            # Get all investigators affiliated with this site
            investigator_results = self.db_manager.query(
                "SELECT * FROM investigators WHERE affiliation_site_id = ?", (site_id,)
            )

            if not investigator_results:
                logger.info(f"No investigators found for site {site_id}")
                return {}

            # Initialize aggregation variables
            total_investigators = len(investigator_results)
            total_h_index = 0
            total_publications = 0
            total_recent_publications = 0
            specialization_counts = defaultdict(int)

            # Process each investigator
            for row in investigator_results:
                h_index = row["h_index"] or 0
                total_publications_count = row["total_publications"] or 0
                recent_publications_count = row["recent_publications_count"] or 0
                specialization = row["specialization"] or "Unknown"

                total_h_index += h_index
                total_publications += total_publications_count
                total_recent_publications += recent_publications_count
                specialization_counts[specialization] += 1

            # Calculate averages
            avg_h_index = (
                total_h_index / total_investigators if total_investigators > 0 else 0
            )
            avg_publications = (
                total_publications / total_investigators
                if total_investigators > 0
                else 0
            )
            avg_recent_publications = (
                total_recent_publications / total_investigators
                if total_investigators > 0
                else 0
            )

            aggregated_data = {
                "total_investigators": total_investigators,
                "avg_h_index": avg_h_index,
                "total_publications": total_publications,
                "avg_publications_per_investigator": avg_publications,
                "total_recent_publications": total_recent_publications,
                "avg_recent_publications_per_investigator": avg_recent_publications,
                "specialization_distribution": dict(specialization_counts),
            }

            logger.info(f"Aggregated investigator data for site {site_id}")
            return aggregated_data

        except Exception as e:
            logger.error(f"Error aggregating investigator data for site {site_id}: {e}")
            return {}

    def create_site_capability_profiles(self, site_id: int) -> Dict[str, Any]:
        """
        Create site capability profiles based on aggregated data

        Args:
            site_id: ID of the site to create capability profile for

        Returns:
            Dictionary with site capability profile
        """
        try:
            # Get site basic information
            site_results = self.db_manager.query(
                "SELECT * FROM sites_master WHERE site_id = ?", (site_id,)
            )

            if not site_results:
                logger.warning(f"No site found with ID {site_id}")
                return {}

            site_data = dict(site_results[0])

            # Aggregate all relevant data
            trial_data = self.aggregate_trial_participation_data(site_id)
            temporal_data = self.calculate_temporal_metrics(site_id)
            investigator_data = self.aggregate_investigator_data(site_id)

            # Create capability profile
            capability_profile = {
                "site_id": site_id,
                "site_name": site_data.get("site_name"),
                "location": {
                    "city": site_data.get("city"),
                    "state": site_data.get("state"),
                    "country": site_data.get("country"),
                },
                "trial_experience": trial_data,
                "temporal_trends": temporal_data,
                "investigator_strength": investigator_data,
                "institutional_characteristics": {
                    "institution_type": site_data.get("institution_type"),
                    "accreditation_status": site_data.get("accreditation_status"),
                    "total_capacity": site_data.get("total_capacity"),
                },
            }

            logger.info(f"Created capability profile for site {site_id}")
            return capability_profile

        except Exception as e:
            logger.error(f"Error creating capability profile for site {site_id}: {e}")
            return {}

    def build_geographic_metadata(self) -> Dict[str, Any]:
        """
        Build geographic metadata for all sites

        Returns:
            Dictionary with geographic metadata
        """
        try:
            # Get all sites with location data
            site_results = self.db_manager.query(
                """
                SELECT site_id, site_name, city, state, country 
                FROM sites_master 
                WHERE city IS NOT NULL AND country IS NOT NULL
                """
            )

            if not site_results:
                logger.warning("No sites with location data found")
                return {}

            # Group sites by geographic regions
            countries_dict: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            regions_dict: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

            # Simple region mapping (in a real implementation, this would be more sophisticated)
            region_mapping = {
                "United States": "North America",
                "Canada": "North America",
                "Mexico": "North America",
                "United Kingdom": "Europe",
                "Germany": "Europe",
                "France": "Europe",
                "Italy": "Europe",
                "Spain": "Europe",
                "China": "Asia",
                "Japan": "Asia",
                "India": "Asia",
                "Australia": "Oceania",
                "Brazil": "South America",
            }

            # Process each site
            for row in site_results:
                site_id = row["site_id"]
                site_name = row["site_name"]
                city = row["city"]
                state = row["state"]
                country = row["country"]

                # Add to country grouping
                countries_dict[country].append(
                    {
                        "site_id": site_id,
                        "site_name": site_name,
                        "city": city,
                        "state": state,
                    }
                )

                # Add to region grouping
                region = region_mapping.get(country, "Other")
                regions_dict[region].append(
                    {
                        "site_id": site_id,
                        "site_name": site_name,
                        "city": city,
                        "country": country,
                    }
                )

            # Convert defaultdict to regular dict
            geographic_metadata = {
                "countries": dict(countries_dict),
                "regions": dict(regions_dict),
            }

            logger.info(f"Built geographic metadata for {len(site_results)} sites")
            return geographic_metadata

        except Exception as e:
            logger.error(f"Error building geographic metadata: {e}")
            return {}

    def populate_sites_master_table(self) -> bool:
        """
        Populate sites_master table with aggregated attributes

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all sites
            site_results = self.db_manager.query("SELECT site_id FROM sites_master")

            if not site_results:
                logger.warning("No sites found to populate")
                return True

            updated_count = 0

            # Process each site
            for row in site_results:
                site_id = row["site_id"]

                # Get aggregated data
                trial_data = self.aggregate_trial_participation_data(site_id)
                investigator_data = self.aggregate_investigator_data(site_id)

                if not trial_data and not investigator_data:
                    continue

                # Prepare update data
                update_data = {}

                # Add trial experience data
                if trial_data:
                    update_data["total_capacity"] = trial_data.get(
                        "total_enrollment", 0
                    )

                # Add investigator strength data
                if investigator_data:
                    # Use average h-index as a measure of research strength
                    avg_h_index = investigator_data.get("avg_h_index", 0)
                    # Map h-index to accreditation status
                    if avg_h_index >= 20:
                        update_data["accreditation_status"] = "Highly Accredited"
                    elif avg_h_index >= 10:
                        update_data["accreditation_status"] = "Accredited"
                    else:
                        update_data["accreditation_status"] = "Standard"

                # Update site record if we have data to update
                if update_data:
                    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
                    values = list(update_data.values()) + [site_id]
                    sql = f"UPDATE sites_master SET {set_clause} WHERE site_id = ?"

                    if self.db_manager.execute(sql, tuple(values)):
                        updated_count += 1
                        logger.info(
                            f"Updated site {site_id} with aggregated attributes"
                        )

            logger.info(
                f"Populated sites_master table with aggregated attributes for {updated_count} sites"
            )
            return True

        except Exception as e:
            logger.error(f"Error populating sites_master table: {e}")
            return False


# Example usage
if __name__ == "__main__":
    print("Metrics Calculator module ready for use")
    print("This module calculates site performance metrics and data quality scores")
