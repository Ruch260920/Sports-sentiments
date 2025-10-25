"""
Utility functions for the OMNI system
"""

import re
from urllib.parse import urlparse

def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\-.,!?;:()]', '', text)
    
    return text

def extract_domain(url):
    """Extract domain from URL"""
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ""

def normalize_source_name(name):
    """Normalize source name for consistency"""
    if not name:
        return ""
    
    # Remove common prefixes and suffixes
    name = re.sub(r'^(The|A|An)\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+(News|Media|Group|Inc|LLC|Corp|Corporation)$', '', name, flags=re.IGNORECASE)
    
    return name.strip()

def safe_json_parse(data, default=None):
    """Safely parse JSON data"""
    if isinstance(data, dict):
        return data
    
    try:
        import json
        if isinstance(data, str):
            return json.loads(data)
        return default
    except:
        return default

def format_timestamp(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
    """Format timestamp consistently"""
    if not timestamp:
        return ""
    
    try:
        if isinstance(timestamp, str):
            from datetime import datetime
            # Try to parse common timestamp formats
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    return dt.strftime(format_str)
                except:
                    continue
        return str(timestamp)
    except:
        return str(timestamp)

def truncate_text(text, max_length=100, suffix="..."):
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def calculate_engagement_score(likes, retweets, replies, quotes):
    """Calculate engagement score for tweets"""
    try:
        likes = int(likes or 0)
        retweets = int(retweets or 0)
        replies = int(replies or 0)
        quotes = int(quotes or 0)
        
        # Weighted scoring: likes=1, retweets=2, replies=3, quotes=2
        score = likes + (retweets * 2) + (replies * 3) + (quotes * 2)
        return score
    except:
        return 0 