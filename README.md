# Clinical Trial Site Analysis Platform

This platform analyzes clinical trial sites to help researchers identify optimal sites for their studies.

## Project Structure

```
├── ai_ml/                 # AI and machine learning components
├── analytics/             # Data analysis and metrics calculation
├── cache/                 # API response caching
├── dashboard/             # Streamlit dashboard application
├── data_ingestion/        # Data collection from external APIs
├── database/              # Database schema and management
├── logs/                  # Application logs
├── pipeline/              # Automated data processing pipelines
├── reports/               # Generated reports and visualizations
├── tests/                 # Unit and integration tests
└── utils/                 # Utility functions and helpers
```

## Configuration

### API Keys
To use this platform, you need API keys for:
- ClinicalTrials.gov
- PubMed
- Google Gemini (optional, for AI insights)
- OpenRouter (optional, for alternative AI insights)

Create a `config.json` file from `config.template.json` and add your API keys, or set them as environment variables:
- `CLINICAL_TRIALS_API_KEY`
- `PUBMED_API_KEY`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`

## Excluded Files

The following files are excluded from version control for security and performance reasons:

### Database Files
- `clinical_trials.db` - Main production database (large file)
- `clinical_trials_backup.db` - Backup of main database
- All `*.db` files - SQLite database files

### Configuration Files
- `config.json` - Contains API keys and sensitive configuration
- `.env` files - Environment variables with sensitive data

### Cache and Logs
- `cache/` directory - Cached API responses
- `logs/` directory - Application logs
- `reports/` directory - Generated reports

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up configuration:
   ```bash
   cp config.template.json config.json
   # Edit config.json with your API keys
   ```

3. Run the main application:
   ```bash
   python main.py
   ```

4. Access the dashboard:
   ```bash
   streamlit run dashboard/app.py
   ```

## Deployment to Streamlit Cloud

To deploy this application to Streamlit Cloud:

1. Fork this repository to your GitHub account
2. Go to [Streamlit Cloud](https://streamlit.io/cloud) and create a new app
3. Select your forked repository
4. Set the main file path to `dashboard/app.py`
5. In the advanced settings, add the following environment variables:
   - `CLINICAL_TRIALS_API_KEY` - Your ClinicalTrials.gov API key
   - `PUBMED_API_KEY` - Your PubMed API key (optional)
   - `GEMINI_API_KEY` - Your Google Gemini API key (optional)
   - `OPENROUTER_API_KEY` - Your OpenRouter API key (optional)

6. Click "Deploy!"

The application will automatically initialize the database schema on first run.

## Local Development

For local development, you may need to initialize the database manually:

```bash
python initialize_dashboard.py
```

Then run the dashboard:

```bash
streamlit run dashboard/app.py
```

## AI Insights Generation

To generate AI insights for all sites:

```bash
python ai_ml/generate_ai_insights.py
```

This script will use either OpenRouter or Gemini (depending on which API key is configured) to generate insights for each site.

## Security Notes

Never commit `config.json` or any files containing API keys to version control. Use environment variables for deployment.