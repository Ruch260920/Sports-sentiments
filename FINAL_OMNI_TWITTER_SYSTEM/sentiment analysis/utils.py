"""
Utility Functions
Common utility functions for the OMNI News Pipeline
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

def generate_webhook_signature(payload: str, secret: str) -> str:
    """Generate webhook signature for verification"""
    return hashlib.sha256(f"{payload}{secret}".encode()).hexdigest()

def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    expected_signature = generate_webhook_signature(payload, secret)
    return signature == expected_signature

def safe_json_loads(data: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def calculate_engagement_score(likes: int, retweets: int, replies: int, quotes: int) -> float:
    """Calculate engagement score for a tweet"""
    # Weighted engagement score
    return (likes * 1.0) + (retweets * 2.0) + (replies * 3.0) + (quotes * 2.5)

def is_high_engagement_tweet(likes: int, retweets: int, replies: int, quotes: int, threshold: int = 1000) -> bool:
    """Check if tweet has high engagement"""
    engagement_score = calculate_engagement_score(likes, retweets, replies, quotes)
    return engagement_score >= threshold 