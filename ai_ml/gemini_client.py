"""
Gemini API Client for Clinical Trial Site Analysis Platform
Handles integration with Google's Gemini API for text generation
"""

import logging
import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "gemini_client.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Try to import Google Generative AI SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning(
        "Google Generative AI SDK not available. Install with: pip install google-generativeai"
    )
    GEMINI_AVAILABLE = False
    genai = None
except Exception as e:
    logger.warning(f"Error importing Google Generative AI SDK: {e}")
    GEMINI_AVAILABLE = False
    genai = None


class RateLimiter:
    """Rate limiter for Gemini API calls"""
    
    def __init__(self, rpm_limit: int = 15, rpd_limit: int = 1500):
        self.rpm_limit = rpm_limit  # Requests per minute
        self.rpd_limit = rpd_limit  # Requests per day
        self.requests_this_minute = 0
        self.requests_today = 0
        self.minute_start = time.time()
        self.day_start = time.time()
    
    def wait_if_needed(self):
        """Wait if rate limits would be exceeded"""
        current_time = time.time()
        
        # Reset minute counter if a minute has passed
        if current_time - self.minute_start >= 60:
            self.requests_this_minute = 0
            self.minute_start = current_time
            
        # Reset day counter if 24 hours have passed
        if current_time - self.day_start >= 86400:  # 24 hours
            self.requests_today = 0
            self.day_start = current_time
            
        # Check if we've hit the rate limits
        if self.requests_this_minute >= self.rpm_limit:
            # Wait until the next minute
            sleep_time = 60 - (current_time - self.minute_start)
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.requests_this_minute = 0
                self.minute_start = current_time
                
        if self.requests_today >= self.rpd_limit:
            # Wait until the next day
            sleep_time = 86400 - (current_time - self.day_start)
            if sleep_time > 0:
                logger.info(f"Daily limit reached, waiting {sleep_time/3600:.1f} hours")
                time.sleep(sleep_time)
                self.requests_today = 0
                self.day_start = time.time()
    
    def increment_request_count(self):
        """Increment request counters"""
        self.requests_this_minute += 1
        self.requests_today += 1


class GeminiClient:
    """Client for interacting with Google's Gemini API"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the Gemini client

        Args:
            api_key: Google Gemini API key (if None, will try to get from environment)
            model_name: Name of the Gemini model to use (default: gemini-2.0-flash)
        """
        # Priority order: parameter > environment variable > config file
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.model = None
        self.is_configured = False
        self.rate_limiter = None

        # Try to load model name and rate limits from config if available
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    # Look for model specification in config
                    self.model_name = config.get("gemini", {}).get(
                        "model", self.model_name
                    )
                    # Get rate limits from config
                    rate_limits = config.get("gemini", {}).get("rate_limits", {})
                    rpm = rate_limits.get("rpm", 15)
                    rpd = rate_limits.get("rpd", 1500)
                    self.rate_limiter = RateLimiter(rpm, rpd)
        except Exception as e:
            logger.debug(f"Could not load model name or rate limits from config: {e}")
            # Use default rate limits
            self.rate_limiter = RateLimiter(15, 1500)

        if GEMINI_AVAILABLE and self.api_key and genai:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.is_configured = True
                logger.info(
                    f"Gemini client configured successfully with model {self.model_name}"
                )
            except Exception as e:
                logger.error(f"Failed to configure Gemini client: {e}")
        else:
            if not GEMINI_AVAILABLE:
                logger.warning("Google Generative AI SDK not installed")
            if not self.api_key:
                logger.warning("No API key provided for Gemini client")

    def configure_client(self, model_name: Optional[str] = None) -> bool:
        """
        Configure Gemini API client

        Args:
            model_name: Name of the Gemini model to use (if None, uses self.model_name)

        Returns:
            True if successful, False otherwise
        """
        if not GEMINI_AVAILABLE or not genai:
            logger.error("Google Generative AI SDK not available")
            return False

        if not self.api_key:
            logger.error("No API key provided")
            return False

        # Use provided model name or fall back to instance model name
        model_to_use = model_name or self.model_name

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_to_use)
            self.model_name = model_to_use
            self.is_configured = True
            logger.info(
                f"Gemini client configured successfully with model {model_to_use}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to configure Gemini client: {e}")
            return False

    def design_prompt_templates(self) -> Dict[str, str]:
        """
        Design prompt templates for site summaries

        Returns:
            Dictionary with prompt templates
        """
        return {
            "site_summary": """
            Generate a comprehensive summary for a clinical trial site based on the following information:
            
            Site Name: {site_name}
            Location: {city}, {state}, {country}
            Institution Type: {institution_type}
            Accreditation Status: {accreditation_status}
            
            Performance Metrics:
            - Total Studies: {total_studies}
            - Completion Ratio: {completion_ratio}
            - Average Enrollment: {avg_enrollment}
            - Experience Index: {experience_index}
            
            Therapeutic Areas: {therapeutic_areas}
            
            Please provide a concise yet comprehensive summary that highlights:
            1. The site's key strengths and areas of expertise
            2. Its performance track record
            3. Geographic and institutional advantages
            4. Any notable specializations or capabilities
            
            Format the response as a well-structured paragraph without markdown formatting.
            """,
            
            "investigator_profile": """
            Generate a professional profile for a clinical trial investigator based on the following information:
            
            Name: {full_name}
            Affiliation: {affiliation}
            Credentials: {credentials}
            Specialization: {specialization}
            Total Trials: {total_trials}
            Active Trials: {active_trials}
            H-Index: {h_index}
            Publications: {publications}
            
            Please provide a concise professional profile that highlights:
            1. The investigator's expertise and specialization
            2. Research impact and productivity (using publication and h-index data)
            3. Clinical trial experience and current activity
            4. Professional credentials and affiliations
            
            Format the response as a well-structured paragraph without markdown formatting.
            """,
            
            "site_recommendation": """
            Generate a recommendation for a clinical trial site based on the match criteria and site profile:
            
            Target Study:
            - Conditions: {target_conditions}
            - Phase: {target_phase}
            - Intervention Type: {target_intervention}
            - Country: {target_country}
            
            Site Profile:
            - Name: {site_name}
            - Location: {location}
            - Match Score: {match_score}
            - Therapeutic Match: {therapeutic_match}
            - Phase Match: {phase_match}
            - Intervention Match: {intervention_match}
            - Geographic Match: {geographic_match}
            
            Performance Metrics:
            - Total Studies: {total_studies}
            - Completion Ratio: {completion_ratio}
            - Average Enrollment: {avg_enrollment}
            
            Please provide a concise recommendation that explains:
            1. Why this site is a good match for the target study
            2. The site's relevant experience and capabilities
            3. Any potential advantages or considerations
            4. Overall suitability assessment
            
            Format the response as a well-structured paragraph without markdown formatting.
            """
        }

    def generate_text(self, prompt: str, max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Generate text using the Gemini API

        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum number of tokens to generate (if None, uses model default)

        Returns:
            Generated text or None if failed
        """
        if not self.is_configured or not self.model:
            logger.warning("Gemini client not configured, returning None")
            return None

        if not self.api_key:
            logger.warning("No API key available, returning None")
            return None

        try:
            # Apply rate limiting
            if self.rate_limiter:
                self.rate_limiter.wait_if_needed()
                self.rate_limiter.increment_request_count()

            # Generate content
            response = None
            if max_tokens and genai:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(max_output_tokens=max_tokens)
                )
            elif genai:
                response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            return None

    def generate_structured_response(self, prompt: str, response_schema: Dict) -> Optional[Dict]:
        """
        Generate a structured response using the Gemini API

        Args:
            prompt: Prompt to send to the model
            response_schema: Schema for the expected response structure

        Returns:
            Structured response dictionary or None if failed
        """
        if not self.is_configured or not self.model:
            logger.warning("Gemini client not configured, returning None")
            return None

        if not self.api_key:
            logger.warning("No API key available, returning None")
            return None

        try:
            # Apply rate limiting
            if self.rate_limiter:
                self.rate_limiter.wait_if_needed()
                self.rate_limiter.increment_request_count()

            # Generate structured content
            response = None
            if genai:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema
                    )
                )
            
            if response and response.text:
                try:
                    # Parse JSON response
                    return json.loads(response.text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return None
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Error generating structured response with Gemini: {e}")
            return None


# Example usage
if __name__ == "__main__":
    print("Gemini API Client module ready for use")
    print("This module handles integration with Google's Gemini API for text generation")