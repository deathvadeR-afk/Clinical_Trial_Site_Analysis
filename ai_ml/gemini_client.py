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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "gemini_client.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import Google Generative AI SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI SDK not available. Install with: pip install google-generativeai")
    GEMINI_AVAILABLE = False
    genai = None

class GeminiClient:
    """Client for interacting with Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = 'gemini-pro'):
        """
        Initialize the Gemini client
        
        Args:
            api_key: Google Gemini API key (if None, will try to get from environment)
            model_name: Name of the Gemini model to use (default: gemini-pro)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.model = None
        self.is_configured = False
        
        # Try to load model name from config if available
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    # Look for model specification in config
                    self.model_name = config.get("gemini", {}).get("model", self.model_name)
        except Exception as e:
            logger.debug(f"Could not load model name from config: {e}")
        
        if GEMINI_AVAILABLE and self.api_key and genai:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.is_configured = True
                logger.info(f"Gemini client configured successfully with model {self.model_name}")
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
            logger.info(f"Gemini client configured successfully with model {model_to_use}")
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
            'site_summary': """
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
            
            Investigators:
            - Total Investigators: {total_investigators}
            - Average H-Index: {avg_h_index}
            
            Please provide a professional summary highlighting the site's strengths and capabilities.
            """,
            
            'study_recommendation': """
            Based on the clinical trial site information and target study parameters, 
            provide a recommendation analysis:
            
            Target Study:
            - Conditions: {target_conditions}
            - Phase: {target_phase}
            - Intervention Type: {target_intervention}
            
            Site Information:
            {site_info}
            
            Please analyze the compatibility and provide a recommendation.
            """,
            
            'investigator_profile': """
            Generate a professional profile summary for a clinical trial investigator:
            
            Name: {full_name}
            Credentials: {credentials}
            Specialization: {specialization}
            Affiliation: {affiliation}
            
            Metrics:
            - H-Index: {h_index}
            - Total Publications: {total_publications}
            - Recent Publications: {recent_publications}
            
            Please provide a concise professional profile highlighting their expertise.
            """
        }
    
    def build_insight_caching_strategy(self) -> Dict[str, Any]:
        """
        Build insight caching strategy
        
        Returns:
            Dictionary with caching configuration
        """
        # Create cache directory if it doesn't exist
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache", "gemini_insights")
        os.makedirs(cache_dir, exist_ok=True)
        
        return {
            'cache_directory': cache_dir,
            'max_cache_age_hours': 24,
            'cache_key_format': '{prompt_hash}_{timestamp}',
            'enabled': True
        }
    
    def _generate_cache_key(self, prompt: str) -> str:
        """
        Generate a cache key for a prompt
        
        Args:
            prompt: The prompt string
            
        Returns:
            Cache key string
        """
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        timestamp = int(time.time() // (self.build_insight_caching_strategy()['max_cache_age_hours'] * 3600))
        return f"{prompt_hash}_{timestamp}"
    
    def _get_cached_response(self, prompt: str) -> Optional[str]:
        """
        Get cached response for a prompt
        
        Args:
            prompt: The prompt string
            
        Returns:
            Cached response or None if not found or expired
        """
        if not self.build_insight_caching_strategy()['enabled']:
            return None
            
        cache_key = self._generate_cache_key(prompt)
        cache_file = os.path.join(self.build_insight_caching_strategy()['cache_directory'], f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                # Check if cache is still valid
                file_age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
                if file_age_hours < self.build_insight_caching_strategy()['max_cache_age_hours']:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        return cached_data.get('response')
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
        
        return None
    
    def _cache_response(self, prompt: str, response: str) -> bool:
        """
        Cache a response for a prompt
        
        Args:
            prompt: The prompt string
            response: The response to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.build_insight_caching_strategy()['enabled']:
            return False
            
        try:
            cache_key = self._generate_cache_key(prompt)
            cache_file = os.path.join(self.build_insight_caching_strategy()['cache_directory'], f"{cache_key}.json")
            
            cache_data = {
                'prompt': prompt,
                'response': response,
                'timestamp': time.time()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
                
            return True
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")
            return False
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, use_cache: bool = True) -> Optional[str]:
        """
        Generate text using Gemini API
        
        Args:
            prompt: Prompt for text generation
            max_tokens: Maximum number of tokens to generate
            use_cache: Whether to use caching
            
        Returns:
            Generated text or None if error occurred
        """
        if not self.is_configured or not GEMINI_AVAILABLE or not self.model or not genai:
            logger.warning("Gemini client not properly configured")
            return None
            
        # Check cache first
        if use_cache:
            cached_response = self._get_cached_response(prompt)
            if cached_response:
                logger.info("Using cached response")
                return cached_response
        
        try:
            # Use generation config if available, otherwise use simpler approach
            if hasattr(genai, 'types') and hasattr(genai.types, 'GenerationConfig'):
                generation_config = genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40
                )
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            else:
                # Fallback for older versions or when types is not available
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": 0.7,
                        "top_p": 0.8,
                        "top_k": 40
                    }
                )
            
            if response and response.text:
                logger.info("Text generated successfully using Gemini API")
                # Cache the response
                if use_cache:
                    self._cache_response(prompt, response.text)
                return response.text
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Error generating text with Gemini API: {e}")
            return None
    
    def implement_batch_processing(self, prompts: List[str]) -> List[Optional[str]]:
        """
        Implement batch processing for site summaries
        
        Args:
            prompts: List of prompts to process
            
        Returns:
            List of generated texts (None for failed generations)
        """
        if not self.is_configured or not GEMINI_AVAILABLE or not self.model:
            logger.warning("Gemini client not properly configured")
            return [None] * len(prompts)
            
        results = []
        
        try:
            for i, prompt in enumerate(prompts):
                logger.info(f"Processing batch item {i+1}/{len(prompts)}")
                result = self.generate_text(prompt)
                results.append(result)
                
                # Add small delay to avoid rate limiting
                import time
                time.sleep(0.1)
                
            logger.info(f"Batch processing completed for {len(prompts)} items")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return [None] * len(prompts)
    
    def create_specialized_prompts(self) -> Dict[str, str]:
        """
        Create specialized prompts for different insight types
        
        Returns:
            Dictionary with specialized prompt templates
        """
        return {
            'strengths_analysis': """
            Analyze the following clinical trial site data and identify key strengths:
            
            {site_data}
            
            Focus on:
            1. Performance metrics that exceed industry standards
            2. Therapeutic area expertise
            3. Investigator credentials and publication record
            4. Operational capabilities
            5. Geographic advantages
            
            Provide a concise list of strengths.
            """,
            
            'weaknesses_analysis': """
            Analyze the following clinical trial site data and identify potential weaknesses or areas for improvement:
            
            {site_data}
            
            Focus on:
            1. Performance metrics below industry standards
            2. Limited experience in certain therapeutic areas
            3. Investigator credential gaps
            4. Operational limitations
            5. Geographic constraints
            
            Provide a constructive list of weaknesses with improvement suggestions.
            """,
            
            'risk_assessment': """
            Assess potential risks for conducting a clinical trial at the following site:
            
            {site_data}
            
            Consider:
            1. Regulatory compliance risks
            2. Recruitment and retention challenges
            3. Operational risks
            4. Data quality concerns
            5. Timeline risks
            
            Provide a risk assessment with mitigation strategies.
            """
        }
    
    def implement_response_validation(self, response: str) -> bool:
        """
        Implement response validation
        
        Args:
            response: Response text to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        if not response:
            return False
            
        # Check for minimum length
        if len(response.strip()) < 10:
            return False
            
        # Check for common error indicators
        error_indicators = ['error', 'sorry', 'unable', 'cannot', 'invalid']
        response_lower = response.lower()
        
        for indicator in error_indicators:
            if indicator in response_lower:
                return False
                
        return True
    
    def generate_meta_insights(self, site_insights: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generate meta-insights across sites
        
        Args:
            site_insights: List of insights from individual sites
            
        Returns:
            Meta-insights text or None if error occurred
        """
        if not self.is_configured or not GEMINI_AVAILABLE or not self.model:
            logger.warning("Gemini client not properly configured")
            return None
            
        try:
            # Create a summary of all site insights
            insights_summary = "Clinical Trial Site Portfolio Analysis:\n\n"
            
            for insight in site_insights:
                site_name = insight.get('site_name', 'Unknown Site')
                strengths = insight.get('strengths', [])
                weaknesses = insight.get('weaknesses', [])
                
                insights_summary += f"Site: {site_name}\n"
                insights_summary += f"Key Strengths: {', '.join(strengths[:3])}\n"
                insights_summary += f"Key Weaknesses: {', '.join(weaknesses[:3])}\n\n"
            
            prompt = f"""
            Based on the clinical trial site portfolio analysis below, provide meta-insights 
            about the overall portfolio strengths, weaknesses, and strategic recommendations:
            
            {insights_summary}
            
            Please provide:
            1. Portfolio-level strengths and competitive advantages
            2. Portfolio-level weaknesses and gaps
            3. Strategic recommendations for portfolio optimization
            4. Geographic and therapeutic area diversification opportunities
            """
            
            return self.generate_text(prompt)
            
        except Exception as e:
            logger.error(f"Error generating meta-insights: {e}")
            return None

# Example usage
if __name__ == "__main__":
    print("Gemini Client module ready for use")
    print("This module handles integration with Google's Gemini API for text generation")
    
    # Example of how to use the client
    # client = GeminiClient("your-api-key-here")
    # if client.configure_client():
    #     prompt = "Generate a summary for a clinical trial site..."
    #     response = client.generate_text(prompt)
    #     if response:
    #         print("Generated response:", response)