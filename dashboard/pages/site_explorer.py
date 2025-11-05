"""
Site Explorer Page for Clinical Trial Site Analysis Platform Dashboard
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import folium

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")

# Import database manager
from database.db_manager import DatabaseManager

# Try to import streamlit_folium with error handling
try:
    from streamlit_folium import st_folium
    ST_FOLIUM_AVAILABLE = True
except ImportError:
    ST_FOLIUM_AVAILABLE = False
    st.warning("Map visualization not available. Please install streamlit-folium for full functionality.")


def get_db_connection():
    """Create and return a database connection"""
    db_path = "clinical_trials.db"
    db_manager = DatabaseManager(db_path)
    if db_manager.connect():
        return db_manager
    return None


def check_database_initialized():
    """Check if the database has been initialized with tables"""
    db_manager = get_db_connection()
    if not db_manager:
        return False
    
    try:
        # Try to query a core table to see if tables exist
        result = db_manager.query("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table' AND name='sites_master'")
        table_exists = result[0]["count"] > 0 if result else False
        db_manager.disconnect()
        return table_exists
    except Exception:
        if db_manager:
            db_manager.disconnect()
        return False


def initialize_database_schema():
    """Initialize database schema if not already done"""
    try:
        db_manager = get_db_connection()
        if not db_manager:
            return False
            
        # Create tables from schema
        success = db_manager.create_tables()
        db_manager.disconnect()
        return success
    except Exception as e:
        st.error(f"Error initializing database schema: {e}")
        return False


def fetch_sites_data(search_term="", therapeutic_area="All", country="All"):
    """Fetch sites data from database with optional filters"""
    db_manager = get_db_connection()
    if not db_manager:
        return []

    try:
        # Check if database is initialized
        if not check_database_initialized():
            st.warning("Database not initialized. Please run data ingestion first.")
            db_manager.disconnect()
            return []

        # Base query
        query = """
        SELECT site_id, site_name, city, state, country, institution_type, 
               total_capacity, accreditation_status
        FROM sites_master 
        WHERE 1=1
        """
        params = []

        # Add search filter
        if search_term:
            query += " AND (site_name LIKE ? OR city LIKE ? OR state LIKE ? OR country LIKE ?)"
            search_pattern = f"%{search_term}%"
            params.extend(
                [search_pattern, search_pattern, search_pattern, search_pattern]
            )

        # Add country filter
        if country != "All":
            query += " AND country = ?"
            params.append(country)

        # Order by site name
        query += " ORDER BY site_name"

        results = db_manager.query(query, tuple(params))
        db_manager.disconnect()

        # Convert to list of dictionaries
        sites_data = []
        for row in results:
            sites_data.append(
                {
                    "ID": row["site_id"],
                    "Name": row["site_name"],
                    "City": row["city"] or "",
                    "State": row["state"] or "",
                    "Country": row["country"] or "",
                    "Institution Type": row["institution_type"] or "Unknown",
                    "Total Capacity": row["total_capacity"] or 0,
                    "Accreditation": row["accreditation_status"] or "Unknown",
                }
            )

        return sites_data
    except Exception as e:
        st.error(f"Error fetching sites data: {e}")
        if db_manager:
            db_manager.disconnect()
        return []


def fetch_site_metrics():
    """Fetch site metrics data from database"""
    db_manager = get_db_connection()
    if not db_manager:
        return []

    try:
        # Check if database is initialized
        if not check_database_initialized():
            st.warning("Database not initialized. Please run data ingestion first.")
            db_manager.disconnect()
            return []

        query = """
        SELECT sm.site_id, sm.site_name, sm.city, sm.country,
               COALESCE(sm.total_capacity, 0) as capacity,
               COALESCE(met.total_studies, 0) as total_studies,
               COALESCE(met.completion_ratio, 0) as completion_ratio
        FROM sites_master sm
        LEFT JOIN site_metrics met ON sm.site_id = met.site_id
        ORDER BY sm.site_name
        LIMIT 100
        """

        results = db_manager.query(query)
        db_manager.disconnect()

        # Convert to list of dictionaries
        metrics_data = []
        for row in results:
            # Convert completion ratio to percentage
            completion_pct = (
                round(row["completion_ratio"] * 100, 1)
                if row["completion_ratio"]
                else 0
            )

            metrics_data.append(
                {
                    "ID": row["site_id"],
                    "Name": row["site_name"],
                    "Location": f"{row['city'] or ''}, {row['country'] or ''}".strip(
                        ", "
                    ),
                    "Studies": row["total_studies"] or 0,
                    "Success Rate": f"{completion_pct}%",
                }
            )

        return metrics_data
    except Exception as e:
        st.error(f"Error fetching site metrics: {e}")
        if db_manager:
            db_manager.disconnect()
        return []


def fetch_map_data():
    """Fetch geographical data for map visualization"""
    db_manager = get_db_connection()
    if not db_manager:
        return pd.DataFrame()

    try:
        # Check if database is initialized
        if not check_database_initialized():
            st.warning("Database not initialized. Please run data ingestion first.")
            db_manager.disconnect()
            return pd.DataFrame()

        query = """
        SELECT site_id, site_name, city, state, country, latitude, longitude
        FROM sites_master 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY site_name
        """

        results = db_manager.query(query)
        db_manager.disconnect()

        # Convert to DataFrame
        map_data = []
        for row in results:
            map_data.append(
                {
                    "lat": row["latitude"],
                    "lon": row["longitude"],
                    "name": row["site_name"],
                    "location": f"{row['city'] or ''}, {row['state'] or ''}, {row['country'] or ''}".strip(
                        ", "
                    ),
                }
            )

        return pd.DataFrame(map_data)
    except Exception as e:
        st.error(f"Error fetching map data: {e}")
        if db_manager:
            db_manager.disconnect()
        return pd.DataFrame()


def show_site_explorer_page():
    """Display the site explorer page"""
    st.title("🔍 Site Explorer")
    st.markdown("---")

    st.write("Search and explore clinical trial sites in our database.")

    # Search filters
    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input(
            "Search Sites", placeholder="Enter site name or location"
        )

    with col2:
        therapeutic_area = st.selectbox(
            "Therapeutic Area",
            [
                "All",
                "Oncology",
                "Cardiology",
                "Neurology",
                "Infectious Disease",
                "Other",
            ],
        )

    with col3:
        country = st.selectbox(
            "Country",
            ["All", "United States", "Canada", "United Kingdom", "Germany", "Other"],
        )

    # Fetch real data from database
    sites_data = fetch_sites_data(search_term, therapeutic_area, country)
    metrics_data = fetch_site_metrics()

    # Display sites data
    st.subheader("Sites Database")
    st.write(f"Displaying {len(sites_data)} sites from the database:")

    if sites_data:
        # Convert to DataFrame for better display
        df = pd.DataFrame(sites_data)
        # Add a column for viewing profile
        if 'ID' in df.columns:
            df['View Profile'] = df['ID'].apply(lambda x: f"[View Profile](?page=site_profile&site_id={x})")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No sites found matching your criteria.")

    # Display metrics data in table format
    st.subheader("Site Performance Metrics")
    st.write("Key performance indicators for clinical trial sites:")

    if metrics_data:
        # Display as table
        metrics_df = pd.DataFrame(metrics_data)
        st.table(metrics_df)
    else:
        st.info("No metrics data available.")

    # Create a map visualization
    st.subheader("Site Locations")
    st.write("Interactive map showing site locations:")

    map_data = fetch_map_data()
    if not map_data.empty and len(map_data) > 0:
        # Create a simple map using Plotly
        fig = px.scatter_mapbox(
            map_data,
            lat="lat",
            lon="lon",
            hover_name="name",
            hover_data=["location"],
            zoom=2,
            height=500,
        )
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No geographical data available for mapping.")


if __name__ == "__main__":
    show_site_explorer_page()
