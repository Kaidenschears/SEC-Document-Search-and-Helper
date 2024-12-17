import functools
from datetime import datetime, timedelta
from typing import Any, Callable
import streamlit as st

def cache_data(ttl_seconds: int = 3600) -> Callable:
    """
    Decorator to cache function results in Streamlit session state with TTL
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function name and arguments
            cache_key = f"cache_{func.__name__}_{str(args)}_{str(kwargs)}"
            timestamp_key = f"{cache_key}_timestamp"
            
            # Check if cached result exists and is still valid
            if cache_key in st.session_state and timestamp_key in st.session_state:
                cached_time = st.session_state[timestamp_key]
                if datetime.now() - cached_time < timedelta(seconds=ttl_seconds):
                    return st.session_state[cache_key]
            
            # Calculate new result
            result = func(*args, **kwargs)
            
            # Cache result and timestamp
            st.session_state[cache_key] = result
            st.session_state[timestamp_key] = datetime.now()
            
            return result
        return wrapper
    return decorator

def format_currency(value: float) -> str:
    """Format float value as currency string"""
    return f"${value:,.2f}"

def format_percentage(value: float) -> str:
    """Format float value as percentage string"""
    return f"{value:.2%}"

def format_large_number(value: float) -> str:
    """Format large numbers with K/M/B suffix"""
    suffixes = ['', 'K', 'M', 'B', 'T']
    suffix_index = 0
    
    while value >= 1000 and suffix_index < len(suffixes) - 1:
        value /= 1000
        suffix_index += 1
    
    return f"{value:.1f}{suffixes[suffix_index]}"

def validate_cik(cik: str) -> bool:
    """Validate CIK format"""
    return bool(cik and cik.isdigit() and len(cik) <= 10)

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    return text.replace("<", "&lt;").replace(">", "&gt;")
