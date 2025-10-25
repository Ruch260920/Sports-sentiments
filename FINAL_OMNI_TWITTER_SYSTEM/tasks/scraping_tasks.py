import os
from celery import shared_task
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from models.database import engine, get_db, create_tables
from models.models import Entity, Article, Source
from scraper.news_scraper import NewsScraper
from scraper.bing_scraper import BingScraper
from services.sentiment_analyzer import SentimentAnalyzer
from services.relevance_scorer import RelevanceScorer
from services.utilities import clean_text, extract_domain, normalize_source_name
from dotenv import load_dotenv

load_dotenv()

# Initialize services
sentiment_analyzer = SentimentAnalyzer()
relevance_scorer = RelevanceScorer()
news_scraper = NewsScraper()
bing_scraper = BingScraper()

@shared_task(bind=True)
def scrape_entity_articles(self, entity_name: str, max_articles: int = 50, days_back: int = 7):
    """
    Scrape articles for a specific entity
    
    Args:
        entity_name (str): Name of the entity to scrape articles for
        max_articles (int): Maximum number of articles to scrape
        days_back (int): Number of days back to search
        
    Returns:
        dict: Summary of scraping results
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Starting scraping process...'})
        
        # Ensure database tables exist
        create_tables()
        
        # Get or create entity
        db = next(get_db())
        entity = db.query(Entity).filter(Entity.name == entity_name).first()
        
        if not entity:
            entity = Entity(
                name=entity_name,
                description=f"News articles about {entity_name}",
                is_active=True
            )
            db.add(entity)
            db.commit()
            db.refresh(entity)
        
        # Scrape articles using multiple methods
        articles = []
        
        # Method 1: Bing News API (if available)
        self.update_state(state='PROGRESS', meta={'status': 'Searching Bing News...'})
        bing_articles = bing_scraper.search_entity_news(entity_name, days_back)
        articles.extend(bing_articles)
        
        # Method 2: Direct web scraping
        self.update_state(state='PROGRESS', meta={'status': 'Scraping news sources...'})
        scraped_articles = news_scraper.scrape_articles(entity_name, max_articles, days_back)
        articles.extend(scraped_articles)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        articles = unique_articles[:max_articles]
        
        # Process and store articles
        processed_count = 0
        skipped_count = 0
        
        for article_data in articles:
            try:
                # Check if article already exists
                existing_article = db.query(Article).filter(Article.url == article_data['url']).first()
                if existing_article:
                    skipped_count += 1
                    continue
                
                # Get or create source
                source_name = normalize_source_name(article_data.get('source_name', 'Unknown'))
                source = db.query(Source).filter(Source.name == source_name).first()
                
                if not source:
                    source = Source(
                        name=source_name,
                        domain=article_data.get('domain', ''),
                        url=article_data.get('url', ''),
                        is_verified=False
                    )
                    db.add(source)
                    db.commit()
                    db.refresh(source)
                
                # Analyze sentiment
                sentiment_result = sentiment_analyzer.analyze_article(
                    article_data.get('title', ''),
                    article_data.get('summary', ''),
                    article_data.get('content', '')
                )
                
                # Calculate relevance score
                relevance_score = relevance_scorer.calculate_relevance_score(
                    article_data.get('title', ''),
                    article_data.get('summary', ''),
                    article_data.get('content', ''),
                    entity_name
                )
                
                # Check if article is relevant enough
                if not relevance_scorer.is_relevant(
                    article_data.get('title', ''),
                    article_data.get('summary', ''),
                    article_data.get('content', ''),
                    entity_name
                ):
                    skipped_count += 1
                    continue
                
                # Create article record
                article = Article(
                    title=clean_text(article_data.get('title', '')),
                    summary=clean_text(article_data.get('summary', '')),
                    url=article_data['url'],
                    content=clean_text(article_data.get('content', '')),
                    published_date=article_data.get('published_date'),
                    entity_id=entity.id,
                    source_id=source.id,
                    relevance_score=relevance_score,
                    sentiment_score=sentiment_result['sentiment_score'],
                    sentiment_label=sentiment_result['sentiment_label']
                )
                
                db.add(article)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing article {article_data.get('url', 'unknown')}: {e}")
                skipped_count += 1
                continue
        
        # Commit all changes
        db.commit()
        
        result = {
            'status': 'SUCCESS',
            'entity_name': entity_name,
            'total_found': len(articles),
            'processed': processed_count,
            'skipped': skipped_count,
            'timestamp': datetime.now().isoformat()
        }
        
        self.update_state(state='SUCCESS', meta=result)
        return result
        
    except Exception as e:
        error_result = {
            'status': 'FAILURE',
            'error': str(e),
            'entity_name': entity_name,
            'timestamp': datetime.now().isoformat()
        }
        self.update_state(state='FAILURE', meta=error_result)
        raise e

@shared_task
def analyze_article(article_id: int):
    """
    Analyze a single article for sentiment and relevance
    
    Args:
        article_id (int): ID of the article to analyze
        
    Returns:
        dict: Analysis results
    """
    try:
        db = next(get_db())
        article = db.query(Article).filter(Article.id == article_id).first()
        
        if not article:
            return {'error': 'Article not found'}
        
        # Re-analyze sentiment
        sentiment_result = sentiment_analyzer.analyze_article(
            article.title,
            article.summary,
            article.content
        )
        
        # Re-calculate relevance score
        relevance_score = relevance_scorer.calculate_relevance_score(
            article.title,
            article.summary,
            article.content,
            article.entity.name
        )
        
        # Update article
        article.sentiment_score = sentiment_result['sentiment_score']
        article.sentiment_label = sentiment_result['sentiment_label']
        article.relevance_score = relevance_score
        
        db.commit()
        
        return {
            'article_id': article_id,
            'sentiment_score': sentiment_result['sentiment_score'],
            'sentiment_label': sentiment_result['sentiment_label'],
            'relevance_score': relevance_score
        }
        
    except Exception as e:
        return {'error': str(e)}

@shared_task
def cleanup_old_articles(days_old: int = 30):
    """
    Clean up old articles from the database
    
    Args:
        days_old (int): Remove articles older than this many days
        
    Returns:
        dict: Cleanup results
    """
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        db = next(get_db())
        deleted_count = db.query(Article).filter(
            Article.scraped_date < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}

@shared_task
def update_entity_status(entity_id: int, is_active: bool):
    """
    Update entity active status
    
    Args:
        entity_id (int): ID of the entity to update
        is_active (bool): New active status
        
    Returns:
        dict: Update results
    """
    try:
        db = next(get_db())
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        
        if not entity:
            return {'error': 'Entity not found'}
        
        entity.is_active = is_active
        db.commit()
        
        return {
            'entity_id': entity_id,
            'entity_name': entity.name,
            'is_active': is_active
        }
        
    except Exception as e:
        return {'error': str(e)} 