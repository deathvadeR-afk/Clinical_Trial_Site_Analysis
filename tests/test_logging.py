"""
Test script to verify logging functionality
"""
import logging
import os

# Set up logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "test_logging.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_logging():
    """Test logging functionality"""
    print("Testing logging functionality...")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    print("Logging test completed.")

if __name__ == "__main__":
    test_logging()