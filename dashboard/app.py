"""
Main Streamlit Application for Clinical Trial Site Analysis Platform Dashboard
"""

import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

# Import page modules with error handling
try:
    from dashboard.pages.home import show_home_page
except ImportError as e:
    st.error(f"Error importing home page: {e}")
    def show_home_page():
        st.error("Home page not available")

try:
    from dashboard.pages.site_explorer import show_site_explorer_page
except ImportError as e:
    st.error(f"Error importing site explorer page: {e}")
    def show_site_explorer_page():
        st.error("Site explorer page not available")

try:
    from dashboard.pages.recommendations import show_recommendations_page
except ImportError as e:
    st.error(f"Error importing recommendations page: {e}")
    def show_recommendations_page():
        st.error("Recommendations page not available")

try:
    from dashboard.pages.analytics import show_analytics_page
except ImportError as e:
    st.error(f"Error importing analytics page: {e}")
    def show_analytics_page():
        st.error("Analytics page not available")

try:
    from dashboard.pages.site_profile import show_site_profile_page
except ImportError as e:
    st.error(f"Error importing site profile page: {e}")
    def show_site_profile_page():
        st.error("Site profile page not available")

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
        "Select Page", ["Home", "Site Explorer", "Site Profile", "Recommendations", "Analytics"]
    )

    # Page routing
    if page == "Home":
        show_home_page()
    elif page == "Site Explorer":
        show_site_explorer_page()
    elif page == "Site Profile":
        show_site_profile_page()
    elif page == "Recommendations":
        show_recommendations_page()
    elif page == "Analytics":
        show_analytics_page()


if __name__ == "__main__":
    main()