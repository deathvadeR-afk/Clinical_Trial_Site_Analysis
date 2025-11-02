"""
Analytics Page for Clinical Trial Site Analysis Platform Dashboard
"""
import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")

def show_analytics_page():
    """Display the analytics page"""
    st.title("📊 Analytics Dashboard")
    st.markdown("---")
    
    st.write("Comprehensive analytics and performance metrics for clinical trial sites.")
    
    # Sample metrics visualization
    st.subheader("Performance Metrics")
    st.info("In a full implementation, this would show interactive charts and visualizations.")
    
    # Sample metrics
    metrics_data = [
        {"Metric": "Average Enrollment Time", "Value": "4.2 months"},
        {"Metric": "Completion Rate", "Value": "87%"},
        {"Metric": "Protocol Adherence", "Value": "93%"},
        {"Metric": "Data Quality Score", "Value": "91%"},
    ]
    
    st.table(metrics_data)
    
    # Create sample charts
    st.subheader("Trend Analysis")
    
    # Sample trend data
    trend_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
        'Sites': [120, 135, 142, 156, 168, 182, 195, 210, 225, 240],
        'Trials': [85, 92, 98, 105, 118, 126, 134, 142, 156, 168]
    })
    
    # Line chart
    fig1 = px.line(trend_data, x='Month', y=['Sites', 'Trials'], 
                   title='Growth Trends')
    st.plotly_chart(fig1, use_container_width=True)
    
    # Sample distribution data
    st.subheader("Performance Distribution")
    distribution_data = pd.DataFrame({
        'Site': ['Mayo Clinic', 'Johns Hopkins', 'Cleveland Clinic', 'Mass General', 'Stanford'],
        'Completion_Rate': [94, 91, 89, 92, 88],
        'Enrollment_Efficiency': [92, 89, 87, 90, 85]
    })
    
    # Scatter plot
    fig2 = px.scatter(distribution_data, x='Completion_Rate', y='Enrollment_Efficiency',
                      text='Site', title='Performance Matrix')
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    show_analytics_page()