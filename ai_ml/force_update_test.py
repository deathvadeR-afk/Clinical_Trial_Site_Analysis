#!/usr/bin/env python3
"""
Force update test for a site to verify OpenRouter provider tracking
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import DatabaseManager
from analytics.strengths_weaknesses import StrengthsWeaknessesDetector
from ai_ml.openrouter_client import OpenRouterClient

def force_update_test():
    """Force update a site's insights to verify provider tracking"""
    print("Force updating site insights with OpenRouter...")
    
    # Initialize database manager
    db_manager = DatabaseManager("../../clinical_trials.db")
    if not db_manager.connect():
        print("ERROR: Failed to connect to database")
        return False
    
    try:
        # Initialize components
        strengths_detector = StrengthsWeaknessesDetector(db_manager)
        
        # Initialize OpenRouter client with the provided API key
        openrouter_api_key = "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"
        openrouter_client = OpenRouterClient(api_key=openrouter_api_key, model_name="meta-llama/llama-3.3-70b-instruct:free")
        
        if not openrouter_client.is_configured:
            print("ERROR: OpenRouter client not configured properly")
            return False
        
        print("OpenRouter client configured successfully")
        
        # Use a specific site ID that we know exists
        site_id = 123  # Using a different site ID
        print(f"Force updating insights for site ID: {site_id}")
        
        # Generate structured strengths and weaknesses using OpenRouter
        analysis = strengths_detector.generate_structured_strengths_weaknesses(
            site_id, None, openrouter_client
        )
        
        if analysis:
            print("SUCCESS: Generated analysis for site")
            
            # Check database for the updated record
            result = db_manager.query("SELECT gemini_model_version FROM ai_insights WHERE site_id = ?", (site_id,))
            if result:
                model_version = result[0]["gemini_model_version"]
                print(f"Model version stored in database: {model_version}")
                
                # Check if it correctly shows OpenRouter
                if "llama" in model_version.lower() or "openrouter" in model_version.lower():
                    print("SUCCESS: Provider correctly tracked as OpenRouter")
                    return True
                else:
                    print("WARNING: Provider not correctly tracked")
                    return False
            else:
                print("No record found in database")
                return False
        else:
            print("ERROR: Failed to generate analysis for site")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    force_update_test()