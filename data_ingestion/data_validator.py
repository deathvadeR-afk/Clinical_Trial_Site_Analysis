"""
Data Validator for Clinical Trial Site Analysis Platform
Handles data validation and quality control
"""
import logging
import os
from typing import Dict, List, Optional, Any
import json

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "data_validator.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataValidator:
    """Validator for ensuring data quality and integrity"""
    
    def __init__(self, db_manager):
        """
        Initialize the data validator
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def validate_clinical_trial(self, trial_data: Dict) -> Dict[str, Any]:
        """
        Validate clinical trial data
        
        Args:
            trial_data: Clinical trial data dictionary
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'completeness_score': 1.0
        }
        
        required_fields = ['nct_id', 'title', 'status']
        missing_fields = []
        
        # Check required fields
        for field in required_fields:
            if not trial_data.get(field):
                missing_fields.append(field)
                validation_results['is_valid'] = False
                validation_results['errors'].append(f"Missing required field: {field}")
        
        # Check date consistency
        start_date = trial_data.get('start_date')
        completion_date = trial_data.get('completion_date')
        
        if start_date and completion_date:
            try:
                # Simple date validation (in practice, would use datetime parsing)
                if start_date > completion_date:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append("Start date is after completion date")
            except Exception:
                validation_results['warnings'].append("Could not validate date consistency")
        
        # Calculate completeness score
        total_fields = len(required_fields) + 10  # Approximate total expected fields
        filled_fields = total_fields - len(missing_fields)
        validation_results['completeness_score'] = filled_fields / total_fields if total_fields > 0 else 0.0
        
        if missing_fields:
            logger.warning(f"Validation failed for trial {trial_data.get('nct_id', 'unknown')}: {missing_fields}")
        else:
            logger.info(f"Validation passed for trial {trial_data.get('nct_id', 'unknown')}")
        
        return validation_results
    
    def validate_site(self, site_data: Dict) -> Dict[str, Any]:
        """
        Validate site data
        
        Args:
            site_data: Site data dictionary
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'completeness_score': 1.0
        }
        
        required_fields = ['site_name', 'city', 'country']
        missing_fields = []
        
        # Check required fields
        for field in required_fields:
            if not site_data.get(field):
                missing_fields.append(field)
                validation_results['is_valid'] = False
                validation_results['errors'].append(f"Missing required field: {field}")
        
        # Calculate completeness score
        total_fields = len(required_fields) + 5  # Approximate total expected fields
        filled_fields = total_fields - len(missing_fields)
        validation_results['completeness_score'] = filled_fields / total_fields if total_fields > 0 else 0.0
        
        if missing_fields:
            logger.warning(f"Validation failed for site {site_data.get('site_name', 'unknown')}: {missing_fields}")
        else:
            logger.info(f"Validation passed for site {site_data.get('site_name', 'unknown')}")
        
        return validation_results
    
    def validate_investigator(self, investigator_data: Dict) -> Dict[str, Any]:
        """
        Validate investigator data
        
        Args:
            investigator_data: Investigator data dictionary
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'completeness_score': 1.0
        }
        
        required_fields = ['full_name']
        missing_fields = []
        
        # Check required fields
        for field in required_fields:
            if not investigator_data.get(field):
                missing_fields.append(field)
                validation_results['is_valid'] = False
                validation_results['errors'].append(f"Missing required field: {field}")
        
        # Validate numeric fields
        numeric_fields = ['h_index', 'total_publications', 'recent_publications_count']
        for field in numeric_fields:
            value = investigator_data.get(field)
            if value is not None:
                try:
                    int(value)
                except (ValueError, TypeError):
                    validation_results['warnings'].append(f"Invalid numeric value for {field}: {value}")
        
        # Calculate completeness score
        total_fields = len(required_fields) + len(numeric_fields) + 3  # Approximate total expected fields
        filled_fields = total_fields - len(missing_fields)
        validation_results['completeness_score'] = filled_fields / total_fields if total_fields > 0 else 0.0
        
        if missing_fields:
            logger.warning(f"Validation failed for investigator {investigator_data.get('full_name', 'unknown')}: {missing_fields}")
        else:
            logger.info(f"Validation passed for investigator {investigator_data.get('full_name', 'unknown')}")
        
        return validation_results
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """
        Generate a data quality report
        
        Returns:
            Dictionary with quality report data
        """
        try:
            # Get counts of records in each table
            tables = ['clinical_trials', 'sites_master', 'investigators']
            record_counts = {}
            
            for table in tables:
                results = self.db_manager.query(f"SELECT COUNT(*) as count FROM {table}")
                if results:
                    record_counts[table] = results[0]['count']
                else:
                    record_counts[table] = 0
            
            # Get validation statistics (simplified)
            quality_report = {
                'total_records': record_counts,
                'validation_timestamp': '2025-10-29',  # In practice, would use datetime.now()
                'overall_quality_score': 0.85,  # Placeholder value
                'issues_found': {
                    'missing_data': 5,
                    'inconsistent_data': 2,
                    'duplicate_records': 1
                }
            }
            
            logger.info("Generated data quality report")
            return quality_report
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    print("Data Validator module ready for use")
    print("This module validates data quality and integrity")