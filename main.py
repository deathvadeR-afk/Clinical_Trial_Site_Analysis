"""
Main Application for Clinical Trial Site Analysis Platform
Demonstrates the data flow and integration of all components
"""
import os
import sys
import logging
from typing import Dict, List

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion.clinicaltrials_api import ClinicalTrialsAPI
from data_ingestion.pubmed_api import PubMedAPI
from database.db_manager import DatabaseManager
from data_ingestion.data_processor import DataProcessor
from data_ingestion.data_validator import DataValidator
from data_ingestion.investigator_metrics import InvestigatorMetricsCalculator
from analytics.match_calculator import MatchScoreCalculator

def setup_logging():
    """Set up logging for the application"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "main_app.log")),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    return logger

def main():
    """Main application function"""
    logger = setup_logging()
    logger.info("Starting Clinical Trial Site Analysis Platform")
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        
        # Initialize database manager
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
            
        # Try to create tables, but continue if they already exist
        try:
            db_manager.create_tables("database/schema.sql")
        except Exception as e:
            logger.info(f"Tables may already exist: {e}")
            pass  # Continue even if tables already exist
            
        # Initialize API clients
        ct_api = ClinicalTrialsAPI()
        pubmed_api = PubMedAPI()
        
        # Initialize processors
        data_processor = DataProcessor(db_manager)
        data_validator = DataValidator(db_manager)
        metrics_calculator = InvestigatorMetricsCalculator(db_manager)
        match_calculator = MatchScoreCalculator(db_manager)
        
        logger.info("All components initialized successfully")
        
        # Demonstrate data ingestion pipeline
        logger.info("=== Demonstrating Data Ingestion Pipeline ===")
        
        # 1. Get clinical trials data
        logger.info("1. Fetching clinical trials data...")
        studies_result = ct_api.get_studies(page_size=20)  # Larger sample for more data
        
        if studies_result:
            logger.info(f"Retrieved {len(studies_result.get('studies', []))} studies")
            
            # Process each study
            for study in studies_result.get('studies', [])[:5]:  # Process first 5 for more data
                nct_id = study['protocolSection']['identificationModule']['nctId']
                logger.info(f"Processing study {nct_id}...")
                
                # Process clinical trial data
                if data_processor.process_clinical_trial_data(study):
                    logger.info(f"Successfully processed clinical trial data for {nct_id}")
                else:
                    logger.error(f"Failed to process clinical trial data for {nct_id}")
                
                # Process site data
                if data_processor.process_site_data(study):
                    logger.info(f"Successfully processed site data for {nct_id}")
                else:
                    logger.error(f"Failed to process site data for {nct_id}")
                
                # Process investigator data
                if data_processor.process_investigator_data(study):
                    logger.info(f"Successfully processed investigator data for {nct_id}")
                else:
                    logger.error(f"Failed to process investigator data for {nct_id}")
        
        # 2. Get investigator publication data
        logger.info("2. Fetching investigator publication data...")
        author_result = pubmed_api.search_authors("Smith J", date_range=("2020/01/01", "2025/12/31"))
        
        if author_result and "esearchresult" in author_result:
            pmids = author_result["esearchresult"].get("idlist", [])[:5]  # First 5 for demo
            logger.info(f"Found {len(pmids)} publications for author")
            
            if pmids:
                # Get publication details
                pub_details = pubmed_api.get_publication_details(pmids)
                if pub_details:
                    logger.info("Successfully retrieved publication details")
                else:
                    logger.error("Failed to retrieve publication details")
        
        # 3. Validate data
        logger.info("3. Validating data...")
        quality_report = data_validator.create_data_quality_report()
        profiling_report = data_validator.build_data_profiling_module()
        
        logger.info("Data quality report generated")
        logger.info("Data profiling report generated")
        
        # 4. Calculate match scores (demo)
        logger.info("4. Calculating match scores...")
        
        # Example target study
        target_study = {
            'conditions': ['diabetes', 'hypertension'],
            'phase': 'Phase 2',
            'intervention_type': 'Drug',
            'country': 'United States'
        }
        
        # Calculate match scores for a sample site (ID 1)
        match_scores = match_calculator.calculate_match_scores_for_site(1, target_study)
        if match_scores:
            logger.info(f"Match scores calculated: {match_scores}")
        else:
            logger.warning("Failed to calculate match scores")
        
        # 5. Generate quality reports
        logger.info("5. Generating quality reports...")
        detailed_report = data_validator.generate_quality_report()
        logger.info("Detailed quality report generated")
        
        # Summary
        logger.info("=== Data Ingestion Pipeline Demo Completed ===")
        logger.info("Summary of operations:")
        logger.info("- Clinical trials data fetched and processed")
        logger.info("- Investigator publication data fetched")
        logger.info("- Data validation and quality control performed")
        logger.info("- Match scores calculated for sample data")
        logger.info("- Quality reports generated")
        
        # Disconnect from database
        db_manager.disconnect()
        logger.info("Disconnected from database")
        
        logger.info("Clinical Trial Site Analysis Platform demo completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in main application: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n Clinical Trial Site Analysis Platform demo completed successfully!")
        print("Check the logs/ directory for detailed logs.")
    else:
        print("\n Clinical Trial Site Analysis Platform demo failed!")
        print("Check the logs/main_app.log file for error details.")