#!/usr/bin/env python3
"""
Simple Webhook Test
Demonstrates webhook processing without full server
"""

import sys
import os
sys.path.append('.')

from services.twitter_webhook_service import TwitterWebhookService
from datetime import datetime

def test_webhook_processing():
    """Test webhook processing with multiple sample tweets"""
    print("🚀 Testing Webhook Processing with Multiple Tweets")
    print("=" * 60)
    
    service = TwitterWebhookService()
    
    # Sample webhook payloads
    sample_payloads = [
        {
            'data': {
                'id': 'tweet_001',
                'text': 'Great win today! The team showed incredible resilience. #Rams #Victory',
                'author_id': {'username': 'SeanMcVay', 'id': '123456789'},
                'created_at': datetime.now().isoformat(),
                'public_metrics': {'retweet_count': 67, 'like_count': 456, 'reply_count': 23, 'quote_count': 12},
                'referenced_tweets': []
            }
        },
        {
            'data': {
                'id': 'tweet_002',
                'text': 'Practice was intense today. Players are really stepping up their game! 💪',
                'author_id': {'username': 'SeanMcVay', 'id': '123456789'},
                'created_at': datetime.now().isoformat(),
                'public_metrics': {'retweet_count': 34, 'like_count': 289, 'reply_count': 15, 'quote_count': 8},
                'referenced_tweets': []
            }
        },
        {
            'data': {
                'id': 'tweet_003',
                'text': 'Excited about the upcoming season! Lots of hard work ahead. #NFL #Rams',
                'author_id': {'username': 'SeanMcVay', 'id': '123456789'},
                'created_at': datetime.now().isoformat(),
                'public_metrics': {'retweet_count': 89, 'like_count': 567, 'reply_count': 34, 'quote_count': 19},
                'referenced_tweets': []
            }
        }
    ]
    
    print("📤 Processing webhook payloads...")
    
    for i, payload in enumerate(sample_payloads, 1):
        print(f"\n🔗 Processing Tweet {i}:")
        print(f"   Text: {payload['data']['text'][:50]}...")
        print(f"   Author: @{payload['data']['author_id']['username']}")
        
        result = service.process_webhook_payload(payload)
        
        if result['status'] == 'success':
            print(f"   ✅ Status: {result['status']}")
            print(f"   📝 Tweet ID: {result['tweet_id']}")
        else:
            print(f"   ❌ Status: {result['status']}")
            print(f"   ⚠️  Message: {result.get('message', 'Unknown error')}")
    
    print("\n🎉 Webhook processing test completed!")

def show_database_state():
    """Show the current state of the database"""
    print("\n📊 Current Database State")
    print("=" * 40)
    
    try:
        from models.database import get_db
        from models.models import Tweet, Entity
        
        db = next(get_db())
        
        # Count tweets
        tweet_count = db.query(Tweet).count()
        print(f"🐦 Total Tweets: {tweet_count}")
        
        # Show all tweets
        tweets = db.query(Tweet).order_by(Tweet.created_at.desc()).all()
        for tweet in tweets:
            print(f"\n📱 Tweet {tweet.id}:")
            print(f"   ID: {tweet.tweet_id}")
            print(f"   Author: @{tweet.author_username}")
            print(f"   Text: {tweet.text[:60]}...")
            print(f"   Engagement: {tweet.like_count} likes, {tweet.retweet_count} retweets")
            print(f"   Created: {tweet.created_at}")
            print(f"   Received: {tweet.received_at}")
        
        # Show entity stats
        entities = db.query(Entity).all()
        for entity in entities:
            tweet_count = len(entity.tweets)
            print(f"\n🏈 {entity.name}:")
            print(f"   Total Tweets: {tweet_count}")
            print(f"   Twitter: @{entity.twitter_username or 'Not tracked'}")
            print(f"   Active: {entity.is_active}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error showing database state: {e}")

if __name__ == "__main__":
    test_webhook_processing()
    show_database_state() 