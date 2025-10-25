"""
Twitter Tasks
Celery tasks for processing Twitter webhooks and analyzing tweets
"""

import os
from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.database import engine, get_db, create_tables
from models.models import Tweet, Entity, TwitterWebhook
from services.twitter_webhook_service import TwitterWebhookService
from services.sentiment_analyzer import SentimentAnalyzer
from services.relevance_scorer import RelevanceScorer
from dotenv import load_dotenv

load_dotenv()

# Initialize services
twitter_service = TwitterWebhookService()
sentiment_analyzer = SentimentAnalyzer()
relevance_scorer = RelevanceScorer()

@shared_task(bind=True)
def process_twitter_webhook(self, webhook_payload: dict):
    """
    Process incoming Twitter webhook payload
    
    Args:
        webhook_payload (dict): Raw webhook payload from twitterapi.io
        
    Returns:
        dict: Processing result
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Processing webhook payload...'})
        
        # Ensure database tables exist
        create_tables()
        
        # Process the webhook payload
        result = twitter_service.process_webhook_payload(webhook_payload)
        
        if result['status'] == 'success':
            # Schedule tweet analysis as a separate task
            analyze_tweet.delay(result['tweet_id'])
            
            self.update_state(state='SUCCESS', meta=result)
            return result
        else:
            self.update_state(state='FAILURE', meta=result)
            return result
            
    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        self.update_state(state='FAILURE', meta=error_result)
        raise e

@shared_task(bind=True)
def analyze_tweet(self, tweet_id: str):
    """
    Analyze a tweet for sentiment and relevance
    
    Args:
        tweet_id (str): ID of the tweet to analyze
        
    Returns:
        dict: Analysis results
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Analyzing tweet...'})
        
        # Ensure database tables exist
        create_tables()
        
        # Analyze the tweet
        result = twitter_service.analyze_tweet(tweet_id)
        
        if 'error' not in result:
            self.update_state(state='SUCCESS', meta=result)
            return result
        else:
            self.update_state(state='FAILURE', meta=result)
            return result
            
    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'error': str(e),
            'tweet_id': tweet_id,
            'timestamp': datetime.now().isoformat()
        }
        self.update_state(state='FAILURE', meta=error_result)
        raise e

@shared_task(bind=True)
def create_twitter_webhook(self, target_username: str, target_user_id: str, events: list = None):
    """
    Create a Twitter webhook subscription
    
    Args:
        target_username (str): Twitter username to follow
        target_user_id (str): Twitter user ID
        events (list): List of events to listen for
        
    Returns:
        dict: Webhook creation result
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Creating webhook subscription...'})
        
        # Ensure database tables exist
        create_tables()
        
        # Create the webhook
        result = twitter_service.create_webhook(target_username, target_user_id, events)
        
        if result['status'] == 'success':
            self.update_state(state='SUCCESS', meta=result)
            return result
        else:
            self.update_state(state='FAILURE', meta=result)
            return result
            
    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'error': str(e),
            'target_username': target_username,
            'timestamp': datetime.now().isoformat()
        }
        self.update_state(state='FAILURE', meta=error_result)
        raise e

@shared_task(bind=True)
def delete_twitter_webhook(self, webhook_id: str):
    """
    Delete a Twitter webhook subscription
    
    Args:
        webhook_id (str): ID of the webhook to delete
        
    Returns:
        dict: Webhook deletion result
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Deleting webhook subscription...'})
        
        # Ensure database tables exist
        create_tables()
        
        # Delete the webhook
        result = twitter_service.delete_webhook(webhook_id)
        
        if result['status'] == 'success':
            self.update_state(state='SUCCESS', meta=result)
            return result
        else:
            self.update_state(state='FAILURE', meta=result)
            return result
            
    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'error': str(e),
            'webhook_id': webhook_id,
            'timestamp': datetime.now().isoformat()
        }
        self.update_state(state='FAILURE', meta=error_result)
        raise e

@shared_task(bind=True)
def batch_analyze_tweets(self, entity_name: str = None, limit: int = 100):
    """
    Batch analyze tweets for sentiment and relevance
    
    Args:
        entity_name (str, optional): Specific entity to analyze tweets for
        limit (int): Maximum number of tweets to analyze
        
    Returns:
        dict: Batch analysis results
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Starting batch tweet analysis...'})
        
        # Ensure database tables exist
        create_tables()
        
        db = next(get_db())
        
        # Get tweets to analyze
        if entity_name:
            entity = db.query(Entity).filter(Entity.name == entity_name).first()
            if not entity:
                return {'error': f'Entity {entity_name} not found'}
            
            tweets = db.query(Tweet).filter(
                Tweet.entity_id == entity.id,
                Tweet.sentiment_score.is_(None)  # Only analyze unanalyzed tweets
            ).limit(limit).all()
        else:
            tweets = db.query(Tweet).filter(
                Tweet.sentiment_score.is_(None)  # Only analyze unanalyzed tweets
            ).limit(limit).all()
        
        if not tweets:
            return {'message': 'No tweets to analyze', 'count': 0}
        
        # Analyze tweets
        analyzed_count = 0
        failed_count = 0
        
        for i, tweet in enumerate(tweets):
            try:
                # Update progress
                progress = (i + 1) / len(tweets) * 100
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'status': f'Analyzing tweet {i + 1} of {len(tweets)}...',
                        'progress': progress
                    }
                )
                
                # Analyze tweet
                result = twitter_service.analyze_tweet(tweet.tweet_id)
                
                if 'error' not in result:
                    analyzed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                print(f"Error analyzing tweet {tweet.tweet_id}: {e}")
                continue
        
        result = {
            'status': 'SUCCESS',
            'total_tweets': len(tweets),
            'analyzed': analyzed_count,
            'failed': failed_count,
            'timestamp': datetime.now().isoformat()
        }
        
        self.update_state(state='SUCCESS', meta=result)
        return result
        
    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        self.update_state(state='FAILURE', meta=error_result)
        raise e

@shared_task(bind=True)
def cleanup_old_tweets(self, days_old: int = 30):
    """
    Clean up old tweets from the database
    
    Args:
        days_old (int): Remove tweets older than this many days
        
    Returns:
        dict: Cleanup results
    """
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        db = next(get_db())
        deleted_count = db.query(Tweet).filter(
            Tweet.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}

@shared_task(bind=True)
def monitor_webhook_health(self):
    """
    Monitor webhook health and report issues
    
    Returns:
        dict: Health monitoring results
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Monitoring webhook health...'})
        
        # Ensure database tables exist
        create_tables()
        
        db = next(get_db())
        
        # Check for webhooks with high failure counts
        problematic_webhooks = db.query(TwitterWebhook).filter(
            TwitterWebhook.failure_count >= 5
        ).all()
        
        # Check for webhooks with no recent activity
        cutoff_time = datetime.now() - timedelta(hours=24)
        inactive_webhooks = db.query(TwitterWebhook).filter(
            TwitterWebhook.last_activity < cutoff_time,
            TwitterWebhook.is_active == True
        ).all()
        
        health_report = {
            'status': 'SUCCESS',
            'total_webhooks': db.query(TwitterWebhook).count(),
            'active_webhooks': db.query(TwitterWebhook).filter(TwitterWebhook.is_active == True).count(),
            'problematic_webhooks': len(problematic_webhooks),
            'inactive_webhooks': len(inactive_webhooks),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add details for problematic webhooks
        if problematic_webhooks:
            health_report['problematic_details'] = [
                {
                    'username': webhook.target_username,
                    'failure_count': webhook.failure_count,
                    'last_activity': webhook.last_activity.isoformat() if webhook.last_activity else None
                }
                for webhook in problematic_webhooks
            ]
        
        self.update_state(state='SUCCESS', meta=health_report)
        return health_report
        
    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        self.update_state(state='FAILURE', meta=error_result)
        raise e 