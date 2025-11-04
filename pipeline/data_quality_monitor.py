"""
Data Quality Monitoring Script for Clinical Trial Site Analysis Platform
Implements comprehensive data quality checks and reporting
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

# Import project modules
from database.db_manager import DatabaseManager
from data_ingestion.data_validator import DataValidator

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "data_quality_monitor.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DataQualityMonitor:
    """Monitor and report on data quality metrics"""

    def __init__(self, db_path: str = "clinical_trials.db"):
        """
        Initialize the data quality monitor

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_manager = None
        self.validator = None

        logger.info("DataQualityMonitor initialized")

    def connect_database(self) -> bool:
        """
        Connect to the database

        Returns:
            True if successful, False otherwise
        """
        try:
            self.db_manager = DatabaseManager(self.db_path)
            return self.db_manager.connect()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def disconnect_database(self):
        """Disconnect from the database"""
        if self.db_manager:
            self.db_manager.disconnect()

    def generate_comprehensive_report(self) -> Dict:
        """
        Generate a comprehensive data quality report

        Returns:
            Dictionary with data quality metrics
        """
        try:
            if not self.db_manager:
                logger.error("No database connection")
                return {}

            # Initialize validator
            self.validator = DataValidator(self.db_manager)

            # Generate comprehensive report
            quality_report = self.validator.create_data_quality_report()
            profiling_report = self.validator.build_data_profiling_module()

            # Get database statistics
            db_stats = self.get_database_statistics()

            # Combine reports
            comprehensive_report = {
                "generated_at": datetime.now().isoformat(),
                "data_quality_metrics": quality_report,
                "data_profiling": profiling_report,
                "database_statistics": db_stats,
            }

            return comprehensive_report

        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {}

    def get_database_statistics(self) -> Dict:
        """
        Get database statistics

        Returns:
            Dictionary with database statistics
        """
        try:
            if not self.db_manager:
                return {}

            stats = {}

            # Get table counts
            tables = [
                "sites_master",
                "clinical_trials",
                "site_trial_participation",
                "investigators",
                "pubmed_publications",
                "site_metrics",
                "data_quality_scores",
                "match_scores",
            ]

            for table in tables:
                try:
                    result = self.db_manager.query(
                        f"SELECT COUNT(*) as count FROM {table}"
                    )
                    if result:
                        stats[table] = result[0]["count"]
                except Exception:
                    stats[table] = 0

            # Get data freshness metrics
            freshness_metrics = self.get_data_freshness_metrics()
            stats["data_freshness"] = freshness_metrics

            return stats

        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            return {}

    def get_data_freshness_metrics(self) -> Dict:
        """
        Get data freshness metrics

        Returns:
            Dictionary with data freshness metrics
        """
        try:
            if not self.db_manager:
                return {}

            freshness = {}

            # Get latest updates for sites
            try:
                result = self.db_manager.query(
                    "SELECT MAX(last_updated) as latest_update FROM sites_master WHERE last_updated IS NOT NULL"
                )
                if result and result[0]["latest_update"]:
                    freshness["sites_latest_update"] = result[0]["latest_update"]
            except Exception:
                pass

            # Get latest updates for clinical trials
            try:
                result = self.db_manager.query(
                    "SELECT MAX(last_update_posted) as latest_update FROM clinical_trials WHERE last_update_posted IS NOT NULL"
                )
                if result and result[0]["latest_update"]:
                    freshness["trials_latest_update"] = result[0]["latest_update"]
            except Exception:
                pass

            return freshness

        except Exception as e:
            logger.error(f"Error getting data freshness metrics: {e}")
            return {}

    def save_report_to_file(
        self, report: Dict, output_path: Optional[str] = None
    ) -> bool:
        """
        Save the report to a JSON file

        Args:
            report: Report data to save
            output_path: Path to save the report (if None, use default)

        Returns:
            True if successful, False otherwise
        """
        try:
            if output_path is None:
                # Create reports directory if it doesn't exist
                reports_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "..", "reports"
                )
                os.makedirs(reports_dir, exist_ok=True)
                output_path = os.path.join(
                    reports_dir,
                    f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                )

            # Save report to file
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Data quality report saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving report to file: {e}")
            return False

    def run_monitoring(self) -> bool:
        """
        Run comprehensive data quality monitoring

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting data quality monitoring...")

        try:
            # Connect to database
            if not self.connect_database():
                logger.error("Failed to connect to database")
                return False

            # Generate comprehensive report
            report = self.generate_comprehensive_report()
            if not report:
                logger.error("Failed to generate comprehensive report")
                return False

            # Save report to file
            if not self.save_report_to_file(report):
                logger.error("Failed to save report to file")
                return False

            # Log summary
            quality_metrics = report.get("data_quality_metrics", {})
            db_stats = report.get("database_statistics", {})

            logger.info("Data Quality Monitoring Summary:")
            logger.info(f"  - Sites: {db_stats.get('sites_master', 0)}")
            logger.info(f"  - Clinical Trials: {db_stats.get('clinical_trials', 0)}")
            logger.info(f"  - Investigators: {db_stats.get('investigators', 0)}")
            logger.info(
                f"  - Data Quality Score: {quality_metrics.get('overall_quality_score', 0):.2f}"
            )

            logger.info("Data quality monitoring completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error running data quality monitoring: {e}")
            return False
        finally:
            # Disconnect from database
            self.disconnect_database()


# Example usage
if __name__ == "__main__":
    # Create and run the data quality monitor
    monitor = DataQualityMonitor()

    print("Running data quality monitoring...")
    success = monitor.run_monitoring()

    if success:
        print("Data quality monitoring completed successfully!")
    else:
        print("Data quality monitoring failed!")
        sys.exit(1)
