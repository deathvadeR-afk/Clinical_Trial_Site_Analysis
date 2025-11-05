#!/bin/bash
# Setup script for Streamlit Cloud deployment

echo "Setting up Clinical Trial Site Analysis Platform..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python initialize_dashboard.py

echo "Setup complete! You can now run the Streamlit app."