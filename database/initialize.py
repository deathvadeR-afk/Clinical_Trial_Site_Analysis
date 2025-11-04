#!/usr/bin/env python3
"""
Initialize Database for Clinical Trial Site Analysis Platform
Creates all necessary tables from the schema
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager


def initialize_database():
    """Initialize the database with all required tables"""
    print("Initializing database...")

    # Create database manager
    db_manager = DatabaseManager()

    # Connect to database
    if not db_manager.connect():
        print("Failed to connect to database")
        return False

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
    if initialize_database():
        print("Database initialization completed successfully!")
        sys.exit(0)
    else:
        print("Database initialization failed!")
        sys.exit(1)
