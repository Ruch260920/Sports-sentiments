"""
Twitter Webhook Service
Handles webhook management and tweet processing from twitterapi.io
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.database import get_db
from models.models import Tweet, Entity, TwitterWebhook
from services.sentiment_analyzer import SentimentAnalyzer
from services.relevance_scorer import RelevanceScorer
from dotenv import load_dotenv

load_dotenv()

class TwitterWebhookService:
    """Service for managing twitterapi.io webhooks and processing incoming tweets"""
    
    def __init__(self):
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.base_url = "https://api.twitterapi.io"
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL', 'https://your-domain.com')
        
        # Initialize services
        self.sentiment_analyzer = SentimentAnalyzer()
        self.relevance_scorer = RelevanceScorer()
        
        if not self.api_key:
            raise ValueError("TWITTER_API_KEY environment variable is required")
    
    def create_webhook(self, target_username: str, target_user_id: str, events: List[str] = None) -> Dict:
        """
        Create a webhook subscription for a Twitter account
        
        Args:
            target_username (str): Twitter username to follow
            target_user_id (str): Twitter user ID
            events (List[str]): List of events to listen for (default: ['tweet'])
            
        Returns:
            Dict: Webhook creation result
        """
        if events is None:
            events = ['tweet']
        
        try:
            # Create webhook endpoint URL
            webhook_url = f"{self.webhook_base_url}/webhook/twitter/{target_username}"
            
            # Call twitterapi.io webhook creation API
            url = f"{self.base_url}/webhooks/create"
            
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "url": webhook_url,
                "events": events,
                "target_user": target_username,
                "target_user_id": target_user_id
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                webhook_id = data.get('webhook_id')
                
                # Store webhook in database
                db = next(get_db())
                webhook = TwitterWebhook(
                    webhook_id=webhook_id,
                    webhook_url=webhook_url,
                    target_username=target_username,
                    target_user_id=target_user_id,
                    events=events,
                    webhook_metadata=data
                )
                
                db.add(webhook)
                db.commit()
                db.refresh(webhook)
                
                # Update entity to mark as Twitter tracked
                entity = db.query(Entity).filter(
                    Entity.twitter_username == target_username
                ).first()
                
                if entity:
                    entity.is_twitter_tracked = True
                    entity.twitter_user_id = target_user_id
                    db.commit()
                
                return {
                    'status': 'success',
                    'webhook_id': webhook_id,
                    'message': f'Webhook created successfully for @{target_username}'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to create webhook: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error creating webhook: {str(e)}'
            }
    
    def delete_webhook(self, webhook_id: str) -> Dict:
        """
        Delete a webhook subscription
        
        Args:
            webhook_id (str): ID of the webhook to delete
            
        Returns:
            Dict: Deletion result
        """
        try:
            # Call twitterapi.io webhook deletion API
            url = f"{self.base_url}/webhooks/{webhook_id}/delete"
            
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 200:
                # Remove from database
                db = next(get_db())
                webhook = db.query(TwitterWebhook).filter(
                    TwitterWebhook.webhook_id == webhook_id
                ).first()
                
                if webhook:
                    # Update entity to mark as not Twitter tracked
                    entity = db.query(Entity).filter(
                        Entity.twitter_username == webhook.target_username
                    ).first()
                    
                    if entity:
                        entity.is_twitter_tracked = False
                    
                    db.delete(webhook)
                    db.commit()
                
                return {
                    'status': 'success',
                    'message': 'Webhook deleted successfully'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to delete webhook: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error deleting webhook: {str(e)}'
            }
    
    def list_webhooks(self) -> List[Dict]:
        """
        List all active webhook subscriptions
        
        Returns:
            List[Dict]: List of webhook information
        """
        try:
            db = next(get_db())
            webhooks = db.query(TwitterWebhook).filter(TwitterWebhook.is_active == True).all()
            
            return [
                {
                    'id': webhook.id,
                    'webhook_id': webhook.webhook_id,
                    'target_username': webhook.target_username,
                    'target_user_id': webhook.target_user_id,
                    'events': webhook.events,
                    'created_at': webhook.created_at.isoformat(),
                    'last_activity': webhook.last_activity.isoformat() if webhook.last_activity else None,
                    'failure_count': webhook.failure_count
                }
                for webhook in webhooks
            ]
            
        except Exception as e:
            return []
    
    def process_webhook_payload(self, payload: Dict) -> Dict:
        """
        Process incoming webhook payload from twitterapi.io
        
        Args:
            payload (Dict): Raw webhook payload
            
        Returns:
            Dict: Processing result
        """
        try:
            # Extract tweet data from payload
            tweet_data = payload.get('data', {})
            
            if not tweet_data:
                return {'status': 'error', 'message': 'No tweet data in payload'}
            
            # Parse tweet information
            tweet_id = tweet_data.get('id')
            text = tweet_data.get('text', '')
            author_username = tweet_data.get('author_id', {}).get('username', '')
            author_user_id = tweet_data.get('author_id', {}).get('id', '')
            created_at_str = tweet_data.get('created_at')
            
            # Parse created_at timestamp
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            except:
                created_at = datetime.utcnow()
            
            # Extract engagement metrics
            public_metrics = tweet_data.get('public_metrics', {})
            retweet_count = public_metrics.get('retweet_count', 0)
            like_count = public_metrics.get('like_count', 0)
            reply_count = public_metrics.get('reply_count', 0)
            quote_count = public_metrics.get('quote_count', 0)
            
            # Determine tweet type
            referenced_tweets = tweet_data.get('referenced_tweets', [])
            is_retweet = any(ref.get('type') == 'retweeted' for ref in referenced_tweets)
            is_quote = any(ref.get('type') == 'quoted' for ref in referenced_tweets)
            is_reply = any(ref.get('type') == 'replied_to' for ref in referenced_tweets)
            
            # Store tweet in database
            db = next(get_db())
            
            # Check if tweet already exists
            existing_tweet = db.query(Tweet).filter(Tweet.tweet_id == tweet_id).first()
            if existing_tweet:
                return {'status': 'skipped', 'message': 'Tweet already exists'}
            
            # Try to associate with an entity
            entity = db.query(Entity).filter(
                Entity.twitter_username == author_username
            ).first()
            
            # Create tweet record
            tweet = Tweet(
                tweet_id=tweet_id,
                text=text,
                author_username=author_username,
                author_user_id=author_user_id,
                created_at=created_at,
                retweet_count=retweet_count,
                like_count=like_count,
                reply_count=reply_count,
                quote_count=quote_count,
                is_retweet=is_retweet,
                is_quote=is_quote,
                is_reply=is_reply,
                raw_data=payload,
                entity_id=entity.id if entity else None
            )
            
            db.add(tweet)
            db.commit()
            db.refresh(tweet)
            
            # Update webhook last activity
            webhook = db.query(TwitterWebhook).filter(
                TwitterWebhook.target_username == author_username
            ).first()
            
            if webhook:
                webhook.last_activity = datetime.utcnow()
                webhook.failure_count = 0  # Reset failure count on successful processing
                db.commit()
            
            # Return success with tweet info
            return {
                'status': 'success',
                'tweet_id': tweet_id,
                'author_username': author_username,
                'message': 'Tweet processed successfully'
            }
            
        except Exception as e:
            # Update webhook failure count
            try:
                db = next(get_db())
                author_username = payload.get('data', {}).get('author_id', {}).get('username', '')
                if author_username:
                    webhook = db.query(TwitterWebhook).filter(
                        TwitterWebhook.target_username == author_username
                    ).first()
                    
                    if webhook:
                        webhook.failure_count += 1
                        db.commit()
            except:
                pass
            
            return {
                'status': 'error',
                'message': f'Error processing tweet: {str(e)}'
            }
    
    def analyze_tweet(self, tweet_id: str) -> Dict:
        """
        Analyze a tweet for sentiment and relevance
        
        Args:
            tweet_id (str): ID of the tweet to analyze
            
        Returns:
            Dict: Analysis results
        """
        try:
            db = next(get_db())
            tweet = db.query(Tweet).filter(Tweet.tweet_id == tweet_id).first()
            
            if not tweet:
                return {'error': 'Tweet not found'}
            
            # Analyze sentiment
            sentiment_result = self.sentiment_analyzer.analyze_article(
                tweet.text,  # Use tweet text as content
                "",          # No summary for tweets
                tweet.text   # Use tweet text as content
            )
            
            # Calculate relevance score (if entity exists)
            relevance_score = None
            if tweet.entity:
                relevance_score = self.relevance_scorer.calculate_relevance_score(
                    tweet.text,
                    "",
                    tweet.text,
                    tweet.entity.name
                )
            
            # Update tweet with analysis results
            tweet.sentiment_score = sentiment_result['sentiment_score']
            tweet.sentiment_label = sentiment_result['sentiment_label']
            tweet.relevance_score = relevance_score
            
            db.commit()
            
            return {
                'tweet_id': tweet_id,
                'sentiment_score': sentiment_result['sentiment_score'],
                'sentiment_label': sentiment_result['sentiment_label'],
                'relevance_score': relevance_score
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_tweets_for_entity(self, entity_name: str, limit: int = 50) -> List[Dict]:
        """
        Get tweets for a specific entity
        
        Args:
            entity_name (str): Name of the entity
            limit (int): Maximum number of tweets to return
            
        Returns:
            List[Dict]: List of tweets
        """
        try:
            db = next(get_db())
            entity = db.query(Entity).filter(Entity.name == entity_name).first()
            
            if not entity:
                return []
            
            tweets = db.query(Tweet).filter(
                Tweet.entity_id == entity.id
            ).order_by(Tweet.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': tweet.id,
                    'tweet_id': tweet.tweet_id,
                    'text': tweet.text,
                    'author_username': tweet.author_username,
                    'created_at': tweet.created_at.isoformat(),
                    'sentiment_score': tweet.sentiment_score,
                    'sentiment_label': tweet.sentiment_label,
                    'relevance_score': tweet.relevance_score,
                    'engagement': {
                        'retweets': tweet.retweet_count,
                        'likes': tweet.like_count,
                        'replies': tweet.reply_count,
                        'quotes': tweet.quote_count
                    }
                }
                for tweet in tweets
            ]
            
        except Exception as e:
            return [] 