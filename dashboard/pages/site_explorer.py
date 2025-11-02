"""
Site Explorer Page for Clinical Trial Site Analysis Platform Dashboard
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")

def show_site_explorer_page():
    """Display the site explorer page"""
    st.title("🔍 Site Explorer")
    st.markdown("---")
    
    st.write("Search and explore clinical trial sites in our database.")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search Sites", placeholder="Enter site name or location")
    
    with col2:
        therapeutic_area = st.selectbox(
            "Therapeutic Area",
            ["All", "Oncology", "Cardiology", "Neurology", "Infectious Disease", "Other"]
        )
    
    with col3:
        country = st.selectbox(
            "Country",
            ["All", "United States", "Canada", "United Kingdom", "Germany", "Other"]
        )
    
    # Display sample sites data
    st.subheader("Sites Database")
    st.write("Displaying sample sites from the database:")
    
    # Sample data - in a real implementation, this would come from the database
    sample_sites = [
        {"ID": 1, "Name": "Mayo Clinic", "Location": "Rochester, MN", "Studies": 127, "Success Rate": "94%"},
        {"ID": 2, "Name": "Johns Hopkins Hospital", "Location": "Baltimore, MD", "Studies": 98, "Success Rate": "91%"},
        {"ID": 3, "Name": "Cleveland Clinic", "Location": "Cleveland, OH", "Studies": 87, "Success Rate": "89%"},
        {"ID": 4, "Name": "Massachusetts General Hospital", "Location": "Boston, MA", "Studies": 112, "Success Rate": "92%"},
        {"ID": 5, "Name": "Stanford Health Care", "Location": "Stanford, CA", "Studies": 76, "Success Rate": "88%"},
    ]
    
    st.table(sample_sites)
    
    # Create a simple map visualization
    st.subheader("Site Locations")
    st.write("Interactive map showing site locations:")
    
    # Sample map data
    map_data = pd.DataFrame({
        'lat': [44.0237, 39.2964, 41.5022, 42.3625, 37.4316],
        'lon': [-92.4665, -76.5922, -81.6722, -71.0750, -122.1774],
        'name': ['Mayo Clinic', 'Johns Hopkins', 'Cleveland Clinic', 'Mass General', 'Stanford']
    })
    
    # Create a simple map using Plotly
    fig = px.scatter_mapbox(
        map_data, 
        lat="lat", 
        lon="lon", 
        hover_name="name",
        zoom=3,
        height=400
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show_site_explorer_page()