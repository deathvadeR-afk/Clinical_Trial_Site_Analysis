"""
Test script for Investigator Metrics Calculator
"""
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion.investigator_metrics import InvestigatorMetricsCalculator
from database.db_manager import DatabaseManager

def test_investigator_metrics():
    """Test the investigator metrics calculator functionality"""
    print("Testing Investigator Metrics Calculator")
    print("=" * 38)
    
    # Initialize database manager
    db_manager = DatabaseManager("test_clinical_trials.db")
    
    # Connect to database
    if db_manager.connect():
        print("✓ Database connection successful")
        
        # Create tables
        if db_manager.create_tables("database/schema.sql"):
            print("✓ Database tables created successfully")
            
            # Initialize investigator metrics calculator
            metrics_calculator = InvestigatorMetricsCalculator(db_manager)
            print("✓ Investigator metrics calculator initialized")
            
            # Test 1: Calculate h-index
            print("\nTest 1: Calculating h-index...")
            citations = [100, 50, 30, 20, 15, 10, 8, 5, 3, 1]
            h_index = metrics_calculator.calculate_h_index(citations)
            print(f"✓ H-index calculated: {h_index}")
            
            # Test 2: Calculate publication counts
            print("\nTest 2: Calculating publication counts...")
            sample_publications = [
                {
                    'publication_date': '2023-01-15',
                    'publication_type': 'Journal Article'
                },
                {
                    'publication_date': '2022-05-20',
                    'publication_type': 'Clinical Trial'
                },
                {
                    'publication_date': '2020-03-10',
                    'publication_type': 'Review'
                },
                {
                    'publication_date': '2019-11-05',
                    'publication_type': 'Journal Article'
                }
            ]
            
            pub_counts = metrics_calculator.calculate_publication_counts(sample_publications)
            print("✓ Publication counts calculated:")
            for key, value in pub_counts.items():
                print(f"  {key}: {value}")
            
            # Test 3: Analyze research focus
            print("\nTest 3: Analyzing research focus...")
            sample_publications_with_keywords = [
                {
                    'keywords': json.dumps(['diabetes', 'metabolism', 'insulin']),
                    'mesh_terms': json.dumps(['Diabetes Mellitus', 'Glucose Metabolism']),
                    'authors': json.dumps(['Dr. Smith', 'Dr. Johnson', 'Dr. Brown'])
                },
                {
                    'keywords': json.dumps(['cardiovascular', 'heart', 'diabetes']),
                    'mesh_terms': json.dumps(['Cardiovascular Diseases', 'Diabetes Mellitus']),
                    'authors': json.dumps(['Dr. Smith', 'Dr. Wilson', 'Dr. Brown'])
                }
            ]
            
            focus_analysis = metrics_calculator.analyze_research_focus(sample_publications_with_keywords)
            print("✓ Research focus analysis completed:")
            print(f"  Primary focus areas: {focus_analysis['primary_focus_areas']}")
            print(f"  Collaboration patterns: {focus_analysis['collaboration_patterns']}")
            
            # Test 4: Insert test data and calculate metrics
            print("\nTest 4: Calculating metrics for investigator in database...")
            
            # Insert test investigator
            test_investigator = {
                'full_name': 'Dr. Jane Smith',
                'normalized_name': 'dr. jane smith',
                'affiliation_site_id': None,
                'credentials': 'MD, PhD',
                'specialization': 'Endocrinology',
                'total_trials_count': 5,
                'active_trials_count': 2,
                'h_index': 0,  # Will be updated
                'total_publications': 0,  # Will be updated
                'recent_publications_count': 0  # Will be updated
            }
            
            if db_manager.insert_data("investigators", test_investigator):
                print("✓ Test investigator inserted successfully")
                
                # Get the investigator ID
                results = db_manager.query("SELECT investigator_id FROM investigators WHERE full_name = ?", 
                                         ("Dr. Jane Smith",))
                if results:
                    investigator_id = results[0]['investigator_id']
                    
                    # Insert test publications
                    test_publications = [
                        {
                            'pmid': '12345678',
                            'title': 'Sample Publication 1',
                            'authors': json.dumps(['Dr. Smith', 'Dr. Johnson']),
                            'journal': 'Journal of Medicine',
                            'publication_date': '2023-01-01',
                            'citations_count': 50,
                            'abstract': 'Sample abstract',
                            'keywords': json.dumps(['diabetes', 'metabolism']),
                            'mesh_terms': json.dumps(['Diabetes Mellitus']),
                            'investigator_id': investigator_id,
                            'site_id': None
                        },
                        {
                            'pmid': '23456789',
                            'title': 'Sample Publication 2',
                            'authors': json.dumps(['Dr. Smith', 'Dr. Wilson']),
                            'journal': 'Clinical Endocrinology',
                            'publication_date': '2022-06-15',
                            'citations_count': 30,
                            'abstract': 'Sample abstract 2',
                            'keywords': json.dumps(['diabetes', 'insulin']),
                            'mesh_terms': json.dumps(['Diabetes Mellitus', 'Insulin']),
                            'investigator_id': investigator_id,
                            'site_id': None
                        }
                    ]
                    
                    if db_manager.insert_many("pubmed_publications", test_publications):
                        print("✓ Test publications inserted successfully")
                        
                        # Calculate metrics
                        metrics = metrics_calculator.calculate_investigator_metrics(investigator_id)
                        if metrics:
                            print("✓ Investigator metrics calculated successfully:")
                            print(f"  H-index: {metrics['h_index']}")
                            print(f"  Total publications: {metrics['total_publications']}")
                            print(f"  Recent publications: {metrics['recent_publications']}")
                            print(f"  Primary focus areas: {metrics['primary_focus_areas']}")
                            
                            # Update investigator record
                            if metrics_calculator.update_investigator_record(investigator_id):
                                print("✓ Investigator record updated with new metrics")
                            else:
                                print("✗ Failed to update investigator record")
                        else:
                            print("✗ Failed to calculate investigator metrics")
                    else:
                        print("✗ Failed to insert test publications")
                else:
                    print("✗ Failed to retrieve investigator ID")
            else:
                print("✗ Failed to insert test investigator")
            
        else:
            print("✗ Failed to create database tables")
        
        # Disconnect
        db_manager.disconnect()
        print("\n✓ Database disconnected")
    else:
        print("✗ Database connection failed")
        return False
    
    print("\n" + "=" * 38)
    print("Investigator Metrics Calculator Tests Complete!")
    return True

if __name__ == "__main__":
    test_investigator_metrics()