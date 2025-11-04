#!/usr/bin/env python3
"""
Update timestamps for existing records in the database
"""
import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def update_timestamps():
    """Update timestamps for existing records"""
    try:
        # Connect to database
        conn = sqlite3.connect("clinical_trials.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Update sites_master table
        current_time = datetime.now().isoformat()
        cursor.execute(
            "UPDATE sites_master SET last_updated = ? WHERE last_updated IS NULL",
            (current_time,),
        )
        updated_sites = cursor.rowcount

        # Update clinical_trials table
        cursor.execute(
            "UPDATE clinical_trials SET last_update_posted = ? WHERE last_update_posted IS NULL",
            (current_time,),
        )
        updated_trials = cursor.rowcount

        # Commit changes
        conn.commit()

        print(f"Updated {updated_sites} sites with timestamps")
        print(f"Updated {updated_trials} trials with timestamps")

        # Close connection
        conn.close()

        return True
    except Exception as e:
        print(f"Error updating timestamps: {e}")
        return False


if __name__ == "__main__":
    if update_timestamps():
        print("Timestamps updated successfully!")
        sys.exit(0)
    else:
        print("Failed to update timestamps!")
        sys.exit(1)
