"""
Helper Functions for Clinical Trial Site Analysis Platform
Provides reusable utility functions across the platform
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Generator
import json


def format_date(date_string: str, input_format: str = "%Y-%m-%d", output_format: str = "%B %d, %Y") -> str:
    """
    Format a date string from one format to another
    
    Args:
        date_string: Date string to format
        input_format: Format of the input date string
        output_format: Desired output format
        
    Returns:
        Formatted date string
    """
    try:
        date_obj = datetime.strptime(date_string, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_string  # Return original if parsing fails


def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace and special characters
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep alphanumeric, spaces, and basic punctuation
    text = re.sub(r'[^\w\s\-.,;:]', '', text)
    
    return text


def calculate_percentage(part: float, whole: float, decimal_places: int = 2) -> float:
    """
    Calculate percentage with specified decimal places
    
    Args:
        part: Part value
        whole: Whole value
        decimal_places: Number of decimal places to round to
        
    Returns:
        Calculated percentage
    """
    if whole == 0:
        return 0.0
    
    return round((part / whole) * 100, decimal_places)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning a default value if denominator is zero
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if denominator is zero
        
    Returns:
        Result of division or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunks(lst: List[Any], n: int) -> Generator[List[Any], None, None]:
    """
    Split a list into chunks of specified size
    
    Args:
        lst: List to split
        n: Chunk size
        
    Yields:
        List chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def is_valid_nct_id(nct_id: str) -> bool:
    """
    Validate if a string is a valid NCT ID format
    
    Args:
        nct_id: NCT ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not nct_id:
        return False
    
    # NCT ID format: NCT followed by 8 digits
    pattern = r'^NCT\d{8}$'
    return bool(re.match(pattern, nct_id))


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely parse JSON string, returning a default value if parsing fails
    
    Args:
        json_string: JSON string to parse
        default: Default value to return if parsing fails
        
    Returns:
        Parsed JSON object or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


# Example usage
if __name__ == "__main__":
    print("Helper Functions module ready for use")
    print("This module provides reusable utility functions")