"""
Celery Tasks Package
Contains all task definitions for the OMNI News Pipeline
"""

from .scraping_tasks import (
    scrape_entity_articles,
    analyze_article,
    cleanup_old_articles,
    update_entity_status
)

from .twitter_tasks import (
    process_twitter_webhook,
    analyze_tweet,
    create_twitter_webhook,
    delete_twitter_webhook,
    batch_analyze_tweets,
    cleanup_old_tweets,
    monitor_webhook_health
)

__all__ = [
    # Scraping tasks
    'scrape_entity_articles',
    'analyze_article',
    'cleanup_old_articles',
    'update_entity_status',
    
    # Twitter tasks
    'process_twitter_webhook',
    'analyze_tweet',
    'create_twitter_webhook',
    'delete_twitter_webhook',
    'batch_analyze_tweets',
    'cleanup_old_tweets',
    'monitor_webhook_health'
] 