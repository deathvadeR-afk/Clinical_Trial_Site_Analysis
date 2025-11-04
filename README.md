# Clinical Trial Site Analysis Platform - Docker Setup

## Prerequisites

- Docker
- Docker Compose

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

## GitHub Actions CI/CD

The project includes three GitHub Actions workflows:

1. **ci-cd.yml**: Continuous integration and deployment pipeline
2. **data-ingestion.yml**: Automated daily data ingestion
3. **ml-retraining.yml**: Weekly ML model retraining

## Environment Variables

The application uses the following environment variables:

- `CLINICAL_TRIALS_API_KEY`: API key for ClinicalTrials.gov (if required)
- `PUBMED_API_KEY`: API key for PubMed (if required)

Set these in your Docker environment or GitHub Secrets.