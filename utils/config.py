"""
Configuration Management for Clinical Trial Site Analysis Platform
Handles loading and management of configuration settings
"""

import json
import os
from typing import Dict, Any, Optional


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from JSON file with environment variable override support
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration settings
    """
    # Handle relative paths correctly using absolute paths
    if not os.path.isabs(config_path):
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file_path = os.path.join(project_root, config_path)
    else:
        config_file_path = config_path

    # Start with default configuration
    config = {
        "database": {
            "path": "clinical_trials.db"
        },
        "api_keys": {
            "clinical_trials": "YOUR_CLINICAL_TRIALS_API_KEY_HERE",
            "pubmed": "YOUR_PUBMED_API_KEY_HERE",
            "gemini": "YOUR_GEMINI_API_KEY_HERE",
            "openrouter": "YOUR_OPENROUTER_API_KEY_HERE"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/app.log"
        },
        "scheduler": {
            "data_pipeline_time": "02:00",
            "quality_monitoring_time": "03:00"
        },
        "gemini": {
            "model": "gemini-2.0-flash",
            "rate_limits": {
                "rpm": 15,
                "rpd": 1500
            }
        }
    }

    # Load from config file if it exists
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, "r") as f:
                file_config = json.load(f)
                # Merge file config with default config
                for key, value in file_config.items():
                    if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                        config[key].update(value)
                    else:
                        config[key] = value
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")

    # Override with environment variables if available
    # Database settings
    database_path = os.getenv("DATABASE_PATH")
    if database_path:
        config["database"]["path"] = database_path
    
    # API keys from environment variables (higher priority)
    clinical_trials_api_key = os.getenv("CLINICAL_TRIALS_API_KEY")
    if clinical_trials_api_key:
        config["api_keys"]["clinical_trials"] = clinical_trials_api_key
        
    pubmed_api_key = os.getenv("PUBMED_API_KEY")
    if pubmed_api_key:
        config["api_keys"]["pubmed"] = pubmed_api_key
        
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        config["api_keys"]["gemini"] = gemini_api_key
    
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_api_key:
        config["api_keys"]["openrouter"] = openrouter_api_key
    
    # Logging settings
    log_level = os.getenv("LOG_LEVEL")
    if log_level:
        config["logging"]["level"] = log_level
        
    log_file = os.getenv("LOG_FILE")
    if log_file:
        config["logging"]["file"] = log_file
    
    # Scheduler settings
    data_pipeline_time = os.getenv("DATA_PIPELINE_TIME")
    if data_pipeline_time:
        config["scheduler"]["data_pipeline_time"] = data_pipeline_time
        
    quality_monitoring_time = os.getenv("QUALITY_MONITORING_TIME")
    if quality_monitoring_time:
        config["scheduler"]["quality_monitoring_time"] = quality_monitoring_time
    
    # Gemini settings
    gemini_model = os.getenv("GEMINI_MODEL")
    if gemini_model:
        config["gemini"]["model"] = gemini_model
        
    gemini_rpm = os.getenv("GEMINI_RPM")
    if gemini_rpm:
        config["gemini"]["rate_limits"]["rpm"] = int(gemini_rpm)
        
    gemini_rpd = os.getenv("GEMINI_RPD")
    if gemini_rpd:
        config["gemini"]["rate_limits"]["rpd"] = int(gemini_rpd)

    return config


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration settings
    
    Returns:
        Dictionary containing database configuration
    """
    config = load_config()
    return config.get("database", {"path": "clinical_trials.db"})


def get_api_keys() -> Dict[str, str]:
    """
    Get API key configuration with environment variable override support
    
    Returns:
        Dictionary containing API keys
    """
    config = load_config()
    api_keys = config.get("api_keys", {})
    
    # Log warning if using placeholder values
    for key_name, key_value in api_keys.items():
        if key_value and key_value.startswith("YOUR_"):
            print(f"Warning: API key '{key_name}' not configured. Some features may be disabled.")
    
    return api_keys


def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration settings
    
    Returns:
        Dictionary containing logging configuration
    """
    config = load_config()
    return config.get("logging", {"level": "INFO", "file": "logs/app.log"})


# Example usage
if __name__ == "__main__":
    print("Configuration Management module ready for use")
    print("This module handles loading and management of configuration settings")