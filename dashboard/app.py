"""
Main Streamlit Application for Clinical Trial Site Analysis Platform Dashboard
"""

import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

# Import page modules
from dashboard.pages.home import show_home_page
from dashboard.pages.site_explorer import show_site_explorer_page
from dashboard.pages.recommendations import show_recommendations_page
from dashboard.pages.analytics import show_analytics_page

# Configure page settings
st.set_page_config(
    page_title="Clinical Trial Site Analysis Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main application function"""
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page", ["Home", "Site Explorer", "Recommendations", "Analytics"]
    )

    # Page routing
    if page == "Home":
        show_home_page()
    elif page == "Site Explorer":
        show_site_explorer_page()
    elif page == "Recommendations":
        show_recommendations_page()
    elif page == "Analytics":
        show_analytics_page()


if __name__ == "__main__":
    main()
