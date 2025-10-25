"""
Configuration Management
Centralized configuration for the OMNI News Pipeline
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/omni_news')
    
    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Twitter API
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'http://localhost:5001')
    
    # Application
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 5001))
    
    # Celery Settings
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_ACKS_LATE = True
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_RESULT_EXPIRES = 3600
    
    # Scraping Settings
    SCRAPING_INTERVAL_HOURS = int(os.getenv('SCRAPING_INTERVAL_HOURS', 6))
    MAX_ARTICLES_PER_ENTITY = int(os.getenv('MAX_ARTICLES_PER_ENTITY', 50))
    
    # Twitter Settings
    TWITTER_WEBHOOK_EVENTS = ['tweet']  # Default events to listen for
    TWITTER_ANALYSIS_BATCH_SIZE = int(os.getenv('TWITTER_ANALYSIS_BATCH_SIZE', 100))
    TWITTER_CLEANUP_DAYS = int(os.getenv('TWITTER_CLEANUP_DAYS', 30))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = ['TWITTER_API_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        return True

# Global config instance
config = Config() 