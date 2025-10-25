#!/usr/bin/env python3
"""
Main entry point for the Sean McVay News Scraping Pipeline

This script provides various commands to test and run the pipeline:
- setup: Initialize database and create tables
- scrape: Run a one-time scraping job
- worker: Start Celery worker
- beat: Start Celery beat scheduler
- dashboard: Start the Flask dashboard
- test: Run tests for all components
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Initialize database and create tables"""
    print("Setting up database...")
    
    try:
        from models.database import create_tables
        from models.models import Entity, Source
        from models.database import SessionLocal
        
        # Create tables
        create_tables()
        print("✓ Database tables created successfully")
        
        # Add initial data
        db = SessionLocal()
        try:
            # Add Sean McVay entity
            entity = db.query(Entity).filter(Entity.name == "Sean McVay").first()
            if not entity:
                entity = Entity(
                    name="Sean McVay",
                    description="Head coach of the Los Angeles Rams",
                    is_active=True
                )
                db.add(entity)
                print("✓ Added Sean McVay entity")
            
            # Add some common sources
            sources = [
                {"name": "ESPN", "domain": "espn.com", "url": "https://www.espn.com"},
                {"name": "NFL.com", "domain": "nfl.com", "url": "https://www.nfl.com"},
                {"name": "Sports Illustrated", "domain": "si.com", "url": "https://www.si.com"},
                {"name": "Bleacher Report", "domain": "bleacherreport.com", "url": "https://bleacherreport.com"},
                {"name": "NBC Sports", "domain": "nbcsports.com", "url": "https://www.nbcsports.com"}
            ]
            
            for source_data in sources:
                source = db.query(Source).filter(Source.name == source_data["name"]).first()
                if not source:
                    source = Source(**source_data, is_verified=True)
                    db.add(source)
                    print(f"✓ Added {source_data['name']} source")
            
            db.commit()
            print("✓ Database setup completed successfully")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"✗ Error setting up database: {e}")
        sys.exit(1)

def run_scraping():
    """Run a one-time scraping job"""
    print("Running scraping job...")
    
    try:
        from tasks.scraping_tasks import scrape_entity_articles
        
        # Run scraping task
        result = scrape_entity_articles.delay("Sean McVay", max_articles=20, days_back=7)
        
        print(f"✓ Scraping task started with ID: {result.id}")
        print("Check the dashboard or logs for progress updates")
        
    except Exception as e:
        print(f"✗ Error running scraping job: {e}")
        sys.exit(1)

def start_worker():
    """Start Celery worker"""
    print("Starting Celery worker...")
    
    try:
        import subprocess
        import sys
        
        # Start worker with proper configuration
        cmd = [
            sys.executable, "-m", "celery", "worker",
            "--app=tasks.celery_app:celery_app",
            "--loglevel=info",
            "--concurrency=2",
            "--queues=scraping,analysis"
        ]
        
        print("Starting worker with command:", " ".join(cmd))
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\nWorker stopped by user")
    except Exception as e:
        print(f"✗ Error starting worker: {e}")
        sys.exit(1)

def start_beat():
    """Start Celery beat scheduler"""
    print("Starting Celery beat scheduler...")
    
    try:
        import subprocess
        import sys
        
        # Start beat scheduler
        cmd = [
            sys.executable, "-m", "celery", "beat",
            "--app=tasks.celery_app:celery_app",
            "--loglevel=info",
            "--schedule=/tmp/celerybeat-schedule",
            "--pidfile=/tmp/celerybeat.pid"
        ]
        
        print("Starting beat scheduler with command:", " ".join(cmd))
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\nBeat scheduler stopped by user")
    except Exception as e:
        print(f"✗ Error starting beat scheduler: {e}")
        sys.exit(1)

def start_dashboard():
    """Start the Flask dashboard"""
    print("Starting Flask dashboard...")
    
    try:
        from dashboard.app import create_app
        
        app = create_app()
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"✗ Error starting Flask dashboard: {e}")
        sys.exit(1)

def start_streamlit_dashboard():
    """Start the Streamlit dashboard"""
    print("Starting Streamlit dashboard...")
    
    try:
        import subprocess
        import sys
        
        # Start Streamlit dashboard
        cmd = [
            sys.executable, "-m", "streamlit", "run", "dashboard_streamlit.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ]
        
        print("Starting Streamlit dashboard with command:", " ".join(cmd))
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\nStreamlit dashboard stopped by user")
    except Exception as e:
        print(f"✗ Error starting Streamlit dashboard: {e}")
        sys.exit(1)

def run_tests():
    """Run tests for all components"""
    print("Running tests...")
    
    try:
        # Test database connection
        from models.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✓ Database connection test passed")
        
        # Test sentiment analyzer
        from services.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_sentiment("Sean McVay is a great coach!")
        print(f"✓ Sentiment analyzer test passed: {result}")
        
        # Test relevance scorer
        from services.relevance_scorer import RelevanceScorer
        scorer = RelevanceScorer()
        score = scorer.calculate_relevance_score("Sean McVay leads Rams to victory", entity_name="Sean McVay")
        print(f"✓ Relevance scorer test passed: {score}")
        
        # Test scraper
        from scraper.news_scraper import NewsScraper
        scraper = NewsScraper()
        print("✓ News scraper initialized successfully")
        
        # Test Bing scraper
        from scraper.bing_scraper import BingScraper
        bing_scraper = BingScraper()
        print("✓ Bing scraper initialized successfully")
        
        print("✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)

def show_status():
    """Show current system status"""
    print("System Status:")
    print("=" * 50)
    
    try:
        from models.database import SessionLocal
        from models.models import Entity, Article, Source
        
        db = SessionLocal()
        
        # Count entities
        entity_count = db.query(Entity).count()
        print(f"Entities: {entity_count}")
        
        # Count articles
        article_count = db.query(Article).count()
        print(f"Articles: {article_count}")
        
        # Count sources
        source_count = db.query(Source).count()
        print(f"Sources: {source_count}")
        
        # Recent articles
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        recent_count = db.query(Article).filter(Article.scraped_date >= week_ago).count()
        print(f"Recent articles (7 days): {recent_count}")
        
        # Sentiment distribution
        sentiment_stats = db.query(Article.sentiment_label).filter(
            Article.sentiment_label.isnot(None)
        ).all()
        
        sentiment_counts = {}
        for label in sentiment_stats:
            label = label[0] if label[0] else 'neutral'
            sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
        
        print("Sentiment distribution:")
        for sentiment, count in sentiment_counts.items():
            print(f"  {sentiment}: {count}")
        
        db.close()
        
    except Exception as e:
        print(f"✗ Error getting status: {e}")

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description="Sean McVay News Scraping Pipeline")
    parser.add_argument('command', choices=['setup', 'scrape', 'worker', 'beat', 'dashboard', 'streamlit', 'test', 'status'],
                       help='Command to run')
    
    args = parser.parse_args()
    
    print("Sean McVay News Scraping Pipeline")
    print("=" * 50)
    
    if args.command == 'setup':
        setup_database()
    elif args.command == 'scrape':
        run_scraping()
    elif args.command == 'worker':
        start_worker()
    elif args.command == 'beat':
        start_beat()
    elif args.command == 'dashboard':
        start_dashboard()
    elif args.command == 'streamlit':
        start_streamlit_dashboard()
    elif args.command == 'test':
        run_tests()
    elif args.command == 'status':
        show_status()

if __name__ == "__main__":
    main() 