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

def show_recommendations_page():
    """Display the recommendations page"""
    st.title("⭐ Site Recommendations")
    st.markdown("---")
    
    st.write("Get AI-powered recommendations for your clinical trial sites based on your criteria.")
    
    # Recommendation criteria form
    st.subheader("Trial Criteria")
    
    col1, col2 = st.columns(2)
    
    with col1:
        condition = st.text_input("Medical Condition", placeholder="e.g., Diabetes, Cancer")
        phase = st.selectbox("Trial Phase", ["Phase 1", "Phase 2", "Phase 3", "Phase 4"])
    
    with col2:
        intervention_type = st.selectbox(
            "Intervention Type",
            ["Drug", "Device", "Biological", "Procedure", "Other"]
        )
        country_preference = st.selectbox(
            "Country Preference",
            ["No Preference", "United States", "Europe", "Asia"]
        )
    
    if st.button("Generate Recommendations"):
        st.subheader("Recommended Sites")
        st.info("In a full implementation, this would show AI-generated site recommendations based on your criteria.")
        
        # Sample recommendations
        sample_recommendations = [
            {"Rank": 1, "Site": "Mayo Clinic", "Match Score": "94%", "Reasoning": "High experience in oncology trials"},
            {"Rank": 2, "Site": "Johns Hopkins Hospital", "Match Score": "91%", "Reasoning": "Strong investigator network"},
            {"Rank": 3, "Site": "Cleveland Clinic", "Match Score": "89%", "Reasoning": "Excellent patient recruitment"},
        ]
        
        st.table(sample_recommendations)
        
        # Create a bar chart of match scores
        df = pd.DataFrame(sample_recommendations)
        fig = px.bar(df, x='Site', y='Match Score', title='Match Scores by Site')
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show_recommendations_page()