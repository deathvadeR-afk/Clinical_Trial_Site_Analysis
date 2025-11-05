"""
Database Manager for Clinical Trial Site Analysis Platform
Handles SQLite database creation, connections, and basic operations
"""

import sqlite3
import os
import logging
from typing import Optional, List, Dict, Any

# Import cache manager
from utils.cache_manager import CacheManager

# Set up logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Create logger for this module
logger = logging.getLogger(__name__)

# Remove any existing handlers to avoid duplicates
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Set logger level
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# File handler
file_handler = logging.FileHandler(os.path.join(log_dir, "database.log"))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class DatabaseManager:
    """Manager for SQLite database operations"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager

        Args:
            db_path: Path to the SQLite database file. If None, uses a default path that works for deployment.
        """
        if db_path is None:
            # Determine the best database path based on the current environment
            db_path = self._find_best_database_path()
        
        self.db_path = db_path
        self.connection = None
        self.cache_manager = CacheManager(
            cache_dir="cache", default_ttl=1800
        )  # 30 minutes default TTL

    def _find_best_database_path(self) -> str:
        """
        Find the best database path that works for both local development and Streamlit Cloud deployment.
        
        Returns:
            Path to the database file
        """
        # List of possible database paths to check
        possible_paths = [
            "clinical_trials.db",           # Current directory
            "../clinical_trials.db",        # Parent directory (from dashboard)
            "../../clinical_trials.db",     # Two levels up
            "dashboard/clinical_trials.db", # Dashboard subdirectory
        ]
        
        # Check if any of these paths exist
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found existing database at: {path}")
                return path
        
        # If no existing database found, determine where to create it
        # For Streamlit Cloud deployment, we want it in the current directory
        current_dir = os.getcwd()
        if os.path.basename(current_dir) == "dashboard":
            # We're in the dashboard directory, create database here for Streamlit Cloud
            db_path = "clinical_trials.db"
        else:
            # We're in project root or another location, use standard path
            db_path = "clinical_trials.db"
            
        logger.info(f"Using database path: {db_path}")
        return db_path

    def _find_schema_file(self) -> str:
        """
        Find the schema file path that works for both local development and Streamlit Cloud deployment.
        
        Returns:
            Path to the schema file
        """
        # List of possible schema paths to check
        possible_paths = [
            "database/schema.sql",           # Standard path
            "../database/schema.sql",        # From dashboard directory
            "../../database/schema.sql",     # From deeper directories
        ]
        
        # Check if any of these paths exist
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found schema file at: {path}")
                return path
        
        # If no existing schema found, use default path
        return "database/schema.sql"

    def connect(self) -> bool:
        """
        Establish connection to the database

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Ensure the directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to database at {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from database")

    def create_tables(self, schema_file: Optional[str] = None) -> bool:
        """
        Create database tables from schema file

        Args:
            schema_file: Path to SQL schema file. If None, tries to find it automatically.

        Returns:
            True if tables created successfully, False otherwise
        """
        if not self.connection:
            logger.error("No database connection")
            return False

        try:
            # Handle relative paths correctly using absolute paths
            if schema_file is None:
                # Try to find the schema file automatically
                schema_file = self._find_schema_file()
            
            # Handle relative paths correctly using absolute paths
            if not os.path.isabs(schema_file):
                # Get the project root directory
                project_root = os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
                schema_path = os.path.join(project_root, schema_file)
            else:
                schema_path = schema_file

            # Check if file exists
            if not os.path.exists(schema_path):
                logger.error(f"Schema file not found at: {schema_path}")
                return False

            # Read schema file
            with open(schema_path, "r") as f:
                schema_sql = f.read()

            # Execute schema
            cursor = self.connection.cursor()
            cursor.executescript(schema_sql)
            self.connection.commit()
            logger.info("Database tables created successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to create tables: {e}")
            return False
        except FileNotFoundError:
            logger.error(f"Schema file not found: {schema_file}")
            return False

    def insert_data(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Insert data into specified table

        Args:
            table: Table name
            data: Dictionary of column-value pairs

        Returns:
            True if insertion successful, False otherwise
        """
        if not self.connection:
            logger.error("No database connection")
            return False

        try:
            cursor = self.connection.cursor()

            # Build INSERT statement
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            # Execute INSERT
            cursor.execute(sql, list(data.values()))
            self.connection.commit()
            logger.debug(f"Inserted data into {table}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to insert data into {table}: {e}")
            return False

    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> bool:
        """
        Insert multiple rows into specified table

        Args:
            table: Table name
            data_list: List of dictionaries containing column-value pairs

        Returns:
            True if insertion successful, False otherwise
        """
        if not data_list:
            logger.warning("No data to insert")
            return True

        if not self.connection:
            logger.error("No database connection")
            return False

        try:
            cursor = self.connection.cursor()

            # Build INSERT statement from first item
            first_item = data_list[0]
            columns = ", ".join(first_item.keys())
            placeholders = ", ".join(["?" for _ in first_item])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            # Extract values from all items
            values_list = [list(item.values()) for item in data_list]

            # Execute INSERT
            cursor.executemany(sql, values_list)
            self.connection.commit()
            logger.info(f"Inserted {len(data_list)} rows into {table}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to insert data into {table}: {e}")
            return False

    def query(
        self,
        sql: str,
        params: Optional[tuple] = None,
        use_cache: bool = False,
        cache_key: Optional[str] = None,
    ) -> List[sqlite3.Row]:
        """
        Execute SELECT query and return results

        Args:
            sql: SQL SELECT statement
            params: Query parameters
            use_cache: Whether to use caching
            cache_key: Custom cache key (if None, generated from SQL and params)

        Returns:
            List of rows matching query
        """
        if not self.connection:
            logger.error("No database connection")
            return []

        # Use cache if requested
        if use_cache:
            # Generate cache key if not provided
            if cache_key is None:
                cache_key = f"query_{hash(sql + str(params))}"

            # Try to get from cache
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for query: {cache_key}")
                return cached_result
            else:
                logger.debug(f"Cache miss for query: {cache_key}")

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            result = cursor.fetchall()

            # Cache the result if requested
            if use_cache and cache_key:
                self.cache_manager.set(cache_key, result)
                logger.debug(f"Cached query result for key: {cache_key}")

            return result
        except sqlite3.Error as e:
            logger.error(f"Query failed: {e}")
            return []

    def execute(self, sql: str, params: Optional[tuple] = None) -> bool:
        """
        Execute non-SELECT SQL statement

        Args:
            sql: SQL statement
            params: Query parameters

        Returns:
            True if execution successful, False otherwise
        """
        if not self.connection:
            logger.error("No database connection")
            return False

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Execution failed: {e}")
            return False

    def __enter__(self):
        """Context manager entry"""
        if not self.connect():
            raise Exception("Failed to connect to database")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
