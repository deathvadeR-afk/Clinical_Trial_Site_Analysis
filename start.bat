@echo off
title Clinical Trial Analysis Platform

echo Starting Clinical Trial Analysis Platform...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not installed. Please install Docker first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Build and start services
echo Building and starting services...
docker-compose up --build

echo Clinical Trial Analysis Platform is now running!
echo Access the dashboard at http://localhost:8501
pause