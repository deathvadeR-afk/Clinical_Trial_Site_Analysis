"""
Site Profile Page for Clinical Trial Site Analysis Platform Dashboard
Displays detailed information for a specific site in the format specified in goal.md
"""

import streamlit as st
import sys
import os
import pandas as pd
import json
import plotly.express as px
try:
    import plotly.graph_objects as go
    PLOTLY_GO_AVAILABLE = True
except ImportError:
    PLOTLY_GO_AVAILABLE = False
    st.warning("Advanced charting features not available. Please install plotly for full functionality.")

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")

# Import database manager
from database.db_manager import DatabaseManager


def get_db_connection():
    """Create and return a database connection"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../clinical_trials.db")
    db_manager = DatabaseManager(db_path)
    if db_manager.connect():
        return db_manager
    return None


def fetch_site_profile_data(site_id):
    """Fetch comprehensive site profile data for display"""
    db_manager = get_db_connection()
    if not db_manager:
        return None

    try:
        # Get basic site information
        site_query = """
        SELECT site_id, site_name, city, state, country, institution_type,
               total_capacity, accreditation_status
        FROM sites_master 
        WHERE site_id = ?
        """
        site_result = db_manager.query(site_query, (site_id,))
        
        if not site_result:
            db_manager.disconnect()
            return None
            
        # Convert to dictionary
        site_data = dict(site_result[0])
        
        # Get site metrics
        metrics_query = """
        SELECT therapeutic_area, total_studies, completed_studies, 
               terminated_studies, withdrawn_studies, completion_ratio
        FROM site_metrics 
        WHERE site_id = ?
        """
        metrics_result = db_manager.query(metrics_query, (site_id,))
        # Convert to list of dictionaries
        metrics_data = [dict(row) for row in metrics_result] if metrics_result else []
        
        # Get data quality scores
        quality_query = """
        SELECT AVG(overall_quality_score) as avg_quality_score
        FROM data_quality_scores 
        WHERE site_id = ?
        """
        quality_result = db_manager.query(quality_query, (site_id,))
        
        # Get match scores (use highest match score as an example)
        match_query = """
        SELECT MAX(overall_match_score) as best_match_score
        FROM match_scores 
        WHERE site_id = ?
        """
        match_result = db_manager.query(match_query, (site_id,))
        
        # Get AI insights if available
        insights_query = """
        SELECT strengths_summary, weaknesses_summary
        FROM ai_insights 
        WHERE site_id = ?
        """
        insights_result = db_manager.query(insights_query, (site_id,))
        
        db_manager.disconnect()
        
        # Combine all data
        profile_data = {
            "site": site_data,
            "metrics": metrics_data,
            "avg_quality_score": quality_result[0]["avg_quality_score"] if quality_result and quality_result[0]["avg_quality_score"] else None,
            "best_match_score": match_result[0]["best_match_score"] if match_result and match_result[0]["best_match_score"] else None,
            "insights": dict(insights_result[0]) if insights_result else None
        }
        
        return profile_data
    except Exception as e:
        st.error(f"Error fetching site profile data: {e}")
        if db_manager:
            db_manager.disconnect()
        return None


def calculate_completion_percentage(metrics_data):
    """Calculate completion percentage from metrics data"""
    if not metrics_data:
        return 0
        
    total_completed = sum(row["completed_studies"] if "completed_studies" in row else 0 for row in metrics_data)
    total_studies = sum(row["total_studies"] if "total_studies" in row else 0 for row in metrics_data)
    
    if total_studies == 0:
        return 0
        
    return round((total_completed / total_studies) * 100, 1)


def show_site_profile_page():
    """Display the site profile page with the example table format"""
    st.title("📋 Site Profile")
    st.markdown("---")
    
    # Initialize session state for site selection
    if 'selected_site_id' not in st.session_state:
        st.session_state.selected_site_id = None
    
    # Show site selection interface
    st.write("Select a site to view its detailed profile:")
    
    db_manager = get_db_connection()
    if db_manager:
        try:
            # Get list of sites for selection
            sites_query = """
            SELECT site_id, site_name, city, country
            FROM sites_master 
            ORDER BY site_name
            LIMIT 100
            """
            sites_result = db_manager.query(sites_query)
            db_manager.disconnect()
            
            if sites_result:
                site_options = {}
                for row in sites_result:
                    display_name = f"{row['site_name']} ({row['city']}, {row['country']})"
                    site_options[display_name] = row['site_id']
                
                # Create selectbox with session state
                selected_site = st.selectbox(
                    "Select Site", 
                    [""] + list(site_options.keys()),
                    index=0 if not st.session_state.selected_site_id else 
                          ["" if not k else k for k in [""] + list(site_options.keys())].index(
                              [k for k, v in site_options.items() if v == st.session_state.selected_site_id][0]
                              if st.session_state.selected_site_id in site_options.values() else ""
                          )
                )
                
                if selected_site and selected_site in site_options:
                    st.session_state.selected_site_id = site_options[selected_site]
                elif not selected_site:
                    st.session_state.selected_site_id = None
            else:
                st.info("No sites available in the database.")
                return
        except Exception as e:
            st.error(f"Error fetching sites: {e}")
            if db_manager:
                db_manager.disconnect()
            return
    else:
        st.error("Failed to connect to database.")
        return
    
    # Only proceed if we have a selected site
    if not st.session_state.selected_site_id:
        st.info("Please select a site from the dropdown above.")
        return
    
    # Fetch site profile data
    profile_data = fetch_site_profile_data(st.session_state.selected_site_id)
    
    if not profile_data:
        st.error("Failed to fetch site profile data.")
        return
    
    site = profile_data["site"]
    metrics = profile_data["metrics"]
    avg_quality_score = profile_data["avg_quality_score"]
    best_match_score = profile_data["best_match_score"]
    insights = profile_data["insights"]
    
    # Display site header information
    st.subheader(f"{site['site_name']}")
    st.write(f"**Location:** {site['city']}, {site['state'] or ''} {site['country']}")
    st.write(f"**Institution Type:** {site['institution_type'] or 'N/A'}")
    st.write(f"**Accreditation Status:** {site['accreditation_status'] or 'N/A'}")
    
    st.markdown("---")
    
    # Display the example table format from goal.md
    st.subheader("Site Performance Summary")
    
    # Calculate values for the table
    completed_studies = sum(row["completed_studies"] if "completed_studies" in row else 0 for row in metrics) if metrics else 0
    total_studies = sum(row["total_studies"] if "total_studies" in row else 0 for row in metrics) if metrics else 0
    ongoing_studies = total_studies - completed_studies
    completion_pct = calculate_completion_percentage(metrics)
    match_score = round(best_match_score * 100, 1) if best_match_score else None
    data_quality = round(avg_quality_score * 100, 1) if avg_quality_score else None
    
    # Create the example table format
    # Extract meaningful text from AI insights
    strength_text = "N/A"
    weakness_text = "N/A"
    
    if insights and "strengths_summary" in insights and insights["strengths_summary"]:
        try:
            import json
            # Handle potentially truncated JSON
            strengths_content = insights["strengths_summary"]
            
            # Check if this looks like truncated JSON
            if strengths_content.strip().endswith('",') or strengths_content.strip().endswith(']') or strengths_content.strip().endswith('}'):
                # Try to parse as JSON
                strengths_data = json.loads(strengths_content)
                if isinstance(strengths_data, dict) and "strengths" in strengths_data:
                    if strengths_data["strengths"]:
                        # Extract first strength description
                        first_strength = strengths_data["strengths"][0]
                        if isinstance(first_strength, dict) and "description" in first_strength:
                            strength_text = first_strength["description"]
                        else:
                            strength_text = str(first_strength)
                    else:
                        strength_text = "No significant strengths identified"
                else:
                    strength_text = "Data processed"
            else:
                # If it looks truncated, try to extract what we can
                # Look for description fields in the truncated JSON
                import re
                descriptions = re.findall(r'"description"\s*:\s*"([^"]*)"', strengths_content)
                if descriptions:
                    strength_text = descriptions[0]
                else:
                    # If no descriptions found, try to get any text that looks like a description
                    # Look for text between quotes that might be descriptions
                    quoted_text = re.findall(r'"([^"]{20,})"', strengths_content)
                    if quoted_text:
                        strength_text = quoted_text[0][:100] + "..." if len(quoted_text[0]) > 100 else quoted_text[0]
                    else:
                        strength_text = strengths_content[:100] + "..." if len(strengths_content) > 100 else strengths_content
        except Exception as e:
            # If parsing fails, try to extract meaningful text
            try:
                # Try to extract description-like text
                import re
                descriptions = re.findall(r'"description"\s*:\s*"([^"]*)"', insights["strengths_summary"])
                if descriptions:
                    strength_text = descriptions[0]
                else:
                    # Try to get any quoted text
                    quoted_text = re.findall(r'"([^"]{20,})"', insights["strengths_summary"])
                    if quoted_text:
                        strength_text = quoted_text[0][:100] + "..." if len(quoted_text[0]) > 100 else quoted_text[0]
                    else:
                        strength_text = insights["strengths_summary"][:100] + "..." if len(insights["strengths_summary"]) > 100 else insights["strengths_summary"]
            except:
                strength_text = insights["strengths_summary"][:100] + "..." if len(insights["strengths_summary"]) > 100 else insights["strengths_summary"]
    
    if insights and "weaknesses_summary" in insights and insights["weaknesses_summary"]:
        try:
            import json
            # Handle potentially truncated JSON
            weaknesses_content = insights["weaknesses_summary"]
            
            # Check if this looks like truncated JSON
            if weaknesses_content.strip().endswith('",') or weaknesses_content.strip().endswith(']') or weaknesses_content.strip().endswith('}'):
                # Try to parse as JSON
                try:
                    weaknesses_data = json.loads(weaknesses_content)
                    if isinstance(weaknesses_data, dict) and "weaknesses" in weaknesses_data:
                        # Get first non-empty category
                        for category, items in weaknesses_data["weaknesses"].items():
                            if items:
                                first_weakness = items[0]
                                if isinstance(first_weakness, dict) and "description" in first_weakness:
                                    weakness_text = first_weakness["description"]
                                else:
                                    weakness_text = str(first_weakness)
                                break
                        else:
                            weakness_text = "No significant weaknesses identified"
                    else:
                        weakness_text = "Analysis complete"
                except json.JSONDecodeError:
                    # Handle truncated JSON by extracting what we can
                    if '"description"' in weaknesses_content:
                        # Try to extract description manually
                        import re
                        match = re.search(r'"description"\s*:\s*"([^"]+)"', weaknesses_content)
                        if match:
                            weakness_text = match.group(1)
                        else:
                            weakness_text = "Analysis in progress"
                    else:
                        weakness_text = "Analysis complete"
            else:
                # If it looks truncated, try to extract what we can
                # Look for description fields in the truncated JSON
                import re
                descriptions = re.findall(r'"description"\s*:\s*"([^"]*)"', weaknesses_content)
                if descriptions:
                    weakness_text = descriptions[0]
                else:
                    # If no descriptions found, try to get any text that looks like a description
                    quoted_text = re.findall(r'"([^"]{20,})"', weaknesses_content)
                    if quoted_text:
                        weakness_text = quoted_text[0][:100] + "..." if len(quoted_text[0]) > 100 else quoted_text[0]
                    else:
                        weakness_text = weaknesses_content[:100] + "..." if len(weaknesses_content) > 100 else weaknesses_content
        except Exception as e:
            # If parsing fails, try to extract meaningful text
            try:
                # Try to extract description-like text
                import re
                descriptions = re.findall(r'"description"\s*:\s*"([^"]*)"', insights["weaknesses_summary"])
                if descriptions:
                    weakness_text = descriptions[0]
                else:
                    # Try to get any quoted text
                    quoted_text = re.findall(r'"([^"]{20,})"', insights["weaknesses_summary"])
                    if quoted_text:
                        weakness_text = quoted_text[0][:100] + "..." if len(quoted_text[0]) > 100 else quoted_text[0]
                    else:
                        weakness_text = insights["weaknesses_summary"][:100] + "..." if len(insights["weaknesses_summary"]) > 100 else insights["weaknesses_summary"]
            except:
                weakness_text = insights["weaknesses_summary"][:100] + "..." if len(insights["weaknesses_summary"]) > 100 else insights["weaknesses_summary"]
    
    profile_table_data = {
        "Site": [site["site_name"]],
        "Country": [site["country"] or 'N/A'],
        "Completed": [completed_studies],
        "Ongoing": [ongoing_studies],
        "Completion %": [f"{completion_pct}%" if completion_pct is not None else "N/A"],
        "Match Score": [f"{match_score}%" if match_score is not None else "N/A"],
        "Data Quality": [f"{data_quality}%" if data_quality is not None else "N/A"],
        "Strength": [strength_text[:100] + "..." if len(strength_text) > 100 else strength_text],
        "Weakness": [weakness_text[:100] + "..." if len(weakness_text) > 100 else weakness_text]
    }
    
    profile_df = pd.DataFrame(profile_table_data)
    st.table(profile_df)
    
    st.markdown("---")
    
    # Display detailed metrics
    st.subheader("Detailed Metrics by Therapeutic Area")
    if metrics:
        metrics_table = []
        for row in metrics:
            metrics_table.append({
                "Therapeutic Area": row["therapeutic_area"] or "N/A",
                "Total Studies": row["total_studies"] or 0,
                "Completed": row["completed_studies"] or 0,
                "Terminated": row["terminated_studies"] or 0,
                "Withdrawn": row["withdrawn_studies"] or 0,
                "Completion Ratio": f"{row['completion_ratio']:.1%}" if row["completion_ratio"] else "N/A"
            })
        
        metrics_df = pd.DataFrame(metrics_table)
        st.dataframe(metrics_df, use_container_width=True)
    else:
        st.info("No detailed metrics available for this site.")
    
    # Display AI insights if available
    if insights:
        st.subheader("AI-Generated Insights")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Strengths:**")
            if "strengths_summary" in insights and insights["strengths_summary"]:
                try:
                    # Try to parse the JSON content
                    strengths_data = json.loads(insights["strengths_summary"])
                    if isinstance(strengths_data, dict) and "strengths" in strengths_data:
                        if strengths_data["strengths"]:
                            # Display each strength as a bullet point
                            for strength in strengths_data["strengths"]:
                                if isinstance(strength, dict) and "description" in strength:
                                    st.info(strength["description"])
                                else:
                                    st.info(str(strength))
                        else:
                            st.info("No significant strengths identified.")
                    else:
                        # If it's not in the expected format, try to extract meaningful text
                        # Look for description fields in the JSON
                        import re
                        descriptions = re.findall(r'"description"\s*:\s*"([^"]*)"', insights["strengths_summary"])
                        if descriptions:
                            for desc in descriptions:
                                st.info(desc)
                        else:
                            # If no descriptions found, display as-is
                            st.info(insights["strengths_summary"])
                except json.JSONDecodeError:
                    # If it's not valid JSON, try to extract meaningful text
                    try:
                        # Try to extract description-like text
                        import re
                        descriptions = re.findall(r'"description"\s*:\s*"([^"]*)"', insights["strengths_summary"])
                        if descriptions:
                            for desc in descriptions:
                                st.info(desc)
                        else:
                            # Try to get any quoted text
                            quoted_text = re.findall(r'"([^"]{20,})"', insights["strengths_summary"])
                            if quoted_text:
                                for text in quoted_text:
                                    st.info(text[:200] + "..." if len(text) > 200 else text)
                            else:
                                st.info(insights["strengths_summary"])
                    except:
                        st.info(insights["strengths_summary"])
                except Exception as e:
                    # If any other error occurs, display as-is
                    st.info(insights["strengths_summary"])
            else:
                st.info("No significant strengths identified.")
        
        with col2:
            st.markdown("**Weaknesses:**")
            if "weaknesses_summary" in insights and insights["weaknesses_summary"]:
                try:
                    # Try to parse the JSON content
                    weaknesses_data = json.loads(insights["weaknesses_summary"])
                    if isinstance(weaknesses_data, dict) and "weaknesses" in weaknesses_data:
                        # Check if there are any weaknesses in any category
                        has_weaknesses = False
                        for category, items in weaknesses_data["weaknesses"].items():
                            if items:
                                has_weaknesses = True
                                # Display category header
                                st.markdown(f"**{category.title()} Issues:**")
                                # Display each weakness as a bullet point
                                for weakness in items:
                                    if isinstance(weakness, dict) and "description" in weakness:
                                        st.warning(weakness["description"])
                                    else:
                                        st.warning(str(weakness))
                        if not has_weaknesses:
                            st.warning("No significant weaknesses identified.")
                    else:
                        # If it's not in the expected format, try to extract meaningful text
                        # Look for description fields in the JSON
                        import re
                        descriptions = re.findall(r'"description"\s*:\s*"([^"]*)"', insights["weaknesses_summary"])
                        if descriptions:
                            for desc in descriptions:
                                st.warning(desc)
                        else:
                            # If no descriptions found, display as-is
                            st.warning(insights["weaknesses_summary"])
                except json.JSONDecodeError:
                    # If it's not valid JSON, try to extract meaningful text
                    try:
                        # Try to extract description-like text
                        import re
                        descriptions = re.findall(r'"description"\s*:\s*"([^"]*)"', insights["weaknesses_summary"])
                        if descriptions:
                            for desc in descriptions:
                                st.warning(desc)
                        else:
                            # Try to get any quoted text
                            quoted_text = re.findall(r'"([^"]{20,})"', insights["weaknesses_summary"])
                            if quoted_text:
                                for text in quoted_text:
                                    st.warning(text[:200] + "..." if len(text) > 200 else text)
                            else:
                                st.warning(insights["weaknesses_summary"])
                    except:
                        st.warning(insights["weaknesses_summary"])
                except Exception as e:
                    # If any other error occurs, display as-is
                    st.warning(insights["weaknesses_summary"])
            else:
                st.warning("No significant weaknesses identified.")


if __name__ == "__main__":
    show_site_profile_page()