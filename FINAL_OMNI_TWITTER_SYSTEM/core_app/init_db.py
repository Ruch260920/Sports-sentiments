#!/usr/bin/env python3
"""
Database initialization script for Sean McVay News Scraping Pipeline
"""

import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from models.database import engine, SessionLocal
from models.models import Base, Entity, Source, Article

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

def add_sample_data():
    """Add sample data to the database"""
    print("Adding sample data...")
    
    db = SessionLocal()
    
    try:
        # Add sample entity
        entity = Entity(
            name="Sean McVay",
            description="Head coach of the Los Angeles Rams",
            is_active=True
        )
        db.add(entity)
        db.flush()  # Get the ID
        
        # Add sample sources
        sources = [
            Source(name="ESPN", domain="espn.com", url="https://www.espn.com", is_verified=True),
            Source(name="NFL.com", domain="nfl.com", url="https://www.nfl.com", is_verified=True),
            Source(name="Los Angeles Times", domain="latimes.com", url="https://www.latimes.com", is_verified=True),
            Source(name="The Athletic", domain="theathletic.com", url="https://www.theathletic.com", is_verified=True)
        ]
        
        for source in sources:
            db.add(source)
        db.flush()
        
        # Add sample articles
        sample_articles = [
            {
                "title": "Sean McVay leads Rams to Super Bowl victory",
                "summary": "The Los Angeles Rams head coach has proven his leadership abilities once again.",
                "url": "https://example.com/article1",
                "content": "Full article content here...",
                "published_date": datetime.now() - timedelta(days=1),
                "entity_id": entity.id,
                "source_id": sources[0].id,
                "relevance_score": 0.95,
                "sentiment_score": 0.8,
                "sentiment_label": "positive"
            },
            {
                "title": "McVay's innovative play-calling continues to impress",
                "summary": "Analysts praise the young coach's strategic approach to the game.",
                "url": "https://example.com/article2",
                "content": "Full article content here...",
                "published_date": datetime.now() - timedelta(days=2),
                "entity_id": entity.id,
                "source_id": sources[1].id,
                "relevance_score": 0.88,
                "sentiment_score": 0.7,
                "sentiment_label": "positive"
            },
            {
                "title": "Rams face challenges in upcoming season",
                "summary": "The team will need to overcome several obstacles to repeat their success.",
                "url": "https://example.com/article3",
                "content": "Full article content here...",
                "published_date": datetime.now() - timedelta(days=3),
                "entity_id": entity.id,
                "source_id": sources[2].id,
                "relevance_score": 0.92,
                "sentiment_score": -0.3,
                "sentiment_label": "negative"
            },
            {
                "title": "McVay discusses team strategy for next season",
                "summary": "The coach shares insights into his planning process and team development.",
                "url": "https://example.com/article4",
                "content": "Full article content here...",
                "published_date": datetime.now() - timedelta(days=4),
                "entity_id": entity.id,
                "source_id": sources[3].id,
                "relevance_score": 0.85,
                "sentiment_score": 0.2,
                "sentiment_label": "neutral"
            }
        ]
        
        for article_data in sample_articles:
            article = Article(**article_data)
            db.add(article)
        
        db.commit()
        print("✅ Sample data added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 Initializing database for Sean McVay News Dashboard...")
    
    # Create tables
    create_tables()
    
    # Add sample data
    add_sample_data()
    
    print("🎉 Database initialization complete!")
    print("You can now run the Streamlit dashboard with: streamlit run dashboard_streamlit.py")

if __name__ == "__main__":
    main() 