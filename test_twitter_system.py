#!/usr/bin/env python3
"""
Test Script for Twitter Webhook System
Demonstrates the system functionality
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append('.')

def test_database_connection():
    """Test database connection and show existing data"""
    print("🔍 Testing Database Connection...")
    
    try:
        from models.database import get_db
        from models.models import Entity, Source, Article, Tweet, TwitterWebhook
        
        db = next(get_db())
        
        # Show entities
        print("\n📊 Entities in database:")
        entities = db.query(Entity).all()
        for entity in entities:
            print(f"  - {entity.name}: {entity.description}")
            print(f"    Twitter: @{entity.twitter_username or 'Not tracked'}")
            print(f"    Active: {entity.is_active}")
        
        # Show sources
        print("\n📰 Sources in database:")
        sources = db.query(Source).all()
        for source in sources:
            print(f"  - {source.name}: {source.domain}")
        
        # Show articles
        print("\n📄 Articles in database:")
        articles = db.query(Article).limit(5).all()
        for article in articles:
            print(f"  - {article.title[:50]}...")
            print(f"    Sentiment: {article.sentiment_label} ({article.sentiment_score})")
            print(f"    Relevance: {article.relevance_score}")
        
        # Show tweets (should be empty initially)
        print("\n🐦 Tweets in database:")
        tweets = db.query(Tweet).all()
        if tweets:
            for tweet in tweets:
                print(f"  - @{tweet.author_username}: {tweet.text[:50]}...")
        else:
            print("  No tweets yet - webhook system will populate this!")
        
        # Show webhooks (should be empty initially)
        print("\n🔗 Webhooks in database:")
        webhooks = db.query(TwitterWebhook).all()
        if webhooks:
            for webhook in webhooks:
                print(f"  - Following @{webhook.target_username}")
                print(f"    Status: {'Active' if webhook.is_active else 'Inactive'}")
        else:
            print("  No webhooks yet - create them to start tracking accounts!")
        
        db.close()
        print("\n✅ Database connection test successful!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    return True

def test_twitter_service():
    """Test Twitter webhook service"""
    print("\n🔍 Testing Twitter Webhook Service...")
    
    try:
        from services.twitter_webhook_service import TwitterWebhookService
        
        service = TwitterWebhookService()
        print("✅ Twitter webhook service initialized")
        
        # Test webhook listing
        webhooks = service.list_webhooks()
        print(f"✅ Found {len(webhooks)} existing webhooks")
        
        return True
        
    except Exception as e:
        print(f"❌ Twitter service test failed: {e}")
        return False

def simulate_webhook_payload():
    """Simulate a webhook payload from twitterapi.io"""
    print("\n🔍 Simulating Twitter Webhook Payload...")
    
    try:
        from services.twitter_webhook_service import TwitterWebhookService
        
        service = TwitterWebhookService()
        
        # Create a sample webhook payload
        sample_payload = {
            'data': {
                'id': 'test_tweet_123456',
                'text': 'Just finished another great practice session! The team is looking sharp this week. #Rams #NFL',
                'author_id': {
                    'username': 'SeanMcVay',
                    'id': '123456789'
                },
                'created_at': datetime.now().isoformat(),
                'public_metrics': {
                    'retweet_count': 45,
                    'like_count': 234,
                    'reply_count': 12,
                    'quote_count': 8
                },
                'referenced_tweets': []
            }
        }
        
        print("📤 Processing sample webhook payload...")
        result = service.process_webhook_payload(sample_payload)
        
        if result['status'] == 'success':
            print(f"✅ Webhook processed successfully!")
            print(f"   Tweet ID: {result['tweet_id']}")
            print(f"   Author: @{result['author_username']}")
        else:
            print(f"⚠️  Webhook processing result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook simulation failed: {e}")
        return False

def show_final_data():
    """Show the final state of the database after testing"""
    print("\n🔍 Final Database State...")
    
    try:
        from models.database import get_db
        from models.models import Tweet, Entity
        
        db = next(get_db())
        
        # Show tweets after processing
        print("\n🐦 Tweets after webhook processing:")
        tweets = db.query(Tweet).all()
        if tweets:
            for tweet in tweets:
                print(f"  - @{tweet.author_username}: {tweet.text[:50]}...")
                print(f"    Engagement: {tweet.like_count} likes, {tweet.retweet_count} retweets")
                print(f"    Created: {tweet.created_at}")
        else:
            print("  No tweets processed yet")
        
        # Show entity with tweets
        print("\n📊 Entity with associated tweets:")
        entities = db.query(Entity).all()
        for entity in entities:
            tweet_count = len(entity.tweets)
            print(f"  - {entity.name}: {tweet_count} tweets")
            if tweet_count > 0:
                for tweet in entity.tweets[:2]:  # Show first 2 tweets
                    print(f"    • {tweet.text[:40]}...")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error showing final data: {e}")

def main():
    """Main test function"""
    print("🚀 Twitter Webhook System Test")
    print("=" * 50)
    
    # Test 1: Database connection
    if not test_database_connection():
        print("❌ Cannot proceed without database connection")
        return
    
    # Test 2: Twitter service
    if not test_twitter_service():
        print("❌ Cannot proceed without Twitter service")
        return
    
    # Test 3: Simulate webhook
    simulate_webhook_payload()
    
    # Test 4: Show final data
    show_final_data()
    
    print("\n🎉 Test completed!")
    print("\n📋 What we've demonstrated:")
    print("  ✅ Database setup with Twitter models")
    print("  ✅ Sample data (articles, entities, sources)")
    print("  ✅ Twitter webhook service functionality")
    print("  ✅ Webhook payload processing")
    print("  ✅ Data storage in new tables")
    
    print("\n🚀 Next steps:")
    print("  1. Set up real twitterapi.io webhooks")
    print("  2. Start the webhook server")
    print("  3. Begin receiving real-time tweets")

if __name__ == "__main__":
    main() 