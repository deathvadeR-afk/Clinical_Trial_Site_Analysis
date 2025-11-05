"""
OpenRouter API Client for Clinical Trial Site Analysis Platform
Handles integration with OpenRouter API for text generation using various models
"""

import logging
import os
import json
import time
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "openrouter_client.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class OpenRouterRateLimiter:
    """Rate limiter for OpenRouter API calls"""
    
    def __init__(self, rpm_limit: int = 10, rpd_limit: int = 1000):
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


class OpenRouterClient:
    """Client for interacting with OpenRouter API"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "meta-llama/llama-3.3-70b-instruct:free"):
        """
        Initialize the OpenRouter client

        Args:
            api_key: OpenRouter API key (if None, will try to get from environment)
            model_name: Name of the model to use (default: meta-llama/llama-3.3-70b-instruct:free)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name
        self.is_configured = False
        self.rate_limiter = OpenRouterRateLimiter(10, 1000)  # Conservative limits for free tier
        self.base_url = "https://openrouter.ai/api/v1"

        if self.api_key:
            self.is_configured = True
            logger.info(
                f"OpenRouter client configured successfully with model {self.model_name}"
            )
        else:
            logger.warning("No API key provided for OpenRouter client")

    def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using OpenRouter API

        Args:
            prompt: Prompt for text generation
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Generated text or None if error occurred
        """
        if not self.is_configured:
            logger.warning("OpenRouter client not properly configured")
            return None

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8501",  # For open source projects
            }

            data = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            # Increment request counter after successful API call
            if self.rate_limiter:
                self.rate_limiter.increment_request_count()

            if response.status_code == 200:
                response_data = response.json()
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    generated_text = response_data["choices"][0]["message"]["content"]
                    logger.info("Text generated successfully using OpenRouter API")
                    return generated_text
                else:
                    logger.warning("Empty response from OpenRouter API")
                    return None
            else:
                logger.error(f"Error generating text with OpenRouter API: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error generating text with OpenRouter API: {e}")
            return None

    def create_specialized_prompts(self) -> Dict[str, str]:
        """
        Create specialized prompts for different insight types

        Returns:
            Dictionary with specialized prompt templates
        """
        return {
            "strengths_analysis": """
            Analyze the following clinical trial site data and identify key strengths:
            
            {site_data}
            
            Focus on:
            1. Performance metrics that exceed industry standards
            2. Therapeutic area expertise
            3. Investigator credentials and publication record
            4. Operational capabilities
            5. Geographic advantages
            
            Provide a concise list of strengths in natural language format.
            """,
            "weaknesses_analysis": """
            Analyze the following clinical trial site data and identify potential weaknesses or areas for improvement:
            
            {site_data}
            
            Focus on:
            1. Performance metrics below industry standards
            2. Limited experience in certain therapeutic areas
            3. Investigator credential gaps
            4. Operational limitations
            5. Geographic constraints
            
            Provide a constructive list of weaknesses with improvement suggestions in natural language format.
            """,
            "risk_assessment": """
            Assess potential risks for conducting a clinical trial at the following site:
            
            {site_data}
            
            Consider:
            1. Regulatory compliance risks
            2. Recruitment and retention challenges
            3. Operational risks
            4. Data quality concerns
            5. Timeline risks
            
            Provide a risk assessment with mitigation strategies in natural language format.
            """,
        }