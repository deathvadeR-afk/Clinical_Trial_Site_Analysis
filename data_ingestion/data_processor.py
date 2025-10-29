"""
Data Processor for Clinical Trial Site Analysis Platform
Handles the flow of data from APIs to the database
"""
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "data_processor.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Processor for handling data flow from APIs to database"""
    
    def __init__(self, db_manager):
        """
        Initialize the data processor
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
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
            protocol_section = study_data.get('protocolSection', {})
            
            # Extract identification module
            id_module = protocol_section.get('identificationModule', {})
            nct_id = id_module.get('nctId')
            brief_title = id_module.get('briefTitle')
            official_title = id_module.get('officialTitle')
            
            # Extract status module
            status_module = protocol_section.get('statusModule', {})
            overall_status = status_module.get('overallStatus')
            
            # Extract design module
            design_module = protocol_section.get('designModule', {})
            study_type = design_module.get('studyType')
            phases = design_module.get('phases', [])
            phase = phases[0] if phases else None
            
            # Extract conditions module
            conditions_module = protocol_section.get('conditionsModule', {})
            conditions = conditions_module.get('conditions', [])
            conditions_json = json.dumps(conditions) if conditions else None
            
            # Extract arms/interventions module
            arms_module = protocol_section.get('armsInterventionsModule', {})
            interventions = arms_module.get('interventions', [])
            interventions_json = json.dumps(interventions) if interventions else None
            
            # Extract enrollment info
            design_info = design_module.get('designInfo', {})
            enrollment_info = design_info.get('enrollmentInfo', {})
            enrollment_count = enrollment_info.get('count')
            
            # Extract dates
            start_date_struct = status_module.get('startDateStruct', {})
            start_date = start_date_struct.get('date')
            
            completion_date_struct = status_module.get('completionDateStruct', {})
            completion_date = completion_date_struct.get('date')
            
            primary_completion_date_struct = status_module.get('primaryCompletionDateStruct', {})
            primary_completion_date = primary_completion_date_struct.get('date')
            
            # Extract sponsor information
            sponsor_module = protocol_section.get('sponsorCollaboratorsModule', {})
            lead_sponsor = sponsor_module.get('leadSponsor', {})
            sponsor_name = lead_sponsor.get('name')
            sponsor_type = lead_sponsor.get('class')
            
            # Extract posting dates
            last_update_posted = status_module.get('lastUpdatePostDateStruct', {}).get('date')
            study_first_posted = status_module.get('studyFirstPostDateStruct', {}).get('date')
            
            # Prepare data for insertion
            trial_data = {
                'nct_id': nct_id,
                'title': brief_title or official_title,
                'status': overall_status,
                'phase': phase,
                'study_type': study_type,
                'conditions': conditions_json,
                'interventions': interventions_json,
                'enrollment_count': enrollment_count,
                'start_date': start_date,
                'completion_date': completion_date,
                'primary_completion_date': primary_completion_date,
                'sponsor_name': sponsor_name,
                'sponsor_type': sponsor_type,
                'last_update_posted': last_update_posted,
                'study_first_posted': study_first_posted
            }
            
            # Insert into database
            success = self.db_manager.insert_data('clinical_trials', trial_data)
            if success:
                logger.info(f"Processed clinical trial data for {nct_id}")
            else:
                logger.error(f"Failed to insert clinical trial data for {nct_id}")
            
            return success
            
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
            protocol_section = study_data.get('protocolSection', {})
            
            # Extract identification info
            id_module = protocol_section.get('identificationModule', {})
            nct_id = id_module.get('nctId')
            
            # Extract locations module
            contacts_locations_module = protocol_section.get('contactsLocationsModule', {})
            locations = contacts_locations_module.get('locations', [])
            
            # Process each location
            for location in locations:
                facility = location.get('facility', '')
                city = location.get('city', '')
                state = location.get('zip', '')
                country = location.get('country', '')
                
                # Create site data (simplified for now)
                site_data = {
                    'site_name': facility,
                    'city': city,
                    'state': state,
                    'country': country,
                    'institution_type': 'Unknown',
                    'accreditation_status': 'Unknown'
                }
                
                # Insert site data
                site_success = self.db_manager.insert_data('sites_master', site_data)
                if site_success:
                    logger.info(f"Processed site data for {facility}")
                
                # TODO: Link site to trial in site_trial_participation table
                # This would require getting the site_id after insertion
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing site data: {e}")
            return False
    
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
            protocol_section = study_data.get('protocolSection', {})
            
            # Extract identification info
            id_module = protocol_section.get('identificationModule', {})
            nct_id = id_module.get('nctId')
            
            # Extract sponsor/collaborators module
            sponsor_module = protocol_section.get('sponsorCollaboratorsModule', {})
            
            # Extract responsible party (principal investigator)
            responsible_party = sponsor_module.get('responsibleParty', {})
            investigator_full_name = responsible_party.get('investigatorFullName')
            investigator_affiliation = responsible_party.get('investigatorAffiliation')
            
            if investigator_full_name:
                # Create investigator data
                investigator_data = {
                    'full_name': investigator_full_name,
                    'normalized_name': investigator_full_name.lower(),
                    'affiliation_site_id': None,  # Would need to link to site
                    'credentials': 'Unknown',
                    'specialization': 'Unknown',
                    'total_trials_count': 1,
                    'active_trials_count': 1,
                    'h_index': 0,
                    'total_publications': 0,
                    'recent_publications_count': 0
                }
                
                # Insert investigator data
                investigator_success = self.db_manager.insert_data('investigators', investigator_data)
                if investigator_success:
                    logger.info(f"Processed investigator data for {investigator_full_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing investigator data: {e}")
            return False

# Example usage
if __name__ == "__main__":
    print("Data Processor module ready for use")
    print("This module processes data from APIs and stores it in the database")