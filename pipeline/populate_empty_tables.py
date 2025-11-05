#!/usr/bin/env python3
"""
Script to populate empty tables with real data by running data enrichment processes.
This script orchestrates the various data ingestion and processing modules to ensure
all tables in the database are properly populated with real clinical trial data.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from data_ingestion.clinicaltrials_api import ClinicalTrialsAPI
from data_ingestion.data_processor import DataProcessor
from data_ingestion.investigator_metrics import InvestigatorMetricsCalculator
from data_ingestion.update_coordinates import update_sites_with_coordinates

# Set up logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "populate_empty_tables.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

def populate_empty_tables():
    """
    Populate empty tables with real data by running the data enrichment processes.
    """
    try:
        logger.info("Starting population of empty tables with real data...")
        
        # Initialize components
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
        
        api_client = ClinicalTrialsAPI()
        data_processor = DataProcessor(db_manager)
        investigator_metrics = InvestigatorMetricsCalculator(db_manager)
        # location_updater is a function, not a class
        
        # Check current state of database
        logger.info("Checking current database state...")
        
        # Get counts for each table to identify empty ones
        tables = ['clinical_trials', 'sites_master', 'investigators', 'site_metrics']
        table_counts = {}
        
        for table in tables:
            result = db_manager.query(f"SELECT COUNT(*) as count FROM {table}")
            count = result[0]['count'] if result else 0
            table_counts[table] = count
            logger.info(f"Table '{table}' has {count} records")
        
        # Process studies data if empty
        if table_counts.get('clinical_trials', 0) == 0:
            logger.info("Populating studies table...")
            # Fetch recent studies (last 3 years, max 1000 results)
            # Fetch recent studies (last 3 years, max 1000 results)
            studies_result = api_client.get_studies(page_size=100)
            
            if studies_result:
                studies = studies_result.get('studies', [])
                logger.info(f"Fetched {len(studies)} studies from API")
                # Process each study
                for study in studies:
                    data_processor.process_clinical_trial_data(study)
                    data_processor.process_site_data(study)
                    data_processor.process_investigator_data(study)
                logger.info("Studies data populated successfully")
            else:
                logger.warning("No studies data fetched from API")
        else:
            logger.info("Studies table already populated, skipping...")
        
        # Process sites data if empty
        if table_counts.get('sites_master', 0) == 0:
            logger.info("Populating sites table...")
            # Get unprocessed sites from studies
            # Sites are processed as part of study processing, no need to extract separately
            
            logger.info("Sites data will be processed as part of study processing")
        else:
            logger.info("Sites table already populated, skipping...")
        
        # Update location coordinates if sites were added
        if table_counts.get('sites', 0) == 0 or table_counts.get('sites', 0) > 0:
            logger.info("Updating location coordinates...")
            try:
                update_sites_with_coordinates()
                logger.info("Location coordinates updated successfully")
            except Exception as e:
                logger.error(f"Failed to update location coordinates: {e}")
        
        # Process investigators data if empty
        if table_counts.get('investigators', 0) == 0:
            logger.info("Populating investigators table...")
            # Get investigators from studies
            # Investigators are processed as part of study processing, no need to extract separately
            
            logger.info("Investigators data will be processed as part of study processing")
        else:
            logger.info("Investigators table already populated, skipping...")
        
        # Calculate investigator metrics if empty
        if table_counts.get('site_metrics', 0) == 0:
            logger.info("Calculating investigator metrics...")
            try:
                # Calculate metrics for all investigators
                investigator_results = db_manager.query("SELECT investigator_id FROM investigators")
                for row in investigator_results:
                    investigator_id = row['investigator_id']
                    investigator_metrics.update_investigator_record(investigator_id)
                logger.info("Investigator metrics calculated successfully")
            except Exception as e:
                logger.error(f"Failed to calculate investigator metrics: {e}")
        else:
            logger.info("Metrics table already populated, skipping...")
        
        logger.info("Completed population of empty tables with real data")
        return True
        
    except Exception as e:
        logger.error(f"Error populating empty tables: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = populate_empty_tables()
    if success:
        print("Successfully populated empty tables with real data")
        sys.exit(0)
    else:
        print("Failed to populate empty tables with real data")
        sys.exit(1)