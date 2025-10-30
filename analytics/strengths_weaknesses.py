"""
Strengths and Weaknesses Detector for Clinical Trial Site Analysis Platform
Handles detection of site strengths and weaknesses based on performance metrics
"""
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
        logging.FileHandler(os.path.join(log_dir, "strengths_weaknesses.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrengthsWeaknessesDetector:
    """Detector for identifying site strengths and weaknesses"""
    
    def __init__(self, db_manager):
        """
        Initialize the strengths and weaknesses detector
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def define_strength_indicators(self) -> Dict[str, float]:
        """
        Define strength indicators with thresholds
        
        Returns:
            Dictionary with strength indicators and their thresholds
        """
        return {
            'completion_ratio': 0.8,  # 80% completion rate
            'recruitment_efficiency': 0.7,  # 70% efficiency score
            'experience_index': 0.6,  # 60% experience index
            'avg_h_index': 15.0,  # Average h-index of 15
            'recent_publications': 5.0  # At least 5 recent publications per investigator
        }
    
    def define_weakness_indicators(self) -> Dict[str, float]:
        """
        Define weakness indicators with thresholds
        
        Returns:
            Dictionary with weakness indicators and their thresholds
        """
        return {
            'completion_ratio': 0.5,  # Below 50% completion rate
            'recruitment_efficiency': 0.4,  # Below 40% efficiency score
            'terminated_studies_ratio': 0.2,  # More than 20% terminated studies
            'avg_h_index': 5.0,  # Average h-index below 5
            'data_quality_score': 0.6  # Data quality score below 0.6
        }
    
    def detect_site_strengths(self, site_id: int) -> List[Dict[str, Any]]:
        """
        Detect strengths for a specific site
        
        Args:
            site_id: ID of the site to analyze
            
        Returns:
            List of strength dictionaries
        """
        try:
            strengths = []
            thresholds = self.define_strength_indicators()
            
            # Get site metrics
            metrics_results = self.db_manager.query(
                "SELECT * FROM site_metrics WHERE site_id = ?", (site_id,))
            
            if not metrics_results:
                logger.info(f"No metrics found for site {site_id}")
                return strengths
            
            # Check each metric against strength thresholds
            for row in metrics_results:
                therapeutic_area = row['therapeutic_area']
                completion_ratio = row['completion_ratio'] or 0
                recruitment_efficiency = row['recruitment_efficiency_score'] or 0
                experience_index = row['experience_index'] or 0
                
                # Check completion ratio strength
                if completion_ratio >= thresholds['completion_ratio']:
                    strengths.append({
                        'type': 'strength',
                        'category': 'performance',
                        'metric': 'completion_ratio',
                        'value': completion_ratio,
                        'threshold': thresholds['completion_ratio'],
                        'therapeutic_area': therapeutic_area,
                        'description': f"High completion ratio ({completion_ratio:.2f}) in {therapeutic_area}"
                    })
                
                # Check recruitment efficiency strength
                if recruitment_efficiency >= thresholds['recruitment_efficiency']:
                    strengths.append({
                        'type': 'strength',
                        'category': 'performance',
                        'metric': 'recruitment_efficiency',
                        'value': recruitment_efficiency,
                        'threshold': thresholds['recruitment_efficiency'],
                        'therapeutic_area': therapeutic_area,
                        'description': f"High recruitment efficiency ({recruitment_efficiency:.2f}) in {therapeutic_area}"
                    })
                
                # Check experience index strength
                if experience_index >= thresholds['experience_index']:
                    strengths.append({
                        'type': 'strength',
                        'category': 'experience',
                        'metric': 'experience_index',
                        'value': experience_index,
                        'threshold': thresholds['experience_index'],
                        'therapeutic_area': therapeutic_area,
                        'description': f"High experience index ({experience_index:.2f}) in {therapeutic_area}"
                    })
            
            # Check investigator metrics
            investigator_results = self.db_manager.query(
                "SELECT AVG(h_index) as avg_h_index, AVG(recent_publications_count) as avg_recent_pubs "
                "FROM investigators WHERE affiliation_site_id = ?", (site_id,))
            
            if investigator_results and investigator_results[0]:
                row = investigator_results[0]
                avg_h_index = row['avg_h_index'] or 0
                avg_recent_pubs = row['avg_recent_pubs'] or 0
                
                # Check average h-index strength
                if avg_h_index >= thresholds['avg_h_index']:
                    strengths.append({
                        'type': 'strength',
                        'category': 'investigator',
                        'metric': 'avg_h_index',
                        'value': avg_h_index,
                        'threshold': thresholds['avg_h_index'],
                        'therapeutic_area': 'Overall',
                        'description': f"High average investigator h-index ({avg_h_index:.1f})"
                    })
                
                # Check recent publications strength
                if avg_recent_pubs >= thresholds['recent_publications']:
                    strengths.append({
                        'type': 'strength',
                        'category': 'investigator',
                        'metric': 'recent_publications',
                        'value': avg_recent_pubs,
                        'threshold': thresholds['recent_publications'],
                        'therapeutic_area': 'Overall',
                        'description': f"High recent publication rate ({avg_recent_pubs:.1f} per investigator)"
                    })
            
            logger.info(f"Detected {len(strengths)} strengths for site {site_id}")
            return strengths
            
        except Exception as e:
            logger.error(f"Error detecting strengths for site {site_id}: {e}")
            return []
    
    def detect_site_weaknesses(self, site_id: int) -> List[Dict[str, Any]]:
        """
        Detect weaknesses for a specific site
        
        Args:
            site_id: ID of the site to analyze
            
        Returns:
            List of weakness dictionaries
        """
        try:
            weaknesses = []
            thresholds = self.define_weakness_indicators()
            
            # Get site metrics
            metrics_results = self.db_manager.query(
                "SELECT * FROM site_metrics WHERE site_id = ?", (site_id,))
            
            if not metrics_results:
                logger.info(f"No metrics found for site {site_id}")
                return weaknesses
            
            # Check each metric against weakness thresholds
            for row in metrics_results:
                therapeutic_area = row['therapeutic_area']
                completion_ratio = row['completion_ratio'] or 0
                recruitment_efficiency = row['recruitment_efficiency_score'] or 0
                terminated_studies = row['terminated_studies'] or 0
                total_studies = row['total_studies'] or 0
                
                # Calculate terminated studies ratio
                terminated_ratio = terminated_studies / total_studies if total_studies > 0 else 0
                
                # Check completion ratio weakness
                if completion_ratio <= thresholds['completion_ratio']:
                    weaknesses.append({
                        'type': 'weakness',
                        'category': 'performance',
                        'metric': 'completion_ratio',
                        'value': completion_ratio,
                        'threshold': thresholds['completion_ratio'],
                        'therapeutic_area': therapeutic_area,
                        'description': f"Low completion ratio ({completion_ratio:.2f}) in {therapeutic_area}"
                    })
                
                # Check recruitment efficiency weakness
                if recruitment_efficiency <= thresholds['recruitment_efficiency']:
                    weaknesses.append({
                        'type': 'weakness',
                        'category': 'performance',
                        'metric': 'recruitment_efficiency',
                        'value': recruitment_efficiency,
                        'threshold': thresholds['recruitment_efficiency'],
                        'therapeutic_area': therapeutic_area,
                        'description': f"Low recruitment efficiency ({recruitment_efficiency:.2f}) in {therapeutic_area}"
                    })
                
                # Check terminated studies weakness
                if terminated_ratio >= thresholds['terminated_studies_ratio']:
                    weaknesses.append({
                        'type': 'weakness',
                        'category': 'performance',
                        'metric': 'terminated_studies_ratio',
                        'value': terminated_ratio,
                        'threshold': thresholds['terminated_studies_ratio'],
                        'therapeutic_area': therapeutic_area,
                        'description': f"High terminated studies ratio ({terminated_ratio:.2f}) in {therapeutic_area}"
                    })
            
            # Check data quality scores
            quality_results = self.db_manager.query(
                "SELECT overall_quality_score FROM data_quality_scores WHERE site_id = ? LIMIT 1", (site_id,))
            
            if quality_results and quality_results[0]:
                quality_score = quality_results[0]['overall_quality_score'] or 0
                
                # Check data quality weakness
                if quality_score <= thresholds['data_quality_score']:
                    weaknesses.append({
                        'type': 'weakness',
                        'category': 'data_quality',
                        'metric': 'overall_quality_score',
                        'value': quality_score,
                        'threshold': thresholds['data_quality_score'],
                        'therapeutic_area': 'Overall',
                        'description': f"Low data quality score ({quality_score:.2f})"
                    })
            
            # Check investigator metrics
            investigator_results = self.db_manager.query(
                "SELECT AVG(h_index) as avg_h_index FROM investigators WHERE affiliation_site_id = ?", (site_id,))
            
            if investigator_results and investigator_results[0]:
                avg_h_index = investigator_results[0]['avg_h_index'] or 0
                
                # Check average h-index weakness
                if avg_h_index <= thresholds['avg_h_index']:
                    weaknesses.append({
                        'type': 'weakness',
                        'category': 'investigator',
                        'metric': 'avg_h_index',
                        'value': avg_h_index,
                        'threshold': thresholds['avg_h_index'],
                        'therapeutic_area': 'Overall',
                        'description': f"Low average investigator h-index ({avg_h_index:.1f})"
                    })
            
            logger.info(f"Detected {len(weaknesses)} weaknesses for site {site_id}")
            return weaknesses
            
        except Exception as e:
            logger.error(f"Error detecting weaknesses for site {site_id}: {e}")
            return []
    
    def implement_comparative_analysis(self, site_id: int) -> Dict[str, Any]:
        """
        Implement comparative analysis detecting relative strengths
        
        Args:
            site_id: ID of the site to analyze
            
        Returns:
            Dictionary with comparative analysis results
        """
        try:
            # Get site metrics
            site_metrics = self.db_manager.query(
                "SELECT * FROM site_metrics WHERE site_id = ?", (site_id,))
            
            if not site_metrics:
                logger.info(f"No metrics found for site {site_id}")
                return {}
            
            # Get overall average metrics for comparison
            avg_metrics = self.db_manager.query("""
                SELECT 
                    AVG(completion_ratio) as avg_completion,
                    AVG(recruitment_efficiency_score) as avg_recruitment,
                    AVG(experience_index) as avg_experience
                FROM site_metrics
                """)
            
            if not avg_metrics or not avg_metrics[0]:
                logger.warning("No average metrics found for comparison")
                return {}
            
            avg_row = avg_metrics[0]
            avg_completion = avg_row['avg_completion'] or 0
            avg_recruitment = avg_row['avg_recruitment'] or 0
            avg_experience = avg_row['avg_experience'] or 0
            
            # Compare site metrics to averages
            comparative_results = {
                'site_id': site_id,
                'comparisons': []
            }
            
            for row in site_metrics:
                therapeutic_area = row['therapeutic_area']
                site_completion = row['completion_ratio'] or 0
                site_recruitment = row['recruitment_efficiency_score'] or 0
                site_experience = row['experience_index'] or 0
                
                # Calculate relative performance
                completion_relative = (site_completion / avg_completion) if avg_completion > 0 else 0
                recruitment_relative = (site_recruitment / avg_recruitment) if avg_recruitment > 0 else 0
                experience_relative = (site_experience / avg_experience) if avg_experience > 0 else 0
                
                # Identify relative strengths (performing 20% better than average)
                if completion_relative >= 1.2:
                    comparative_results['comparisons'].append({
                        'type': 'relative_strength',
                        'metric': 'completion_ratio',
                        'therapeutic_area': therapeutic_area,
                        'site_value': site_completion,
                        'average_value': avg_completion,
                        'relative_performance': completion_relative,
                        'description': f"Completion ratio {((completion_relative - 1) * 100):.1f}% above average in {therapeutic_area}"
                    })
                
                if recruitment_relative >= 1.2:
                    comparative_results['comparisons'].append({
                        'type': 'relative_strength',
                        'metric': 'recruitment_efficiency',
                        'therapeutic_area': therapeutic_area,
                        'site_value': site_recruitment,
                        'average_value': avg_recruitment,
                        'relative_performance': recruitment_relative,
                        'description': f"Recruitment efficiency {((recruitment_relative - 1) * 100):.1f}% above average in {therapeutic_area}"
                    })
                
                if experience_relative >= 1.2:
                    comparative_results['comparisons'].append({
                        'type': 'relative_strength',
                        'metric': 'experience_index',
                        'therapeutic_area': therapeutic_area,
                        'site_value': site_experience,
                        'average_value': avg_experience,
                        'relative_performance': experience_relative,
                        'description': f"Experience index {((experience_relative - 1) * 100):.1f}% above average in {therapeutic_area}"
                    })
            
            logger.info(f"Completed comparative analysis for site {site_id}")
            return comparative_results
            
        except Exception as e:
            logger.error(f"Error in comparative analysis for site {site_id}: {e}")
            return {}
    
    def build_pattern_detection(self, site_id: int) -> Dict[str, Any]:
        """
        Build pattern detection for specialized capabilities
        
        Args:
            site_id: ID of the site to analyze
            
        Returns:
            Dictionary with pattern detection results
        """
        try:
            patterns = {
                'site_id': site_id,
                'specialized_areas': [],
                'consistent_performance': [],
                'emerging_strengths': []
            }
            
            # Get temporal metrics to identify trends
            temporal_query = """
                SELECT 
                    therapeutic_area,
                    COUNT(*) as years_active,
                    AVG(completion_ratio) as avg_completion,
                    AVG(recruitment_efficiency_score) as avg_recruitment
                FROM site_metrics 
                WHERE site_id = ? 
                GROUP BY therapeutic_area
                HAVING COUNT(*) >= 2
                ORDER BY avg_completion DESC
                """
            
            temporal_results = self.db_manager.query(temporal_query, (site_id,))
            
            if temporal_results:
                # Identify specialized areas (high performance in specific therapeutic areas)
                for row in temporal_results:
                    therapeutic_area = row['therapeutic_area']
                    avg_completion = row['avg_completion'] or 0
                    avg_recruitment = row['avg_recruitment'] or 0
                    years_active = row['years_active'] or 0
                    
                    # Specialized area if consistently high performance over multiple years
                    if avg_completion >= 0.7 and avg_recruitment >= 0.6 and years_active >= 2:
                        patterns['specialized_areas'].append({
                            'therapeutic_area': therapeutic_area,
                            'avg_completion': avg_completion,
                            'avg_recruitment': avg_recruitment,
                            'years_active': years_active,
                            'description': f"Specialized in {therapeutic_area} with consistent high performance"
                        })
            
            # Check for consistent performance across therapeutic areas
            all_metrics = self.db_manager.query(
                "SELECT therapeutic_area, completion_ratio FROM site_metrics WHERE site_id = ?", (site_id,))
            
            if all_metrics and len(all_metrics) > 1:
                completion_scores = [row['completion_ratio'] or 0 for row in all_metrics]
                if completion_scores:
                    avg_completion = sum(completion_scores) / len(completion_scores)
                    # Consistent if low variance
                    variance = sum((score - avg_completion) ** 2 for score in completion_scores) / len(completion_scores)
                    if variance < 0.05:  # Low variance threshold
                        patterns['consistent_performance'].append({
                            'type': 'consistent_performance',
                            'average_completion': avg_completion,
                            'variance': variance,
                            'description': "Consistently performs well across therapeutic areas"
                        })
            
            logger.info(f"Built pattern detection for site {site_id}")
            return patterns
            
        except Exception as e:
            logger.error(f"Error in pattern detection for site {site_id}: {e}")
            return {}
    
    def create_weakness_categorization(self, weaknesses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create weakness categorization taxonomy
        
        Args:
            weaknesses: List of weakness dictionaries
            
        Returns:
            Dictionary with categorized weaknesses
        """
        try:
            categorized_weaknesses = {
                'performance': [],
                'data_quality': [],
                'investigator': [],
                'operational': [],
                'regulatory': []
            }
            
            # Categorize each weakness
            for weakness in weaknesses:
                category = weakness.get('category', 'operational')
                if category in categorized_weaknesses:
                    categorized_weaknesses[category].append(weakness)
                else:
                    categorized_weaknesses['operational'].append(weakness)
            
            logger.info(f"Categorized {len(weaknesses)} weaknesses")
            return categorized_weaknesses
            
        except Exception as e:
            logger.error(f"Error categorizing weaknesses: {e}")
            return {}
    
    def generate_structured_strengths_weaknesses(self, site_id: int) -> Dict[str, Any]:
        """
        Generate structured strength/weakness JSON objects
        
        Args:
            site_id: ID of the site to analyze
            
        Returns:
            Dictionary with structured strengths and weaknesses
        """
        try:
            # Detect strengths and weaknesses
            strengths = self.detect_site_strengths(site_id)
            weaknesses = self.detect_site_weaknesses(site_id)
            
            # Categorize weaknesses
            categorized_weaknesses = self.create_weakness_categorization(weaknesses)
            
            # Implement comparative analysis
            comparative_analysis = self.implement_comparative_analysis(site_id)
            
            # Build pattern detection
            patterns = self.build_pattern_detection(site_id)
            
            # Create structured output
            structured_output = {
                'site_id': site_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'strengths': strengths,
                'weaknesses': categorized_weaknesses,
                'comparative_analysis': comparative_analysis,
                'patterns': patterns
            }
            
            # Store in database
            self.store_strengths_weaknesses(site_id, structured_output)
            
            logger.info(f"Generated structured strengths/weaknesses for site {site_id}")
            return structured_output
            
        except Exception as e:
            logger.error(f"Error generating structured strengths/weaknesses for site {site_id}: {e}")
            return {}
    
    def store_strengths_weaknesses(self, site_id: int, analysis_data: Dict[str, Any]) -> bool:
        """
        Store strengths and weaknesses analysis in the database
        
        Args:
            site_id: ID of the site
            analysis_data: Dictionary with analysis results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert analysis data to JSON string for storage
            import json
            analysis_json = json.dumps(analysis_data, indent=2)
            
            # Check if record already exists
            existing = self.db_manager.query(
                "SELECT insight_id FROM ai_insights WHERE site_id = ?", (site_id,))
            
            if existing:
                # Update existing record
                sql = "UPDATE ai_insights SET strengths_summary = ?, weaknesses_summary = ?, generated_at = ? WHERE site_id = ?"
                strengths_summary = analysis_json[:500]  # Limit length
                weaknesses_summary = analysis_json[500:1000]  # Limit length
                success = self.db_manager.execute(
                    sql, (strengths_summary, weaknesses_summary, datetime.now().isoformat(), site_id))
            else:
                # Insert new record
                insight_data = {
                    'site_id': site_id,
                    'strengths_summary': analysis_json[:500],  # Limit length
                    'weaknesses_summary': analysis_json[500:1000],  # Limit length
                    'recommendation_text': 'Analysis completed',
                    'confidence_score': 0.8,
                    'gemini_model_version': 'N/A',
                    'generated_at': datetime.now().isoformat()
                }
                success = self.db_manager.insert_data('ai_insights', insight_data)
            
            if success:
                logger.info(f"Stored strengths/weaknesses analysis for site {site_id}")
            else:
                logger.error(f"Failed to store strengths/weaknesses analysis for site {site_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error storing strengths/weaknesses for site {site_id}: {e}")
            return False

# Example usage
if __name__ == "__main__":
    print("Strengths and Weaknesses Detector module ready for use")
    print("This module detects site strengths and weaknesses based on performance metrics")