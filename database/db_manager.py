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
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
    
    def __init__(self, db_path: str = "clinical_trials.db"):
        """
        Initialize the database manager
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.cache_manager = CacheManager(cache_dir="cache", default_ttl=1800)  # 30 minutes default TTL
        
    def connect(self) -> bool:
        """
        Establish connection to the database
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
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
    
    def create_tables(self, schema_file: str = "database/schema.sql") -> bool:
        """
        Create database tables from schema file
        
        Args:
            schema_file: Path to SQL schema file
            
        Returns:
            True if tables created successfully, False otherwise
        """
        if not self.connection:
            logger.error("No database connection")
            return False
            
        try:
            # Handle relative paths correctly using absolute paths
            if not os.path.isabs(schema_file):
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                schema_path = os.path.join(project_root, schema_file)
            else:
                schema_path = schema_file
                
            # Check if file exists
            if not os.path.exists(schema_path):
                logger.error(f"Schema file not found at: {schema_path}")
                return False
                
            # Read schema file
            with open(schema_path, 'r') as f:
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
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
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
            columns = ', '.join(first_item.keys())
            placeholders = ', '.join(['?' for _ in first_item])
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
    
    def query(self, sql: str, params: Optional[tuple] = None, use_cache: bool = False, cache_key: Optional[str] = None) -> List[sqlite3.Row]:
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
