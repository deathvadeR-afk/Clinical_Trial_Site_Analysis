#!/bin/bash

# Start the Clinical Trial Analysis Platform using Docker Compose

echo "Starting Clinical Trial Analysis Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build and start services
echo "Building and starting services..."
docker-compose up --build

echo "Clinical Trial Analysis Platform is now running!"
echo "Access the dashboard at http://localhost:8501"