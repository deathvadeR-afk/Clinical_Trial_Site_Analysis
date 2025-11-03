"""
Automated Data Pipeline for Clinical Trial Site Analysis Platform
Implements incremental updates and data processing automation
"""

import sys
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

# Import project modules
from data_ingestion.clinicaltrials_api import ClinicalTrialsAPI
from data_ingestion.pubmed_api import PubMedAPI
from database.db_manager import DatabaseManager
from data_ingestion.data_processor import DataProcessor
from data_ingestion.data_validator import DataValidator
from analytics.metrics_calculator import MetricsCalculator
from analytics.match_calculator import MatchScoreCalculator

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "automated_pipeline.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AutomatedPipeline:
    """Automated data pipeline for incremental updates"""

    def __init__(self, db_path: str = "clinical_trials.db"):
        """
        Initialize the automated pipeline

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_manager = None
        self.clinicaltrials_api = ClinicalTrialsAPI()
        self.pubmed_api = PubMedAPI()

        logger.info("AutomatedPipeline initialized")

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

    def get_last_update_time(self) -> Optional[datetime]:
        """
        Get the last update time from the database

        Returns:
            Last update datetime or None if not found
        """
        try:
            if not self.db_manager or not self.db_manager.connection:
                # Try to connect if not already connected
                if not self.connect_database():
                    return None

            # Get the latest update time from any table that has last_updated column
            # Check tables that actually have the last_updated column
            tables_to_check = ["sites_master", "clinical_trials"]
            latest_time = None

            for table in tables_to_check:
                try:
                    # First check if the column exists by querying a sample
                    try:
                        if self.db_manager:
                            result = self.db_manager.query(
                                f"SELECT MAX(last_updated) as last_update FROM {table} WHERE last_updated IS NOT NULL"
                            )
                            if result and result[0]["last_update"]:
                                update_str = result[0]["last_update"]
                                try:
                                    # Handle different date formats
                                    if "T" in update_str:
                                        update_time = datetime.fromisoformat(update_str)
                                    else:
                                        update_time = datetime.strptime(
                                            update_str, "%Y-%m-%d %H:%M:%S"
                                        )
                                    if latest_time is None or update_time > latest_time:
                                        latest_time = update_time
                                except ValueError:
                                    continue
                    except Exception:
                        # Column doesn't exist or other error, continue to next table
                        continue
                except Exception as e:
                    logger.debug(f"Could not query {table} for last_updated: {e}")
                    continue

            # Also check clinical_trials table for last_update_posted
            try:
                if self.db_manager:
                    result = self.db_manager.query(
                        "SELECT MAX(last_update_posted) as last_update FROM clinical_trials WHERE last_update_posted IS NOT NULL"
                    )
                    if result and result[0]["last_update"]:
                        update_str = result[0]["last_update"]
                        try:
                            # Handle date format (YYYY-MM-DD)
                            update_time = datetime.strptime(update_str, "%Y-%m-%d")
                            if latest_time is None or update_time > latest_time:
                                latest_time = update_time
                        except ValueError:
                            pass
            except Exception as e:
                logger.debug(
                    f"Could not query clinical_trials for last_update_posted: {e}"
                )

            return latest_time
        except Exception as e:
            logger.error(f"Error getting last update time: {e}")
            return None

    def fetch_new_clinical_trials(self, since_date: Optional[datetime] = None) -> Dict:
        """
        Fetch new clinical trials since the last update

        Args:
            since_date: Date to fetch trials from (if None, use last update time)

        Returns:
            Dictionary with clinical trials data
        """
        try:
            if since_date is None:
                since_date = self.get_last_update_time()

            # If no previous update time, fetch recent trials
            if since_date is None:
                since_date = datetime.now() - timedelta(days=30)

            # Format date for API query
            date_str = since_date.strftime("%Y-%m-%d")
            logger.info(f"Fetching clinical trials updated since {date_str}")

            # Use the date filter in the API query for more efficient retrieval
            # We'll fetch trials updated since the specified date
            params = {
                "fmt": "json",
                "filter.overallStatus": " recruiting, active, completed, withdrawn, terminated, unknown_status",
                "filter.lastUpdateDate": f"[{date_str},]",
                "pageSize": 100
            }
            
            # Get studies using the ClinicalTrialsAPI with filters
            studies_result = self.clinicaltrials_api._make_request(params)

            # Handle None result
            if studies_result is None:
                logger.warning("No studies returned from API")
                studies_result = {}

            logger.info(
                f"Fetched {len(studies_result.get('studies', []))} clinical trials"
            )
            return studies_result

        except Exception as e:
            logger.error(f"Error fetching clinical trials: {e}")
            return {}

    def fetch_investigator_data(self, investigator_names: List[str]) -> Dict:
        """
        Fetch investigator publication data

        Args:
            investigator_names: List of investigator names to search for

        Returns:
            Dictionary with investigator data
        """
        try:
            logger.info(
                f"Fetching publication data for {len(investigator_names)} investigators"
            )

            # For demo purposes, search for a common name
            author_result = self.pubmed_api.search_authors(
                "Smith", date_range=("2020/01/01", "2025/12/31")
            )

            if author_result and "esearchresult" in author_result:
                pmids = author_result["esearchresult"].get("idlist", [])[
                    :10  # Increased from 5 to 10 for more data
                ]
                if pmids:
                    pub_details = self.pubmed_api.get_publication_details(pmids)
                    if pub_details:
                        logger.info(
                            f"Fetched publication details for {len(pmids)} publications"
                        )
                        return pub_details
                    else:
                        logger.warning("Failed to fetch publication details")
                        return {}
                else:
                    logger.info("No publications found for investigator")
            else:
                logger.info("No investigator data found in search results")

            return {}

        except Exception as e:
            logger.error(f"Error fetching investigator data: {e}")
            return {}

    def process_data(self, clinical_trials_data: Dict, investigator_data: Dict) -> bool:
        """
        Process fetched data and update database

        Args:
            clinical_trials_data: Clinical trials data to process
            investigator_data: Investigator data to process

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.db_manager:
                logger.error("No database connection")
                return False

            # Initialize processors
            data_processor = DataProcessor(self.db_manager)
            data_validator = DataValidator(self.db_manager)

            # Process clinical trials data
            studies = clinical_trials_data.get("studies", [])
            logger.info(f"Processing {len(studies)} clinical trials")

            processed_count = 0
            failed_count = 0
            
            # Process all studies, not just the first 5
            for study in studies:
                nct_id = "unknown"  # Initialize nct_id to avoid unbound variable error
                try:
                    nct_id = study["protocolSection"]["identificationModule"]["nctId"]
                    logger.info(f"Processing study {nct_id}...")

                    # Process clinical trial data
                    if data_processor.process_clinical_trial_data(study):
                        logger.info(
                            f"Successfully processed clinical trial data for {nct_id}"
                        )
                        processed_count += 1
                    else:
                        logger.error(f"Failed to process clinical trial data for {nct_id}")
                        failed_count += 1

                    # Process site data
                    if data_processor.process_site_data(study):
                        logger.info(f"Successfully processed site data for {nct_id}")
                    else:
                        logger.error(f"Failed to process site data for {nct_id}")

                    # Process investigator data
                    if data_processor.process_investigator_data(study):
                        logger.info(
                            f"Successfully processed investigator data for {nct_id}"
                        )
                    else:
                        logger.error(f"Failed to process investigator data for {nct_id}")
                        
                except KeyError as e:
                    logger.error(f"Missing key in study data: {e}")
                    failed_count += 1
                    continue
                except Exception as e:
                    logger.error(f"Error processing study {nct_id}: {e}")
                    failed_count += 1
                    continue

            logger.info(f"Processed {processed_count} clinical trials successfully, {failed_count} failed")

            # Validate data
            logger.info("Validating processed data...")
            quality_report = data_validator.create_data_quality_report()
            profiling_report = data_validator.build_data_profiling_module()

            logger.info("Data validation completed")
            return processed_count > 0  # Return True if at least one study was processed

        except Exception as e:
            logger.error(f"Error processing data: {e}")
            return False

    def calculate_metrics(self) -> bool:
        """
        Calculate site metrics and match scores

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.db_manager:
                logger.error("No database connection")
                return False

            # Initialize calculators
            metrics_calculator = MetricsCalculator(self.db_manager)
            match_calculator = MatchScoreCalculator(self.db_manager)

            # Calculate metrics for all sites
            logger.info("Calculating site metrics...")

            # Get all sites
            site_results = self.db_manager.query("SELECT site_id FROM sites_master")

            if not site_results:
                logger.warning("No sites found to calculate metrics for")
                return True

            # Calculate metrics for each site
            for row in site_results:
                site_id = row["site_id"]
                logger.info(f"Calculating metrics for site {site_id}...")

                # Actually calculate metrics using the MetricsCalculator
                try:
                    # Aggregate trial participation data
                    trial_data = metrics_calculator.aggregate_trial_participation_data(
                        site_id
                    )

                    # Calculate temporal metrics
                    temporal_data = metrics_calculator.calculate_temporal_metrics(
                        site_id
                    )

                    # Aggregate investigator data
                    investigator_data = metrics_calculator.aggregate_investigator_data(
                        site_id
                    )

                    # Create capability profiles
                    capability_profile = (
                        metrics_calculator.create_site_capability_profiles(site_id)
                    )

                    # Store metrics in database
                    if trial_data:
                        # Prepare metrics data for storage
                        metrics_data = {
                            "site_id": site_id,
                            "therapeutic_area": "General",  # Simplified for demo
                            "total_studies": trial_data.get("total_studies", 0),
                            "completed_studies": trial_data.get("completed_studies", 0),
                            "terminated_studies": trial_data.get(
                                "terminated_studies", 0
                            ),
                            "withdrawn_studies": trial_data.get("withdrawn_studies", 0),
                            "avg_enrollment_duration_days": trial_data.get(
                                "avg_enrollment_duration_days", 0
                            ),
                            "completion_ratio": trial_data.get("completion_ratio", 0),
                            "recruitment_efficiency_score": trial_data.get(
                                "completion_ratio", 0
                            ),  # Simplified
                            "experience_index": trial_data.get(
                                "total_studies", 0
                            ),  # Simplified
                            "last_calculated": datetime.now().isoformat(),
                        }

                        # Try to insert first
                        insert_success = self.db_manager.insert_data(
                            "site_metrics", metrics_data
                        )

                        # If insert fails, try to update existing record
                        if not insert_success:
                            # Check if the record already exists
                            existing_record = self.db_manager.query(
                                "SELECT metric_id FROM site_metrics WHERE site_id = ?",
                                (site_id,),
                            )

                            if existing_record:
                                # Build update query (exclude site_id from update)
                                update_data = {
                                    k: v
                                    for k, v in metrics_data.items()
                                    if k != "site_id"
                                }
                                set_clause = ", ".join(
                                    [f"{key} = ?" for key in update_data.keys()]
                                )
                                values = list(update_data.values()) + [site_id]
                                sql = f"UPDATE site_metrics SET {set_clause} WHERE site_id = ?"

                                update_success = self.db_manager.execute(
                                    sql, tuple(values)
                                )
                                if update_success:
                                    logger.info(f"Updated metrics for site {site_id}")
                                else:
                                    logger.error(
                                        f"Failed to update metrics for site {site_id}"
                                    )
                            else:
                                logger.error(
                                    f"Failed to insert metrics for site {site_id}"
                                )
                        else:
                            logger.info(f"Stored metrics for site {site_id}")

                    # Calculate match scores for this site with a sample study
                    # In a real implementation, this would be done for actual target studies
                    sample_study = {
                        "conditions": ["Cancer", "Breast Cancer"],
                        "phase": "Phase 2",
                        "intervention_type": "Drug",
                        "country": "United States",
                    }

                    # Calculate base match scores
                    base_scores = match_calculator.calculate_match_scores_for_site(
                        site_id, sample_study
                    )

                    if base_scores:
                        # Apply experience-based adjustments
                        adjusted_scores = (
                            match_calculator.apply_experience_based_adjustments(
                                site_id, base_scores, sample_study
                            )
                        )

                        # Store match scores
                        match_calculator.store_match_scores(
                            site_id, sample_study, adjusted_scores
                        )
                        logger.info(f"Stored match scores for site {site_id}")

                    logger.info(f"Successfully calculated metrics for site {site_id}")

                except Exception as e:
                    logger.error(f"Error calculating metrics for site {site_id}: {e}")
                    continue

            logger.info("Metrics calculation completed")
            return True

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return False

    def download_historical_trials(self, start_date: str, end_date: str) -> bool:
        """
        Download historical clinical trials data for enhanced ML training

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(
                f"Downloading historical trials from {start_date} to {end_date}"
            )

            # Connect to database if not already connected
            if not self.db_manager and not self.connect_database():
                logger.error("Failed to connect to database")
                return False

            # Initialize data processor
            data_processor = DataProcessor(self.db_manager)

            # Fetch trials with specific search criteria to get trials with enrollment data
            # Search for completed trials within the date range that likely have enrollment info
            page_token = None
            total_downloaded = 0
            total_with_enrollment = 0
            max_pages = 30  # Increase for more data
            pages_processed = 0

            while pages_processed < max_pages:
                # Fetch a page of studies
                studies_result = self.clinicaltrials_api.get_studies(
                    page_size=100, page_token=page_token
                )

                if not studies_result:
                    logger.warning("Failed to retrieve studies")
                    break

                studies = studies_result.get("studies", [])
                if not studies:
                    logger.info("No more studies found")
                    break

                # Process each study, prioritizing those with enrollment data
                processed_count = 0
                enrollment_count = 0
                for study in studies:
                    try:
                        nct_id = study["protocolSection"]["identificationModule"][
                            "nctId"
                        ]

                        # Check if study has enrollment data before processing
                        protocol_section = study.get("protocolSection", {})
                        design_module = protocol_section.get("designModule", {})
                        design_info = design_module.get("designInfo", {})
                        enrollment_info = design_info.get("enrollmentInfo", {})
                        enrollment_count_value = enrollment_info.get("count")

                        # Only process studies with enrollment data
                        if enrollment_count_value is not None:
                            # Process clinical trial data
                            if data_processor.process_clinical_trial_data(study):
                                processed_count += 1
                                total_downloaded += 1
                                total_with_enrollment += 1

                                # Process site data
                                data_processor.process_site_data(study)

                                # Process investigator data
                                data_processor.process_investigator_data(study)

                                logger.debug(
                                    f"Processed study {nct_id} with enrollment count: {enrollment_count_value}"
                                )
                            else:
                                logger.debug(
                                    f"Failed to process clinical trial data for {nct_id}"
                                )
                        else:
                            # Still process the study but don't count it toward enrollment stats
                            if data_processor.process_clinical_trial_data(study):
                                processed_count += 1
                                total_downloaded += 1

                                # Process site data
                                data_processor.process_site_data(study)

                                # Process investigator data
                                data_processor.process_investigator_data(study)

                                logger.debug(
                                    f"Processed study {nct_id} without enrollment data"
                                )

                    except Exception as e:
                        logger.debug(f"Error processing study: {e}")
                        continue

                logger.info(
                    f"Processed {processed_count} studies in current batch ({enrollment_count} with enrollment data)"
                )

                # Check for next page
                next_page_token = studies_result.get("nextPageToken")
                if not next_page_token:
                    logger.info("No more pages available")
                    break

                page_token = next_page_token
                pages_processed += 1

                # Rate limiting
                time.sleep(0.1)

            logger.info(
                f"Downloaded {total_downloaded} historical trials ({total_with_enrollment} with enrollment data)"
            )
            return True

        except Exception as e:
            logger.error(f"Error downloading historical trials: {e}")
            return False

    def download_trials_with_complete_dates(self, months_back: int = 12) -> bool:
        """
        Download trials with complete start and completion dates for better ML training

        Args:
            months_back: Number of months back to search for trials

        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime, timedelta

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)

            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            logger.info(
                f"Downloading trials with complete dates from {start_date_str} to {end_date_str}"
            )

            # Connect to database if not already connected
            if not self.db_manager and not self.connect_database():
                logger.error("Failed to connect to database")
                return False

            # Initialize data processor
            data_processor = DataProcessor(self.db_manager)

            # Fetch trials and filter for those with complete dates
            page_token = None
            total_downloaded = 0
            total_with_complete_dates = 0
            max_pages = 25
            pages_processed = 0

            while pages_processed < max_pages:
                # Fetch a page of studies
                studies_result = self.clinicaltrials_api.get_studies(
                    page_size=100, page_token=page_token
                )

                if not studies_result:
                    logger.warning("Failed to retrieve studies")
                    break

                studies = studies_result.get("studies", [])
                if not studies:
                    logger.info("No more studies found")
                    break

                # Process each study, prioritizing those with complete dates
                processed_count = 0
                complete_dates_count = 0
                for study in studies:
                    try:
                        nct_id = study["protocolSection"]["identificationModule"][
                            "nctId"
                        ]

                        # Check if study has complete date information
                        protocol_section = study.get("protocolSection", {})
                        status_module = protocol_section.get("statusModule", {})

                        start_date_struct = status_module.get("startDateStruct", {})
                        start_date_value = start_date_struct.get("date")

                        completion_date_struct = status_module.get(
                            "completionDateStruct", {}
                        )
                        completion_date_value = completion_date_struct.get("date")

                        # Only process studies with complete date information
                        if (
                            start_date_value is not None
                            and completion_date_value is not None
                        ):
                            # Process clinical trial data
                            if data_processor.process_clinical_trial_data(study):
                                processed_count += 1
                                total_downloaded += 1
                                total_with_complete_dates += 1

                                # Process site data
                                data_processor.process_site_data(study)

                                # Process investigator data
                                data_processor.process_investigator_data(study)

                                logger.debug(
                                    f"Processed study {nct_id} with complete dates: {start_date_value} to {completion_date_value}"
                                )
                            else:
                                logger.debug(
                                    f"Failed to process clinical trial data for {nct_id}"
                                )
                        else:
                            # Still process the study but don't count it toward complete dates stats
                            if data_processor.process_clinical_trial_data(study):
                                processed_count += 1
                                total_downloaded += 1

                                # Process site data
                                data_processor.process_site_data(study)

                                # Process investigator data
                                data_processor.process_investigator_data(study)

                                logger.debug(
                                    f"Processed study {nct_id} without complete dates"
                                )

                    except Exception as e:
                        logger.debug(f"Error processing study: {e}")
                        continue

                logger.info(
                    f"Processed {processed_count} studies in current batch ({complete_dates_count} with complete dates)"
                )

                # Check for next page
                next_page_token = studies_result.get("nextPageToken")
                if not next_page_token:
                    logger.info("No more pages available")
                    break

                page_token = next_page_token
                pages_processed += 1

                # Rate limiting
                time.sleep(0.1)

            logger.info(
                f"Downloaded {total_downloaded} trials ({total_with_complete_dates} with complete dates)"
            )
            return True

        except Exception as e:
            logger.error(f"Error downloading trials with complete dates: {e}")
            return False

    def download_diverse_site_metrics_data(self) -> bool:
        """
        Download data to create more diverse site metrics for better ML training

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Downloading diverse site metrics data")

            # Connect to database if not already connected
            if not self.db_manager and not self.connect_database():
                logger.error("Failed to connect to database")
                return False

            # Initialize data processor
            data_processor = DataProcessor(self.db_manager)
            metrics_calculator = MetricsCalculator(self.db_manager)

            # Fetch more trials to increase site diversity
            page_token = None
            total_downloaded = 0
            max_pages = 20
            pages_processed = 0

            while pages_processed < max_pages:
                # Fetch a page of studies
                studies_result = self.clinicaltrials_api.get_studies(
                    page_size=100, page_token=page_token
                )

                if not studies_result:
                    logger.warning("Failed to retrieve studies")
                    break

                studies = studies_result.get("studies", [])
                if not studies:
                    logger.info("No more studies found")
                    break

                # Process each study
                processed_count = 0
                for study in studies:
                    try:
                        nct_id = study["protocolSection"]["identificationModule"][
                            "nctId"
                        ]

                        # Process clinical trial data
                        if data_processor.process_clinical_trial_data(study):
                            processed_count += 1
                            total_downloaded += 1

                            # Process site data (this will create more diverse sites)
                            data_processor.process_site_data(study)

                            # Process investigator data
                            data_processor.process_investigator_data(study)

                            logger.debug(
                                f"Processed study {nct_id} for diverse site metrics"
                            )

                    except Exception as e:
                        logger.debug(f"Error processing study: {e}")
                        continue

                logger.info(
                    f"Processed {processed_count} studies for diverse site metrics"
                )

                # Check for next page
                next_page_token = studies_result.get("nextPageToken")
                if not next_page_token:
                    logger.info("No more pages available")
                    break

                page_token = next_page_token
                pages_processed += 1

                # Rate limiting
                time.sleep(0.1)

            logger.info(
                f"Downloaded {total_downloaded} trials for diverse site metrics"
            )

            # Now recalculate metrics for all sites to get more diverse data
            logger.info("Recalculating site metrics for diversity...")
            self.calculate_metrics()

            return True

        except Exception as e:
            logger.error(f"Error downloading diverse site metrics data: {e}")
            return False

    def run_pipeline(self) -> bool:
        """
        Run the complete automated pipeline

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting automated pipeline run...")
        start_time = time.time()

        try:
            # Connect to database
            if not self.connect_database():
                logger.error("Failed to connect to database")
                return False

            # Fetch new clinical trials
            clinical_trials_data = self.fetch_new_clinical_trials()
            if not clinical_trials_data:
                logger.warning("No clinical trials data fetched")

            # Fetch investigator data
            investigator_data = self.fetch_investigator_data(["Investigator Name"])

            # Process data
            if not self.process_data(clinical_trials_data, investigator_data):
                logger.error("Failed to process data")
                return False

            # Calculate metrics
            if not self.calculate_metrics():
                logger.error("Failed to calculate metrics")
                return False

            # Log completion
            end_time = time.time()
            duration = end_time - start_time
            logger.info(
                f"Automated pipeline completed successfully in {duration:.2f} seconds"
            )
            return True

        except Exception as e:
            logger.error(f"Error running automated pipeline: {e}")
            return False
        finally:
            # Disconnect from database
            self.disconnect_database()


# Example usage
if __name__ == "__main__":
    # Create and run the automated pipeline
    pipeline = AutomatedPipeline()

    print("Running automated data pipeline...")
    success = pipeline.run_pipeline()

    if success:
        print("Automated pipeline completed successfully!")
    else:
        print("Automated pipeline failed!")
        sys.exit(1)
