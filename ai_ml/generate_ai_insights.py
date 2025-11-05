#!/usr/bin/env python3
"""
Script to generate AI insights for all sites in the database.
"""

import sys
import os
import json
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from analytics.strengths_weaknesses import StrengthsWeaknessesDetector
from ai_ml.gemini_client import GeminiClient
from ai_ml.openrouter_client import OpenRouterClient  # Added OpenRouter client import
from utils.config import get_api_keys

def setup_logging():
    """Set up logging for the script."""
    log_dir = "../logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "generate_ai_insights.log")),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)

def generate_ai_insights():
    """Generate AI insights for all sites in the database."""
    logger = setup_logging()
    logger.info("Starting AI insights generation for all sites...")
    
    db_manager = None
    try:
        # Initialize database manager
        db_manager = DatabaseManager("../clinical_trials.db")
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Initialize components
        strengths_detector = StrengthsWeaknessesDetector(db_manager)
        
        # Get API keys from config
        api_keys = get_api_keys()
        gemini_api_key = api_keys.get("gemini")
        
        # Initialize Gemini client with API key from config
        gemini_client = GeminiClient(api_key=gemini_api_key)
        
        # Initialize OpenRouter client with the provided API key
        openrouter_api_key = "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"
        openrouter_client = OpenRouterClient(api_key=openrouter_api_key, model_name="meta-llama/llama-3.3-70b-instruct:free")
        
        # Check if clients are configured
        if not gemini_client.is_configured and not openrouter_client.is_configured:
            logger.warning("Neither Gemini nor OpenRouter API configured. Using basic analysis only.")
        else:
            if openrouter_client.is_configured:
                logger.info("OpenRouter API configured successfully with rate limiting")
            if gemini_client.is_configured:
                logger.info("Gemini API configured successfully with rate limiting")
        
        # Get all sites
        site_results = db_manager.query("SELECT site_id, site_name FROM sites_master")
        
        if not site_results:
            logger.warning("No sites found in database")
            return False
        
        logger.info(f"Found {len(site_results)} sites to process")
        
        processed_count = 0
        success_count = 0
        
        # Process each site
        for row in site_results:
            site_id = row["site_id"]
            site_name = row["site_name"]
            
            processed_count += 1
            logger.info(f"Processing site {processed_count}/{len(site_results)}: {site_name} (ID: {site_id})")
            
            try:
                # Generate structured strengths and weaknesses using OpenRouter first, then Gemini as fallback
                analysis = strengths_detector.generate_structured_strengths_weaknesses(
                    site_id, gemini_client, openrouter_client
                )
                
                if analysis:
                    # Check for AI-generated content or algorithmic analysis
                    ai_raw_response = analysis.get("ai_raw_response")
                    has_ai_content = ai_raw_response and isinstance(ai_raw_response, str) and len(ai_raw_response) > 0
                    
                    strengths = analysis.get("strengths")
                    weaknesses = analysis.get("weaknesses")
                    has_algorithmic_content = (strengths and isinstance(strengths, (list, dict)) and len(strengths) > 0) or \
                                            (weaknesses and isinstance(weaknesses, (list, dict)) and len(weaknesses) > 0)
                    
                    if has_ai_content or has_algorithmic_content:
                        success_count += 1
                        logger.info(f"Successfully generated analysis for site {site_id}")
                        if has_ai_content:
                            logger.info(f"AI-generated insights stored for site {site_id}")
                        elif has_algorithmic_content:
                            logger.info(f"Algorithmic analysis completed for site {site_id}")
                    else:
                        logger.warning(f"No significant strengths/weaknesses detected for site {site_id}")
                else:
                    logger.warning(f"Failed to generate analysis for site {site_id}")
                
            except Exception as e:
                logger.error(f"Error processing site {site_id}: {e}")
                continue
        
        logger.info(f"Completed AI insights generation. Processed: {processed_count}, Successful: {success_count}")
        return True
        
    except Exception as e:
        logger.error(f"Error in AI insights generation: {e}")
        return False
    finally:
        try:
            if db_manager:
                db_manager.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")

def main():
    """Main function."""
    print("Clinical Trial Site Analysis - AI Insights Generation")
    print("=" * 55)
    
    success = generate_ai_insights()
    
    if success:
        print("\nSUCCESS: AI insights generation completed!")
        print("Check the ai_insights table in the database for results.")
    else:
        print("\nFAILED: AI insights generation failed!")
        print("Check logs/generate_ai_insights.log for details.")

if __name__ == "__main__":
    main()