"""
Investigator Metrics Calculator for Clinical Trial Site Analysis Platform
Handles calculation of investigator metrics from PubMed data
"""
import logging
import os
import json
from typing import Dict, List, Optional, Any
from collections import Counter

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "investigator_metrics.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InvestigatorMetricsCalculator:
    """Calculator for determining investigator metrics from publication data"""
    
    def __init__(self, db_manager):
        """
        Initialize the investigator metrics calculator
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def calculate_h_index(self, citations: List[int]) -> int:
        """
        Calculate h-index for an investigator
        
        The h-index is the largest number h such that h publications have at least h citations each.
        
        Args:
            citations: List of citation counts for each publication
            
        Returns:
            h-index value
        """
        if not citations:
            return 0
            
        # Sort citations in descending order
        sorted_citations = sorted(citations, reverse=True)
        
        # Find h-index
        h_index = 0
        for i, citation_count in enumerate(sorted_citations):
            # h-index is the largest h such that the hth paper has at least h citations
            if citation_count >= i + 1:
                h_index = i + 1
            else:
                break
                
        logger.info(f"Calculated h-index: {h_index}")
        return h_index
    
    def calculate_publication_counts(self, publications: List[Dict]) -> Dict[str, int]:
        """
        Calculate various publication counts
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            Dictionary with publication counts
        """
        if not publications:
            return {
                'total_publications': 0,
                'recent_publications': 0,
                'journal_articles': 0,
                'clinical_trials': 0,
                'reviews': 0
            }
        
        total_count = len(publications)
        recent_count = 0
        journal_articles = 0
        clinical_trials = 0
        reviews = 0
        
        current_year = 2025  # In practice, would use datetime.now().year
        
        for pub in publications:
            # Count recent publications (last 5 years)
            pub_year_str = pub.get('publication_date', '')[:4]  # Extract year from YYYY-MM-DD
            try:
                pub_year = int(pub_year_str)
                if current_year - pub_year <= 5:
                    recent_count += 1
            except (ValueError, TypeError):
                pass  # Invalid date format
            
            # Count publication types
            pub_type = pub.get('publication_type', '').lower()
            if 'journal' in pub_type:
                journal_articles += 1
            elif 'clinical' in pub_type:
                clinical_trials += 1
            elif 'review' in pub_type:
                reviews += 1
                
        return {
            'total_publications': total_count,
            'recent_publications': recent_count,
            'journal_articles': journal_articles,
            'clinical_trials': clinical_trials,
            'reviews': reviews
        }
    
    def analyze_research_focus(self, publications: List[Dict]) -> Dict[str, Any]:
        """
        Analyze research focus areas from publication data
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            Dictionary with research focus analysis
        """
        if not publications:
            return {
                'primary_focus_areas': [],
                'focus_area_counts': {},
                'collaboration_patterns': []
            }
        
        # Extract keywords and MeSH terms
        all_keywords = []
        all_mesh_terms = []
        all_authors = []
        
        for pub in publications:
            # Extract keywords
            keywords_str = pub.get('keywords', '[]')
            try:
                keywords = json.loads(keywords_str) if keywords_str else []
                all_keywords.extend(keywords)
            except json.JSONDecodeError:
                pass  # Invalid JSON
            
            # Extract MeSH terms
            mesh_str = pub.get('mesh_terms', '[]')
            try:
                mesh_terms = json.loads(mesh_str) if mesh_str else []
                all_mesh_terms.extend(mesh_terms)
            except json.JSONDecodeError:
                pass  # Invalid JSON
            
            # Extract authors for collaboration analysis
            authors_str = pub.get('authors', '[]')
            try:
                authors = json.loads(authors_str) if authors_str else []
                all_authors.extend(authors)
            except json.JSONDecodeError:
                pass  # Invalid JSON
        
        # Count focus areas
        focus_counter = Counter()
        focus_counter.update(all_keywords)
        focus_counter.update(all_mesh_terms)
        
        # Get top focus areas
        top_focus_areas = [item[0] for item in focus_counter.most_common(5)]
        
        # Analyze collaboration patterns
        author_counter = Counter(all_authors)
        frequent_collaborators = [author for author, count in author_counter.most_common(10) 
                                if count > 1 and author]  # Exclude empty names
        
        return {
            'primary_focus_areas': top_focus_areas,
            'focus_area_counts': dict(focus_counter),
            'collaboration_patterns': frequent_collaborators
        }
    
    def calculate_investigator_metrics(self, investigator_id: int) -> Dict[str, Any]:
        """
        Calculate all metrics for a specific investigator
        
        Args:
            investigator_id: ID of the investigator
            
        Returns:
            Dictionary with all calculated metrics
        """
        try:
            # Get investigator data
            investigator_results = self.db_manager.query(
                "SELECT * FROM investigators WHERE investigator_id = ?", (investigator_id,))
            
            if not investigator_results:
                logger.warning(f"No investigator found with ID {investigator_id}")
                return {}
            
            # Get publications for this investigator
            publication_results = self.db_manager.query(
                "SELECT * FROM pubmed_publications WHERE investigator_id = ?", (investigator_id,))
            
            publications = [dict(row) for row in publication_results]
            
            # Extract citation counts
            citations = []
            for pub in publications:
                try:
                    citations.append(int(pub.get('citations_count', 0)))
                except (ValueError, TypeError):
                    citations.append(0)
            
            # Calculate h-index
            h_index = self.calculate_h_index(citations)
            
            # Calculate publication counts
            pub_counts = self.calculate_publication_counts(publications)
            
            # Analyze research focus
            focus_analysis = self.analyze_research_focus(publications)
            
            # Combine all metrics
            metrics = {
                'investigator_id': investigator_id,
                'h_index': h_index,
                'total_publications': pub_counts['total_publications'],
                'recent_publications': pub_counts['recent_publications'],
                'journal_articles': pub_counts['journal_articles'],
                'clinical_trials': pub_counts['clinical_trials'],
                'reviews': pub_counts['reviews'],
                'primary_focus_areas': focus_analysis['primary_focus_areas'],
                'collaboration_patterns': focus_analysis['collaboration_patterns']
            }
            
            logger.info(f"Calculated metrics for investigator {investigator_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics for investigator {investigator_id}: {e}")
            return {}
    
    def update_investigator_record(self, investigator_id: int) -> bool:
        """
        Update investigator record with calculated metrics
        
        Args:
            investigator_id: ID of the investigator to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Calculate metrics
            metrics = self.calculate_investigator_metrics(investigator_id)
            
            if not metrics:
                logger.warning(f"No metrics calculated for investigator {investigator_id}")
                return False
            
            # Update investigator record
            update_data = {
                'h_index': metrics['h_index'],
                'total_publications': metrics['total_publications'],
                'recent_publications_count': metrics['recent_publications']
            }
            
            # Build UPDATE statement
            set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
            values = list(update_data.values()) + [investigator_id]
            sql = f"UPDATE investigators SET {set_clause} WHERE investigator_id = ?"
            
            success = self.db_manager.execute(sql, tuple(values))
            
            if success:
                logger.info(f"Updated investigator {investigator_id} with new metrics")
            else:
                logger.error(f"Failed to update investigator {investigator_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating investigator {investigator_id}: {e}")
            return False

# Example usage
if __name__ == "__main__":
    print("Investigator Metrics Calculator module ready for use")
    print("This module calculates investigator metrics from publication data")