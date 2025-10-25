import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from newspaper import Article as NewspaperArticle
from .article_parser import ArticleParser
from services.utilities import clean_text, extract_domain, normalize_source_name

class NewsScraper:
    """Main news scraper for fetching articles about entities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.parser = ArticleParser()
        
    def scrape_articles(self, entity_name: str, max_articles: int = 50, 
                       days_back: int = 7) -> List[Dict]:
        """
        Scrape articles about the given entity
        
        Args:
            entity_name (str): Name of the entity to search for
            max_articles (int): Maximum number of articles to scrape
            days_back (int): Number of days back to search
            
        Returns:
            List[Dict]: List of article dictionaries
        """
        articles = []
        
        # Search queries for the entity
        search_queries = self._generate_search_queries(entity_name)
        
        for query in search_queries:
            if len(articles) >= max_articles:
                break
                
            # Scrape from different sources
            sources = self._get_news_sources()
            
            for source in sources:
                if len(articles) >= max_articles:
                    break
                    
                try:
                    source_articles = self._scrape_from_source(
                        source, query, max_articles - len(articles), days_back
                    )
                    articles.extend(source_articles)
                    time.sleep(1)  # Be respectful to servers
                    
                except Exception as e:
                    print(f"Error scraping from {source['name']}: {e}")
                    continue
        
        return articles[:max_articles]
    
    def _generate_search_queries(self, entity_name: str) -> List[str]:
        """Generate search queries for the entity"""
        queries = [
            f'"{entity_name}"',
            f'"{entity_name}" news',
            f'"{entity_name}" latest',
            f'"{entity_name}" today',
            f'"{entity_name}" coach',
            f'"{entity_name}" rams'
        ]
        
        # Add variations for Sean McVay specifically
        if 'sean mcvay' in entity_name.lower():
            queries.extend([
                '"Sean McVay" coach',
                '"Sean McVay" Rams',
                '"Sean McVay" NFL',
                'McVay coach',
                'McVay Rams'
            ])
        
        return queries
    
    def _get_news_sources(self) -> List[Dict]:
        """Get list of news sources to scrape from"""
        return [
            {
                'name': 'ESPN',
                'url': 'https://www.espn.com',
                'search_url': 'https://www.espn.com/search/results?q={query}'
            },
            {
                'name': 'NFL.com',
                'url': 'https://www.nfl.com',
                'search_url': 'https://www.nfl.com/search?query={query}'
            },
            {
                'name': 'Sports Illustrated',
                'url': 'https://www.si.com',
                'search_url': 'https://www.si.com/search?q={query}'
            },
            {
                'name': 'Bleacher Report',
                'url': 'https://bleacherreport.com',
                'search_url': 'https://bleacherreport.com/search?q={query}'
            },
            {
                'name': 'NBC Sports',
                'url': 'https://www.nbcsports.com',
                'search_url': 'https://www.nbcsports.com/search?q={query}'
            }
        ]
    
    def _scrape_from_source(self, source: Dict, query: str, 
                           max_articles: int, days_back: int) -> List[Dict]:
        """Scrape articles from a specific source"""
        articles = []
        
        try:
            # Use newspaper3k to extract articles from the source
            source_url = source['url']
            response = self.session.get(source_url, timeout=10)
            
            if response.status_code == 200:
                # Parse the main page for recent articles
                page_articles = self.parser.parse_source_page(
                    response.text, source['name'], query
                )
                
                # Filter articles by date and relevance
                filtered_articles = self._filter_articles(
                    page_articles, query, days_back
                )
                
                articles.extend(filtered_articles[:max_articles])
                
        except Exception as e:
            print(f"Error scraping from {source['name']}: {e}")
        
        return articles
    
    def _filter_articles(self, articles: List[Dict], query: str, 
                        days_back: int) -> List[Dict]:
        """Filter articles by date and relevance"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered = []
        
        for article in articles:
            # Check if article is recent enough
            if article.get('published_date'):
                if article['published_date'] < cutoff_date:
                    continue
            
            # Check if article is relevant to the query
            if self._is_article_relevant(article, query):
                filtered.append(article)
        
        return filtered
    
    def _is_article_relevant(self, article: Dict, query: str) -> bool:
        """Check if article is relevant to the search query"""
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        
        # Extract entity name from query (remove quotes)
        entity_name = query.replace('"', '').lower()
        
        # Check if entity name appears in title or summary
        if entity_name in title or entity_name in summary:
            return True
        
        # For Sean McVay, check for variations
        if 'sean mcvay' in entity_name:
            if 'mcvay' in title or 'mcvay' in summary:
                return True
        
        return False
    
    def scrape_single_article(self, url: str) -> Optional[Dict]:
        """
        Scrape a single article from its URL
        
        Args:
            url (str): URL of the article to scrape
            
        Returns:
            Optional[Dict]: Article data or None if scraping fails
        """
        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()
            
            # Extract article data
            article_data = {
                'title': clean_text(article.title),
                'summary': clean_text(article.summary),
                'content': clean_text(article.text),
                'url': url,
                'published_date': article.publish_date,
                'source_name': extract_domain(url),
                'domain': extract_domain(url)
            }
            
            return article_data
            
        except Exception as e:
            print(f"Error scraping article {url}: {e}")
            return None 