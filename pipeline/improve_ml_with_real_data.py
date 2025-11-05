#!/usr/bin/env python3
"""
Enhanced Clinical Trial Site Analysis Pipeline
Downloads real historical data from ClinicalTrials.gov API and retrains ML models
Note: This is a time-consuming process. For faster alternatives, see:
- retrain_ml_with_existing_data.py (uses existing data, no download)
- incremental_ml_update.py (downloads only recent data)
"""

import sys
import os
import time
from datetime import date, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.automated_pipeline import AutomatedPipeline
from database.db_manager import DatabaseManager
from ai_ml.predictive_model import PredictiveEnrollmentModel
from ai_ml.clustering import SiteClustering

def main():
    """Main function to download real data and retrain ML models"""
    print("=" * 60)
    print("Clinical Trial Site Analysis - Enhanced ML Pipeline")
    print("=" * 60)
    print("WARNING: This script downloads ALL historical data from ClinicalTrials.gov")
    print("This process can take several hours to complete!")
    print()
    print("For faster alternatives, consider:")
    print("- retrain_ml_with_existing_data.py (uses existing data, no download)")
    print("- incremental_ml_update.py (downloads only recent data)")
    print("=" * 60)
    print()
    
    # Ask for user confirmation
    response = input("Do you want to continue with the full data download? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled. Consider using the faster alternatives mentioned above.")
        return
    
    print("\nStarting full data download and ML retraining...")
    start_time = time.time()
    
    try:
        # Initialize the automated pipeline
        pipeline = AutomatedPipeline()
        
        # Download historical trials data (last 12 months for demo purposes)
        print("\n1. Downloading historical clinical trials data from ClinicalTrials.gov API...")
        end_date = date.today()
        start_date = end_date - timedelta(days=365)  # Last 12 months
        
        success = pipeline.download_historical_trials(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        if success:
            print("SUCCESS: Historical clinical trials data downloaded")
        else:
            print("FAILED: Historical clinical trials data download")
            return
        
        # Fetch additional historical data for ML training
        print("\n2. Fetching additional historical data for ML training...")
        additional_success = pipeline.fetch_historical_data_for_ml()
        
        if additional_success:
            print("SUCCESS: Additional historical data fetched")
        else:
            print("WARNING: Additional historical data fetch may have issues")
            
        # Calculate metrics
        print("\n3. Calculating site metrics...")
        metrics_success = pipeline.calculate_metrics()
        
        if metrics_success:
            print("SUCCESS: Site metrics calculated")
        else:
            print("WARNING: Site metrics calculation may have issues")
            
        # Initialize database manager for ML models
        print("\n4. Initializing database for ML model training...")
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            print("FAILED: Database connection")
            return
            
        try:
            # Retrain predictive enrollment model
            print("\n5. Retraining Predictive Enrollment Model...")
            predictive_model = PredictiveEnrollmentModel(db_manager)
            
            if predictive_model.is_configured:
                # Prepare training dataset
                print("Preparing training dataset...")
                df = predictive_model.prepare_training_dataset()
                
                if df is not None and len(df) > 0:
                    print(f"Training dataset prepared with {len(df)} records")
                    
                    # Engineer additional features
                    print("Engineering additional features...")
                    df = predictive_model.engineer_additional_features(df)
                    
                    # Train the model
                    print("Training predictive model...")
                    training_success = predictive_model.train_regression_model(df)
                    
                    if training_success:
                        print("SUCCESS: Predictive enrollment model retrained")
                        
                        # Evaluate model performance
                        print("Evaluating model performance...")
                        performance_metrics = predictive_model.evaluate_model_performance(df)
                        if performance_metrics:
                            print("Performance Metrics:")
                            if isinstance(performance_metrics, dict):
                                for metric, value in performance_metrics.items():
                                    print(f"  - {metric}: {value}")
                            else:
                                print(f"  - {performance_metrics}")
                    else:
                        print("FAILED: Predictive enrollment model training")
                else:
                    print("WARNING: No training data available")
            else:
                print("FAILED: Predictive model not configured")
                
            # Retrain site clustering model
            print("\n6. Retraining Site Clustering Model...")
            clustering_model = SiteClustering(db_manager)
            
            if clustering_model.is_configured:
                print("Performing site clustering...")
                clustering_results = clustering_model.perform_site_clustering()
                
                if clustering_results:
                    clusters_found = len(clustering_results.get('cluster_characteristics', {}))
                    print(f"SUCCESS: Site clustering completed with {clusters_found} clusters")
                    
                    # Display some cluster characteristics
                    cluster_characteristics = clustering_results.get('cluster_characteristics', {})
                    if cluster_characteristics:
                        print("Sample Cluster Characteristics:")
                        for cluster_id, characteristics in list(cluster_characteristics.items())[:3]:
                            print(f"  Cluster {cluster_id}:")
                            print(f"    - Size: {characteristics.get('size', 'N/A')} sites")
                            print(f"    - Average completion ratio: {characteristics.get('average_completion_ratio', 0):.2f}")
                            print(f"    - Average recruitment efficiency: {characteristics.get('average_recruitment_efficiency', 0):.2f}")
                            
                    # Display quality metrics
                    quality_metrics = clustering_results.get('quality_metrics', {})
                    if quality_metrics:
                        print("Quality Metrics:")
                        if isinstance(quality_metrics, dict):
                            for metric, value in list(quality_metrics.items())[:3]:
                                print(f"  - {metric}: {value}")
                else:
                    print("FAILED: Site clustering")
            else:
                print("FAILED: Clustering model not configured")
                
        finally:
            db_manager.disconnect()
            
        # Calculate and display total execution time
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"\nTotal execution time: {execution_time:.2f} seconds ({execution_time/60:.2f} minutes)")
        
        print("\n" + "=" * 60)
        print("Enhanced ML Pipeline completed successfully!")
        print("Next time, consider using the faster alternatives for quicker updates.")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR in enhanced ML pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()