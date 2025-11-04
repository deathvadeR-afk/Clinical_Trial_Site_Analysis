"""
Scheduler for Clinical Trial Site Analysis Platform
Implements automated scheduling of data pipeline tasks
"""

import sys
import os
import schedule
import time
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

# Import project modules
from pipeline.automated_pipeline import AutomatedPipeline
from pipeline.data_quality_monitor import DataQualityMonitor

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "scheduler.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Scheduler for automated pipeline execution"""

    def __init__(self):
        """Initialize the pipeline scheduler"""
        logger.info("PipelineScheduler initialized")

    def run_data_pipeline(self):
        """Run the automated data pipeline"""
        try:
            logger.info("Starting scheduled data pipeline execution...")

            # Create and run the automated pipeline
            pipeline = AutomatedPipeline("clinical_trials.db")
            success = pipeline.run_pipeline()

            if success:
                logger.info("Scheduled data pipeline completed successfully")
            else:
                logger.error("Scheduled data pipeline failed")

        except Exception as e:
            logger.error(f"Error running scheduled data pipeline: {e}")

    def run_quality_monitoring(self):
        """Run data quality monitoring"""
        try:
            logger.info("Starting scheduled data quality monitoring...")

            # Create and run the data quality monitor
            monitor = DataQualityMonitor("clinical_trials.db")
            success = monitor.run_monitoring()

            if success:
                logger.info("Scheduled data quality monitoring completed successfully")
            else:
                logger.error("Scheduled data quality monitoring failed")

        except Exception as e:
            logger.error(f"Error running scheduled data quality monitoring: {e}")

    def setup_schedule(self):
        """Setup the scheduling configuration"""
        # Run data pipeline daily at 2:00 AM
        schedule.every().day.at("02:00").do(self.run_data_pipeline)

        # Run quality monitoring weekly on Monday at 3:00 AM
        schedule.every().monday.at("03:00").do(self.run_quality_monitoring)

        # For demo purposes, also run every 10 minutes
        schedule.every(10).minutes.do(self.run_data_pipeline)

        logger.info("Schedule setup completed")
        logger.info("Scheduled jobs:")
        for job in schedule.jobs:
            logger.info(f"  - {job}")

    def run_scheduler(self):
        """Run the scheduler indefinitely"""
        logger.info("Starting pipeline scheduler...")

        # Setup schedule
        self.setup_schedule()

        # Run scheduler loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Continue running despite errors


# Example usage
if __name__ == "__main__":
    # Create and run the scheduler
    scheduler = PipelineScheduler()

    print("Starting pipeline scheduler...")
    print("Press Ctrl+C to stop the scheduler")

    try:
        scheduler.run_scheduler()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
        sys.exit(0)
