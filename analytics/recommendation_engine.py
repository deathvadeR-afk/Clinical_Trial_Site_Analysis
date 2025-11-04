"""
Recommendation Engine for Clinical Trial Site Analysis Platform
Handles site recommendations based on match scores and performance metrics
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the project root to the Python path for imports
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from analytics.match_calculator import MatchScoreCalculator
from analytics.strengths_weaknesses import StrengthsWeaknessesDetector

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "recommendation_engine.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Engine for generating site recommendations for clinical trials"""

    def __init__(self, db_manager):
        """
        Initialize the recommendation engine

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.match_calculator = MatchScoreCalculator(db_manager)
        self.strengths_detector = StrengthsWeaknessesDetector(db_manager)

    def accept_target_study_parameters(self, target_study: Dict[str, Any]) -> bool:
        """
        Accept target study parameters as input and validate them

        Args:
            target_study: Dictionary containing target study parameters

        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            required_fields = ["conditions", "phase", "intervention_type"]

            for field in required_fields:
                if field not in target_study or not target_study[field]:
                    logger.error(f"Missing required field: {field}")
                    return False

            logger.info("Target study parameters validated successfully")
            return True

        except Exception as e:
            logger.error(f"Error validating target study parameters: {e}")
            return False

    def apply_mandatory_filtering_criteria(
        self, target_study: Dict[str, Any]
    ) -> List[int]:
        """
        Apply mandatory filtering criteria to identify eligible sites

        Args:
            target_study: Dictionary containing target study parameters

        Returns:
            List of eligible site IDs
        """
        try:
            # Start with all sites
            site_results = self.db_manager.query("SELECT site_id FROM sites_master")
            eligible_sites = [row["site_id"] for row in site_results]

            logger.info(f"Identified {len(eligible_sites)} potentially eligible sites")
            return eligible_sites

        except Exception as e:
            logger.error(f"Error applying mandatory filtering criteria: {e}")
            return []

    def execute_match_score_calculation(
        self, eligible_sites: List[int], target_study: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute match score calculation for all eligible sites

        Args:
            eligible_sites: List of eligible site IDs
            target_study: Dictionary containing target study parameters

        Returns:
            List of dictionaries with site IDs and match scores
        """
        try:
            site_scores = []

            for site_id in eligible_sites:
                # Calculate base match scores
                base_scores = self.match_calculator.calculate_match_scores_for_site(
                    site_id, target_study
                )

                if base_scores:
                    # Apply experience-based adjustments
                    adjusted_scores = (
                        self.match_calculator.apply_experience_based_adjustments(
                            site_id, base_scores, target_study
                        )
                    )

                    # Store match scores
                    self.match_calculator.store_match_scores(
                        site_id, target_study, adjusted_scores
                    )

                    # Add to results
                    site_scores.append({"site_id": site_id, "scores": adjusted_scores})

            # Sort by overall match score
            site_scores.sort(
                key=lambda x: x["scores"].get("overall_match_score", 0), reverse=True
            )

            logger.info(f"Calculated match scores for {len(site_scores)} sites")
            return site_scores

        except Exception as e:
            logger.error(f"Error executing match score calculation: {e}")
            return []

    def implement_portfolio_optimization(
        self, site_scores: List[Dict[str, Any]], target_study: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Implement portfolio optimization algorithm to diversify site selection

        Args:
            site_scores: List of dictionaries with site IDs and match scores
            target_study: Dictionary containing target study parameters

        Returns:
            List of optimized site recommendations
        """
        try:
            # For now, we'll implement a simple geographic diversification
            # In a real implementation, this would be more sophisticated

            optimized_sites = []
            selected_countries = set()
            max_sites = min(10, len(site_scores))  # Limit to top 10 or fewer

            for site_data in site_scores:
                if len(optimized_sites) >= max_sites:
                    break

                site_id = site_data["site_id"]

                # Get site country
                site_result = self.db_manager.query(
                    "SELECT country FROM sites_master WHERE site_id = ?", (site_id,)
                )

                if site_result:
                    country = (
                        site_result[0]["country"]
                        if site_result[0]["country"]
                        else "Unknown"
                    )

                    # Prefer geographic diversity (simple approach)
                    if country not in selected_countries or len(selected_countries) < 3:
                        optimized_sites.append(site_data)
                        selected_countries.add(country)

            logger.info(
                f"Optimized site selection to {len(optimized_sites)} sites with geographic diversity"
            )
            return optimized_sites

        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return site_scores  # Return original scores if optimization fails

    def generate_site_selection_tiers(
        self, optimized_sites: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate site selection tiers based on match scores

        Args:
            optimized_sites: List of optimized site recommendations

        Returns:
            Dictionary with tiered site recommendations
        """
        try:
            tiers = {
                "primary": [],  # Overall match score >= 0.8
                "secondary": [],  # Overall match score >= 0.6
                "tertiary": [],  # Overall match score >= 0.4
            }

            for site_data in optimized_sites:
                overall_score = site_data["scores"].get("overall_match_score", 0)

                if overall_score >= 0.8:
                    tiers["primary"].append(site_data)
                elif overall_score >= 0.6:
                    tiers["secondary"].append(site_data)
                elif overall_score >= 0.4:
                    tiers["tertiary"].append(site_data)

            logger.info(
                f"Generated site selection tiers: "
                f"Primary={len(tiers['primary'])}, "
                f"Secondary={len(tiers['secondary'])}, "
                f"Tertiary={len(tiers['tertiary'])}"
            )
            return tiers

        except Exception as e:
            logger.error(f"Error generating site selection tiers: {e}")
            return {"primary": optimized_sites, "secondary": [], "tertiary": []}

    def create_recommendation_reports(
        self, tiers: Dict[str, List[Dict[str, Any]]], target_study: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create recommendation reports with detailed site information

        Args:
            tiers: Dictionary with tiered site recommendations
            target_study: Dictionary containing target study parameters

        Returns:
            Dictionary with recommendation report
        """
        try:
            report = {
                "target_study": target_study,
                "recommendation_timestamp": datetime.now().isoformat(),
                "tiers": {},
            }

            # Process each tier
            for tier_name, sites in tiers.items():
                detailed_sites = []

                for site_data in sites:
                    site_id = site_data["site_id"]
                    scores = site_data["scores"]

                    # Get detailed site information
                    site_result = self.db_manager.query(
                        "SELECT site_name, city, state, country, institution_type FROM sites_master WHERE site_id = ?",
                        (site_id,),
                    )

                    if site_result:
                        site_info = dict(site_result[0])

                        # Get strengths and weaknesses
                        strengths_weaknesses = self.strengths_detector.generate_structured_strengths_weaknesses(
                            site_id
                        )

                        detailed_site = {
                            "site_id": site_id,
                            "site_info": site_info,
                            "match_scores": scores,
                            "strengths_weaknesses": strengths_weaknesses,
                        }

                        detailed_sites.append(detailed_site)

                report["tiers"][tier_name] = detailed_sites

            logger.info("Created detailed recommendation report")
            return report

        except Exception as e:
            logger.error(f"Error creating recommendation reports: {e}")
            return {}

    def support_alternative_scenarios(
        self, base_target_study: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Support alternative scenarios by varying target study parameters

        Args:
            base_target_study: Base target study parameters

        Returns:
            Dictionary with alternative scenario recommendations
        """
        try:
            scenarios = {
                "base": base_target_study,
                "conservative": base_target_study.copy(),
                "aggressive": base_target_study.copy(),
            }

            # Conservative scenario: Focus more on completion ratio
            scenarios["conservative"][
                "phase"
            ] = "Phase 3"  # Typically higher completion

            # Aggressive scenario: Consider earlier phases
            scenarios["aggressive"]["phase"] = "Phase 1"  # Broader potential

            scenario_recommendations = {}

            # Generate recommendations for each scenario
            for scenario_name, scenario_params in scenarios.items():
                eligible_sites = self.apply_mandatory_filtering_criteria(
                    scenario_params
                )
                site_scores = self.execute_match_score_calculation(
                    eligible_sites, scenario_params
                )
                optimized_sites = self.implement_portfolio_optimization(
                    site_scores, scenario_params
                )
                tiers = self.generate_site_selection_tiers(optimized_sites)
                report = self.create_recommendation_reports(tiers, scenario_params)

                scenario_recommendations[scenario_name] = report

            logger.info("Generated alternative scenario recommendations")
            return scenario_recommendations

        except Exception as e:
            logger.error(f"Error supporting alternative scenarios: {e}")
            return {}

    def enable_interactive_refinement(
        self, current_recommendations: Dict[str, Any], refinement_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enable interactive refinement of recommendations

        Args:
            current_recommendations: Current recommendation results
            refinement_params: Parameters for refining recommendations

        Returns:
            Dictionary with refined recommendations
        """
        try:
            # For now, we'll implement a simple refinement based on geographic preferences
            # In a real implementation, this would be more interactive

            refined_recommendations = current_recommendations.copy()

            if "preferred_countries" in refinement_params:
                preferred_countries = set(refinement_params["preferred_countries"])

                # Filter sites by preferred countries
                for tier_name, sites in refined_recommendations["tiers"].items():
                    filtered_sites = [
                        site
                        for site in sites
                        if site.get("site_info", {}).get("country")
                        in preferred_countries
                    ]
                    refined_recommendations["tiers"][tier_name] = filtered_sites

            logger.info("Applied interactive refinement to recommendations")
            return refined_recommendations

        except Exception as e:
            logger.error(f"Error in interactive refinement: {e}")
            return current_recommendations

    def generate_recommendations(self, target_study: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to generate site recommendations for a target study

        Args:
            target_study: Dictionary containing target study parameters

        Returns:
            Dictionary with complete recommendation results
        """
        try:
            # Validate input
            if not self.accept_target_study_parameters(target_study):
                logger.error("Invalid target study parameters")
                return {}

            # Apply mandatory filtering
            eligible_sites = self.apply_mandatory_filtering_criteria(target_study)
            if not eligible_sites:
                logger.warning("No eligible sites found")
                return {}

            # Calculate match scores
            site_scores = self.execute_match_score_calculation(
                eligible_sites, target_study
            )
            if not site_scores:
                logger.warning("No match scores calculated")
                return {}

            # Optimize portfolio
            optimized_sites = self.implement_portfolio_optimization(
                site_scores, target_study
            )

            # Generate tiers
            tiers = self.generate_site_selection_tiers(optimized_sites)

            # Create reports
            report = self.create_recommendation_reports(tiers, target_study)

            logger.info("Successfully generated site recommendations")
            return report

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    print("Recommendation Engine module ready for use")
    print("This module generates site recommendations for clinical trials")
