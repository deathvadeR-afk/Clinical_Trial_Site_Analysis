"""
Analytics Page for Clinical Trial Site Analysis Platform Dashboard
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


def show_analytics_page():
    """Display the analytics page"""
    st.title("📊 Analytics Dashboard")
    st.markdown("---")

    st.write(
        "Comprehensive analytics and performance metrics for clinical trial sites."
    )

    # Initialize database connection
    db_manager = DatabaseManager("clinical_trials.db")
    if not db_manager.connect():
        st.error("Failed to connect to database. Showing sample data instead.")
        show_sample_data()
        return

    try:
        # Fetch real metrics data from database with caching
        st.subheader("Performance Metrics")

        # Get site metrics summary with caching
        metrics_query = """
        SELECT 
            COUNT(*) as total_sites,
            AVG(completion_ratio) as avg_completion_rate,
            AVG(recruitment_efficiency_score) as avg_recruitment_efficiency,
            AVG(experience_index) as avg_experience_index
        FROM site_metrics
        WHERE completion_ratio IS NOT NULL
        """

        metrics_result = db_manager.query(
            metrics_query, use_cache=True, cache_key="analytics_metrics_summary"
        )
        if metrics_result and metrics_result[0]["total_sites"] > 0:
            metrics_data = metrics_result[0]
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Sites", metrics_data["total_sites"])

            with col2:
                st.metric(
                    "Avg Completion Rate", f"{metrics_data['avg_completion_rate']:.1%}"
                )

            with col3:
                st.metric(
                    "Avg Recruitment Efficiency",
                    f"{metrics_data['avg_recruitment_efficiency']:.1f}",
                )

            with col4:
                st.metric(
                    "Avg Experience Index",
                    f"{metrics_data['avg_experience_index']:.1f}",
                )
        else:
            # If no metrics data, show basic site count
            site_count_query = "SELECT COUNT(*) as total_sites FROM sites_master"
            site_count_result = db_manager.query(
                site_count_query, use_cache=True, cache_key="analytics_site_count"
            )
            if site_count_result:
                st.metric("Total Sites", site_count_result[0]["total_sites"])
            else:
                st.metric("Total Sites", "N/A")
            st.info(
                "No detailed metrics data available yet. Run the full data pipeline to generate metrics."
            )

        # Create real charts from database data with caching
        st.subheader("Site Distribution")

        # Get country distribution with caching
        country_query = """
        SELECT 
            country,
            COUNT(*) as site_count
        FROM sites_master
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY site_count DESC
        """

        country_result = db_manager.query(
            country_query, use_cache=True, cache_key="analytics_country_distribution"
        )
        if country_result:
            # Convert query results to properly formatted DataFrame
            country_data = []
            for row in country_result:
                country_data.append(
                    {"country": row["country"], "site_count": row["site_count"]}
                )
            country_df = pd.DataFrame(country_data)
            fig1 = px.bar(
                country_df, x="country", y="site_count", title="Sites by Country"
            )
            fig1.update_layout(xaxis_title="Country", yaxis_title="Number of Sites")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No country data available.")

        # Performance distribution scatter plot
        st.subheader("Site Information")

        # Get basic site information with caching
        site_info_query = """
        SELECT 
            site_name,
            city,
            state,
            country,
            institution_type
        FROM sites_master
        WHERE site_name IS NOT NULL
        ORDER BY site_name
        """

        site_info_result = db_manager.query(
            site_info_query, use_cache=True, cache_key="analytics_site_info"
        )
        if site_info_result:
            # Convert query results to properly formatted DataFrame
            site_info_data = []
            for row in site_info_result:
                site_info_data.append(
                    {
                        "site_name": row["site_name"],
                        "city": row["city"] or "",
                        "state": row["state"] or "",
                        "country": row["country"] or "",
                        "institution_type": row["institution_type"] or "",
                    }
                )
            site_info_df = pd.DataFrame(site_info_data)
            st.dataframe(site_info_df)
        else:
            st.info("No site information available.")

        # Clinical trial information
        st.subheader("Clinical Trials")

        trial_info_query = """
        SELECT 
            nct_id,
            title,
            status,
            phase,
            conditions
        FROM clinical_trials
        ORDER BY title
        """

        trial_info_result = db_manager.query(
            trial_info_query, use_cache=True, cache_key="analytics_trial_info"
        )
        if trial_info_result:
            # Convert query results to properly formatted DataFrame
            trial_info_data = []
            for row in trial_info_result:
                trial_info_data.append(
                    {
                        "nct_id": row["nct_id"],
                        "title": row["title"] or "",
                        "status": row["status"] or "",
                        "phase": row["phase"] or "",
                        "conditions": row["conditions"] or "",
                    }
                )
            trial_info_df = pd.DataFrame(trial_info_data)
            st.dataframe(trial_info_df)
        else:
            st.info("No clinical trial information available.")

        # Top-performing sites by therapeutic area
        st.subheader("Top-performing Sites by Therapeutic Area")
        
        # Get distinct therapeutic areas
        therapeutic_areas_query = """
        SELECT DISTINCT therapeutic_area
        FROM site_metrics
        WHERE therapeutic_area IS NOT NULL
        ORDER BY therapeutic_area
        """
        
        therapeutic_areas_result = db_manager.query(therapeutic_areas_query)
        if therapeutic_areas_result:
            therapeutic_areas = [row["therapeutic_area"] for row in therapeutic_areas_result]
            
            # Create a selectbox for therapeutic area selection
            selected_area = st.selectbox(
                "Select Therapeutic Area",
                ["All"] + therapeutic_areas,
                key="therapeutic_area_selector"
            )
            
            # Query for top-performing sites based on completion ratio
            top_sites_query = """
            SELECT 
                sm.site_name,
                sm.country,
                smt.therapeutic_area,
                smt.completed_studies,
                smt.total_studies,
                ROUND(smt.completion_ratio * 100, 1) as completion_percentage,
                smt.recruitment_efficiency_score
            FROM sites_master sm
            JOIN site_metrics smt ON sm.site_id = smt.site_id
            WHERE smt.completion_ratio IS NOT NULL
            """
            
            params = []
            if selected_area != "All":
                top_sites_query += " AND smt.therapeutic_area = ?"
                params.append(selected_area)
            
            top_sites_query += """
            ORDER BY smt.completion_ratio DESC
            LIMIT 10
            """
            
            top_sites_result = db_manager.query(top_sites_query, tuple(params))
            if top_sites_result:
                # Convert query results to properly formatted DataFrame
                top_sites_data = []
                for row in top_sites_result:
                    top_sites_data.append({
                        "Site": row["site_name"],
                        "Country": row["country"] or "N/A",
                        "Therapeutic Area": row["therapeutic_area"] or "N/A",
                        "Completed Studies": row["completed_studies"] or 0,
                        "Total Studies": row["total_studies"] or 0,
                        "Completion %": f"{row['completion_percentage']}%" if row['completion_percentage'] else "N/A",
                        "Recruitment Efficiency": round(row["recruitment_efficiency_score"], 1) if row["recruitment_efficiency_score"] else "N/A"
                    })
                
                top_sites_df = pd.DataFrame(top_sites_data)
                st.dataframe(top_sites_df, use_container_width=True)
                
                # Create a bar chart of completion rates
                fig2 = px.bar(
                    top_sites_df, 
                    x="Site", 
                    y="Completion %", 
                    title=f"Top 10 Sites by Completion Rate ({selected_area if selected_area != 'All' else 'All Areas'})",
                    color="Country"
                )
                fig2.update_layout(xaxis_title="Site", yaxis_title="Completion Rate (%)")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No performance data available for the selected therapeutic area.")
        else:
            st.info("No therapeutic area data available.")

    except Exception as e:
        st.error(f"Error fetching data from database: {str(e)}")
        st.info("Showing sample data instead.")
        show_sample_data()
    finally:
        db_manager.disconnect()


def show_sample_data():
    """Display sample data when database is not available or has no relevant data"""
    st.subheader("Performance Metrics")
    st.info(
        "In a full implementation with real data, this would show interactive charts and visualizations."
    )

    # Sample metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sites", "1,248")
    with col2:
        st.metric("Avg Completion Rate", "87%")
    with col3:
        st.metric("Avg Recruitment Efficiency", "92.5")
    with col4:
        st.metric("Avg Experience Index", "88.3")

    # Create sample charts
    st.subheader("Site Distribution")

    # Sample country data
    country_data = pd.DataFrame(
        {
            "country": [
                "United States",
                "Germany",
                "United Kingdom",
                "Canada",
                "France",
                "Italy",
                "Australia",
                "Japan",
            ],
            "site_count": [420, 180, 156, 98, 87, 76, 65, 58],
        }
    )

    # Bar chart
    fig1 = px.bar(
        country_data,
        x="country",
        y="site_count",
        title="Sites by Country (Sample Data)",
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Sample site information
    st.subheader("Sample Sites")
    sample_sites = pd.DataFrame(
        {
            "site_name": [
                "Mayo Clinic",
                "Johns Hopkins Hospital",
                "Cleveland Clinic",
                "Massachusetts General Hospital",
                "Stanford Health Care",
            ],
            "city": ["Rochester", "Baltimore", "Cleveland", "Boston", "Stanford"],
            "state": ["MN", "MD", "OH", "MA", "CA"],
            "country": [
                "United States",
                "United States",
                "United States",
                "United States",
                "United States",
            ],
            "institution_type": [
                "Academic Medical Center",
                "Academic Medical Center",
                "Academic Medical Center",
                "Academic Medical Center",
                "Academic Medical Center",
            ],
        }
    )

    st.dataframe(sample_sites)

    # Sample trial information
    st.subheader("Sample Clinical Trials")
    sample_trials = pd.DataFrame(
        {
            "nct_id": [
                "NCT03353935",
                "NCT06858735",
                "NCT05432198",
                "NCT04321098",
                "NCT03210987",
            ],
            "title": [
                "Functional Outcomes After Nerve Sparing Surgery for Deep Endometriosis",
                "HYPERION CCA: a Phase 2 Trial",
                "Novel Immunotherapy for Melanoma",
                "Cardiovascular Outcomes in Diabetes",
                "Alzheimer's Disease Prevention Study",
            ],
            "status": ["COMPLETED", "RECRUITING", "ACTIVE", "COMPLETED", "RECRUITING"],
            "phase": ["N/A", "PHASE 2", "PHASE 3", "PHASE 4", "PHASE 1"],
            "conditions": [
                "Endometriosis",
                "Cholangiocarcinoma",
                "Melanoma",
                "Diabetes",
                "Alzheimer Disease",
            ],
        }
    )

    st.dataframe(sample_trials)


if __name__ == "__main__":
    show_analytics_page()
