"""
Match Score Calculator for Clinical Trial Site Analysis Platform
Handles calculation of compatibility scores between sites and studies
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the project root to the Python path for imports
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from analytics.metrics_calculator import MetricsCalculator

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "match_calculator.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MatchScoreCalculator:
    """Calculator for determining site-study compatibility scores"""

    def __init__(self, db_manager):
        """
        Initialize the match score calculator

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def calculate_therapeutic_match_score(
        self, site_conditions: List[str], target_conditions: List[str]
    ) -> float:
        """
        Calculate therapeutic area match score

        Args:
            site_conditions: List of conditions the site has experience with
            target_conditions: List of conditions for the target study

        Returns:
            Therapeutic match score (0.0 to 1.0)
        """
        if not target_conditions:
            return 0.0

        if not site_conditions:
            return 0.0

        # Convert to sets for easier comparison
        site_set = set(condition.lower() for condition in site_conditions)
        target_set = set(condition.lower() for condition in target_conditions)

        # Calculate exact matches
        exact_matches = site_set.intersection(target_set)
        exact_match_score = len(exact_matches) / len(target_set)

        # Calculate related matches (partial matches)
        related_matches = 0
        for target_condition in target_set:
            for site_condition in site_set:
                # Simple substring matching for related conditions
                if (
                    target_condition in site_condition
                    or site_condition in target_condition
                ) and target_condition not in exact_matches:
                    related_matches += 1
                    break

        related_match_score = related_matches / len(target_set) * 0.5  # Weighted lower

        # Total score
        total_score = min(1.0, exact_match_score + related_match_score)

        logger.info(
            f"Therapeutic match score: {total_score:.3f} "
            f"(Exact: {exact_match_score:.3f}, Related: {related_match_score:.3f})"
        )

        return total_score

    def calculate_phase_match_score(
        self, site_phases: List[str], target_phase: str
    ) -> float:
        """
        Calculate phase match score

        Args:
            site_phases: List of phases the site has experience with
            target_phase: Target study phase

        Returns:
            Phase match score (0.0 to 1.0)
        """
        if not target_phase:
            return 0.0

        if not site_phases:
            return 0.0

        # Normalize case for comparison
        target_phase_normalized = target_phase.lower().replace(" ", "")
        site_phases_normalized = [phase.lower().replace(" ", "") for phase in site_phases]

        # Exact match with normalized case
        if target_phase_normalized in site_phases_normalized:
            return 1.0

        # Adjacent phase matches
        phase_order = ["phase1", "phase2", "phase3", "phase4"]
        try:
            target_index = phase_order.index(target_phase_normalized)

            # Check for adjacent phases
            adjacent_matches = 0
            if target_index > 0 and phase_order[target_index - 1] in site_phases_normalized:
                adjacent_matches += 1
            if (
                target_index < len(phase_order) - 1
                and phase_order[target_index + 1] in site_phases_normalized
            ):
                adjacent_matches += 1

            if adjacent_matches > 0:
                return 0.7

            # Two phases apart
            if target_index > 1 and phase_order[target_index - 2] in site_phases_normalized:
                return 0.4
            if (
                target_index < len(phase_order) - 2
                and phase_order[target_index + 2] in site_phases_normalized
            ):
                return 0.4

        except ValueError:
            # Target phase not in standard order
            pass

        return 0.0

    def calculate_intervention_match_score(
        self, site_interventions: List[str], target_intervention: str
    ) -> float:
        """
        Calculate intervention match score

        Args:
            site_interventions: List of interventions the site has experience with
            target_intervention: Target study intervention type

        Returns:
            Intervention match score (0.0 to 1.0)
        """
        if not target_intervention:
            return 0.0

        if not site_interventions:
            return 0.0

        # Normalize case for comparison
        target_intervention_normalized = target_intervention.lower()
        site_interventions_normalized = [intervention.lower() for intervention in site_interventions]

        # Exact match with normalized case
        if target_intervention_normalized in site_interventions_normalized:
            return 1.0

        # Similar mechanism matches (simplified)
        similar_matches = {
            "drug": ["biologic", "medication"],
            "biologic": ["drug", "medication"],
            "device": ["medical device", "implant"],
            "procedure": ["surgery", "operation"],
        }

        if target_intervention_normalized in similar_matches:
            for similar in similar_matches[target_intervention_normalized]:
                if similar in site_interventions_normalized:
                    return 0.8

        # Different modality
        return 0.5

    def calculate_geographic_match_score(
        self, site_country: str, target_country: str
    ) -> float:
        """
        Calculate geographic match score

        Args:
            site_country: Country where the site is located
            target_country: Target study country preference

        Returns:
            Geographic match score (0.0 to 1.0)
        """
        if not target_country:
            return 0.5  # Neutral score if no preference

        if not site_country:
            return 0.3  # Lower score if site location unknown

        # Exact match
        if site_country.lower() == target_country.lower():
            return 1.0

        # Regional matches (simplified)
        us_regions = ["united states", "usa", "us", "america"]
        eu_regions = [
            "germany",
            "france",
            "uk",
            "united kingdom",
            "italy",
            "spain",
            "netherlands",
        ]

        site_in_us = site_country.lower() in us_regions
        target_in_us = target_country.lower() in us_regions
        site_in_eu = site_country.lower() in eu_regions
        target_in_eu = target_country.lower() in eu_regions

        if (site_in_us and target_in_us) or (site_in_eu and target_in_eu):
            return 0.8

        # Same continent (simplified)
        return 0.6

    def calculate_overall_match_score(
        self,
        therapeutic_score: float,
        phase_score: float,
        intervention_score: float,
        geographic_score: float,
    ) -> float:
        """
        Calculate weighted overall match score

        Args:
            therapeutic_score: Therapeutic area match score
            phase_score: Phase match score
            intervention_score: Intervention match score
            geographic_score: Geographic match score

        Returns:
            Overall match score (0.0 to 1.0)
        """
        # Weighted calculation based on blueprint
        overall_score = (
            therapeutic_score * 0.35
            + phase_score * 0.20
            + intervention_score * 0.20
            + geographic_score * 0.15
            # Note: Capacity match would be added here but we're simplifying
        )

        logger.info(f"Overall match score: {overall_score:.3f}")
        return overall_score

    def calculate_match_scores_for_site(
        self, site_id: int, target_study: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate all match scores for a specific site and target study

        Args:
            site_id: ID of the site to evaluate
            target_study: Dictionary containing target study parameters

        Returns:
            Dictionary with all match scores
        """
        try:
            # Get site data from database
            site_results = self.db_manager.query(
                "SELECT * FROM sites_master WHERE site_id = ?", (site_id,)
            )

            if not site_results:
                logger.warning(f"No site found with ID {site_id}")
                return {}

            site_data = dict(site_results[0])

            # Get site experience data from trial participation
            participation_results = self.db_manager.query(
                "SELECT ct.conditions, ct.phase, ct.interventions FROM site_trial_participation stp JOIN clinical_trials ct ON stp.nct_id = ct.nct_id WHERE stp.site_id = ?",
                (site_id,),
            )

            site_conditions = []
            site_phases = []
            site_interventions = []

            # Extract experience data from participation records
            for row in participation_results:
                # Extract conditions
                if row["conditions"]:
                    try:
                        conditions = json.loads(row["conditions"])
                        site_conditions.extend(conditions)
                    except json.JSONDecodeError:
                        pass

                # Extract phases
                if row["phase"]:
                    site_phases.append(row["phase"])

                # Extract interventions
                if row["interventions"]:
                    try:
                        interventions = json.loads(row["interventions"])
                        for intervention in interventions:
                            if (
                                isinstance(intervention, dict)
                                and "interventionType" in intervention
                            ):
                                site_interventions.append(
                                    intervention["interventionType"]
                                )
                    except json.JSONDecodeError:
                        pass

            # Remove duplicates
            site_conditions = list(set(site_conditions))
            site_phases = list(set(site_phases))
            site_interventions = list(set(site_interventions))

            # Extract target study parameters
            target_conditions = target_study.get("conditions", [])
            target_phase = target_study.get("phase", "")
            target_intervention = target_study.get("intervention_type", "")
            target_country = target_study.get("country", "United States")

            # Calculate individual scores
            therapeutic_score = self.calculate_therapeutic_match_score(
                site_conditions, target_conditions
            )

            phase_score = self.calculate_phase_match_score(
                site_phases, target_phase if target_phase else ""
            )

            intervention_score = self.calculate_intervention_match_score(
                site_interventions, target_intervention if target_intervention else ""
            )

            geographic_score = self.calculate_geographic_match_score(
                site_data.get("country", ""), target_country
            )

            # Calculate overall score
            overall_score = self.calculate_overall_match_score(
                therapeutic_score, phase_score, intervention_score, geographic_score
            )

            # Return all scores
            scores = {
                "therapeutic_match_score": therapeutic_score,
                "phase_match_score": phase_score,
                "intervention_match_score": intervention_score,
                "geographic_match_score": geographic_score,
                "overall_match_score": overall_score,
            }

            logger.info(f"Match scores calculated for site {site_id}")
            return scores

        except Exception as e:
            logger.error(f"Error calculating match scores for site {site_id}: {e}")
            return {}

    def apply_experience_based_adjustments(
        self, site_id: int, base_scores: Dict[str, float], target_study: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Apply experience-based adjustments to match scores based on site performance metrics

        Args:
            site_id: ID of the site to adjust scores for
            base_scores: Dictionary with base match scores
            target_study: Dictionary containing target study parameters

        Returns:
            Dictionary with adjusted match scores
        """
        try:
            # Get site performance metrics
            metrics_calculator = MetricsCalculator(self.db_manager)
            trial_data = metrics_calculator.aggregate_trial_participation_data(site_id)

            if not trial_data:
                logger.info(
                    f"No performance metrics found for site {site_id}, returning base scores"
                )
                return base_scores

            # Extract relevant metrics
            completion_ratio = trial_data.get("completion_ratio", 0)
            avg_enrollment = trial_data.get("avg_enrollment", 0)
            total_studies = trial_data.get("total_studies", 0)

            # Apply adjustments based on experience
            adjusted_scores = base_scores.copy()

            # Adjustment factor based on completion ratio (0.8 to 1.2 multiplier)
            completion_adjustment = 0.8 + (
                completion_ratio * 0.4
            )  # Maps 0-1 to 0.8-1.2

            # Adjustment factor based on study volume (more studies = more reliable)
            volume_adjustment = min(1.2, 1.0 + (total_studies / 100))  # Caps at 1.2x

            # Apply adjustments to overall score
            adjusted_scores["overall_match_score"] = min(
                1.0,
                base_scores["overall_match_score"]
                * completion_adjustment
                * volume_adjustment,
            )

            # Log adjustments
            logger.info(
                f"Applied experience adjustments for site {site_id}: "
                f"completion_adj={completion_adjustment:.3f}, "
                f"volume_adj={volume_adjustment:.3f}"
            )

            return adjusted_scores

        except Exception as e:
            logger.error(
                f"Error applying experience-based adjustments for site {site_id}: {e}"
            )
            return base_scores

    def store_match_scores(
        self, site_id: int, target_study: Dict[str, Any], scores: Dict[str, float]
    ) -> bool:
        """
        Store match scores with target study parameters in the database

        Args:
            site_id: ID of the site
            target_study: Dictionary containing target study parameters
            scores: Dictionary with calculated match scores

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract target study parameters for storage
            target_therapeutic_area = ", ".join(target_study.get("conditions", []))[
                :100
            ]  # Limit length
            target_phase = target_study.get("phase", "")[:50]  # Limit length
            target_intervention_type = target_study.get("intervention_type", "")[
                :50
            ]  # Limit length

            # Prepare data for insertion
            match_data = {
                "site_id": site_id,
                "target_therapeutic_area": target_therapeutic_area,
                "target_phase": target_phase,
                "target_intervention_type": target_intervention_type,
                "therapeutic_match_score": scores.get("therapeutic_match_score", 0),
                "phase_match_score": scores.get("phase_match_score", 0),
                "intervention_match_score": scores.get("intervention_match_score", 0),
                "geographic_match_score": scores.get("geographic_match_score", 0),
                "overall_match_score": scores.get("overall_match_score", 0),
                "calculated_at": datetime.now().isoformat(),
            }

            # Insert into database
            success = self.db_manager.insert_data("match_scores", match_data)

            if success:
                logger.info(f"Stored match scores for site {site_id}")
            else:
                logger.error(f"Failed to store match scores for site {site_id}")

            return success

        except Exception as e:
            logger.error(f"Error storing match scores for site {site_id}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    print("Match Score Calculator module ready for use")
    print("This module calculates compatibility scores between sites and studies")
