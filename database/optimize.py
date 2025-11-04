"""
Script to optimize the database with additional indexes for better performance
"""

import sqlite3
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager


def optimize_database():
    """Add additional indexes to optimize database performance"""
    print("Optimizing database with additional indexes...")

    # Initialize database manager
    db_manager = DatabaseManager("clinical_trials.db")
    if not db_manager.connect():
        print("Failed to connect to database")
        return False

    try:
        # Check existing indexes
        print("Checking existing indexes...")
        indexes_result = db_manager.query(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        existing_indexes = [row["name"] for row in indexes_result]
        print(f"Existing indexes: {existing_indexes}")

        # Define additional indexes to add
        additional_indexes = [
            # Indexes for faster joins and lookups
            (
                "CREATE INDEX IF NOT EXISTS idx_site_trial_site_id ON site_trial_participation(site_id)",
                "idx_site_trial_site_id",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_site_trial_nct_id ON site_trial_participation(nct_id)",
                "idx_site_trial_nct_id",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_investigator_affiliation ON investigators(affiliation_site_id)",
                "idx_investigator_affiliation",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_publication_investigator ON pubmed_publications(investigator_id)",
                "idx_publication_investigator",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_publication_site ON pubmed_publications(site_id)",
                "idx_publication_site",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_match_scores_site_id ON match_scores(site_id)",
                "idx_match_scores_site_id",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_data_quality_site_id ON data_quality_scores(site_id)",
                "idx_data_quality_site_id",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_ai_insights_site_id ON ai_insights(site_id)",
                "idx_ai_insights_site_id",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_site_clusters_site_id ON site_clusters(site_id)",
                "idx_site_clusters_site_id",
            ),
            # Composite indexes for common query patterns
            (
                "CREATE INDEX IF NOT EXISTS idx_clinical_trials_phase ON clinical_trials(phase, status)",
                "idx_clinical_trials_phase",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_clinical_trials_dates ON clinical_trials(start_date, completion_date)",
                "idx_clinical_trials_dates",
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_site_metrics_composite ON site_metrics(site_id, therapeutic_area, completion_ratio)",
                "idx_site_metrics_composite",
            ),
        ]

        # Add missing indexes
        indexes_added = 0
        for index_sql, index_name in additional_indexes:
            if index_name not in existing_indexes:
                print(f"Adding index: {index_name}")
                if db_manager.execute(index_sql):
                    print(f"  Successfully added index: {index_name}")
                    indexes_added += 1
                else:
                    print(f"  Failed to add index: {index_name}")
            else:
                print(f"Index already exists: {index_name}")

        print(f"Added {indexes_added} new indexes to optimize database performance")
        return True

    except Exception as e:
        print(f"Error optimizing database: {e}")
        return False
    finally:
        db_manager.disconnect()


if __name__ == "__main__":
    success = optimize_database()
    if success:
        print("Database optimization completed successfully!")
    else:
        print("Failed to optimize database!")
