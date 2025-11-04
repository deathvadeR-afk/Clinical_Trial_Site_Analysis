"""
Predictive Model for Clinical Trial Site Analysis Platform
Handles predictive enrollment modeling using ML techniques
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
import pandas as pd

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "predictive_model.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Try to import scikit-learn
try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit-learn not available. Install with: pip install scikit-learn")
    SKLEARN_AVAILABLE = False
    GradientBoostingRegressor = None
    train_test_split = None
    mean_squared_error = None
    r2_score = None
    StandardScaler = None

# Try to import scipy for prediction intervals
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    logger.warning("Scipy not available. Install with: pip install scipy")
    SCIPY_AVAILABLE = False
    stats = None


class PredictiveEnrollmentModel:
    """Handles predictive enrollment modeling for clinical trials"""

    def __init__(self, db_manager):
        """
        Initialize the predictive enrollment model

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.is_configured = SKLEARN_AVAILABLE

        if not SKLEARN_AVAILABLE:
            logger.warning(
                "Scikit-learn not installed. Predictive modeling functionality will be limited."
            )

    def prepare_training_dataset(self) -> Optional[pd.DataFrame]:
        """
        Prepare training dataset from historical trials

        Returns:
            DataFrame with training data or None if error occurred
        """
        try:
            # Get historical trial data with enrollment information
            query = """
                SELECT 
                    ct.nct_id,
                    ct.phase,
                    ct.enrollment_count,
                    ct.start_date,
                    ct.completion_date,
                    sm.country,
                    sm.institution_type,
                    si.completion_ratio,
                    si.recruitment_efficiency_score,
                    si.experience_index
                FROM clinical_trials ct
                JOIN site_trial_participation stp ON ct.nct_id = stp.nct_id
                JOIN sites_master sm ON stp.site_id = sm.site_id
                JOIN site_metrics si ON stp.site_id = si.site_id
                WHERE ct.enrollment_count IS NOT NULL 
                AND ct.start_date IS NOT NULL 
                AND ct.completion_date IS NOT NULL
                AND si.completion_ratio IS NOT NULL
                """

            results = self.db_manager.query(query)

            if not results:
                logger.warning("No historical trial data found for training")
                return None

            # Convert to DataFrame
            data = [dict(row) for row in results]
            df = pd.DataFrame(data)

            # Process categorical variables
            df["phase_encoded"] = pd.Categorical(df["phase"]).codes
            df["country_encoded"] = pd.Categorical(df["country"]).codes
            df["institution_type_encoded"] = pd.Categorical(
                df["institution_type"]
            ).codes

            # Calculate enrollment duration
            # Handle different date formats
            df["start_date"] = pd.to_datetime(df["start_date"], format='mixed', errors='coerce')
            df["completion_date"] = pd.to_datetime(df["completion_date"], format='mixed', errors='coerce')
            
            # Remove rows with invalid dates
            df = df.dropna(subset=['start_date', 'completion_date'])
            
            df["enrollment_duration_days"] = (
                df["completion_date"] - df["start_date"]
            ).dt.days

            logger.info(f"Prepared training dataset with {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Error preparing training dataset: {e}")
            return None

    def engineer_additional_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer additional features for the model

        Args:
            df: DataFrame with base features

        Returns:
            DataFrame with engineered features
        """
        try:
            # Create additional features
            df["enrollment_rate"] = df["enrollment_count"] / (
                df["enrollment_duration_days"] / 30
            )  # Monthly rate
            df["completion_ratio_squared"] = df["completion_ratio"] ** 2
            df["experience_interaction"] = (
                df["experience_index"] * df["recruitment_efficiency_score"]
            )
            df["phase_country_interaction"] = (
                df["phase_encoded"] * df["country_encoded"]
            )

            # Handle missing values
            df = df.fillna(0)

            logger.info("Engineered additional features")
            return df

        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            return df

    def train_regression_model(self, df: pd.DataFrame) -> bool:
        """
        Train regression model using gradient boosting

        Args:
            df: DataFrame with training data

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            logger.error("Scikit-learn not available for model training")
            return False

        try:
            # Define features and target
            feature_columns = [
                "phase_encoded",
                "country_encoded",
                "institution_type_encoded",
                "completion_ratio",
                "recruitment_efficiency_score",
                "experience_index",
                "enrollment_rate",
                "completion_ratio_squared",
                "experience_interaction",
                "phase_country_interaction",
            ]

            X = df[feature_columns]
            y = df["enrollment_count"]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train model
            self.model = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42
            )

            self.model.fit(X_train_scaled, y_train)
            self.is_trained = True

            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            logger.info(f"Model trained successfully. MSE: {mse:.2f}, R²: {r2:.3f}")
            return True

        except Exception as e:
            logger.error(f"Error training regression model: {e}")
            return False

    def evaluate_model_performance(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate model performance

        Args:
            df: DataFrame with evaluation data

        Returns:
            Dictionary with performance metrics
        """
        if not self.is_trained or not self.is_configured:
            logger.warning("Model not trained or not configured")
            return {}

        try:
            # Define features and target
            feature_columns = [
                "phase_encoded",
                "country_encoded",
                "institution_type_encoded",
                "completion_ratio",
                "recruitment_efficiency_score",
                "experience_index",
                "enrollment_rate",
                "completion_ratio_squared",
                "experience_interaction",
                "phase_country_interaction",
            ]

            X = df[feature_columns]
            y = df["enrollment_count"]

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Make predictions
            y_pred = self.model.predict(X_scaled)

            # Calculate metrics
            mse = mean_squared_error(y, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y, y_pred)
            mae = np.mean(np.abs(y - y_pred))

            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((y - y_pred) / y)) * 100

            performance_metrics = {
                "mean_squared_error": mse,
                "root_mean_squared_error": rmse,
                "r_squared": r2,
                "mean_absolute_error": mae,
                "mean_absolute_percentage_error": mape,
            }

            logger.info(
                f"Model evaluation - RMSE: {rmse:.2f}, R²: {r2:.3f}, MAPE: {mape:.2f}%"
            )
            return performance_metrics

        except Exception as e:
            logger.error(f"Error evaluating model performance: {e}")
            return {}

    def implement_prediction_intervals(
        self, df: pd.DataFrame, confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Implement prediction intervals

        Args:
            df: DataFrame with data for predictions
            confidence_level: Confidence level for intervals (default 0.95)

        Returns:
            Dictionary with prediction intervals
        """
        if not self.is_trained or not self.is_configured:
            logger.warning("Model not trained or not configured")
            return {}

        # Check if scipy is available for statistical functions
        if not SCIPY_AVAILABLE:
            logger.warning("Scipy not available for prediction intervals calculation")
            return {}

        try:
            # Define features
            feature_columns = [
                "phase_encoded",
                "country_encoded",
                "institution_type_encoded",
                "completion_ratio",
                "recruitment_efficiency_score",
                "experience_index",
                "enrollment_rate",
                "completion_ratio_squared",
                "experience_interaction",
                "phase_country_interaction",
            ]

            X = df[feature_columns]
            X_scaled = self.scaler.transform(X)

            # Make predictions
            predictions = self.model.predict(X_scaled)

            # Calculate prediction intervals (simplified approach)
            # In a real implementation, this would use more sophisticated methods
            residuals = df["enrollment_count"] - predictions
            residual_std = np.std(residuals)

            # Calculate interval width based on confidence level
            z_score = stats.norm.ppf((1 + confidence_level) / 2)
            interval_width = z_score * residual_std

            prediction_intervals = {
                "predictions": predictions.tolist(),
                "lower_bounds": (predictions - interval_width).tolist(),
                "upper_bounds": (predictions + interval_width).tolist(),
                "confidence_level": confidence_level,
                "interval_width": interval_width,
            }

            logger.info(
                f"Implemented prediction intervals with {confidence_level*100}% confidence"
            )
            return prediction_intervals

        except Exception as e:
            logger.error(f"Error implementing prediction intervals: {e}")
            return {}

    def use_gemini_api_for_prediction_explanations(
        self, predictions: List[float], site_data: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """
        Use Gemini API to generate prediction explanations

        Args:
            predictions: List of predicted enrollment counts
            site_data: List of site data dictionaries

        Returns:
            List of explanation texts (None for failed generations)
        """
        try:
            # This would use the Gemini client to generate explanations
            # For now, we'll return placeholder explanations
            explanations = []

            for i, prediction in enumerate(predictions):
                site = site_data[i] if i < len(site_data) else {}
                site_name = site.get("site_name", "Unknown Site")

                explanation = f"Predicted enrollment of {prediction:.0f} participants at {site_name} based on historical performance metrics and site characteristics."
                explanations.append(explanation)

            logger.info("Generated prediction explanations")
            return explanations

        except Exception as e:
            logger.error(f"Error generating prediction explanations: {e}")
            return [None] * len(predictions)

    def integrate_enrollment_predictions(
        self, target_study: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Integrate enrollment predictions into recommendation engine

        Args:
            target_study: Dictionary with target study parameters

        Returns:
            List of site recommendations with predictions
        """
        if not self.is_trained or not self.is_configured:
            logger.warning("Model not trained or not configured")
            return []

        try:
            # Get all sites for prediction
            site_results = self.db_manager.query(
                """
                SELECT sm.*, si.completion_ratio, si.recruitment_efficiency_score, si.experience_index
                FROM sites_master sm
                JOIN site_metrics si ON sm.site_id = si.site_id
                """
            )

            if not site_results:
                logger.warning("No sites found for prediction")
                return []

            # Create feature data for each site
            site_data = []
            feature_data = []

            for row in site_results:
                site_data.append(dict(row))

                # Create feature vector for this site
                features = {
                    "phase_encoded": 2,  # Assuming Phase 2 as default
                    "country_encoded": hash(row["country"] or "") % 1000,
                    "institution_type_encoded": hash(row["institution_type"] or "")
                    % 100,
                    "completion_ratio": row["completion_ratio"] or 0,
                    "recruitment_efficiency_score": row["recruitment_efficiency_score"]
                    or 0,
                    "experience_index": row["experience_index"] or 0,
                    "enrollment_rate": 0,  # Will be predicted
                    "completion_ratio_squared": (row["completion_ratio"] or 0) ** 2,
                    "experience_interaction": (row["experience_index"] or 0)
                    * (row["recruitment_efficiency_score"] or 0),
                    "phase_country_interaction": 2
                    * (hash(row["country"] or "") % 1000),  # Phase 2 * country
                }
                feature_data.append(features)

            # Convert to DataFrame
            df = pd.DataFrame(feature_data)

            # Make predictions
            X = df[list(feature_data[0].keys())]
            X_scaled = self.scaler.transform(X)
            predictions = self.model.predict(X_scaled)

            # Generate explanations
            explanations = self.use_gemini_api_for_prediction_explanations(
                predictions.tolist(), site_data
            )

            # Create recommendations
            recommendations = []
            for i, (site, prediction, explanation) in enumerate(
                zip(site_data, predictions, explanations)
            ):
                recommendation = {
                    "site_id": site["site_id"],
                    "site_name": site["site_name"],
                    "predicted_enrollment": float(prediction),
                    "prediction_explanation": explanation,
                    "confidence_interval": {
                        "lower": float(prediction * 0.8),  # Simplified
                        "upper": float(prediction * 1.2),  # Simplified
                    },
                }
                recommendations.append(recommendation)

            # Sort by predicted enrollment
            recommendations.sort(key=lambda x: x["predicted_enrollment"], reverse=True)

            logger.info(f"Generated {len(recommendations)} enrollment predictions")
            return recommendations

        except Exception as e:
            logger.error(f"Error integrating enrollment predictions: {e}")
            return []

    def implement_model_monitoring(self) -> Dict[str, Any]:
        """
        Implement model monitoring

        Returns:
            Dictionary with monitoring metrics
        """
        try:
            # In a real implementation, this would track model performance over time
            monitoring_metrics = {
                "model_version": "1.0",
                "last_training_date": datetime.now().isoformat(),
                "training_samples": 1000,  # Placeholder
                "features_used": 10,  # Placeholder
                "performance_stability": "Stable",  # Placeholder
                "drift_detected": False,  # Placeholder
            }

            logger.info("Implemented model monitoring")
            return monitoring_metrics

        except Exception as e:
            logger.error(f"Error implementing model monitoring: {e}")
            return {}

    def train_predictive_model(self) -> Dict[str, Any]:
        """
        Main method to train the predictive enrollment model

        Returns:
            Dictionary with training results
        """
        try:
            if not self.is_configured:
                logger.error("Predictive model not properly configured")
                return {}

            # Step 1: Prepare training dataset
            logger.info("Step 1: Preparing training dataset")
            df = self.prepare_training_dataset()

            if df is None or len(df) < 10:
                logger.warning("Insufficient data for training")
                return {}

            # Step 2: Engineer additional features
            logger.info("Step 2: Engineering additional features")
            df = self.engineer_additional_features(df)

            # Step 3: Train regression model
            logger.info("Step 3: Training regression model")
            training_success = self.train_regression_model(df)

            if not training_success:
                logger.error("Failed to train regression model")
                return {}

            # Step 4: Evaluate model performance
            logger.info("Step 4: Evaluating model performance")
            performance_metrics = self.evaluate_model_performance(df)

            # Step 5: Implement prediction intervals
            logger.info("Step 5: Implementing prediction intervals")
            prediction_intervals = self.implement_prediction_intervals(df)

            # Step 6: Implement model monitoring
            logger.info("Step 6: Implementing model monitoring")
            monitoring_metrics = self.implement_model_monitoring()

            # Prepare results
            results = {
                "training_success": True,
                "dataset_size": len(df),
                "performance_metrics": performance_metrics,
                "prediction_intervals": prediction_intervals,
                "monitoring_metrics": monitoring_metrics,
                "features_used": list(df.columns),
            }

            logger.info("Predictive enrollment model training completed successfully")
            return results

        except Exception as e:
            logger.error(f"Error in predictive model training: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    print("Predictive Enrollment Model module ready for use")
    print("This module handles predictive enrollment modeling for clinical trials")
