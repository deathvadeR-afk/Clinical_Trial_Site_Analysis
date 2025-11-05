#!/usr/bin/env python3
"""
Script to populate PubMed publications data and calculate data quality scores.
"""

import sys
import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from data_ingestion.pubmed_api import PubMedAPI
from data_ingestion.data_validator import DataValidator
from pipeline.data_quality_monitor import DataQualityMonitor
from utils.config import get_api_keys

def setup_logging():
    """Set up logging for the script."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "populate_pubmed_data.log")),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)

def calculate_site_data_quality_scores(db_manager, site_id: int) -> Dict[str, Any]:
    """
    Calculate data quality scores for a specific site.
    
    Args:
        db_manager: Database manager instance
        site_id: ID of the site to calculate scores for
        
    Returns:
        Dictionary with quality scores
    """
    # Import datetime here to ensure it's available
    from datetime import datetime
    
    try:
        # Calculate completeness score (percentage of required fields that are filled)
        completeness_query = """
            SELECT 
                COUNT(*) as total_fields,
                SUM(CASE WHEN site_name IS NOT NULL AND site_name != '' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN city IS NOT NULL AND city != '' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN country IS NOT NULL AND country != '' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN latitude IS NOT NULL THEN 1 ELSE 0 END) +
                SUM(CASE WHEN longitude IS NOT NULL THEN 1 ELSE 0 END)
                as filled_fields
            FROM sites_master 
            WHERE site_id = ?
        """
        
        completeness_result = db_manager.query(completeness_query, (site_id,))
        
        if completeness_result and len(completeness_result) > 0:
            row = completeness_result[0]
            total_fields = row["total_fields"] * 5  # 5 required fields
            filled_fields = row["filled_fields"] or 0
            completeness_score = filled_fields / total_fields if total_fields > 0 else 0
        else:
            completeness_score = 0
        
        # Calculate recency score (how recently the site data was updated)
        recency_query = """
            SELECT last_updated 
            FROM sites_master 
            WHERE site_id = ? AND last_updated IS NOT NULL
        """
        
        recency_result = db_manager.query(recency_query, (site_id,))
        
        if recency_result and len(recency_result) > 0:
            # Simple recency score: 1.0 for recently updated, decreasing over time
            from datetime import datetime
            last_updated_str = recency_result[0]["last_updated"]
            try:
                last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                days_since_update = (datetime.now().astimezone() - last_updated).days
                # Recency score: 1.0 for today, 0.5 for 30 days ago, 0.0 for 90+ days ago
                if days_since_update <= 30:
                    recency_score = 1.0 - (days_since_update / 60)
                elif days_since_update <= 90:
                    recency_score = 0.5 - ((days_since_update - 30) / 120)
                else:
                    recency_score = 0.0
                recency_score = max(0.0, min(1.0, recency_score))
            except Exception:
                recency_score = 0.5  # Default score if parsing fails
        else:
            recency_score = 0.0
        
        # Calculate consistency score (based on data patterns)
        # For simplicity, we'll use a fixed score based on the presence of trial participation data
        participation_query = """
            SELECT COUNT(*) as participation_count
            FROM site_trial_participation
            WHERE site_id = ?
        """
        
        participation_result = db_manager.query(participation_query, (site_id,))
        
        if participation_result and len(participation_result) > 0:
            participation_count = participation_result[0]["participation_count"] or 0
            # Consistency score: higher for sites with more participation records
            consistency_score = min(1.0, participation_count / 50.0)  # Max score at 50 records
        else:
            consistency_score = 0.0
        
        # Calculate overall quality score as average of component scores
        overall_quality_score = (completeness_score + recency_score + consistency_score) / 3
        
        # Identify missing fields
        missing_fields_query = """
            SELECT 
                CASE WHEN site_name IS NULL OR site_name = '' THEN 'site_name' ELSE NULL END as missing_site_name,
                CASE WHEN city IS NULL OR city = '' THEN 'city' ELSE NULL END as missing_city,
                CASE WHEN country IS NULL OR country = '' THEN 'country' ELSE NULL END as missing_country,
                CASE WHEN latitude IS NULL THEN 'latitude' ELSE NULL END as missing_latitude,
                CASE WHEN longitude IS NULL THEN 'longitude' ELSE NULL END as missing_longitude
            FROM sites_master 
            WHERE site_id = ?
        """
        
        missing_fields_result = db_manager.query(missing_fields_query, (site_id,))
        missing_fields = []
        
        if missing_fields_result and len(missing_fields_result) > 0:
            row = missing_fields_result[0]
            for field in ['missing_site_name', 'missing_city', 'missing_country', 'missing_latitude', 'missing_longitude']:
                if row[field] is not None:
                    missing_fields.append(row[field].replace('missing_', ''))
        
        # Calculate last update lag
        if recency_result and len(recency_result) > 0 and 'last_updated' in recency_result[0]:
            try:
                from datetime import datetime
                last_updated_str = recency_result[0]["last_updated"]
                last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                last_update_lag_days = (datetime.now().astimezone() - last_updated).days
            except Exception:
                last_update_lag_days = 0
        else:
            last_update_lag_days = 0
        
        return {
            "completeness_score": completeness_score,
            "recency_score": recency_score,
            "consistency_score": consistency_score,
            "overall_quality_score": overall_quality_score,
            "missing_fields": missing_fields,
            "last_update_lag_days": last_update_lag_days,
            "calculation_date": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating data quality scores for site {site_id}: {e}")
        return {}

def populate_pubmed_publications():
    """Populate PubMed publications data for investigators."""
    logger = setup_logging()
    logger.info("Starting PubMed publications data population...")
    
    db_manager = None
    pubmed_api = None
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Get API keys from config
        api_keys = get_api_keys()
        pubmed_api_key = api_keys.get("pubmed")
        
        # Initialize PubMed API with API key and database manager from config
        pubmed_api = PubMedAPI(api_key=pubmed_api_key, db_manager=db_manager)
        
        # Get all investigators
        investigator_results = db_manager.query("SELECT investigator_id, full_name FROM investigators")
        
        if not investigator_results:
            logger.warning("No investigators found in database")
            return False
        
        logger.info(f"Found {len(investigator_results)} investigators to process")
        
        processed_count = 0
        success_count = 0
        
        # Process each investigator
        for row in investigator_results:
            investigator_id = row["investigator_id"]
            full_name = row["full_name"]
            
            processed_count += 1
            logger.info(f"Processing investigator {processed_count}/{len(investigator_results)}: {full_name} (ID: {investigator_id})")
            
            try:
                # Search for publications by investigator name
                search_result = pubmed_api.search_authors(full_name, date_range=("2020/01/01", "2025/12/31"))
                
                if search_result and "esearchresult" in search_result:
                    pmids = search_result["esearchresult"].get("idlist", [])[:5]  # Limit to 5 publications
                    
                    if pmids:
                        # Get publication details
                        pub_details = pubmed_api.get_publication_details(pmids)
                        
                        if pub_details and "text" in pub_details:
                            # Parse XML to extract publication data
                            publications = pubmed_api.parse_publication_xml(pub_details["text"])
                            
                            if publications:
                                # Store publication records
                                success = pubmed_api.store_publication_records(
                                    publications,
                                    investigator_id=investigator_id
                                )
                                
                                if success:
                                    success_count += 1
                                    logger.info(f"Successfully stored {len(publications)} publications for investigator {investigator_id}")
                                else:
                                    logger.warning(f"Failed to store publications for investigator {investigator_id}")
                            else:
                                logger.warning(f"No publications parsed for investigator {investigator_id}")
                        else:
                            logger.warning(f"No publication details found for investigator {investigator_id}")
                    else:
                        logger.info(f"No publications found for investigator {investigator_id}")
                else:
                    logger.warning(f"Search failed for investigator {investigator_id}")
                    
            except Exception as e:
                logger.error(f"Error processing investigator {investigator_id}: {e}")
                continue
        
        logger.info(f"Completed PubMed publications data population. Processed: {processed_count}, Successful: {success_count}")
        return True
        
    except Exception as e:
        logger.error(f"Error in PubMed publications data population: {e}")
        return False
    finally:
        try:
            if db_manager:
                db_manager.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")

def calculate_data_quality_scores():
    """Calculate data quality scores for all sites."""
    logger = setup_logging()
    logger.info("Starting data quality scores calculation...")
    
    db_manager = None
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager("clinical_trials.db")
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Initialize data validator
        data_validator = DataValidator(db_manager)
        
        # Get all sites
        site_results = db_manager.query("SELECT site_id FROM sites_master")
        
        if not site_results:
            logger.warning("No sites found in database")
            return False
        
        logger.info(f"Found {len(site_results)} sites to process")
        
        processed_count = 0
        success_count = 0
        
        # Process each site
        for row in site_results:
            site_id = row["site_id"]
            
            processed_count += 1
            logger.info(f"Processing site {processed_count}/{len(site_results)}: ID {site_id}")
            
            try:
                # Calculate data quality scores for this site
                # Calculate data quality scores for this site
                quality_scores = calculate_site_data_quality_scores(db_manager, site_id)
                
                if quality_scores:
                    # Prepare data for insertion
                    quality_data = {
                        "site_id": site_id,
                        "completeness_score": quality_scores.get("completeness_score", 0),
                        "recency_score": quality_scores.get("recency_score", 0),
                        "consistency_score": quality_scores.get("consistency_score", 0),
                        "overall_quality_score": quality_scores.get("overall_quality_score", 0),
                        "missing_fields": json.dumps(quality_scores.get("missing_fields", [])),
                        "last_update_lag_days": quality_scores.get("last_update_lag_days", 0),
                        "calculation_date": quality_scores.get("calculation_date", ""),
                    }
                    
                    # Insert or update data quality scores
                    existing = db_manager.query(
                        "SELECT quality_id FROM data_quality_scores WHERE site_id = ?", 
                        (site_id,)
                    )
                    
                    if existing:
                        # Update existing record, excluding nct_id which may not be in quality_data
                        update_fields = [key for key in quality_data.keys() if key != "site_id" and key != "nct_id"]
                        set_clause = ", ".join([f"{key} = ?" for key in update_fields])
                        values = [quality_data[key] for key in update_fields] + [site_id]
                        sql = f"UPDATE data_quality_scores SET {set_clause} WHERE site_id = ?"
                        success = db_manager.execute(sql, tuple(values))
                    else:
                        # Insert new record
                        success = db_manager.insert_data("data_quality_scores", quality_data)
                    
                    if success:
                        success_count += 1
                        logger.info(f"Successfully calculated and stored quality scores for site {site_id}")
                    else:
                        logger.warning(f"Failed to store quality scores for site {site_id}")
                else:
                    logger.warning(f"No quality scores calculated for site {site_id}")
                    
            except Exception as e:
                logger.error(f"Error processing site {site_id}: {e}")
                continue
        
        logger.info(f"Completed data quality scores calculation. Processed: {processed_count}, Successful: {success_count}")
        return True
        
    except Exception as e:
        logger.error(f"Error in data quality scores calculation: {e}")
        return False
    finally:
        try:
            if db_manager:
                db_manager.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")

def main():
    """Main function."""
    print("Clinical Trial Site Analysis - PubMed Data Population and Quality Scores")
    print("=" * 75)
    
    # Populate PubMed publications data
    print("\n1. Populating PubMed publications data...")
    pubmed_success = populate_pubmed_publications()
    
    if pubmed_success:
        print("✓ PubMed publications data population completed!")
    else:
        print("✗ PubMed publications data population failed!")
    
    # Calculate data quality scores
    print("\n2. Calculating data quality scores...")
    quality_success = calculate_data_quality_scores()
    
    if quality_success:
        print("✓ Data quality scores calculation completed!")
    else:
        print("✗ Data quality scores calculation failed!")
    
    # Run data quality monitoring to generate report
    print("\n3. Running data quality monitoring...")
    monitor = DataQualityMonitor()
    monitoring_success = monitor.run_monitoring()
    
    if monitoring_success:
        print("✓ Data quality monitoring completed!")
    else:
        print("✗ Data quality monitoring failed!")
    
    if pubmed_success and quality_success and monitoring_success:
        print("\n🎉 All operations completed successfully!")
    else:
        print("\n⚠️  Some operations failed. Check logs for details.")

if __name__ == "__main__":
    main()