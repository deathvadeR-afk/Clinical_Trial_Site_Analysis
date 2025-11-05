"""
PubMed API Integration Module
Handles data extraction from PubMed E-utilities API
"""

import requests
import time
import json
from typing import Dict, List, Optional, Any
import logging
import os
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)

# Create logger for this module
logger = logging.getLogger(__name__)

# Remove any existing handlers to avoid duplicates
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Set logger level
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# File handler
file_handler = logging.FileHandler(os.path.join(log_dir, "pubmed_api.log"))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class RateLimiter:
    """Rate limiter for PubMed API calls"""
    
    def __init__(self, requests_per_second: int = 3, requests_per_day: int = 10000):
        self.requests_per_second = requests_per_second  # Default without API key
        self.requests_per_day = requests_per_day  # Default without API key
        self.requests_today = 0
        self.day_start = time.time()
        self.last_request_time = 0
    
    def update_limits(self, has_api_key: bool = False):
        """Update rate limits based on whether an API key is provided"""
        if has_api_key:
            # With API key: 10 requests per second, 10,000 per day
            self.requests_per_second = 10
            self.requests_per_day = 10000
        else:
            # Without API key: 3 requests per second, 10,000 per day
            self.requests_per_second = 3
            self.requests_per_day = 10000
    
    def wait_if_needed(self):
        """Wait if rate limits would be exceeded"""
        current_time = time.time()
        
        # Reset day counter if 24 hours have passed
        if current_time - self.day_start >= 86400:  # 24 hours
            self.requests_today = 0
            self.day_start = current_time
            
        # Check if we've hit the daily limit
        if self.requests_today >= self.requests_per_day:
            # Wait until the next day
            sleep_time = 86400 - (current_time - self.day_start)
            if sleep_time > 0:
                logger.info(f"Daily limit reached, waiting {sleep_time/3600:.1f} hours")
                time.sleep(sleep_time)
                self.requests_today = 0
                self.day_start = time.time()
        
        # Check per-second rate limit
        time_since_last_request = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f} seconds")
            time.sleep(sleep_time)
    
    def increment_request_count(self):
        """Increment request counter"""
        self.requests_today += 1
        self.last_request_time = time.time()


class PubMedAPI:
    """API client for PubMed E-utilities"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        timeout: int = 30,
        db_manager = None,
    ):
        """
        Initialize the PubMed API client

        Args:
            api_key: Optional API key for higher rate limits
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            db_manager: Optional database manager for storing results
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ClinicalTrialAnalysis/1.0 (research purposes)",
                "Accept": "application/json",
            }
        )
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter()
        if api_key:
            self.rate_limiter.update_limits(has_api_key=True)

    def _rate_limit(self):
        """Implement rate limiting to avoid exceeding API limits"""
        self.rate_limiter.wait_if_needed()
        self.rate_limiter.increment_request_count()

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Make a request to the PubMed API with error handling

        Args:
            endpoint: API endpoint (e.g., "esearch.fcgi")
            params: Query parameters for the API request

        Returns:
            JSON response or None if error occurred
        """
        self._rate_limit()

        # Add API key to params if available
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.base_url}{endpoint}"
        response = None
        try:
            logger.info(f"Making request to {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            logger.info(f"Response status code: {response.status_code}")
            response.raise_for_status()

            # PubMed API returns XML by default, but we can request JSON
            if "retmode" in params and params["retmode"] == "json":
                return response.json()
            else:
                # Return text content for XML responses
                return {"text": response.text}
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
            # Return text content if JSON parsing fails
            if response is not None:
                return {"text": response.text}
            return None

    def search_authors(
        self,
        author_name: str,
        affiliation: Optional[str] = None,
        date_range: Optional[tuple] = None,
    ) -> Optional[Dict]:
        """
        Search for publications by author name and optional affiliation

        Args:
            author_name: Author name to search for
            affiliation: Optional affiliation to filter by
            date_range: Optional tuple of (start_date, end_date) in YYYY/MM/DD format

        Returns:
            API response with search results or None if error occurred
        """
        # Format the search query
        search_terms = [f"{author_name}[Author]"]

        if affiliation:
            search_terms.append(f"{affiliation}[Affiliation]")

        if date_range:
            start_date, end_date = date_range
            search_terms.append(f"{start_date}:{end_date}[Date - Publication]")

        query = " AND ".join(search_terms)

        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": 100,  # Maximum number of results
            "sort": "pub+date",  # Sort by publication date
        }

        logger.info(f"Searching PubMed for author: {author_name}")
        return self._make_request("esearch.fcgi", params)

    def get_publication_details(self, pmids: List[str]) -> Optional[Dict]:
        """
        Get detailed information for specific publications by PMID

        Args:
            pmids: List of PubMed IDs

        Returns:
            API response with publication details or None if error occurred
        """
        if not pmids:
            logger.warning("No PMIDs provided for detail retrieval")
            return None

        # PubMed API has limits on how many IDs can be requested at once
        # Process in batches of 200
        batch_size = 200
        all_results = []

        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i : i + batch_size]
            id_list = ",".join(batch_pmids)

            params = {
                "db": "pubmed",
                "id": id_list,
                "retmode": "xml",  # PubMed ESummary returns XML
                "rettype": "abstract",
                "retmax": len(batch_pmids),
            }

            logger.info(f"Fetching details for {len(batch_pmids)} publications")
            result = self._make_request("esummary.fcgi", params)
            if result:
                all_results.append(result)
            else:
                logger.error(f"Failed to fetch details for batch {i//batch_size + 1}")

        if all_results:
            # Combine results from all batches
            combined_result = {"text": ""}
            for result in all_results:
                if "text" in result:
                    combined_result["text"] += result["text"]
            return combined_result
        else:
            return None

    def parse_publication_xml(self, xml_text: str) -> List[Dict]:
        """
        Parse XML response from PubMed ESummary API into publication dictionaries

        Args:
            xml_text: XML text response from PubMed API

        Returns:
            List of publication dictionaries
        """
        publications = []
        try:
            root = ET.fromstring(xml_text)
            
            # Parse each DocSum element
            for doc_sum in root.findall('.//DocSum'):
                pub_data = {}
                
                # Extract PMID
                pmid_elem = doc_sum.find('.//Id')
                if pmid_elem is not None:
                    pub_data['pmid'] = pmid_elem.text
                
                # Extract other fields
                for item in doc_sum.findall('.//Item'):
                    name = item.get('Name')
                    if name == 'Title':
                        pub_data['title'] = item.text or ''
                    elif name == 'AuthorList':
                        authors = []
                        for author_elem in item.findall('.//Item'):
                            if author_elem.text:
                                authors.append(author_elem.text)
                        pub_data['authors'] = authors
                    elif name == 'PubDate':
                        pub_data['publication_date'] = item.text or ''
                    elif name == 'Source':
                        pub_data['journal'] = item.text or ''
                    elif name == 'Volume':
                        pub_data['volume'] = item.text or ''
                    elif name == 'Issue':
                        pub_data['issue'] = item.text or ''
                    elif name == 'Pages':
                        pub_data['pages'] = item.text or ''
                    elif name == 'FullJournalName':
                        pub_data['full_journal_name'] = item.text or ''
                    elif name == 'ESSN':
                        pub_data['essn'] = item.text or ''
                    elif name == 'DOI':
                        pub_data['doi'] = item.text or ''
                
                # Add default values for missing fields
                if 'authors' not in pub_data:
                    pub_data['authors'] = []
                if 'title' not in pub_data:
                    pub_data['title'] = ''
                if 'journal' not in pub_data:
                    pub_data['journal'] = ''
                if 'publication_date' not in pub_data:
                    pub_data['publication_date'] = ''
                
                publications.append(pub_data)
            
            logger.info(f"Parsed {len(publications)} publications from XML")
            return publications
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing publication XML: {e}")
            return []

    def extract_condition_specific_counts(
        self, publications: List[Dict], conditions: List[str]
    ) -> Dict[str, int]:
        """
        Extract publication counts specific to certain medical conditions

        Args:
            publications: List of publication dictionaries
            conditions: List of medical conditions to search for

        Returns:
            Dictionary mapping conditions to publication counts
        """
        condition_counts = {condition: 0 for condition in conditions}

        for pub in publications:
            # Extract title and abstract for text analysis
            title = pub.get("title", "").lower()
            abstract = pub.get("abstract", "").lower()
            mesh_terms = pub.get("mesh_terms", [])

            # Check each condition
            for condition in conditions:
                condition_lower = condition.lower()

                # Check in title
                if condition_lower in title:
                    condition_counts[condition] += 1
                    continue  # Count each publication only once per condition

                # Check in abstract
                if condition_lower in abstract:
                    condition_counts[condition] += 1
                    continue

                # Check in MeSH terms
                for mesh_term in mesh_terms:
                    if condition_lower in mesh_term.lower():
                        condition_counts[condition] += 1
                        break

        return condition_counts

    def store_publication_records(
        self,
        publications: List[Dict],
        investigator_id: Optional[int] = None,
        site_id: Optional[int] = None,
    ) -> bool:
        """
        Store publication records in the database

        Args:
            publications: List of publication dictionaries
            investigator_id: Optional investigator ID to link publications to
            site_id: Optional site ID to link publications to

        Returns:
            True if successful, False otherwise
        """
        if not self.db_manager:
            logger.warning("No database manager available, cannot store publications")
            return False
            
        try:
            logger.info(f"Storing {len(publications)} publication records")
            
            # Store each publication in the database
            stored_count = 0
            for pub in publications:
                # Extract publication data
                pmid = pub.get("pmid")
                title = pub.get("title", "")
                authors = json.dumps(pub.get("authors", []))
                journal = pub.get("journal", "")
                publication_date = pub.get("publication_date", "")
                citations_count = pub.get("citations_count", 0)
                abstract = pub.get("abstract", "")
                keywords = json.dumps(pub.get("keywords", []))
                mesh_terms = json.dumps(pub.get("mesh_terms", []))
                
                # Prepare data for insertion
                pub_data = {
                    "pmid": pmid,
                    "title": title,
                    "authors": authors,
                    "journal": journal,
                    "publication_date": publication_date,
                    "citations_count": citations_count,
                    "abstract": abstract,
                    "keywords": keywords,
                    "mesh_terms": mesh_terms,
                    "investigator_id": investigator_id,
                    "site_id": site_id
                }
                
                # Insert publication record
                success = self.db_manager.insert_data("pubmed_publications", pub_data)
                if success:
                    stored_count += 1
                else:
                    logger.warning(f"Failed to store publication {pmid}")

            logger.info(
                f"Successfully stored {stored_count}/{len(publications)} publication records"
            )
            return stored_count > 0
        except Exception as e:
            logger.error(f"Error storing publication records: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize the API client
    pubmed_api = PubMedAPI()

    # Search for publications by author
    print("Testing PubMed API integration...")
    print("=" * 50)

    # Test 1: Search for publications by author
    print("Test 1: Searching for publications by author...")
    result = pubmed_api.search_authors("Smith J")

    if result:
        print("✓ Author search test passed")
        if "esearchresult" in result:
            id_list = result["esearchresult"].get("idlist", [])
            print(f"  Found {len(id_list)} publications")

            # Test 2: Get details for first few publications
            if id_list:
                print(
                    f"\nTest 2: Getting details for first {min(3, len(id_list))} publications..."
                )
                details = pubmed_api.get_publication_details(id_list[:3])

                if details:
                    print("✓ Publication details retrieval test passed")
                    print(f"  Retrieved details for publications")
                else:
                    print("✗ Publication details retrieval test failed")
    else:
        print("✗ Author search test failed")