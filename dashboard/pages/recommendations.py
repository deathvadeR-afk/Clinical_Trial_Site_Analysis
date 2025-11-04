"""
Recommendations Page for Clinical Trial Site Analysis Platform Dashboard
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")

# Import database manager
from database.db_manager import DatabaseManager


def get_db_connection():
    """Create and return a database connection"""
    db_path = "clinical_trials.db"
    db_manager = DatabaseManager(db_path)
    if db_manager.connect():
        return db_manager
    return None


def fetch_top_sites_by_match_score(
    condition="", phase="", intervention_type="", country_preference=""
):
    """Fetch top sites based on match scores from database"""
    db_manager = get_db_connection()
    if not db_manager:
        return []

    try:
        # Base query to get sites with match scores
        query = """
        SELECT sm.site_id, sm.site_name, ms.overall_match_score,
               ms.therapeutic_match_score, ms.phase_match_score,
               ms.intervention_match_score, ms.geographic_match_score
        FROM sites_master sm
        JOIN match_scores ms ON sm.site_id = ms.site_id
        WHERE 1=1
        """
        params = []

        # Order by overall match score
        query += " ORDER BY ms.overall_match_score DESC LIMIT 10"

        results = db_manager.query(query, tuple(params))
        db_manager.disconnect()

        # Convert to list of dictionaries
        recommendations = []
        for i, row in enumerate(results):
            recommendations.append(
                {
                    "Rank": i + 1,
                    "Site": row["site_name"],
                    "Match Score": f"{round(row['overall_match_score'] * 100, 1)}%",
                    "Therapeutic Match": f"{round(row['therapeutic_match_score'] * 100, 1)}%",
                    "Phase Match": f"{round(row['phase_match_score'] * 100, 1)}%",
                    "Intervention Match": f"{round(row['intervention_match_score'] * 100, 1)}%",
                    "Geographic Match": f"{round(row['geographic_match_score'] * 100, 1)}%",
                }
            )

        return recommendations
    except Exception as e:
        st.error(f"Error fetching recommendations: {e}")
        if db_manager:
            db_manager.disconnect()
        return []


def show_recommendations_page():
    """Display the recommendations page"""
    st.title("⭐ Site Recommendations")
    st.markdown("---")

    st.write(
        "Get AI-powered recommendations for your clinical trial sites based on your criteria."
    )

    # Recommendation criteria form
    st.subheader("Trial Criteria")

    col1, col2 = st.columns(2)

    with col1:
        condition = st.text_input(
            "Medical Condition", placeholder="e.g., Diabetes, Cancer"
        )
        phase = st.selectbox(
            "Trial Phase", ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        )

    with col2:
        intervention_type = st.selectbox(
            "Intervention Type", ["Drug", "Device", "Biological", "Procedure", "Other"]
        )
        country_preference = st.selectbox(
            "Country Preference", ["No Preference", "United States", "Europe", "Asia"]
        )

    if st.button("Generate Recommendations"):
        st.subheader("Recommended Sites")

        # Fetch real recommendations from database
        recommendations = fetch_top_sites_by_match_score(
            condition, phase, intervention_type, country_preference
        )

        if recommendations:
            st.table(recommendations)

            # Create a bar chart of match scores
            df = pd.DataFrame(recommendations)
            fig = px.bar(df, x="Site", y="Match Score", title="Match Scores by Site")
            st.plotly_chart(fig, use_container_width=True)

            # Show detailed breakdown
            st.subheader("Detailed Match Score Breakdown")
            detailed_df = pd.DataFrame(recommendations)
            st.dataframe(
                detailed_df[
                    [
                        "Site",
                        "Therapeutic Match",
                        "Phase Match",
                        "Intervention Match",
                        "Geographic Match",
                    ]
                ],
                use_container_width=True,
            )
        else:
            st.info(
                "No recommendations found. Try adjusting your criteria or check back later as more data is ingested."
            )


if __name__ == "__main__":
    show_recommendations_page()
