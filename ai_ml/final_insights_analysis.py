import sqlite3
import os

def final_insights_analysis():
    """Final analysis of AI vs algorithmic insights after generation process"""
    print("🔍 Final Insights Analysis")
    print("=" * 50)
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'clinical_trials.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get total number of insights
        cursor.execute("SELECT COUNT(*) FROM ai_insights")
        total_insights = cursor.fetchone()[0]
        print(f"Total insights records: {total_insights}")
        
        # Check gemini_model_version to distinguish between AI and algorithmic
        cursor.execute("""
            SELECT 
                gemini_model_version,
                COUNT(*) as count
            FROM ai_insights
            GROUP BY gemini_model_version
            ORDER BY count DESC
        """)
        model_versions = cursor.fetchall()
        
        print("\nInsights by generation method:")
        ai_count = 0
        algorithmic_count = 0
        
        for version, count in model_versions:
            if version and ('gemini' in version.lower() or 'ai' in version.lower()):
                ai_count += count
                print(f"  AI-generated ({version}): {count}")
            else:
                algorithmic_count += count
                print(f"  Algorithmic ({version if version else 'default'}): {count}")
        
        print(f"\n📊 Summary:")
        print(f"  AI-generated insights: {ai_count} ({ai_count/total_insights*100:.1f}%)")
        print(f"  Algorithmically-generated insights: {algorithmic_count} ({algorithmic_count/total_insights*100:.1f}%)")
        
        # Check confidence scores distribution
        print(f"\n📈 Confidence Scores Distribution:")
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN confidence_score >= 0.9 THEN 'High (≥0.9)'
                    WHEN confidence_score >= 0.8 THEN 'Medium (0.8-0.89)'
                    WHEN confidence_score >= 0.7 THEN 'Low-Medium (0.7-0.79)'
                    ELSE 'Low (<0.7)'
                END as confidence_range,
                COUNT(*) as count
            FROM ai_insights
            GROUP BY 
                CASE 
                    WHEN confidence_score >= 0.9 THEN 'High (≥0.9)'
                    WHEN confidence_score >= 0.8 THEN 'Medium (0.8-0.89)'
                    WHEN confidence_score >= 0.7 THEN 'Low-Medium (0.7-0.79)'
                    ELSE 'Low (<0.7)'
                END
            ORDER BY confidence_score DESC
        """)
        confidence_data = cursor.fetchall()
        
        for range_name, count in confidence_data:
            print(f"  {range_name}: {count}")
        
        # Check if there are any new AI-generated insights
        print(f"\n🆕 Recently AI-generated insights:")
        cursor.execute("""
            SELECT site_id, strengths_summary, weaknesses_summary, confidence_score
            FROM ai_insights 
            WHERE gemini_model_version = 'gemini-2.0-flash'
            ORDER BY confidence_score DESC
            LIMIT 5
        """)
        ai_details = cursor.fetchall()
        
        for site_id, strengths, weaknesses, confidence in ai_details:
            print(f"  Site {site_id} (Confidence: {confidence}):")
            print(f"    Strengths: {strengths[:100] if strengths else 'None'}...")
            print(f"    Weaknesses: {weaknesses[:100] if weaknesses else 'None'}...")
        
        # Check a sample of algorithmic insights to see if they've been updated
        print(f"\n🔄 Algorithmic insights sample:")
        cursor.execute("""
            SELECT site_id, strengths_summary, weaknesses_summary, confidence_score, gemini_model_version
            FROM ai_insights 
            WHERE gemini_model_version IS NULL OR gemini_model_version != 'gemini-2.0-flash'
            LIMIT 3
        """)
        algo_samples = cursor.fetchall()
        
        for site_id, strengths, weaknesses, confidence, model_version in algo_samples:
            print(f"  Site {site_id} (Model: {model_version or 'N/A'}, Confidence: {confidence}):")
            # Check if this looks like JSON or plain text
            if strengths and strengths.startswith('{'):
                print(f"    Strengths: JSON data ({len(strengths)} chars)")
            else:
                print(f"    Strengths: {strengths[:100] if strengths else 'None'}...")
                
            if weaknesses and weaknesses.startswith('{'):
                print(f"    Weaknesses: JSON data ({len(weaknesses)} chars)")
            else:
                print(f"    Weaknesses: {weaknesses[:100] if weaknesses else 'None'}...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    final_insights_analysis()