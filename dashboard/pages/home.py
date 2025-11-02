"""
Home Page for Clinical Trial Site Analysis Platform Dashboard
"""
import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")

def show_home_page():
    """Display the home page"""
    st.title("🏥 Clinical Trial Site Analysis Platform")
    st.markdown("---")
    
    st.header("Overview")
    st.write("""
    Welcome to the Clinical Trial Site Analysis Platform dashboard. This platform helps clinical research 
    organizations identify and evaluate the best sites for their clinical trials based on comprehensive 
    data analysis and AI-powered insights.
    """)
    
    st.subheader("Key Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sites Analyzed", "1,248")
        st.info("Comprehensive site database")
    
    with col2:
        st.metric("Trials Processed", "3,876")
        st.success("Up-to-date trial information")
    
    with col3:
        st.metric("Recommendations Generated", "2,156")
        st.warning("AI-powered insights")
    
    st.subheader("Platform Capabilities")
    st.markdown("""
    - **Data Ingestion**: Real-time data from ClinicalTrials.gov and PubMed
    - **Intelligent Analysis**: Advanced analytics and machine learning
    - **Site Matching**: AI-powered site recommendations
    - **Performance Metrics**: Comprehensive site evaluation
    - **Visualization**: Interactive dashboards and maps
    """)
    
    st.subheader("Getting Started")
    st.markdown("""
    1. Navigate to **Site Explorer** to search and filter clinical trial sites
    2. Use **Recommendations** to find the best sites for your trial criteria
    3. Explore **Analytics** for detailed performance metrics and insights
    """)

if __name__ == "__main__":
    show_home_page()