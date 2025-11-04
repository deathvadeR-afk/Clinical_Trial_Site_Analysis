import os

# Define the project structure
project_structure = {
    "data_ingestion": {
        "__init__.py": None,
        "clinicaltrials_api.py": None,
        "pubmed_api.py": None,
        "data_validator.py": None,
    },
    "database": {
        "__init__.py": None,
        "db_manager.py": None,
        "models.py": None,
        "schema.sql": None,
    },
    "analytics": {
        "__init__.py": None,
        "match_calculator.py": None,
        "metrics_calculator.py": None,
        "recommendation_engine.py": None,
    },
    "ai_ml": {
        "__init__.py": None,
        "gemini_client.py": None,
        "clustering.py": None,
        "predictive_model.py": None,
        "nl_query.py": None,
    },
    "dashboard": {
        "__init__.py": None,
        "app.py": None,
        "pages": {
            "__init__.py": None,
            "home.py": None,
            "site_explorer.py": None,
            "recommendations.py": None,
            "analytics.py": None,
        },
    },
    "utils": {
        "__init__.py": None,
        "config.py": None,
        "logger.py": None,
        "helpers.py": None,
    },
    "tests": {
        "__init__.py": None,
        "test_data_ingestion.py": None,
        "test_analytics.py": None,
        "test_ai_ml.py": None,
    },
    "logs": {  # ✅ New logs folder
        ".gitkeep": None  # placeholder so folder is tracked in git
    },
    # Top-level files
    "requirements.txt": None,
    "config.json": None,
    "main.py": None,
}


def create_project_structure(base_path, structure):
    """Recursively create the project directory structure"""
    for name, contents in structure.items():
        path = os.path.join(base_path, name)

        if contents is None:
            # It's a file
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                if name.endswith(".py"):
                    f.write("# Auto-generated file\n")
                else:
                    f.write("")
            print(f"Created file: {path}")
        elif isinstance(contents, dict):
            # It's a directory
            os.makedirs(path, exist_ok=True)
            print(f"Created directory: {path}")
            create_project_structure(path, contents)
        else:
            raise ValueError(f"Unexpected type for {name}: {type(contents)}")


# Run the generator
if __name__ == "__main__":
    base_path = "."
    create_project_structure(base_path, project_structure)

    print("\nProject structure created successfully!")
    print("Next steps:")
    print("1. Install required packages with: pip install -r requirements.txt")
    print("2. Configure your API keys in config.json")
    print(
        "3. Start implementing the ClinicalTrials.gov API integration in "
        "data_ingestion/clinicaltrials_api.py"
    )
    print("4. Use the logs/ folder for runtime and audit logs")
