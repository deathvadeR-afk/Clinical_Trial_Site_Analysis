#!/usr/bin/env python3
"""
Data Quality Monitoring for Clinical Trial Site Analysis Platform
Monitors data quality and generates reports
"""
import sys
import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from data_ingestion.data_validator import DataValidator
from database.db_manager import DatabaseManager


class DataQualityMonitor:
    """Monitor data quality and generate reports"""

    def __init__(self, db_path: str = "clinical_trials.db"):
        """
        Initialize the data quality monitor

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_manager = None

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
            print(f"Failed to connect to database: {e}")
            return False

    def disconnect_database(self):
        """Disconnect from the database"""
        if self.db_manager:
            self.db_manager.disconnect()

    def check_completeness(self) -> Dict[str, Any]:
        """
        Check data completeness across tables

        Returns:
            Dictionary with completeness metrics
        """
        completeness_report = {}

        try:
            if not self.db_manager:
                raise Exception("Database not connected")

            # Check sites_master table
            sites_result = self.db_manager.query(
                "SELECT COUNT(*) as count FROM sites_master"
            )
            sites_count = sites_result[0]["count"] if sites_result else 0

            sites_name_result = self.db_manager.query(
                "SELECT COUNT(*) as count FROM sites_master WHERE site_name IS NOT NULL"
            )
            sites_with_name = sites_name_result[0]["count"] if sites_name_result else 0

            sites_completeness = sites_with_name / sites_count if sites_count > 0 else 0

            completeness_report["sites_master"] = {
                "total_records": sites_count,
                "complete_records": sites_with_name,
                "completeness_ratio": sites_completeness,
            }

            # Check clinical_trials table
            trials_result = self.db_manager.query(
                "SELECT COUNT(*) as count FROM clinical_trials"
            )
            trials_count = trials_result[0]["count"] if trials_result else 0

            trials_title_result = self.db_manager.query(
                "SELECT COUNT(*) as count FROM clinical_trials WHERE title IS NOT NULL"
            )
            trials_with_title = (
                trials_title_result[0]["count"] if trials_title_result else 0
            )

            trials_completeness = (
                trials_with_title / trials_count if trials_count > 0 else 0
            )

            completeness_report["clinical_trials"] = {
                "total_records": trials_count,
                "complete_records": trials_with_title,
                "completeness_ratio": trials_completeness,
            }

            # Check investigators table
            investigators_result = self.db_manager.query(
                "SELECT COUNT(*) as count FROM investigators"
            )
            investigators_count = (
                investigators_result[0]["count"] if investigators_result else 0
            )

            investigators_name_result = self.db_manager.query(
                "SELECT COUNT(*) as count FROM investigators WHERE full_name IS NOT NULL"
            )
            investigators_with_name = (
                investigators_name_result[0]["count"]
                if investigators_name_result
                else 0
            )

            investigators_completeness = (
                investigators_with_name / investigators_count
                if investigators_count > 0
                else 0
            )

            completeness_report["investigators"] = {
                "total_records": investigators_count,
                "complete_records": investigators_with_name,
                "completeness_ratio": investigators_completeness,
            }

        except Exception as e:
            print(f"Error checking completeness: {e}")

        return completeness_report

    def check_recency(self) -> Dict[str, Any]:
        """
        Check data recency across tables

        Returns:
            Dictionary with recency metrics
        """
        recency_report = {}

        try:
            if not self.db_manager:
                raise Exception("Database not connected")

            # Get current date
            current_date = datetime.now()

            # Check sites_master table
            sites_with_dates_result = self.db_manager.query(
                "SELECT last_updated FROM sites_master WHERE last_updated IS NOT NULL"
            )
            if sites_with_dates_result:
                sites_with_dates = sites_with_dates_result
                total_sites = len(sites_with_dates)
                recent_sites = 0
                for row in sites_with_dates:
                    try:
                        update_date = datetime.fromisoformat(row["last_updated"])
                        days_old = (current_date - update_date).days
                        if days_old <= 30:  # Consider recent if updated within 30 days
                            recent_sites += 1
                    except ValueError:
                        pass  # Skip invalid dates

                recency_report["sites_master"] = {
                    "total_with_dates": total_sites,
                    "recent_records": recent_sites,
                    "recency_ratio": (
                        recent_sites / total_sites if total_sites > 0 else 0
                    ),
                }

            # Check clinical_trials table
            trials_with_dates_result = self.db_manager.query(
                "SELECT last_update_posted FROM clinical_trials WHERE last_update_posted IS NOT NULL"
            )
            if trials_with_dates_result:
                trials_with_dates = trials_with_dates_result
                total_trials = len(trials_with_dates)
                recent_trials = 0
                for row in trials_with_dates:
                    try:
                        update_date = datetime.fromisoformat(row["last_update_posted"])
                        days_old = (current_date - update_date).days
                        if days_old <= 30:  # Consider recent if updated within 30 days
                            recent_trials += 1
                    except ValueError:
                        pass  # Skip invalid dates

                recency_report["clinical_trials"] = {
                    "total_with_dates": total_trials,
                    "recent_records": recent_trials,
                    "recency_ratio": (
                        recent_trials / total_trials if total_trials > 0 else 0
                    ),
                }

        except Exception as e:
            print(f"Error checking recency: {e}")

        return recency_report

    def check_consistency(self) -> Dict[str, Any]:
        """
        Check data consistency across tables

        Returns:
            Dictionary with consistency metrics
        """
        consistency_report = {}

        try:
            if not self.db_manager:
                raise Exception("Database not connected")

            # Check for duplicate sites
            duplicate_sites_result = self.db_manager.query(
                """
                SELECT site_name, COUNT(*) as count 
                FROM sites_master 
                GROUP BY site_name 
                HAVING COUNT(*) > 1
            """
            )

            duplicate_sites = duplicate_sites_result if duplicate_sites_result else []

            consistency_report["duplicate_sites"] = {
                "count": len(duplicate_sites),
                "details": [
                    {"site_name": row["site_name"], "occurrences": row["count"]}
                    for row in duplicate_sites
                ],
            }

            # Check for trials with invalid dates
            invalid_dates_result = self.db_manager.query(
                """
                SELECT nct_id, start_date, completion_date
                FROM clinical_trials 
                WHERE start_date IS NOT NULL AND completion_date IS NOT NULL 
                AND start_date > completion_date
            """
            )

            invalid_dates = invalid_dates_result if invalid_dates_result else []

            consistency_report["invalid_date_sequences"] = {
                "count": len(invalid_dates),
                "details": [
                    {
                        "nct_id": row["nct_id"],
                        "start_date": row["start_date"],
                        "completion_date": row["completion_date"],
                    }
                    for row in invalid_dates
                ],
            }

        except Exception as e:
            print(f"Error checking consistency: {e}")

        return consistency_report

    def generate_quality_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report

        Returns:
            Dictionary with quality report
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "completeness": self.check_completeness(),
            "recency": self.check_recency(),
            "consistency": self.check_consistency(),
        }

        return report

    def save_report(self, report: Dict[str, Any], output_file: Optional[str] = None):
        """
        Save quality report to file

        Args:
            report: Quality report dictionary
            output_file: Output file path (optional)
        """
        try:
            # Use default path if not provided
            if output_file is None:
                # Get absolute path relative to script location
                script_dir = os.path.dirname(os.path.abspath(__file__))
                reports_dir = os.path.join(os.path.dirname(script_dir), "reports")
                output_file = os.path.join(reports_dir, "data_quality_report.json")

            # Create reports directory if it doesn't exist
            reports_dir = os.path.dirname(output_file)
            print(f"Creating directory: {reports_dir}")
            os.makedirs(reports_dir, exist_ok=True)

            # Save report
            print(f"Saving report to: {output_file}")
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)

            print(f"Quality report saved to {output_file}")
        except Exception as e:
            print(f"Error saving report: {e}")
            import traceback

            traceback.print_exc()

    def run_monitoring(self) -> bool:
        """
        Run complete data quality monitoring

        Returns:
            True if successful, False otherwise
        """
        print("Starting data quality monitoring...")

        try:
            # Connect to database
            if not self.connect_database():
                print("Failed to connect to database")
                return False

            # Generate quality report
            report = self.generate_quality_report()

            # Save report
            self.save_report(report)

            # Print summary
            print("\nData Quality Summary:")
            print("====================")

            # Completeness summary
            print("\nCompleteness:")
            for table, metrics in report["completeness"].items():
                print(
                    f"  {table}: {metrics['completeness_ratio']:.2%} ({metrics['complete_records']}/{metrics['total_records']})"
                )

            # Recency summary
            print("\nRecency:")
            for table, metrics in report["recency"].items():
                print(
                    f"  {table}: {metrics['recency_ratio']:.2%} ({metrics['recent_records']}/{metrics['total_with_dates']})"
                )

            # Consistency summary
            print("\nConsistency Issues:")
            print(
                f"  Duplicate sites: {report['consistency']['duplicate_sites']['count']}"
            )
            print(
                f"  Invalid date sequences: {report['consistency']['invalid_date_sequences']['count']}"
            )

            print(f"\nReport generated at: {report['generated_at']}")

            return True

        except Exception as e:
            print(f"Error running monitoring: {e}")
            return False
        finally:
            # Disconnect from database
            self.disconnect_database()


def main():
    """Main function"""
    monitor = DataQualityMonitor()

    if monitor.run_monitoring():
        print("\nData quality monitoring completed successfully!")
    else:
        print("\nData quality monitoring failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
