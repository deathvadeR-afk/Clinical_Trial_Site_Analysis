#!/usr/bin/env python3
"""
Database Initialization Script for Clinical Trial Site Analysis Platform Dashboard
This script initializes the database schema when deploying to Streamlit Cloud
"""

import sys
import os
import shutil

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from database.db_manager import DatabaseManager


def initialize_dashboard_database():
    """Initialize the database with schema for the dashboard"""
    print("Initializing dashboard database...")
    
    # Create database manager (let it handle the path automatically)
    db_manager = DatabaseManager()
    
    print(f"Database path: {db_manager.db_path}")
    
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


def copy_database_if_needed():
    """Copy database from project root to dashboard directory if needed for Streamlit Cloud"""
    try:
        # Check if we're in the dashboard directory
        current_dir = os.getcwd()
        print(f"Current directory: {current_dir}")
        
        # If database doesn't exist in current location but exists in parent directory
        if (os.path.basename(current_dir) == "dashboard" and 
            not os.path.exists("clinical_trials.db") and 
            os.path.exists("../clinical_trials.db")):
            
            print("Copying database from parent directory...")
            shutil.copy2("../clinical_trials.db", "clinical_trials.db")
            print("Database copied successfully!")
            return True
        elif not os.path.exists("clinical_trials.db") and os.path.exists("../clinical_trials.db"):
            print("Copying database from project root...")
            shutil.copy2("../clinical_trials.db", "clinical_trials.db")
            print("Database copied successfully!")
            return True
        elif os.path.exists("clinical_trials.db"):
            print("Database already exists in current directory")
            return True
        else:
            print("No existing database found to copy")
            return True
    except Exception as e:
        print(f"Error copying database: {e}")
        return False


if __name__ == "__main__":
    # Try to copy existing database if needed
    copy_database_if_needed()
    
    # Initialize database schema
    if initialize_dashboard_database():
        print("Dashboard database initialization completed successfully!")
        sys.exit(0)
    else:
        print("Dashboard database initialization failed!")
        sys.exit(1)