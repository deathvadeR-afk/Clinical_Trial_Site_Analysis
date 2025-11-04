"""
Script to run ML operations including training predictive models and clustering analysis
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from ai_ml.predictive_model import PredictiveEnrollmentModel
from ai_ml.clustering import SiteClustering


def train_predictive_model():
    """Train the predictive enrollment model"""
    print("Training Predictive Enrollment Model")
    print("=" * 40)

    db_manager = None
    try:
        # Initialize database manager
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            print("ERROR: Failed to connect to database")
            return False

        # Initialize predictive model
        predictive_model = PredictiveEnrollmentModel(db_manager)

        if not predictive_model.is_configured:
            print(
                "ERROR: Scikit-learn not available. Install with: pip install scikit-learn"
            )
            return False

        # Train the model
        print("Starting model training...")
        results = predictive_model.train_predictive_model()

        if results.get("training_success", False):
            print("✅ Model training completed successfully!")
            print(f"Dataset size: {results.get('dataset_size', 0)} records")

            # Print performance metrics
            performance = results.get("performance_metrics", {})
            if performance:
                print("\nPerformance Metrics:")
                print("-" * 20)
                print(f"R² Score: {performance.get('r_squared', 'N/A')}")
                print(
                    f"Mean Squared Error: {performance.get('mean_squared_error', 'N/A')}"
                )
                print(
                    f"Root Mean Squared Error: {performance.get('root_mean_squared_error', 'N/A')}"
                )
                print(
                    f"Mean Absolute Error: {performance.get('mean_absolute_error', 'N/A')}"
                )
                print(
                    f"Mean Absolute Percentage Error: {performance.get('mean_absolute_percentage_error', 'N/A')}"
                )

            # Print prediction intervals
            intervals = results.get("prediction_intervals", {})
            if intervals:
                print("\nPrediction Intervals:")
                print("-" * 20)
                print(f"Confidence Level: {intervals.get('confidence_level', 'N/A')}")
                print(f"Lower Bound: {intervals.get('lower_bound', 'N/A')}")
                print(f"Upper Bound: {intervals.get('upper_bound', 'N/A')}")

            return True
        else:
            print("❌ Model training failed!")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        if db_manager:
            db_manager.disconnect()


def run_clustering():
    """Run the site clustering analysis"""
    print("Running Site Clustering Analysis")
    print("=" * 35)

    db_manager = None
    try:
        # Initialize database manager
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            print("ERROR: Failed to connect to database")
            return False

        # Initialize clustering module
        clustering = SiteClustering(db_manager)

        if not clustering.is_configured:
            print(
                "ERROR: Scikit-learn not available. Install with: pip install scikit-learn"
            )
            return False

        # Run clustering
        print("Starting clustering analysis...")
        results = clustering.perform_site_clustering(n_clusters=5)

        if results:
            print("✅ Clustering analysis completed successfully!")

            # Print cluster information
            cluster_labels = results.get("cluster_labels", [])
            if cluster_labels:
                unique_clusters = len(set(cluster_labels))
                print(f"Number of clusters created: {unique_clusters}")

            # Print cluster characteristics
            cluster_characteristics = results.get("cluster_characteristics", {})
            if cluster_characteristics:
                print(
                    f"Number of cluster characteristics: {len(cluster_characteristics)}"
                )

            # Print quality metrics
            quality_metrics = results.get("quality_metrics", {})
            if quality_metrics:
                print("\nClustering Quality Metrics:")
                print("-" * 25)
                for metric, value in quality_metrics.items():
                    print(f"{metric}: {value}")

            return True
        else:
            print("❌ Clustering analysis failed!")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if db_manager:
            db_manager.disconnect()


def main():
    """Main function to run all ML operations"""
    print("Clinical Trial Site Analysis Platform - ML Operations")
    print("=" * 55)

    # Run predictive model training
    print("\n1. PREDICTIVE MODEL TRAINING")
    predictive_success = train_predictive_model()

    # Run clustering analysis
    print("\n2. CLUSTERING ANALYSIS")
    clustering_success = run_clustering()

    # Summary
    print("\n" + "=" * 55)
    print("ML OPERATIONS SUMMARY")
    print("=" * 55)
    print(f"Predictive Model Training: {'SUCCESS' if predictive_success else 'FAILED'}")
    print(f"Clustering Analysis: {'SUCCESS' if clustering_success else 'FAILED'}")

    overall_success = predictive_success and clustering_success

    if overall_success:
        print("\n✅ All ML operations completed successfully!")
    else:
        print("\n⚠️  Some ML operations completed with issues.")
        print("Check the detailed output above for specific results.")

    print("=" * 55)
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
