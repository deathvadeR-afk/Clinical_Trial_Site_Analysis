import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import time
from urllib.parse import quote_plus

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "data_processor.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Import fuzzy matching libraries
try:
    from fuzzywuzzy import fuzz, process
    FUZZY_MATCHING_AVAILABLE = True
except ImportError:
    FUZZY_MATCHING_AVAILABLE = False
    logger.warning("Fuzzy matching libraries not available. Install with: pip install fuzzywuzzy python-levenshtein")


class DataProcessor:
    """Processor for handling data flow from APIs to database"""

    def __init__(self, db_manager):
        """
        Initialize the data processor

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def geocode_address(
        self, city: str, state: str, country: str
    ) -> Optional[Dict[str, float]]:
        """
        Geocode an address to get latitude and longitude coordinates.
        Uses OpenStreetMap Nominatim API for geocoding.

        Args:
            city: City name
            state: State/region
            country: Country name

        Returns:
            Dictionary with 'lat' and 'lon' keys, or None if geocoding failed
        """
        # Construct address string
        address_parts = [part for part in [city, state, country] if part]
        address = ", ".join(address_parts) if address_parts else ""

        if not address:
            return None

        # Create cache directory if it doesn't exist
        cache_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "cache"
        )
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "geocoding_cache.json")

        # Load existing cache
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load geocoding cache: {e}")

        # Check if address is already cached
        if address in cache:
            cached_entry = cache[address]
            # Check if cache is still valid (24 hours)
            if time.time() - cached_entry.get("timestamp", 0) < 24 * 60 * 60:
                logger.info(f"Using cached coordinates for {address}")
                return cached_entry["coordinates"]
            else:
                # Remove expired entry
                del cache[address]

        try:
            # Use OpenStreetMap Nominatim API (free, no API key required)
            # Note: This service has usage limits, so we should cache results
            base_url = "https://nominatim.openstreetmap.org/search"
            params = {"q": address, "format": "json", "limit": 1, "addressdetails": 1}

            headers = {
                "User-Agent": "ClinicalTrialSiteAnalysis/1.0 (research purposes)"
            }

            logger.info(f"Geocoding address: {address}")

            # Implement retry logic for better error handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Rate limiting - wait before making request
                    time.sleep(1)  # 1 second delay between requests

                    response = requests.get(
                        base_url, params=params, headers=headers, timeout=10
                    )
                    response.raise_for_status()

                    data = response.json()
                    if data and len(data) > 0:
                        result = data[0]
                        # Validate that we have the required fields
                        if "lat" in result and "lon" in result:
                            coordinates = {
                                "lat": float(result["lat"]),
                                "lon": float(result["lon"]),
                            }
                            logger.info(f"Geocoded {address} to {coordinates}")

                            # Cache the result
                            cache[address] = {
                                "coordinates": coordinates,
                                "timestamp": time.time(),
                            }
                            try:
                                with open(cache_file, "w") as f:
                                    json.dump(cache, f)
                            except Exception as e:
                                logger.warning(f"Failed to save geocoding cache: {e}")

                            return coordinates
                        else:
                            logger.warning(
                                f"Geocoding result missing lat/lon for address: {address}"
                            )
                            return None
                    else:
                        logger.warning(f"No geocoding results for address: {address}")
                        return None

                except requests.exceptions.Timeout:
                    logger.warning(
                        f"Geocoding timeout for address: {address} (attempt {attempt + 1}/{max_retries})"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)  # Exponential backoff
                        continue
                    else:
                        logger.error(
                            f"Geocoding failed after {max_retries} attempts due to timeout: {address}"
                        )
                        return None

                except requests.exceptions.RequestException as e:
                    logger.error(
                        f"Geocoding request error for address '{address}' (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)  # Exponential backoff
                        continue
                    else:
                        logger.error(
                            f"Geocoding failed after {max_retries} attempts: {address}"
                        )
                        return None

                except (ValueError, KeyError) as e:
                    logger.error(
                        f"Geocoding data parsing error for address '{address}': {e}"
                    )
                    return None

                except Exception as e:
                    logger.error(
                        f"Unexpected error during geocoding for address '{address}': {e}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            return None

    def _validate_trial_data(self, trial_data: Dict) -> bool:
        """
        Validate clinical trial data before insertion

        Args:
            trial_data: Dictionary with trial data

        Returns:
            True if data is valid, False otherwise
        """
        # Check required fields
        required_fields = ["nct_id"]
        for field in required_fields:
            if not trial_data.get(field):
                logger.warning(f"Missing required field: {field}")
                return False

        # Validate data types and ranges
        if trial_data.get("enrollment_count") is not None:
            try:
                enrollment = int(trial_data["enrollment_count"])
                if enrollment < 0:
                    logger.warning(f"Invalid enrollment count: {enrollment}")
                    return False
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid enrollment count type: {trial_data['enrollment_count']}"
                )
                return False

        # Validate dates if present
        date_fields = ["start_date", "completion_date", "primary_completion_date"]
        for field in date_fields:
            if trial_data.get(field):
                try:
                    # Try to parse the date
                    if isinstance(trial_data[field], str):
                        datetime.strptime(trial_data[field], "%Y-%m-%d")
                except ValueError:
                    logger.warning(
                        f"Invalid date format for {field}: {trial_data[field]}"
                    )
                    # Don't return False, just log the warning

        return True

    def process_clinical_trial_data(self, study_data: Dict) -> bool:
        """
        Process clinical trial data and store in database

        Args:
            study_data: Raw study data from ClinicalTrials.gov API

        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Extract protocol section
            protocol_section = study_data.get("protocolSection", {})

            # Extract identification module
            id_module = protocol_section.get("identificationModule", {})
            nct_id = id_module.get("nctId")
            brief_title = id_module.get("briefTitle")
            official_title = id_module.get("officialTitle")

            # Validate required data
            if not nct_id:
                logger.warning("Missing NCT ID in study data")
                return False

            # Extract status module
            status_module = protocol_section.get("statusModule", {})
            overall_status = status_module.get("overallStatus")

            # Extract design module
            design_module = protocol_section.get("designModule", {})
            study_type = design_module.get("studyType")
            phases = design_module.get("phases", [])
            phase = phases[0] if phases else None

            # Extract conditions module
            conditions_module = protocol_section.get("conditionsModule", {})
            conditions = conditions_module.get("conditions", [])
            conditions_json = json.dumps(conditions) if conditions else None

            # Extract arms/interventions module
            arms_module = protocol_section.get("armsInterventionsModule", {})
            interventions = arms_module.get("interventions", [])
            interventions_json = json.dumps(interventions) if interventions else None

            # Extract enrollment info
            # FIX: enrollmentInfo is a direct child of design_module, not design_info
            enrollment_info = design_module.get("enrollmentInfo", {})
            enrollment_count = enrollment_info.get("count")

            # Extract dates
            start_date_struct = status_module.get("startDateStruct", {})
            start_date = start_date_struct.get("date")

            completion_date_struct = status_module.get("completionDateStruct", {})
            completion_date = completion_date_struct.get("date")

            primary_completion_date_struct = status_module.get(
                "primaryCompletionDateStruct", {}
            )
            primary_completion_date = primary_completion_date_struct.get("date")

            # Extract sponsor information
            sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsor_module.get("leadSponsor", {})
            sponsor_name = lead_sponsor.get("name")
            sponsor_type = lead_sponsor.get("class")

            # Extract posting dates
            last_update_posted = status_module.get("lastUpdatePostDateStruct", {}).get(
                "date"
            )
            study_first_posted = status_module.get("studyFirstPostDateStruct", {}).get(
                "date"
            )

            # Prepare data for insertion
            trial_data = {
                "nct_id": nct_id,
                "title": brief_title or official_title,
                "status": overall_status,
                "phase": phase,
                "study_type": study_type,
                "conditions": conditions_json,
                "interventions": interventions_json,
                "enrollment_count": enrollment_count,
                "start_date": start_date,
                "completion_date": completion_date,
                "primary_completion_date": primary_completion_date,
                "sponsor_name": sponsor_name,
                "sponsor_type": sponsor_type,
                "last_update_posted": last_update_posted,
                "study_first_posted": study_first_posted,
            }

            # Validate data before insertion
            if not self._validate_trial_data(trial_data):
                logger.error(f"Invalid data for trial {nct_id}")
                return False

            # Try to insert first
            success = self.db_manager.insert_data("clinical_trials", trial_data)

            # If insert fails, try to update existing record
            if not success:
                # Check if the record already exists
                existing_record = self.db_manager.query(
                    "SELECT nct_id FROM clinical_trials WHERE nct_id = ?", (nct_id,)
                )

                if existing_record and len(existing_record) > 0:
                    # Build update query
                    set_clause = ", ".join(
                        [f"{key} = ?" for key in trial_data.keys() if key != "nct_id"]
                    )
                    values = [
                        trial_data[key] for key in trial_data.keys() if key != "nct_id"
                    ] + [nct_id]
                    sql = f"UPDATE clinical_trials SET {set_clause} WHERE nct_id = ?"

                    success = self.db_manager.execute(sql, tuple(values))
                    if success:
                        logger.info(f"Updated clinical trial data for {nct_id}")
                    else:
                        logger.error(
                            f"Failed to update clinical trial data for {nct_id}"
                        )
                else:
                    logger.error(
                        f"Failed to insert clinical trial data for {nct_id} and record does not exist"
                    )
                    return False
            else:
                logger.info(f"Processed clinical trial data for {nct_id}")

            # Regardless of insert/update, continue with site processing
            return True

        except Exception as e:
            logger.error(f"Error processing clinical trial data: {e}")
            return False

    def process_site_data(self, study_data: Dict) -> bool:
        """
        Process site data from clinical trial and store in database

        Args:
            study_data: Raw study data from ClinicalTrials.gov API

        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Extract protocol section
            protocol_section = study_data.get("protocolSection", {})

            # Extract identification info
            id_module = protocol_section.get("identificationModule", {})
            nct_id = id_module.get("nctId")

            # Extract status module for recruitment status
            status_module = protocol_section.get("statusModule", {})
            overall_status = status_module.get("overallStatus", "Unknown")

            # Extract design module for enrollment info
            design_module = protocol_section.get("designModule", {})
            # FIX: enrollmentInfo is a direct child of design_module, not design_info
            enrollment_info = design_module.get("enrollmentInfo", {})
            enrollment_count = enrollment_info.get("count")

            # Extract dates
            start_date_struct = status_module.get("startDateStruct", {})
            start_date = start_date_struct.get("date")

            completion_date_struct = status_module.get("completionDateStruct", {})
            completion_date = completion_date_struct.get("date")

            # Extract locations module
            contacts_locations_module = protocol_section.get(
                "contactsLocationsModule", {}
            )
            locations = contacts_locations_module.get("locations", [])

            # Process each location
            for location in locations:
                facility = location.get("facility", "")
                city = location.get("city", "")
                state = location.get("zip", "")
                country = location.get("country", "")

                # Skip if facility name is empty
                if not facility or facility.strip() == "":
                    logger.warning(f"Skipping location with empty facility name")
                    continue

                # Skip if facility name is only numbers (likely data quality issue)
                if facility.isdigit() and len(facility) <= 5:
                    logger.warning(f"Skipping location with numeric-only facility name: '{facility}'")
                    continue

                # Infer institution type from facility name
                institution_type = self._infer_institution_type(facility)
                
                # If we couldn't infer the type, set it to "Other" instead of "Unknown"
                if institution_type == "Unknown":
                    institution_type = "Other"

                # Check if site already exists using fuzzy matching
                site_id = self._get_or_create_site_id(facility, city, state, country, institution_type)

                if site_id and nct_id:
                    # Link site to trial in site_trial_participation table
                    logger.info(f"Attempting to link site {site_id} to trial {nct_id}")
                    # Check if the link already exists
                    existing_link = self.db_manager.query(
                        "SELECT site_trial_id FROM site_trial_participation WHERE site_id = ? AND nct_id = ?",
                        (site_id, nct_id),
                    )

                    if not existing_link or len(existing_link) == 0:
                        # Create the link
                        link_data = {
                            "site_id": site_id,
                            "nct_id": nct_id,
                            "role": "Facility",  # Default role
                            "recruitment_status": overall_status,
                            "actual_enrollment": enrollment_count,
                            "enrollment_start_date": start_date,
                            "enrollment_end_date": completion_date,
                            "data_submission_quality_score": 1.0,  # Default score
                        }

                        logger.info(f"Inserting link data: {link_data}")
                        link_success = self.db_manager.insert_data(
                            "site_trial_participation", link_data
                        )
                        if link_success:
                            logger.info(f"Linked site {site_id} to trial {nct_id}")
                        else:
                            logger.error(
                                f"Failed to link site {site_id} to trial {nct_id}"
                            )
                            return False
                    else:
                        logger.info(f"Site {site_id} already linked to trial {nct_id}")
                else:
                    logger.warning(
                        f"Skipping link creation: site_id={site_id}, nct_id={nct_id}"
                    )

            return True

        except Exception as e:
            logger.error(f"Error processing site data: {e}")
            return False

    def _get_or_create_site_id(self, facility: str, city: str, state: str, country: str, institution_type: str) -> Optional[int]:
        """
        Get existing site ID or create a new site with fuzzy matching for similar names

        Args:
            facility: Facility name
            city: City name
            state: State name
            country: Country name
            institution_type: Type of institution

        Returns:
            Site ID if successful, None otherwise
        """
        if not facility:
            return None

        # First, try exact match
        existing_site = self.db_manager.query(
            "SELECT site_id FROM sites_master WHERE site_name = ?", (facility,)
        )

        if existing_site and len(existing_site) > 0:
            return existing_site[0]["site_id"]

        # If fuzzy matching is available, try to find similar sites
        if FUZZY_MATCHING_AVAILABLE:
            similar_site_id = self._find_similar_site(facility)
            if similar_site_id:
                logger.info(f"Found similar site for '{facility}' with ID {similar_site_id}")
                return similar_site_id

        # If no similar site found, create new site
        return self._create_new_site(facility, city, state, country, institution_type)

    def _find_similar_site(self, facility: str) -> Optional[int]:
        """
        Find a similar site using fuzzy matching

        Args:
            facility: Facility name to match

        Returns:
            Site ID of the most similar site if found, None otherwise
        """
        try:
            # Get all existing site names
            all_sites = self.db_manager.query(
                "SELECT site_id, site_name FROM sites_master"
            )

            if not all_sites:
                return None

            site_names = [site["site_name"] for site in all_sites]
            site_ids = [site["site_id"] for site in all_sites]

            # Use fuzzy matching to find the best match
            best_match, score = process.extractOne(facility, site_names)
            
            # If similarity score is high enough (e.g., > 85), consider it a match
            if score > 85:
                # Find the ID of the best matching site
                best_match_index = site_names.index(best_match)
                return site_ids[best_match_index]
            
            return None
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")
            return None

    def _create_new_site(self, facility: str, city: str, state: str, country: str, institution_type: str) -> Optional[int]:
        """
        Create a new site in the database

        Args:
            facility: Facility name
            city: City name
            state: State name
            country: Country name
            institution_type: Type of institution

        Returns:
            Site ID if successful, None otherwise
        """
        try:
            # Geocode the address to get coordinates
            coordinates = self.geocode_address(city, state, country)
            latitude = coordinates["lat"] if coordinates else None
            longitude = coordinates["lon"] if coordinates else None

            # Create new site data
            site_data = {
                "site_name": facility,
                "normalized_name": self._normalize_site_name(facility) if facility else None,
                "city": city,
                "state": state,
                "country": country,
                "latitude": latitude,
                "longitude": longitude,
                "institution_type": institution_type,
                "total_capacity": 0,
                "accreditation_status": "Unknown",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }

            # Insert site data
            site_success = self.db_manager.insert_data(
                "sites_master", site_data
            )
            if site_success:
                # Get the site_id of the newly inserted site
                site_result = self.db_manager.query(
                    "SELECT site_id FROM sites_master WHERE site_name = ?",
                    (facility,),
                )
                logger.info(f"Site insertion result: {site_result}")
                if site_result and len(site_result) > 0:
                    site_id = site_result[0]["site_id"]
                    logger.info(f"Created new site with ID {site_id} for {facility}")
                    return site_id
                else:
                    logger.error(f"Failed to retrieve site_id for {facility}")
                    return None
            else:
                logger.error(f"Failed to insert site data for {facility}")
                return None
        except Exception as e:
            logger.error(f"Error creating new site: {e}")
            return None

    def _normalize_site_name(self, name: str) -> str:
        """
        Normalize site name for better matching

        Args:
            name: Original site name

        Returns:
            Normalized site name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common punctuation variations
        normalized = normalized.replace(",", "")
        normalized = normalized.replace(".", "")
        normalized = normalized.replace(";", "")
        
        # Standardize common terms
        normalized = normalized.replace("university", "univ")
        normalized = normalized.replace("medical center", "med ctr")
        normalized = normalized.replace("medical centre", "med ctr")
        normalized = normalized.replace("health center", "health ctr")
        normalized = normalized.replace("health centre", "health ctr")
        
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        
        return normalized

    def _infer_institution_type(self, facility_name: str) -> str:
        """
        Infer institution type from facility name

        Args:
            facility_name: Name of the facility

        Returns:
            Inferred institution type
        """
        if not facility_name:
            return "Other"

        # Convert to lowercase for case-insensitive matching
        name_lower = facility_name.lower()

        # Define institution type keywords
        institution_types = {
            "hospital": ["hospital", "medical center", "medical centre", "general hospital"],
            "university": ["university", "college", "medical school", "school of"],
            "clinic": ["clinic", "health center", "health centre", "medical group"],
            "research institute": ["institute", "research center", "research centre", "laboratory", "research foundation"],
            "foundation": ["foundation", "trust", "charity"],
            "pharmacy": ["pharmacy"],
            "private practice": ["private practice", "medical practice", "physician"],
        }

        # Check each institution type
        for inst_type, keywords in institution_types.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return inst_type.title()

        # If we can't determine the type, return "Other" instead of "Unknown"
        return "Other"

    def process_investigator_data(self, study_data: Dict) -> bool:
        """
        Process investigator data from clinical trial and store in database

        Args:
            study_data: Raw study data from ClinicalTrials.gov API

        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Extract protocol section
            protocol_section = study_data.get("protocolSection", {})

            # Extract identification info
            id_module = protocol_section.get("identificationModule", {})
            nct_id = id_module.get("nctId")

            # Extract sponsor/collaborators module
            sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})

            # Extract responsible party (principal investigator)
            responsible_party = sponsor_module.get("responsibleParty", {})
            investigator_full_name = responsible_party.get("investigatorFullName")
            investigator_affiliation = responsible_party.get("investigatorAffiliation")

            if investigator_full_name:
                # Create investigator data
                investigator_data = {
                    "full_name": investigator_full_name,
                    "normalized_name": investigator_full_name.lower(),
                    "affiliation_site_id": None,  # Would need to link to site
                    "credentials": "Unknown",
                    "specialization": "Unknown",
                    "total_trials_count": 1,
                    "active_trials_count": 1,
                    "h_index": 0,
                    "total_publications": 0,
                    "recent_publications_count": 0,
                }

                # Insert investigator data
                investigator_success = self.db_manager.insert_data(
                    "investigators", investigator_data
                )
                if investigator_success:
                    logger.info(
                        f"Processed investigator data for {investigator_full_name}"
                    )

            return True

        except Exception as e:
            logger.error(f"Error processing investigator data: {e}")
            return False


# Example usage
if __name__ == "__main__":
    print("Data Processor module ready for use")
    print("This module processes data from APIs and stores it in the database")
