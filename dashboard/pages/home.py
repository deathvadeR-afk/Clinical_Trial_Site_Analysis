"""
Home Page for Clinical Trial Site Analysis Platform Dashboard
"""

import streamlit as st
import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from database.db_manager import DatabaseManager

# Import pipeline and ML modules (for data ingestion and model retraining)
ML_MODULES_AVAILABLE = False
try:
    from pipeline.automated_pipeline import AutomatedPipeline
    from ai_ml.predictive_model import PredictiveEnrollmentModel
    from ai_ml.clustering import SiteClustering

    ML_MODULES_AVAILABLE = True
except ImportError:
    pass


def get_db_connection():
    """Create and return a database connection"""
    # Use consistent database path
    db_path = "clinical_trials.db"
    db_manager = DatabaseManager(db_path)
    if db_manager.connect():
        return db_manager
    return None


def check_database_initialized():
    """Check if the database has been initialized with tables"""
    db_manager = get_db_connection()
    if not db_manager:
        return False
    
    try:
        # Try to query a core table to see if tables exist
        result = db_manager.query("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table' AND name='sites_master'")
        table_exists = result[0]["count"] > 0 if result else False
        db_manager.disconnect()
        return table_exists
    except Exception:
        if db_manager:
            db_manager.disconnect()
        return False


def initialize_database_schema():
    """Initialize database schema if not already done"""
    try:
        db_manager = get_db_connection()
        if not db_manager:
            return False
            
        # Create tables from schema
        success = db_manager.create_tables()
        db_manager.disconnect()
        return success
    except Exception as e:
        st.error(f"Error initializing database schema: {e}")
        return False


def fetch_platform_statistics():
    """Fetch platform statistics from database"""
    db_manager = get_db_connection()
    if not db_manager:
        return {"sites": 0, "trials": 0, "recommendations": 0}

    try:
        # Check if tables exist
        if not check_database_initialized():
            # Try to initialize schema
            if not initialize_database_schema():
                st.warning("Database schema not initialized. Please run data ingestion first.")
                db_manager.disconnect()
                return {"sites": 0, "trials": 0, "recommendations": 0}

        # Get site count
        try:
            site_result = db_manager.query("SELECT COUNT(*) as count FROM sites_master")
            sites_count = site_result[0]["count"] if site_result else 0
        except Exception:
            sites_count = 0

        # Get trial count
        try:
            trial_result = db_manager.query("SELECT COUNT(*) as count FROM clinical_trials")
            trials_count = trial_result[0]["count"] if trial_result else 0
        except Exception:
            trials_count = 0

        # Get match score count (as proxy for recommendations)
        try:
            recommendation_result = db_manager.query(
                "SELECT COUNT(*) as count FROM match_scores"
            )
            recommendations_count = (
                recommendation_result[0]["count"] if recommendation_result else 0
            )
        except Exception:
            recommendations_count = 0

        db_manager.disconnect()

        return {
            "sites": sites_count,
            "trials": trials_count,
            "recommendations": recommendations_count,
        }
    except Exception as e:
        st.error(f"Error fetching statistics: {e}")
        if db_manager:
            db_manager.disconnect()
        return {"sites": 0, "trials": 0, "recommendations": 0}


def run_data_ingestion():
    """Run the automated data ingestion pipeline"""
    try:
        # Create pipeline instance
        db_path = "clinical_trials.db"
        if ML_MODULES_AVAILABLE:
            from pipeline.automated_pipeline import AutomatedPipeline

            pipeline = AutomatedPipeline(db_path)

            # Run the pipeline
            success = pipeline.run_pipeline()

            if success:
                st.success("Data ingestion completed successfully!")
                return True
            else:
                st.error("Data ingestion failed. Check logs for details.")
                return False
        else:
            st.error("Pipeline module not available. Please check your installation.")
            return False
    except Exception as e:
        st.error(f"Error running data ingestion: {e}")
        return False


def run_model_retraining():
    """Run model retraining with latest data"""
    try:
        if not ML_MODULES_AVAILABLE:
            st.error("ML modules not available. Please check your installation.")
            return False

        # Get database connection
        db_path = "clinical_trials.db"
        db_manager = DatabaseManager(db_path)
        if not db_manager.connect():
            st.error("Failed to connect to database")
            return False

        # Train predictive model
        st.info("Training predictive enrollment model...")
        from ai_ml.predictive_model import PredictiveEnrollmentModel

        predictive_model = PredictiveEnrollmentModel(db_manager)
        training_results = predictive_model.train_predictive_model()

        if training_results.get("training_success", False):
            st.success(
                f"Predictive model trained successfully! Dataset size: {training_results.get('dataset_size', 0)}"
            )
        else:
            st.warning("Predictive model training completed but with limited data.")

        # Run clustering
        st.info("Running site clustering...")
        from ai_ml.clustering import SiteClustering

        clustering_model = SiteClustering(db_manager)
        clustering_results = clustering_model.perform_site_clustering(n_clusters=5)

        if clustering_results:
            clusters_found = len(clustering_results.get("cluster_characteristics", {}))
            st.success(f"Site clustering completed! Found {clusters_found} clusters.")
        else:
            st.warning("Site clustering completed but no results generated.")

        db_manager.disconnect()
        return True

    except Exception as e:
        st.error(f"Error running model retraining: {e}")
        return False


def download_historical_data(start_date: str, end_date: str):
    """Download historical clinical trial data for ML training"""
    try:
        # Create pipeline instance
        db_path = "clinical_trials.db"
        if ML_MODULES_AVAILABLE:
            from pipeline.automated_pipeline import AutomatedPipeline

            pipeline = AutomatedPipeline(db_path)

            # Download historical data
            success = pipeline.download_historical_trials(start_date, end_date)

            if success:
                st.success(
                    f"Historical data from {start_date} to {end_date} downloaded successfully!"
                )
                return True
            else:
                st.error("Historical data download failed. Check logs for details.")
                return False
        else:
            st.error("Pipeline module not available. Please check your installation.")
            return False
    except Exception as e:
        st.error(f"Error downloading historical data: {e}")
        return False


def show_home_page():
    """Display the home page"""
    st.title("🏥 Clinical Trial Site Analysis Platform")
    st.markdown("---")

    # Fetch real statistics from database
    stats = fetch_platform_statistics()

    st.header("Overview")
    st.write(
        """
    Welcome to the Clinical Trial Site Analysis Platform dashboard. This platform helps clinical research 
    organizations identify and evaluate the best sites for their clinical trials based on comprehensive 
    data analysis and AI-powered insights.
    """
    )

    st.subheader("Key Features")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Sites Analyzed", stats["sites"])
        st.info("Comprehensive site database")

    with col2:
        st.metric("Trials Processed", stats["trials"])
        st.success("Up-to-date trial information")

    with col3:
        st.metric("Recommendations Generated", stats["recommendations"])
        st.warning("AI-powered insights")

    st.subheader("Platform Capabilities")
    st.markdown(
        """
    - **Data Ingestion**: Real-time data from ClinicalTrials.gov and PubMed
    - **Intelligent Analysis**: Advanced analytics and machine learning
    - **Site Matching**: AI-powered site recommendations
    - **Performance Metrics**: Comprehensive site evaluation
    - **Visualization**: Interactive dashboards and maps
    """
    )

    st.subheader("Getting Started")
    st.markdown(
        """
    1. Navigate to **Site Explorer** to search and filter clinical trial sites
    2. Use **Recommendations** to find the best sites for your trial criteria
    3. Explore **Analytics** for detailed performance metrics and insights
    """
    )

    # System Controls
    st.markdown("---")
    st.subheader("System Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Data Management**")
        if st.button("📥 Ingest Latest Data"):
            with st.spinner("Ingesting latest data from APIs..."):
                success = run_data_ingestion()
                if success:
                    st.rerun()

        st.markdown(
            "_Fetches the latest clinical trial and investigator data from ClinicalTrials.gov and PubMed_"
        )

    with col2:
        st.markdown("**Historical Data**")
        st.markdown("_Download historical data for ML training_")
        # Calculate default dates (1 year ago to today)
        default_end = datetime.now()
        default_start = default_end - timedelta(days=365)
        start_date = st.date_input("Start Date", value=default_start)
        end_date = st.date_input("End Date", value=default_end)
        if st.button("📥 Download Historical Data"):
            with st.spinner("Downloading historical data from APIs..."):
                success = download_historical_data(str(start_date), str(end_date))
                if success:
                    st.rerun()

    with col3:
        st.markdown("**Model Management**")
        if st.button("🧠 Retrain ML Models"):
            with st.spinner("Retraining machine learning models with latest data..."):
                success = run_model_retraining()
                if success:
                    st.rerun()

        st.markdown(
            "_Retrains predictive and clustering models with the latest data in the database_"
        )


if __name__ == "__main__":
    show_home_page()