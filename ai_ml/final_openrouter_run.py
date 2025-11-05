#!/usr/bin/env python3
"""
Final run to generate AI insights for all sites using OpenRouter
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import DatabaseManager
from analytics.strengths_weaknesses import StrengthsWeaknessesDetector
from ai_ml.openrouter_client import OpenRouterClient

def setup_logging():
    """Set up logging for the script."""
    log_dir = "../logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "final_openrouter_run.log")),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)

def final_openrouter_run():
    """Generate AI insights for all sites using OpenRouter"""
    logger = setup_logging()
    logger.info("Starting final OpenRouter AI insights generation...")
    
    db_manager = None
    try:
        # Initialize database manager
        db_manager = DatabaseManager("../../clinical_trials.db")
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Initialize components
        strengths_detector = StrengthsWeaknessesDetector(db_manager)
        
        # Initialize OpenRouter client with the provided API key
        openrouter_api_key = "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"
        openrouter_client = OpenRouterClient(api_key=openrouter_api_key, model_name="meta-llama/llama-3.3-70b-instruct:free")
        
        if not openrouter_client.is_configured:
            logger.error("OpenRouter client not configured properly")
            return False
        
        logger.info("OpenRouter client configured successfully")
        
        # Get all sites
        site_results = db_manager.query("SELECT site_id, site_name FROM sites_master ORDER BY site_id")
        
        if not site_results:
            logger.warning("No sites found in database")
            return False
        
        logger.info(f"Found {len(site_results)} sites to process")
        
        processed_count = 0
        success_count = 0
        openrouter_count = 0
        error_count = 0
        
        # Process each site
        for row in site_results:
            site_id = row["site_id"]
            site_name = row["site_name"]
            
            processed_count += 1
            logger.info(f"Processing site {processed_count}/{len(site_results)}: {site_name} (ID: {site_id})")
            
            try:
                # Generate structured strengths and weaknesses using OpenRouter only
                analysis = strengths_detector.generate_structured_strengths_weaknesses(
                    site_id, None, openrouter_client
                )
                
                if analysis:
                    success_count += 1
                    # Check if it was generated using OpenRouter
                    ai_raw_response = analysis.get("ai_raw_response")
                    if ai_raw_response and isinstance(ai_raw_response, str) and len(ai_raw_response) > 0:
                        openrouter_count += 1
                    logger.info(f"Successfully generated analysis for site {site_id}")
                else:
                    logger.warning(f"Failed to generate analysis for site {site_id}")
                    error_count += 1
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing site {site_id}: {e}")
                error_count += 1
                continue
        
        logger.info(f"Completed final OpenRouter run.")
        logger.info(f"Processed: {processed_count}, Successful: {success_count}, OpenRouter: {openrouter_count}, Errors: {error_count}")
        return True
        
    except Exception as e:
        logger.error(f"Error in final OpenRouter run: {e}")
        return False
    finally:
        try:
            if db_manager:
                db_manager.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")

if __name__ == "__main__":
    print("Clinical Trial Site Analysis - Final OpenRouter Run")
    print("=" * 55)
    
    success = final_openrouter_run()
    
    if success:
        print("\nSUCCESS: Final OpenRouter run completed!")
        print("Check the ai_insights table in the database for results.")
    else:
        print("\nFAILED: Final OpenRouter run failed!")
        print("Check logs/final_openrouter_run.log for details.")