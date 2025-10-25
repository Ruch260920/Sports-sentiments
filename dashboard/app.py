from flask import Flask, render_template, jsonify, request
from sqlalchemy.orm import sessionmaker
from models.database import engine, get_db
from models.models import Entity, Article, Source
from services.sentiment_analyzer import SentimentAnalyzer
from services.relevance_scorer import RelevanceScorer
import pandas as pd
from datetime import datetime, timedelta
import json

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Initialize services
    sentiment_analyzer = SentimentAnalyzer()
    relevance_scorer = RelevanceScorer()
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('index.html')
    
    @app.route('/api/stats')
    def get_stats():
        """Get overall statistics"""
        try:
            db = next(get_db())
            
            # Get basic counts
            total_articles = db.query(Article).count()
            total_sources = db.query(Source).count()
            total_entities = db.query(Entity).count()
            
            # Get recent articles (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_articles = db.query(Article).filter(
                Article.scraped_date >= week_ago
            ).count()
            
            # Get sentiment distribution
            sentiment_stats = db.query(Article.sentiment_label).filter(
                Article.sentiment_label.isnot(None)
            ).all()
            
            sentiment_counts = {}
            for label in sentiment_stats:
                label = label[0] if label[0] else 'neutral'
                sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
            
            return jsonify({
                'total_articles': total_articles,
                'total_sources': total_sources,
                'total_entities': total_entities,
                'recent_articles': recent_articles,
                'sentiment_distribution': sentiment_counts
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/articles')
    def get_articles():
        """Get articles with pagination and filtering"""
        try:
            db = next(get_db())
            
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            sentiment = request.args.get('sentiment')
            source = request.args.get('source')
            entity = request.args.get('entity')
            
            # Build query
            query = db.query(Article).join(Source).join(Entity)
            
            if sentiment:
                query = query.filter(Article.sentiment_label == sentiment)
            if source:
                query = query.filter(Source.name == source)
            if entity:
                query = query.filter(Entity.name == entity)
            
            # Order by scraped date (newest first)
            query = query.order_by(Article.scraped_date.desc())
            
            # Paginate
            articles = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Convert to JSON
            articles_data = []
            for article in articles:
                articles_data.append({
                    'id': article.id,
                    'title': article.title,
                    'summary': article.summary,
                    'url': article.url,
                    'published_date': article.published_date.isoformat() if article.published_date else None,
                    'scraped_date': article.scraped_date.isoformat(),
                    'relevance_score': article.relevance_score,
                    'sentiment_score': article.sentiment_score,
                    'sentiment_label': article.sentiment_label,
                    'source': {
                        'name': article.source.name,
                        'domain': article.source.domain
                    },
                    'entity': {
                        'name': article.entity.name
                    }
                })
            
            return jsonify({
                'articles': articles_data,
                'page': page,
                'per_page': per_page,
                'total': query.count()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sources')
    def get_sources():
        """Get all sources with article counts"""
        try:
            db = next(get_db())
            
            sources = db.query(Source).all()
            sources_data = []
            
            for source in sources:
                article_count = db.query(Article).filter(
                    Article.source_id == source.id
                ).count()
                
                sources_data.append({
                    'id': source.id,
                    'name': source.name,
                    'domain': source.domain,
                    'url': source.url,
                    'article_count': article_count,
                    'is_verified': source.is_verified
                })
            
            return jsonify(sources_data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/entities')
    def get_entities():
        """Get all entities with article counts"""
        try:
            db = next(get_db())
            
            entities = db.query(Entity).all()
            entities_data = []
            
            for entity in entities:
                article_count = db.query(Article).filter(
                    Article.entity_id == entity.id
                ).count()
                
                entities_data.append({
                    'id': entity.id,
                    'name': entity.name,
                    'description': entity.description,
                    'article_count': article_count,
                    'is_active': entity.is_active
                })
            
            return jsonify(entities_data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/charts/sentiment-timeline')
    def get_sentiment_timeline():
        """Get sentiment data over time"""
        try:
            db = next(get_db())
            
            # Get articles from last 30 days
            month_ago = datetime.now() - timedelta(days=30)
            articles = db.query(Article).filter(
                Article.scraped_date >= month_ago,
                Article.sentiment_label.isnot(None)
            ).order_by(Article.scraped_date).all()
            
            # Group by date and sentiment
            timeline_data = {}
            for article in articles:
                date = article.scraped_date.strftime('%Y-%m-%d')
                sentiment = article.sentiment_label or 'neutral'
                
                if date not in timeline_data:
                    timeline_data[date] = {'positive': 0, 'negative': 0, 'neutral': 0}
                
                timeline_data[date][sentiment] += 1
            
            # Convert to chart format
            dates = sorted(timeline_data.keys())
            positive_data = [timeline_data[date]['positive'] for date in dates]
            negative_data = [timeline_data[date]['negative'] for date in dates]
            neutral_data = [timeline_data[date]['neutral'] for date in dates]
            
            return jsonify({
                'dates': dates,
                'positive': positive_data,
                'negative': negative_data,
                'neutral': neutral_data
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/charts/source-distribution')
    def get_source_distribution():
        """Get article distribution by source"""
        try:
            db = next(get_db())
            
            # Get article counts by source
            source_counts = db.query(
                Source.name,
                db.func.count(Article.id).label('count')
            ).join(Article).group_by(Source.name).all()
            
            sources = [row[0] for row in source_counts]
            counts = [row[1] for row in source_counts]
            
            return jsonify({
                'sources': sources,
                'counts': counts
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/charts/relevance-distribution')
    def get_relevance_distribution():
        """Get relevance score distribution"""
        try:
            db = next(get_db())
            
            # Get articles with relevance scores
            articles = db.query(Article.relevance_score).filter(
                Article.relevance_score.isnot(None)
            ).all()
            
            scores = [article[0] for article in articles]
            
            # Create histogram bins
            bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
            bin_counts = [0] * (len(bins) - 1)
            
            for score in scores:
                for i in range(len(bins) - 1):
                    if bins[i] <= score < bins[i + 1]:
                        bin_counts[i] += 1
                        break
            
            bin_labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins) - 1)]
            
            return jsonify({
                'labels': bin_labels,
                'counts': bin_counts
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/search')
    def search_articles():
        """Search articles by title or content"""
        try:
            db = next(get_db())
            
            query = request.args.get('q', '')
            if not query:
                return jsonify({'articles': []})
            
            # Search in title and summary
            articles = db.query(Article).filter(
                db.or_(
                    Article.title.ilike(f'%{query}%'),
                    Article.summary.ilike(f'%{query}%')
                )
            ).order_by(Article.scraped_date.desc()).limit(20).all()
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    'id': article.id,
                    'title': article.title,
                    'summary': article.summary,
                    'url': article.url,
                    'published_date': article.published_date.isoformat() if article.published_date else None,
                    'sentiment_label': article.sentiment_label,
                    'relevance_score': article.relevance_score,
                    'source': article.source.name
                })
            
            return jsonify({'articles': articles_data})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app 