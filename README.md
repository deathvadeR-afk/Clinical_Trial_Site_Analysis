# Clinical Trial Site Analysis Platform

## Project Overview

The Clinical Trial Site Analysis Platform is a sophisticated system designed to help pharmaceutical companies and research organizations identify the best locations for conducting clinical trials. The platform automates and optimizes the site selection process using advanced data analysis and artificial intelligence.

## Key Features

1. **Data Integration**: Comprehensive data collection from ClinicalTrials.gov and PubMed APIs
2. **Intelligent Analytics**: Advanced algorithms for site-study matching and performance evaluation
3. **AI/ML Enhancement**: Machine learning and natural language processing for deeper insights
4. **Interactive Dashboard**: User-friendly interface for data exploration and decision making
5. **Production Ready**: Optimized for performance and reliability in real-world deployment

## Quick Start

### Using the startup scripts:

**On Windows:**
```cmd
start.bat
```

**On macOS/Linux:**
```bash
./start.sh
```

### Using consolidated analysis scripts:

**Analyze data for ML readiness:**
```bash
python data_analysis.py
```

**Run ML operations (training and clustering):**
```bash
python ml_operations.py
```

### Using Docker Compose directly:

```bash
# Build and start services
docker-compose up --build

# Start in detached mode
docker-compose up --build -d

# Stop services
docker-compose down
```

## Accessing the Application

Once the containers are running, access the dashboard at:
- http://localhost:8501

## Services Overview

- **clinical-trial-app**: Main application with Streamlit dashboard
- **data-ingestion**: Automated data ingestion pipeline
- **ml-training**: Machine learning model training service

## Dashboard Controls

The dashboard provides direct user control over key operations:

1. **Data Ingestion**: Trigger fetching of latest data from ClinicalTrials.gov and PubMed APIs
2. **Historical Data Download**: Download historical clinical trial data for enhanced ML training
3. **Model Retraining**: Retrain machine learning models with current data

## GitHub Actions CI/CD

The project includes three GitHub Actions workflows:

1. **ci-cd.yml**: Continuous integration and deployment pipeline
2. **data-ingestion.yml**: Automated daily data ingestion
3. **ml-retraining.yml**: Weekly ML model retraining

## Environment Variables

The application uses the following environment variables:

- `CLINICAL_TRIALS_API_KEY`: API key for ClinicalTrials.gov (if required)
- `PUBMED_API_KEY`: API key for PubMed (if required)
- `GEMINI_API_KEY`: API key for Google's Gemini API (for AI features)

Set these in your Docker environment or GitHub Secrets.

## Technical Architecture

### Core Components

1. **Data Ingestion Layer**: ClinicalTrials.gov and PubMed API integration
2. **Database Layer**: SQLite database with comprehensive schema
3. **Analytics Engine**: Match scoring and recommendation algorithms
4. **AI/ML Layer**: Google Gemini API integration and machine learning models
5. **Presentation Layer**: Streamlit dashboard with interactive visualizations
6. **Automation Layer**: Scheduled pipelines and monitoring systems

## For Detailed Documentation

See [CLINICAL_TRIAL_PLATFORM_CONSOLIDATED.md](CLINICAL_TRIAL_PLATFORM_CONSOLIDATED.md) for comprehensive documentation of the platform architecture, implementation details, and future roadmap.