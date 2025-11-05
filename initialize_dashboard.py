#!/usr/bin/env python3
"""
Database Initialization Script for Clinical Trial Site Analysis Platform Dashboard
This script initializes the database schema when deploying to Streamlit Cloud
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager


def initialize_dashboard_database():
    """Initialize the database with schema for the dashboard"""
    print("Initializing dashboard database...")
    
    # Create database manager with the standard database name
    db_manager = DatabaseManager("clinical_trials.db")
    
    # Connect to database
    if not db_manager.connect():
        print("Failed to connect to database")
        return False
    
    print("Connected to database successfully")
    
    # Create tables from schema
    if db_manager.create_tables():
        print("Database tables created successfully!")
        success = True
    else:
        print("Failed to create database tables")
        success = False
    
    # Disconnect from database
    db_manager.disconnect()
    
    return success


if __name__ == "__main__":
    if initialize_dashboard_database():
        print("Dashboard database initialization completed successfully!")
        sys.exit(0)
    else:
        print("Dashboard database initialization failed!")
        sys.exit(1)