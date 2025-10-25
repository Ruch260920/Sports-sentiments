"""
Twitter Analytics Service
Provides analytics and insights for Twitter data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, and_
from models.database import get_db
from models.models import Tweet, Entity, TwitterWebhook

class TwitterAnalytics:
    """Service for Twitter data analytics"""
    
    def __init__(self):
        pass
    
    def get_tweet_volume_over_time(self, entity_name: str = None, days: int = 30) -> Dict:
        """Get tweet volume over time for an entity or all entities"""
        try:
            db = next(get_db())
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if entity_name:
                # Filter by specific entity
                query = db.query(
                    func.date(Tweet.created_at).label('date'),
                    func.count(Tweet.id).label('count')
                ).join(Entity).filter(
                    Entity.name == entity_name,
                    Tweet.created_at >= cutoff_date
                ).group_by(func.date(Tweet.created_at))
            else:
                # All entities
                query = db.query(
                    func.date(Tweet.created_at).label('date'),
                    func.count(Tweet.id).label('count')
                ).filter(
                    Tweet.created_at >= cutoff_date
                ).group_by(func.date(Tweet.created_at))
            
            results = query.order_by(func.date(Tweet.created_at)).all()
            
            return {
                'entity_name': entity_name,
                'period_days': days,
                'data': [
                    {
                        'date': result.date.isoformat(),
                        'tweet_count': result.count
                    }
                    for result in results
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_sentiment_distribution(self, entity_name: str = None, days: int = 30) -> Dict:
        """Get sentiment distribution for tweets"""
        try:
            db = next(get_db())
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if entity_name:
                query = db.query(
                    Tweet.sentiment_label,
                    func.count(Tweet.id).label('count')
                ).join(Entity).filter(
                    Entity.name == entity_name,
                    Tweet.created_at >= cutoff_date,
                    Tweet.sentiment_label.isnot(None)
                ).group_by(Tweet.sentiment_label)
            else:
                query = db.query(
                    Tweet.sentiment_label,
                    func.count(Tweet.id).label('count')
                ).filter(
                    Tweet.created_at >= cutoff_date,
                    Tweet.sentiment_label.isnot(None)
                ).group_by(Tweet.sentiment_label)
            
            results = query.all()
            
            return {
                'entity_name': entity_name,
                'period_days': days,
                'distribution': [
                    {
                        'sentiment': result.sentiment_label,
                        'count': result.count
                    }
                    for result in results
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_engagement_metrics(self, entity_name: str = None, days: int = 30) -> Dict:
        """Get engagement metrics for tweets"""
        try:
            db = next(get_db())
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if entity_name:
                query = db.query(
                    func.avg(Tweet.retweet_count).label('avg_retweets'),
                    func.avg(Tweet.like_count).label('avg_likes'),
                    func.avg(Tweet.reply_count).label('avg_replies'),
                    func.avg(Tweet.quote_count).label('avg_quotes'),
                    func.sum(Tweet.retweet_count).label('total_retweets'),
                    func.sum(Tweet.like_count).label('total_likes'),
                    func.sum(Tweet.reply_count).label('total_replies'),
                    func.sum(Tweet.quote_count).label('total_quotes')
                ).join(Entity).filter(
                    Entity.name == entity_name,
                    Tweet.created_at >= cutoff_date
                )
            else:
                query = db.query(
                    func.avg(Tweet.retweet_count).label('avg_retweets'),
                    func.avg(Tweet.like_count).label('avg_likes'),
                    func.avg(Tweet.reply_count).label('avg_replies'),
                    func.avg(Tweet.quote_count).label('avg_quotes'),
                    func.sum(Tweet.retweet_count).label('total_retweets'),
                    func.sum(Tweet.like_count).label('total_likes'),
                    func.sum(Tweet.reply_count).label('total_replies'),
                    func.sum(Tweet.quote_count).label('total_quotes')
                ).filter(
                    Tweet.created_at >= cutoff_date
                )
            
            result = query.first()
            
            return {
                'entity_name': entity_name,
                'period_days': days,
                'averages': {
                    'retweets': float(result.avg_retweets or 0),
                    'likes': float(result.avg_likes or 0),
                    'replies': float(result.avg_replies or 0),
                    'quotes': float(result.avg_quotes or 0)
                },
                'totals': {
                    'retweets': int(result.total_retweets or 0),
                    'likes': int(result.total_likes or 0),
                    'replies': int(result.total_replies or 0),
                    'quotes': int(result.total_quotes or 0)
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_webhook_health_summary(self) -> Dict:
        """Get summary of webhook health"""
        try:
            db = next(get_db())
            
            total_webhooks = db.query(TwitterWebhook).count()
            active_webhooks = db.query(TwitterWebhook).filter(TwitterWebhook.is_active == True).count()
            
            # Webhooks with high failure count
            problematic_webhooks = db.query(TwitterWebhook).filter(
                TwitterWebhook.failure_count >= 5
            ).count()
            
            # Inactive webhooks (no activity in 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            inactive_webhooks = db.query(TwitterWebhook).filter(
                and_(
                    TwitterWebhook.last_activity < cutoff_time,
                    TwitterWebhook.is_active == True
                )
            ).count()
            
            return {
                'total_webhooks': total_webhooks,
                'active_webhooks': active_webhooks,
                'problematic_webhooks': problematic_webhooks,
                'inactive_webhooks': inactive_webhooks,
                'health_score': max(0, 100 - (problematic_webhooks * 20) - (inactive_webhooks * 10))
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_top_tweets(self, entity_name: str = None, limit: int = 10, metric: str = 'likes') -> Dict:
        """Get top tweets by engagement metric"""
        try:
            db = next(get_db())
            
            if entity_name:
                query = db.query(Tweet).join(Entity).filter(Entity.name == entity_name)
            else:
                query = db.query(Tweet)
            
            # Order by specified metric
            if metric == 'likes':
                query = query.order_by(Tweet.like_count.desc())
            elif metric == 'retweets':
                query = query.order_by(Tweet.retweet_count.desc())
            elif metric == 'replies':
                query = query.order_by(Tweet.reply_count.desc())
            elif metric == 'quotes':
                query = query.order_by(Tweet.quote_count.desc())
            else:
                query = query.order_by(Tweet.like_count.desc())
            
            tweets = query.limit(limit).all()
            
            return {
                'entity_name': entity_name,
                'metric': metric,
                'tweets': [
                    {
                        'id': tweet.id,
                        'tweet_id': tweet.tweet_id,
                        'text': tweet.text[:100] + "..." if len(tweet.text) > 100 else tweet.text,
                        'author_username': tweet.author_username,
                        'created_at': tweet.created_at.isoformat(),
                        'sentiment_label': tweet.sentiment_label,
                        'engagement': {
                            'likes': tweet.like_count,
                            'retweets': tweet.retweet_count,
                            'replies': tweet.reply_count,
                            'quotes': tweet.quote_count
                        }
                    }
                    for tweet in tweets
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}

# Example usage
if __name__ == "__main__":
    analytics = TwitterAnalytics()
    
    # Get analytics for Sean McVay
    print("🏈 Sean McVay Twitter Analytics:")
    print(analytics.get_tweet_volume_over_time("Sean McVay", 7))
    print(analytics.get_sentiment_distribution("Sean McVay", 7))
    print(analytics.get_engagement_metrics("Sean McVay", 7))
    
    # Get webhook health
    print("\n🔗 Webhook Health:")
    print(analytics.get_webhook_health_summary()) 