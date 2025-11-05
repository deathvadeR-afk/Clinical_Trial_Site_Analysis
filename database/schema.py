"""
Database Schema for Clinical Trial Site Analysis Platform
Exports the database schema as a Python string constant
"""

import os

# Read the schema SQL file
schema_file_path = os.path.join(os.path.dirname(__file__), "schema.sql")

try:
    with open(schema_file_path, "r", encoding="utf-8") as f:
        SCHEMA = f.read()
except FileNotFoundError:
    # Fallback to empty schema if file not found
    SCHEMA = ""

# Export the schema as a constant
__all__ = ["SCHEMA"]

# Example usage
if __name__ == "__main__":
    print("Database Schema module ready for use")
    print("This module exports the database schema as a Python string constant")
    print(f"Schema length: {len(SCHEMA)} characters")