"""
Cache Manager for Clinical Trial Site Analysis Platform
Implements caching strategies to improve performance
"""
import json
import os
import time
from typing import Any, Optional, Dict
import logging

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "cache_manager.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CacheManager:
    """Manages caching for frequently accessed data"""
    
    def __init__(self, cache_dir: str = "../cache", default_ttl: int = 3600):
        """
        Initialize the cache manager
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"CacheManager initialized with cache_dir={cache_dir}, default_ttl={default_ttl}")
    
    def _get_cache_file_path(self, key: str) -> str:
        """
        Get the file path for a cache key
        
        Args:
            key: Cache key
            
        Returns:
            File path for the cache entry
        """
        # Sanitize key for file system with more comprehensive approach
        # Replace any non-alphanumeric characters (except . _ -) with underscores
        safe_key = "".join(c if c.isalnum() or c in "._-" else "_" for c in key)
        
        # Limit key length to prevent filesystem issues (most filesystems have ~255 char limits)
        max_key_length = 200
        if len(safe_key) > max_key_length:
            # If key is too long, hash it to create a fixed-length identifier
            import hashlib
            hash_object = hashlib.md5(key.encode())
            safe_key = hash_object.hexdigest()[:50] + "_" + safe_key[-100:] if len(safe_key) > 150 else safe_key[:max_key_length]
        
        # Ensure the key doesn't start with a dot or dash which might be problematic
        if safe_key.startswith('.') or safe_key.startswith('-'):
            safe_key = 'key_' + safe_key[1:]
            
        # Ensure we have at least one character for the key
        if not safe_key:
            safe_key = "empty_key"
            
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            cache_file = self._get_cache_file_path(key)
            
            # Check if cache file exists
            if not os.path.exists(cache_file):
                logger.debug(f"Cache miss for key: {key} (file not found)")
                return None
            
            # Read cache file
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            current_time = time.time()
            if current_time > cache_data.get('expires_at', 0):
                logger.debug(f"Cache miss for key: {key} (expired)")
                # Remove expired cache file
                os.remove(cache_file)
                return None
            
            logger.debug(f"Cache hit for key: {key}")
            return cache_data.get('value')
            
        except Exception as e:
            logger.error(f"Error reading cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_file = self._get_cache_file_path(key)
            expires_at = time.time() + (ttl or self.default_ttl)
            
            cache_data = {
                'key': key,
                'value': value,
                'created_at': time.time(),
                'expires_at': expires_at
            }
            
            # Write cache file
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cache set for key: {key} (expires in {ttl or self.default_ttl} seconds)")
            return True
            
        except Exception as e:
            logger.error(f"Error writing cache for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful (or if key didn't exist), False on error
        """
        try:
            cache_file = self._get_cache_file_path(key)
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.debug(f"Cache deleted for key: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            logger.info("Cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = os.listdir(self.cache_dir)
            total_entries = len(cache_files)
            
            expired_entries = 0
            current_time = time.time()
            
            for filename in cache_files:
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            cache_data = json.load(f)
                        if current_time > cache_data.get('expires_at', 0):
                            expired_entries += 1
                    except:
                        expired_entries += 1
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'cache_dir': self.cache_dir
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    # Create cache manager
    cache = CacheManager()
    
    # Test cache operations
    print("Testing cache operations...")
    
    # Set a value
    cache.set("test_key", {"name": "Test", "value": 123}, ttl=10)
    print("Set cache value for 'test_key'")
    
    # Get the value
    value = cache.get("test_key")
    print(f"Retrieved value: {value}")
    
    # Get stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
    
    print("Cache Manager test completed!")