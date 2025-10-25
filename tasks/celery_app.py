import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'news_scraper',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['tasks.scraping_tasks', 'tasks.twitter_tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Time settings
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'tasks.scraping_tasks.scrape_entity_articles': {'queue': 'scraping'},
        'tasks.scraping_tasks.analyze_article': {'queue': 'analysis'},
        'tasks.twitter_tasks.process_twitter_webhook': {'queue': 'twitter'},
        'tasks.twitter_tasks.analyze_tweet': {'queue': 'analysis'},
        'tasks.twitter_tasks.create_twitter_webhook': {'queue': 'twitter'},
        'tasks.twitter_tasks.delete_twitter_webhook': {'queue': 'twitter'},
        'tasks.twitter_tasks.batch_analyze_tweets': {'queue': 'analysis'},
        'tasks.twitter_tasks.cleanup_old_tweets': {'queue': 'maintenance'},
        'tasks.twitter_tasks.monitor_webhook_health': {'queue': 'monitoring'},
    },
    
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        'scrape-sean-mcvay-articles': {
            'task': 'tasks.scraping_tasks.scrape_entity_articles',
            'schedule': int(os.getenv('SCRAPING_INTERVAL_HOURS', 6)) * 3600,  # Convert hours to seconds
            'args': ('Sean McVay',),
            'kwargs': {
                'max_articles': int(os.getenv('MAX_ARTICLES_PER_ENTITY', 50)),
                'days_back': 7
            }
        },
        'monitor-twitter-webhooks': {
            'task': 'tasks.twitter_tasks.monitor_webhook_health',
            'schedule': 3600,  # Every hour
        },
        'cleanup-old-tweets': {
            'task': 'tasks.twitter_tasks.cleanup_old_tweets',
            'schedule': 86400,  # Every 24 hours
            'kwargs': {'days_old': 30}
        },
    }
)

if __name__ == '__main__':
    celery_app.start() 