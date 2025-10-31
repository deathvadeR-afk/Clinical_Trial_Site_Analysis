"""
Natural Language Query Module for Clinical Trial Site Analysis Platform
Handles LLM-powered natural language querying of the database
"""
import logging
import os
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "nl_query.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NLQueryProcessor:
    """Handles natural language querying of the clinical trial database"""
    
    def __init__(self, db_manager, gemini_client=None):
        """
        Initialize the NL query processor
        
        Args:
            db_manager: Database manager instance
            gemini_client: Optional Gemini client for advanced processing
        """
        self.db_manager = db_manager
        self.gemini_client = gemini_client
        self.conversation_history = []
    
    def design_query_interface(self) -> Dict[str, Any]:
        """
        Design natural language query interface
        
        Returns:
            Dictionary with interface configuration
        """
        return {
            'input_types': ['text'],
            'output_formats': ['text', 'json', 'table'],
            'supported_queries': [
                'site_search',
                'trial_search',
                'investigator_search',
                'performance_analysis',
                'recommendation_queries'
            ],
            'example_queries': [
                "Find sites in the United States with experience in oncology trials",
                "Show me investigators with high h-index in cardiology",
                "Which sites have the highest completion ratios?",
                "Recommend sites for a Phase 2 diabetes study"
            ]
        }
    
    def implement_query_understanding_pipeline(self, query: str) -> Dict[str, Any]:
        """
        Implement query understanding pipeline
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary with parsed query information
        """
        try:
            # Convert to lowercase for processing
            query_lower = query.lower()
            
            # Identify query type based on keywords
            query_type = 'general'
            target_entity = 'site'
            
            if 'site' in query_lower or 'location' in query_lower:
                query_type = 'site_search'
                target_entity = 'site'
            elif 'trial' in query_lower or 'study' in query_lower:
                query_type = 'trial_search'
                target_entity = 'trial'
            elif 'investigator' in query_lower or 'researcher' in query_lower:
                query_type = 'investigator_search'
                target_entity = 'investigator'
            elif 'performance' in query_lower or 'ratio' in query_lower:
                query_type = 'performance_analysis'
                target_entity = 'site'
            elif 'recommend' in query_lower:
                query_type = 'recommendation_queries'
                target_entity = 'site'
            
            # Extract key entities and filters
            entities = self._extract_entities(query_lower)
            filters = self._extract_filters(query_lower)
            therapeutic_areas = self._extract_therapeutic_areas(query_lower)
            phases = self._extract_phases(query_lower)
            
            # Extract numerical values
            numerical_values = self._extract_numerical_values(query)
            
            parsed_query = {
                'original_query': query,
                'query_type': query_type,
                'target_entity': target_entity,
                'entities': entities,
                'filters': filters,
                'therapeutic_areas': therapeutic_areas,
                'phases': phases,
                'numerical_values': numerical_values,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Parsed query: {query_type} for {target_entity}")
            return parsed_query
            
        except Exception as e:
            logger.error(f"Error in query understanding pipeline: {e}")
            return {
                'original_query': query,
                'query_type': 'unknown',
                'target_entity': 'unknown',
                'error': str(e)
            }
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from query"""
        entities = []
        
        # Simple entity extraction based on common terms
        entity_patterns = {
            'countries': r'\b(united states|usa|uk|germany|france|japan|china|india|canada|australia|brazil)\b',
            'cities': r'\b(new york|boston|london|paris|tokyo|beijing|mumbai|toronto|sydney|são paulo)\b',
            'institutions': r'\b(hospital|university|clinic|research center|medical center)\b'
        }
        
        for category, pattern in entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
            
        return list(set(entities))  # Remove duplicates
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract filter conditions from query"""
        filters = {}
        
        # Extract comparison operators
        if 'greater than' in query or 'more than' in query or '>' in query:
            filters['comparison'] = 'greater_than'
        elif 'less than' in query or '<' in query:
            filters['comparison'] = 'less_than'
        elif 'equal' in query or '=' in query:
            filters['comparison'] = 'equal'
        else:
            filters['comparison'] = 'any'
            
        # Extract date ranges
        date_patterns = [
            r'(\d{4})',  # Year
            r'(\d{4}-\d{2})',  # Year-Month
            r'(\d{4}-\d{2}-\d{2})'  # Year-Month-Day
        ]
        
        date_matches = []
        for pattern in date_patterns:
            matches = re.findall(pattern, query)
            date_matches.extend(matches)
            
        if date_matches:
            filters['dates'] = date_matches
            
        return filters
    
    def _extract_therapeutic_areas(self, query: str) -> List[str]:
        """Extract therapeutic areas from query"""
        therapeutic_areas = []
        
        # Common therapeutic areas
        areas = [
            'oncology', 'cancer', 'tumor',
            'cardiology', 'heart', 'cardiac',
            'neurology', 'brain', 'neuro',
            'endocrinology', 'diabetes', 'thyroid',
            'psychiatry', 'mental health', 'depression',
            'infectious disease', 'virus', 'bacteria',
            'pediatrics', 'children',
            'dermatology', 'skin',
            'gastroenterology', 'digestive'
        ]
        
        for area in areas:
            if area in query:
                therapeutic_areas.append(area)
                
        return list(set(therapeutic_areas))  # Remove duplicates
    
    def _extract_phases(self, query: str) -> List[str]:
        """Extract trial phases from query"""
        phases = []
        
        # Phase patterns
        phase_patterns = [r'phase\s*[1-4]', r'phase\s*(i{1,4}|iv)']
        
        for pattern in phase_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            phases.extend(matches)
            
        return list(set(phases))  # Remove duplicates
    
    def _extract_numerical_values(self, query: str) -> List[float]:
        """Extract numerical values from query"""
        # Find all numbers in the query
        numbers = re.findall(r'\b\d+\.?\d*\b', query)
        return [float(num) for num in numbers if num.replace('.', '').isdigit()]
    
    def execute_generated_queries(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute generated queries against database
        
        Args:
            parsed_query: Dictionary with parsed query information
            
        Returns:
            List of query results
        """
        try:
            query_type = parsed_query.get('query_type', 'general')
            target_entity = parsed_query.get('target_entity', 'site')
            therapeutic_areas = parsed_query.get('therapeutic_areas', [])
            phases = parsed_query.get('phases', [])
            numerical_values = parsed_query.get('numerical_values', [])
            
            # Generate SQL based on query type
            if query_type == 'site_search':
                sql = self._generate_site_search_query(therapeutic_areas, phases, numerical_values)
            elif query_type == 'trial_search':
                sql = self._generate_trial_search_query(therapeutic_areas, phases, numerical_values)
            elif query_type == 'investigator_search':
                sql = self._generate_investigator_search_query(therapeutic_areas, numerical_values)
            elif query_type == 'performance_analysis':
                sql = self._generate_performance_analysis_query(numerical_values)
            elif query_type == 'recommendation_queries':
                sql = self._generate_recommendation_query(therapeutic_areas, phases, numerical_values)
            else:
                # Default general query
                sql = "SELECT * FROM sites_master LIMIT 10"
            
            # Execute query
            results = self.db_manager.query(sql)
            
            # Convert to list of dictionaries
            formatted_results = [dict(row) for row in results] if results else []
            
            logger.info(f"Executed query and retrieved {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error executing generated queries: {e}")
            return []
    
    def _generate_site_search_query(self, therapeutic_areas: List[str], 
                                 phases: List[str], numerical_values: List[float]) -> str:
        """Generate SQL for site search queries"""
        # Base query
        sql = """
            SELECT sm.*, si.completion_ratio, si.recruitment_efficiency_score
            FROM sites_master sm
            LEFT JOIN site_metrics si ON sm.site_id = si.site_id
        """
        
        # Add conditions if therapeutic areas or phases are specified
        conditions = []
        
        if therapeutic_areas:
            area_conditions = " OR ".join([f"si.therapeutic_area LIKE '%{area}%'" for area in therapeutic_areas])
            conditions.append(f"({area_conditions})")
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        sql += " LIMIT 50"
        return sql
    
    def _generate_trial_search_query(self, therapeutic_areas: List[str], 
                                 phases: List[str], numerical_values: List[float]) -> str:
        """Generate SQL for trial search queries"""
        sql = "SELECT * FROM clinical_trials"
        
        conditions = []
        
        if therapeutic_areas:
            area_conditions = " OR ".join([f"conditions LIKE '%{area}%'" for area in therapeutic_areas])
            conditions.append(f"({area_conditions})")
            
        if phases:
            phase_conditions = " OR ".join([f"phase LIKE '%{phase}%'" for phase in phases])
            conditions.append(f"({phase_conditions})")
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        sql += " LIMIT 50"
        return sql
    
    def _generate_investigator_search_query(self, therapeutic_areas: List[str], 
                                        numerical_values: List[float]) -> str:
        """Generate SQL for investigator search queries"""
        sql = """
            SELECT i.*, sm.site_name
            FROM investigators i
            JOIN sites_master sm ON i.affiliation_site_id = sm.site_id
        """
        
        conditions = []
        
        if therapeutic_areas:
            # This would require joining with trial data to get therapeutic areas
            conditions.append("1=1")  # Placeholder
            
        if numerical_values:
            # Filter by h-index or publication count if specified
            for value in numerical_values:
                if value > 10:  # Assume it's an h-index threshold
                    conditions.append(f"i.h_index >= {value}")
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        sql += " LIMIT 50"
        return sql
    
    def _generate_performance_analysis_query(self, numerical_values: List[float]) -> str:
        """Generate SQL for performance analysis queries"""
        sql = """
            SELECT sm.site_name, sm.country, si.completion_ratio, 
                   si.recruitment_efficiency_score, si.experience_index
            FROM sites_master sm
            JOIN site_metrics si ON sm.site_id = si.site_id
        """
        
        conditions = []
        
        if numerical_values:
            # Filter by performance metrics if thresholds are specified
            for value in numerical_values:
                if 0 <= value <= 1:  # Assume it's a ratio threshold
                    conditions.append(f"si.completion_ratio >= {value}")
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        sql += " ORDER BY si.completion_ratio DESC LIMIT 50"
        return sql
    
    def _generate_recommendation_query(self, therapeutic_areas: List[str], 
                                 phases: List[str], numerical_values: List[float]) -> str:
        """Generate SQL for recommendation queries"""
        sql = """
            SELECT sm.site_name, sm.country, sm.city, 
                   si.completion_ratio, si.experience_index,
                   si.recruitment_efficiency_score
            FROM sites_master sm
            JOIN site_metrics si ON sm.site_id = si.site_id
        """
        
        conditions = []
        
        if therapeutic_areas:
            area_conditions = " OR ".join([f"si.therapeutic_area LIKE '%{area}%'" for area in therapeutic_areas])
            conditions.append(f"({area_conditions})")
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        sql += " ORDER BY si.completion_ratio DESC, si.experience_index DESC LIMIT 20"
        return sql
    
    def generate_natural_language_responses(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        Generate natural language responses to queries
        
        Args:
            query: Original natural language query
            results: Query results
            
        Returns:
            Natural language response text
        """
        try:
            if not results:
                return f"I couldn't find any results for your query: '{query}'"
            
            # Count results
            result_count = len(results)
            
            # Generate response based on query type
            if 'recommend' in query.lower():
                response = f"I found {result_count} recommended sites based on your query. "
                if results:
                    top_sites = results[:3]
                    site_names = [site.get('site_name', 'Unknown Site') for site in top_sites]
                    response += f"The top recommendations are: {', '.join(site_names)}."
            elif 'performance' in query.lower() or 'ratio' in query.lower():
                response = f"I found {result_count} sites matching your performance criteria. "
                if results:
                    avg_completion = sum(site.get('completion_ratio', 0) for site in results) / len(results)
                    response += f"The average completion ratio is {avg_completion:.2f}."
            elif 'investigator' in query.lower():
                response = f"I found {result_count} investigators matching your criteria. "
                if results:
                    avg_h_index = sum(site.get('h_index', 0) for site in results) / len(results)
                    response += f"The average h-index is {avg_h_index:.1f}."
            else:
                response = f"I found {result_count} results matching your query: '{query}'. "
                if results:
                    # List first few results
                    first_results = results[:3]
                    items = []
                    for result in first_results:
                        if 'site_name' in result:
                            items.append(result['site_name'])
                        elif 'full_name' in result:
                            items.append(result['full_name'])
                        elif 'nct_id' in result:
                            items.append(result['nct_id'])
                    
                    if items:
                        response += f"Examples include: {', '.join(items)}."
            
            # Add to conversation history
            self.conversation_history.append({
                'query': query,
                'results_count': result_count,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info("Generated natural language response")
            return response
            
        except Exception as e:
            logger.error(f"Error generating natural language response: {e}")
            return f"Sorry, I encountered an error processing your query: {query}"
    
    def implement_multi_turn_conversation(self, query: str) -> str:
        """
        Implement multi-turn conversation support
        
        Args:
            query: Natural language query string
            
        Returns:
            Response text
        """
        try:
            # Add query to conversation history
            self.conversation_history.append({
                'query': query,
                'timestamp': datetime.now().isoformat()
            })
            
            # Process query
            parsed_query = self.implement_query_understanding_pipeline(query)
            results = self.execute_generated_queries(parsed_query)
            response = self.generate_natural_language_responses(query, results)
            
            # Update conversation history with response
            if self.conversation_history:
                self.conversation_history[-1]['response'] = response
                self.conversation_history[-1]['results_count'] = len(results)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in multi-turn conversation: {e}")
            return f"Sorry, I encountered an error: {e}"
    
    def add_query_suggestion_system(self) -> List[str]:
        """
        Add query suggestion system
        
        Returns:
            List of suggested queries
        """
        return [
            "Find sites with high completion ratios in oncology",
            "Show me investigators with h-index above 20",
            "Recommend sites for a Phase 3 cardiovascular study",
            "Which sites have experience with diabetes trials?",
            "List sites in the United States with university affiliation",
            "Show performance metrics for sites in Europe",
            "Find investigators specializing in neurology",
            "Recommend sites based on enrollment capacity"
        ]
    
    def implement_safety_controls(self, query: str) -> bool:
        """
        Implement safety controls for queries
        
        Args:
            query: Query to check
            
        Returns:
            True if query is safe, False otherwise
        """
        try:
            # Check for potentially dangerous SQL patterns
            dangerous_patterns = [
                r'\b(drop|delete|truncate|alter|update|insert)\b',
                r'[;]',  # Semicolon
                r'--',    # SQL comment
                r'/\*',   # SQL comment start
                r'\*/',   # SQL comment end
            ]
            
            query_lower = query.lower()
            
            for pattern in dangerous_patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.warning(f"Potentially dangerous query detected: {query}")
                    return False
            
            # Check query length
            if len(query) > 1000:
                logger.warning(f"Query too long: {len(query)} characters")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in safety controls: {e}")
            return False
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main method to process a natural language query
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Implement safety controls
            if not self.implement_safety_controls(query):
                return {
                    'success': False,
                    'error': 'Query failed safety checks',
                    'response': 'Sorry, your query contains potentially unsafe elements.'
                }
            
            # Process query through pipeline
            parsed_query = self.implement_query_understanding_pipeline(query)
            results = self.execute_generated_queries(parsed_query)
            response = self.generate_natural_language_responses(query, results)
            
            # Prepare results
            processing_results = {
                'success': True,
                'original_query': query,
                'parsed_query': parsed_query,
                'database_results': results,
                'response': response,
                'results_count': len(results),
                'processing_time': datetime.now().isoformat()
            }
            
            logger.info(f"Processed natural language query successfully: {query}")
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing natural language query: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Sorry, I encountered an error processing your query: {e}",
                'original_query': query
            }

# Example usage
if __name__ == "__main__":
    print("NL Query Processor module ready for use")
    print("This module handles LLM-powered natural language querying of the database")