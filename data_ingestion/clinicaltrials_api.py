"""
ClinicalTrials.gov API Integration Module
Handles data extraction from ClinicalTrials.gov API
"""
import requests
import time
import json
from typing import Dict, List, Optional, Any
import logging
import os

# Set up logging
# Use absolute path to ensure we can write to the logs directory
current_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(current_dir, "..", "logs")
os.makedirs(log_dir, exist_ok=True)

# Create logger for this module
logger = logging.getLogger(__name__)

# Remove any existing handlers to avoid duplicates
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Set logger level
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler with absolute path
log_file_path = os.path.join(log_dir, "clinicaltrials_api.log")
print(f"Attempting to create log file at: {log_file_path}")  # Debug print
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
print(f"Logger handlers added. Handlers: {len(logger.handlers)}")  # Debug print

class ClinicalTrialsAPI:
    """API client for ClinicalTrials.gov"""
    
    def __init__(self, base_url: str = "https://clinicaltrials.gov/api/v2/studies", 
                 max_requests_per_second: int = 5, timeout: int = 30):
        """
        Initialize the ClinicalTrials API client
        
        Args:
            base_url: Base URL for the API
            max_requests_per_second: Maximum requests per second to avoid rate limiting
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.max_requests_per_second = max_requests_per_second
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ClinicalTrialAnalysis/1.0 (research purposes)",
            "Accept": "application/json"
        })
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting to avoid exceeding API limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        min_interval = 1.0 / self.max_requests_per_second
        
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Make a request to the ClinicalTrials.gov API with error handling
        
        Args:
            params: Query parameters for the API request
            
        Returns:
            JSON response or None if error occurred
        """
        self._rate_limit()
        
        response = None
        try:
            logger.info(f"Making request to {self.base_url} with params: {params}")
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            logger.info(f"Response status code: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            if response is not None:
                logger.error(f"Response content: {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            return None
    
    def get_studies(self, page_size: int = 100, page_token: Optional[str] = None) -> Optional[Dict]:
        """
        Get clinical studies (basic retrieval without search filters)
        
        Args:
            page_size: Number of results per page (max 1000)
            page_token: Token for pagination
            
        Returns:
            API response with study data or None if error occurred
        """
        params: Dict[str, Any] = {
            "pageSize": min(page_size, 1000)  # API limit is 1000
        }
        
        if page_token:
            params["pageToken"] = page_token
            
        logger.info(f"Getting studies with params: {params}")
        return self._make_request(params)
    
    def find_study_in_results(self, nct_id: str, studies_data: Dict) -> Optional[Dict]:
        """
        Find a specific study by NCT ID in the results from get_studies
        
        Args:
            nct_id: National Clinical Trial ID to search for
            studies_data: Data returned from get_studies
            
        Returns:
            Study data if found, None otherwise
        """
        studies = studies_data.get('studies', [])
        for study in studies:
            try:
                id_module = study['protocolSection']['identificationModule']
                if id_module['nctId'] == nct_id:
                    return study
            except KeyError:
                continue
        return None

    def get_studies_since_date(self, since_date: str, page_size: int = 100) -> List[Dict]:
        """
        Get studies updated since a specific date (client-side filtering)
        
        Args:
            since_date: Date string in YYYY-MM-DD format
            page_size: Number of results per page
            
        Returns:
            List of studies updated since the specified date
        """
        import datetime
        
        try:
            target_date = datetime.datetime.strptime(since_date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {since_date}. Expected YYYY-MM-DD")
            return []
        
        matching_studies = []
        page_token = None
        processed_count = 0
        max_pages = 50  # Limit to prevent infinite loops
        pages_processed = 0
        
        logger.info(f"Searching for studies updated since {since_date}")
        
        while pages_processed < max_pages:
            # Get a page of studies
            result = self.get_studies(page_size=page_size, page_token=page_token)
            
            if not result:
                logger.warning("Failed to retrieve studies")
                break
                
            studies = result.get('studies', [])
            if not studies:
                logger.info("No more studies found")
                break
                
            # Filter studies by last update date
            for study in studies:
                try:
                    status_module = study['protocolSection']['statusModule']
                    last_update_date_str = status_module['lastUpdateSubmitDate']
                    last_update_date = datetime.datetime.strptime(last_update_date_str, "%Y-%m-%d")
                    
                    if last_update_date >= target_date:
                        matching_studies.append(study)
                except (KeyError, ValueError):
                    # Skip studies with missing or invalid dates
                    continue
            
            processed_count += len(studies)
            logger.info(f"Processed {processed_count} studies, found {len(matching_studies)} matching")
            
            # Check for next page
            next_page_token = result.get('nextPageToken')
            if not next_page_token:
                logger.info("No more pages available")
                break
                
            page_token = next_page_token
            pages_processed += 1
            
            # Rate limiting
            time.sleep(0.1)
        
        logger.info(f"Found {len(matching_studies)} studies updated since {since_date}")
        return matching_studies

    def save_raw_response(self, response_data: Dict, filename: str) -> bool:
        """
        Save raw API response to JSON file for debugging and analysis
        
        Args:
            response_data: Raw API response data
            filename: Name of file to save data to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create raw_data directory if it doesn't exist
            raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data")
            os.makedirs(raw_data_dir, exist_ok=True)
            
            # Save response to file
            file_path = os.path.join(raw_data_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved raw response to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save raw response: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Initialize the API client
    ct_api = ClinicalTrialsAPI()
    
    # Get studies
    print("Testing ClinicalTrials.gov API integration...")
    print("=" * 50)
    
    # Test 1: Basic retrieval without filters
    print("Test 1: Basic study retrieval...")
    result = ct_api.get_studies(page_size=10)
    
    if result:
        print("✓ Basic study retrieval test passed")
        studies = result.get('studies', [])
        print(f"  Retrieved {len(studies)} studies")
        
        if studies:
            first_study = studies[0]
            id_module = first_study['protocolSection']['identificationModule']
            nct_id = id_module['nctId']
            title = id_module.get('briefTitle', 'N/A')
            print(f"  First study: {nct_id} - {title}")
            
            # Test 2: Find the same study in the results
            print(f"\nTest 2: Finding study {nct_id} in results...")
            found_study = ct_api.find_study_in_results(nct_id, result)
            
            if found_study:
                print("✓ Study search test passed")
                print(f"  Found study {nct_id} in results")
            else:
                print("✗ Study search test failed")
    else:
        print("✗ Basic study retrieval test failed")