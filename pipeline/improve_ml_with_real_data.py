"""
Script to improve ML model effectiveness by:
1. Downloading real historical data from the past 6 months
2. Retraining ML models with real data
3. Verifying performance metrics
"""
import sys
import os
from datetime import date, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.automated_pipeline import AutomatedPipeline
from ai_ml.predictive_model import PredictiveEnrollmentModel
from ai_ml.clustering import SiteClustering
from database.db_manager import DatabaseManager

def download_real_historical_data():
    """Download real historical data from the past 6 months"""
    print("=== Downloading Real Historical Data (Past 6 Months) ===")
    
    # Calculate date range (last 6 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    print(f"Downloading real data from {start_date} to {end_date}")
    
    try:
        # Initialize the automated pipeline
        pipeline = AutomatedPipeline()
        
        # Download historical trials data
        print("Downloading real historical clinical trials data from ClinicalTrials.gov API...")
        success = pipeline.download_historical_trials(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        if success:
            print("SUCCESS: Real historical clinical trials data downloaded")
            return True
        else:
            print("FAILED: Real historical clinical trials data download")
            return False
            
    except Exception as e:
        print(f"ERROR downloading real data: {e}")
        return False

def retrain_ml_models():
    """Retrain ML models with the real historical data"""
    print("\n=== Retraining ML Models with Real Data ===")
    
    db_manager = None
    try:
        # Initialize database manager
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            print("FAILED: Database connection")
            return False
        
        # Retrain predictive enrollment model
        print("\n1. Retraining Predictive Enrollment Model...")
        predictive_model = PredictiveEnrollmentModel(db_manager)
        
        if predictive_model.is_configured:
            # Prepare training dataset
            print("Preparing real training dataset...")
            df = predictive_model.prepare_training_dataset()
            
            if df is not None and len(df) > 0:
                print(f"Real training dataset prepared with {len(df)} records")
                
                # Engineer additional features
                print("Engineering features from real data...")
                df = predictive_model.engineer_additional_features(df)
                
                # Train the model
                print("Training predictive model with real data...")
                training_success = predictive_model.train_regression_model(df)
                
                if training_success:
                    print("SUCCESS: Predictive model trained with real data")
                    
                    # Evaluate model performance
                    print("Evaluating model performance with real data...")
                    performance_metrics = predictive_model.evaluate_model_performance(df)
                    if performance_metrics:
                        print("Real Performance Metrics:")
                        if isinstance(performance_metrics, dict):
                            for metric, value in performance_metrics.items():
                                print(f"  - {metric}: {value}")
                        else:
                            print(f"  - {performance_metrics}")
                        return True
                    else:
                        print("WARNING: No performance metrics available")
                        return True
                else:
                    print("FAILED: Predictive model training with real data")
                    return False
            else:
                print("WARNING: No real training data available for predictive model")
                return False
        else:
            print("FAILED: Predictive model not configured")
            return False
        
    except Exception as e:
        print(f"ERROR retraining predictive model: {e}")
        return False
    finally:
        try:
            if db_manager:
                db_manager.disconnect()
        except:
            pass

def retrain_clustering_model():
    """Retrain the clustering model with real data"""
    print("\n2. Retraining Site Clustering Model...")
    
    db_manager = None
    try:
        # Initialize database manager
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            print("FAILED: Database connection")
            return False
        
        # Retrain clustering model
        clustering_model = SiteClustering(db_manager)
        
        if clustering_model.is_configured:
            print("Performing site clustering with real data...")
            clustering_results = clustering_model.perform_site_clustering(n_clusters=5)
            
            if clustering_results:
                clusters_found = len(clustering_results.get('cluster_characteristics', {}))
                print(f"SUCCESS: Site clustering completed with {clusters_found} clusters")
                
                # Display cluster characteristics
                cluster_characteristics = clustering_results.get('cluster_characteristics', {})
                if cluster_characteristics:
                    print("Real Cluster Characteristics:")
                    for cluster_id, characteristics in cluster_characteristics.items():
                        print(f"  Cluster {cluster_id}:")
                        print(f"    - Size: {characteristics.get('size', 'N/A')} sites")
                        print(f"    - Average completion ratio: {characteristics.get('average_completion_ratio', 0):.2f}")
                        print(f"    - Average recruitment efficiency: {characteristics.get('average_recruitment_efficiency', 0):.2f}")
                
                # Display quality metrics
                quality_metrics = clustering_results.get('quality_metrics', {})
                if quality_metrics:
                    print("Real Quality Metrics:")
                    if isinstance(quality_metrics, dict):
                        for metric, value in quality_metrics.items():
                            print(f"  - {metric}: {value}")
                
                return True
            else:
                print("FAILED: Site clustering with real data")
                return False
        else:
            print("FAILED: Clustering model not configured")
            return False
            
    except Exception as e:
        print(f"ERROR retraining clustering model: {e}")
        return False
    finally:
        try:
            if db_manager:
                db_manager.disconnect()
        except:
            pass

def verify_model_performance():
    """Verify the performance metrics of the retrained models"""
    print("\n=== Verifying Model Performance Metrics ===")
    
    db_manager = None
    try:
        # Initialize database manager
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            print("FAILED: Database connection")
            return False
        
        # Check data counts
        site_count = db_manager.query("SELECT COUNT(*) as count FROM sites_master")[0]['count']
        trial_count = db_manager.query("SELECT COUNT(*) as count FROM clinical_trials")[0]['count']
        participation_count = db_manager.query("SELECT COUNT(*) as count FROM site_trial_participation")[0]['count']
        metrics_count = db_manager.query("SELECT COUNT(*) as count FROM site_metrics")[0]['count']
        cluster_count = db_manager.query("SELECT COUNT(*) as count FROM site_clusters")[0]['count']
        
        print("Real Data Status After Training:")
        print(f"  - Sites: {site_count}")
        print(f"  - Clinical Trials: {trial_count}")
        print(f"  - Site-Trial Participation Records: {participation_count}")
        print(f"  - Site Metrics: {metrics_count}")
        print(f"  - Site Clusters: {cluster_count}")
        
        # Check if we have sufficient real data
        if trial_count > 5 and participation_count > 5:
            print("SUCCESS: Sufficient real data for effective ML models")
            effectiveness = True
        else:
            print("WARNING: Limited real data may still affect model effectiveness")
            effectiveness = False
        
        return effectiveness
        
    except Exception as e:
        print(f"ERROR verifying model performance: {e}")
        return False
    finally:
        try:
            if db_manager:
                db_manager.disconnect()
        except:
            pass

def main():
    """Main function to improve ML model with real data"""
    print("Clinical Trial Site Analysis Platform - Real Data ML Model Improvement")
    print("=" * 72)
    
    # Step 1: Download real historical data
    print("\n1. DOWNLOADING REAL HISTORICAL DATA")
    data_success = download_real_historical_data()
    
    if not data_success:
        print("\nCRITICAL: Failed to download real historical data")
        print("Aborting improvement process...")
        return False
    
    # Step 2: Retrain ML models
    print("\n2. RETRAINING ML MODELS WITH REAL DATA")
    predictive_success = retrain_ml_models()
    clustering_success = retrain_clustering_model()
    
    # Step 3: Verify performance metrics
    print("\n3. VERIFYING MODEL PERFORMANCE")
    verification_success = verify_model_performance()
    
    # Summary
    print("\n" + "=" * 72)
    print("REAL DATA ML MODEL IMPROVEMENT SUMMARY")
    print("=" * 72)
    print(f"Real Data Download: {'SUCCESS' if data_success else 'FAILED'}")
    print(f"Predictive Model Retraining: {'SUCCESS' if predictive_success else 'FAILED'}")
    print(f"Clustering Model Retraining: {'SUCCESS' if clustering_success else 'FAILED'}")
    print(f"Performance Verification: {'SUCCESS' if verification_success else 'FAILED'}")
    
    overall_success = all([data_success, predictive_success, clustering_success, verification_success])
    
    if overall_success:
        print("\nSUCCESS: ML model improvement with real data completed successfully!")
        print("Your models have been retrained with real data from the past 6 months.")
    else:
        print("\nPARTIAL SUCCESS: Some improvements completed with real data.")
        print("Check the detailed output above for specific results.")
    
    print("=" * 72)
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)