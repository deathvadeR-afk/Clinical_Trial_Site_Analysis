# Configuration Setup

This document explains how to properly configure the Clinical Trial Site Analysis Platform to avoid committing API keys to version control.

## Security Best Practices

To prevent GitHub from flagging secret leaks, we use the following approach:

1. **Environment Variables (Highest Priority)**: API keys are loaded from environment variables
2. **Config Files**: Only template config files are committed to version control
3. **Git Ignore**: Sensitive config files are excluded from version control

## Configuration Files

### 1. Template Configuration (`config.template.json`)
This file is safe to commit and contains placeholder values:
```json
{
    "api_keys": {
        "clinical_trials": "YOUR_CLINICAL_TRIALS_API_KEY_HERE",
        "pubmed": "YOUR_PUBMED_API_KEY_HERE",
        "gemini": "YOUR_GEMINI_API_KEY_HERE"
    }
}
```

### 2. User Configuration (`config.json`)
This file should NEVER be committed to version control. Create your own by copying the template:
```bash
cp config.template.json config.json
```

Then edit `config.json` to add your actual API keys.

## Environment Variables

For maximum security, use environment variables instead of config files:

```bash
# Set your API keys as environment variables
export CLINICAL_TRIALS_API_KEY="your_actual_key_here"
export PUBMED_API_KEY="your_actual_key_here"
export GEMINI_API_KEY="your_actual_key_here"

# Optional: Override other settings
export DATABASE_PATH="path/to/your/database.db"
export LOG_LEVEL="INFO"
```

## Priority Order

The application loads configuration in this priority order:
1. Function parameters
2. Environment variables
3. Config file values
4. Default values

## Git Ignore

The following files are excluded from version control:
- `config.json` (contains real API keys)
- `.env` files (contains environment variables)
- Any other files with sensitive information

## Setup Instructions

1. **Copy the template**:
   ```bash
   cp config.template.json config.json
   ```

2. **Edit config.json** with your actual API keys (or use environment variables)

3. **Verify .gitignore** includes sensitive files:
   ```
   config.json
   .env
   .env.local
   ```

## API Key Requirements

- **ClinicalTrials.gov API Key**: Required for data ingestion
- **PubMed API Key**: Required for publication data
- **Gemini API Key**: Required for AI-powered insights

If any API key is missing, the corresponding features will be disabled gracefully.